#!/bin/bash
# Claude Code statusline: Context % | 5h: % (reset) | 7d: % (reset)
# Set WAZA_STATUSLINE_DEBUG=1 to surface stderr (jq parse errors, missing tools).
[ "${WAZA_STATUSLINE_DEBUG:-}" = "1" ] || exec 2>/dev/null

CACHE_DIR="$HOME/.cache/waza-statusline"
CACHE_FILE="$CACHE_DIR/last.json"
HIGHWATER_FILE="$CACHE_DIR/highwater.json"
HIGHWATER_LOCK_DIR="$CACHE_DIR/highwater.lock"
CACHE_MAX_AGE=21600  # 6 hours: one full rate_limit window
HIGHWATER_LOCK_MAX_AGE=10
HIGHWATER_RESET_SKEW_MAX=7200  # tolerate session jitter, reject crossed windows
HIGHWATER_DROP_RESET_MIN=5  # fresh lower live values must drop by at least 5%

input=$(cat)

tab=$(printf '\t')

jq_full='[
  ((.context_window.current_usage.input_tokens // 0)
   + (.context_window.current_usage.cache_creation_input_tokens // 0)
   + (.context_window.current_usage.cache_read_input_tokens // 0) | tostring),
  (.context_window.context_window_size // 0 | tostring),
  (.session_id // "null" | tostring),
  (.cost.total_api_duration_ms // 0 | tonumber? // 0 | floor | tostring),
  (.context_window.total_output_tokens // 0 | tonumber? // 0 | floor | tostring),
  (.rate_limits.five_hour.used_percentage // null | if . then (. | round | tostring) else "null" end),
  (.rate_limits.five_hour.resets_at // "" | tostring),
  (.rate_limits.seven_day.used_percentage // null | if . then (. | round | tostring) else "null" end),
  (.rate_limits.seven_day.resets_at // "" | tostring)
] | @tsv'

jq_rl='[
  (.rate_limits.five_hour.used_percentage // null | if . then (. | round | tostring) else "null" end),
  (.rate_limits.five_hour.resets_at // "" | tostring),
  (.rate_limits.seven_day.used_percentage // null | if . then (. | round | tostring) else "null" end),
  (.rate_limits.seven_day.resets_at // "" | tostring)
] | @tsv'

jq_hw='[
  (.five_hour.used_percentage // null | if . then (. | round | tostring) else "null" end),
  (.five_hour.resets_at // "null" | tostring),
  (.seven_day.used_percentage // null | if . then (. | round | tostring) else "null" end),
  (.seven_day.resets_at // "null" | tostring),
  (._last.session_id // "null" | tostring),
  (._last.api_duration_ms // 0 | tonumber? // 0 | floor | tostring),
  (._last.output_tokens // 0 | tonumber? // 0 | floor | tostring)
] | @tsv'

cache_file_mtime() {
  local path="$1"
  local ts=""
  ts=$(stat -c %Y "$path" 2>/dev/null || true)
  if [ -z "$ts" ]; then
    ts=$(stat -f %m "$path" 2>/dev/null || true)
  fi
  printf '%s\n' "${ts:-0}"
}

is_uint() {
  case "$1" in
    ''|null) return 1 ;;
    *[!0-9]*) return 1 ;;
    *) return 0 ;;
  esac
}

acquire_highwater_lock() {
  mkdir -p "$CACHE_DIR" 2>/dev/null || return 1
  local attempts=0 lock_mtime now
  while [ "$attempts" -lt 5 ]; do
    attempts=$((attempts + 1))
    if mkdir "$HIGHWATER_LOCK_DIR" 2>/dev/null; then
      return 0
    fi
    lock_mtime=$(cache_file_mtime "$HIGHWATER_LOCK_DIR")
    now=$(date +%s)
    if [ $((now - lock_mtime)) -gt "$HIGHWATER_LOCK_MAX_AGE" ]; then
      rmdir "$HIGHWATER_LOCK_DIR" 2>/dev/null || true
      continue
    fi
    sleep 0.05
  done
  return 1
}

release_highwater_lock() {
  rmdir "$HIGHWATER_LOCK_DIR" 2>/dev/null || true
}

read_highwater() {
  hw_5h_pct=""
  hw_5h_reset=""
  hw_7d_pct=""
  hw_7d_reset=""
  hw_last_session_id=""
  hw_last_api_ms="0"
  hw_last_output_tokens="0"
  [ -f "$HIGHWATER_FILE" ] || return
  highwater_data=$(jq -r "$jq_hw" "$HIGHWATER_FILE" 2>/dev/null)
  IFS="$tab" read -r hw_5h_pct hw_5h_reset hw_7d_pct hw_7d_reset hw_last_session_id hw_last_api_ms hw_last_output_tokens <<EOF
$highwater_data
EOF
  [ "$hw_5h_pct" = "null" ] && hw_5h_pct=""
  [ "$hw_5h_reset" = "null" ] && hw_5h_reset=""
  [ "$hw_7d_pct" = "null" ] && hw_7d_pct=""
  [ "$hw_7d_reset" = "null" ] && hw_7d_reset=""
  [ "$hw_last_session_id" = "null" ] && hw_last_session_id=""
  is_uint "$hw_last_api_ms" || hw_last_api_ms=0
  is_uint "$hw_last_output_tokens" || hw_last_output_tokens=0
}

json_quote() {
  printf '%s' "$1" | jq -Rs . 2>/dev/null
}

compute_fresh_activity() {
  fresh_activity=0
  [ "$live_rate_limits_present" = "1" ] || return
  [ -n "$live_session_id" ] && [ "$live_session_id" != "null" ] || return
  [ "$live_session_id" = "$hw_last_session_id" ] || return
  is_uint "$live_api_ms" || live_api_ms=0
  is_uint "$live_output_tokens" || live_output_tokens=0
  is_uint "$hw_last_api_ms" || hw_last_api_ms=0
  is_uint "$hw_last_output_tokens" || hw_last_output_tokens=0
  if [ "$live_api_ms" -gt "$hw_last_api_ms" ] 2>/dev/null \
    || [ "$live_output_tokens" -gt "$hw_last_output_tokens" ] 2>/dev/null; then
    fresh_activity=1
  fi
}

# apply_hw: compares live vs high-water marks for a single counter (5h or 7d).
# Mutates four caller-scope globals by name (no return, by design):
#   applied_pct, applied_reset       : values to render in the statusline now
#   applied_hw_pct, applied_hw_reset : values to persist back to highwater.json
# Caller must read these immediately after the call; the next invocation
# clobbers them. Side effect is intentional: bash can't return composite values
# cleanly, and threading four out-params through every call site was worse.
apply_hw() {
  local live_pct="$1" live_reset="$2" hw_pct="$3" hw_reset="$4"
  local now reset_diff live_ok=0 hw_ok=0
  now=$(date +%s)

  if is_uint "$hw_reset" && [ "$hw_reset" -le "$now" ]; then
    hw_pct=""
    hw_reset=""
  fi
  if is_uint "$live_reset" && [ "$live_reset" -le "$now" ]; then
    live_pct=""
    live_reset=""
  fi
  if is_uint "$live_reset" && is_uint "$hw_reset"; then
    reset_diff=$((live_reset - hw_reset))
    [ "$reset_diff" -lt 0 ] && reset_diff=$((-reset_diff))
    if [ "$reset_diff" -gt "$HIGHWATER_RESET_SKEW_MAX" ]; then
      hw_pct=""
      hw_reset=""
    fi
  fi

  is_uint "$live_pct" && live_ok=1
  is_uint "$hw_pct" && hw_ok=1

  applied_pct=""
  applied_reset=""
  applied_hw_pct=""
  applied_hw_reset=""
  if [ "$live_ok" = "0" ] && [ "$hw_ok" = "0" ]; then
    return
  fi
  if [ "$live_ok" = "0" ]; then
    applied_pct="$hw_pct"
    applied_reset="$hw_reset"
    applied_hw_pct="$hw_pct"
    applied_hw_reset="$hw_reset"
    return
  fi
  if [ "$hw_ok" = "0" ] || [ "$live_pct" -gt "$hw_pct" ] 2>/dev/null; then
    applied_pct="$live_pct"
    applied_reset="$live_reset"
    applied_hw_pct="$live_pct"
    applied_hw_reset="$live_reset"
    return
  fi
  if [ "$fresh_activity" = "1" ] \
    && is_uint "$live_reset" && is_uint "$hw_reset" \
    && [ "$live_pct" -lt "$hw_pct" ] 2>/dev/null \
    && [ $((hw_pct - live_pct)) -ge "$HIGHWATER_DROP_RESET_MIN" ] 2>/dev/null; then
    applied_pct="$live_pct"
    applied_reset="$live_reset"
    applied_hw_pct="$live_pct"
    applied_hw_reset="$live_reset"
    return
  fi

  applied_pct="$hw_pct"
  applied_reset="${live_reset:-$hw_reset}"
  applied_hw_pct="$hw_pct"
  applied_hw_reset="$hw_reset"
}

write_highwater() {
  is_uint "$new_hw_5h_pct" || is_uint "$new_hw_7d_pct" || return
  mkdir -p "$CACHE_DIR" 2>/dev/null || return
  local r5="${new_hw_5h_reset:-0}" r7="${new_hw_7d_reset:-0}"
  local wrote=0 sid_json
  is_uint "$r5" || r5=0
  is_uint "$r7" || r7=0
  if ! {
    {
      printf '{\n'
      if [ "$live_rate_limits_present" = "1" ] \
        && [ -n "$live_session_id" ] && [ "$live_session_id" != "null" ]; then
        sid_json=$(json_quote "$live_session_id")
        printf '  "_last": {"session_id": %s, "api_duration_ms": %s, "output_tokens": %s}' \
          "${sid_json:-\"\"}" "${live_api_ms:-0}" "${live_output_tokens:-0}"
        wrote=1
      elif [ -n "$hw_last_session_id" ]; then
        sid_json=$(json_quote "$hw_last_session_id")
        printf '  "_last": {"session_id": %s, "api_duration_ms": %s, "output_tokens": %s}' \
          "${sid_json:-\"\"}" "${hw_last_api_ms:-0}" "${hw_last_output_tokens:-0}"
        wrote=1
      fi
      if is_uint "$new_hw_5h_pct"; then
        [ "$wrote" = "1" ] && printf ',\n'
        printf '  "five_hour": {"used_percentage": %s, "resets_at": %s}' "$new_hw_5h_pct" "$r5"
        wrote=1
      fi
      if is_uint "$new_hw_7d_pct"; then
        [ "$wrote" = "1" ] && printf ',\n'
        printf '  "seven_day": {"used_percentage": %s, "resets_at": %s}\n' "$new_hw_7d_pct" "$r7"
      else
        printf '\n'
      fi
      printf '}\n'
    } > "${HIGHWATER_FILE}.tmp" 2>/dev/null \
      && mv "${HIGHWATER_FILE}.tmp" "$HIGHWATER_FILE" 2>/dev/null
  }; then
    :
  fi
}

apply_highwater_all() {
  read_highwater
  compute_fresh_activity

  apply_hw "$five_pct" "$five_reset" "$hw_5h_pct" "$hw_5h_reset"
  five_pct="$applied_pct"
  five_reset="$applied_reset"
  new_hw_5h_pct="$applied_hw_pct"
  new_hw_5h_reset="$applied_hw_reset"

  apply_hw "$seven_pct" "$seven_reset" "$hw_7d_pct" "$hw_7d_reset"
  seven_pct="$applied_pct"
  seven_reset="$applied_reset"
  new_hw_7d_pct="$applied_hw_pct"
  new_hw_7d_reset="$applied_hw_reset"
}

# Single jq pass for live input
parsed=""
[ -n "$input" ] && parsed=$(printf '%s' "$input" | jq -r "$jq_full" 2>/dev/null)

IFS="$tab" read -r used_tokens window_size live_session_id live_api_ms live_output_tokens live_five_pct live_five_reset live_seven_pct live_seven_reset <<EOF
$parsed
EOF

live_session_id="${live_session_id:-}"
[ "$live_session_id" = "null" ] && live_session_id=""
live_api_ms="${live_api_ms:-0}"
live_output_tokens="${live_output_tokens:-0}"
five_pct="${live_five_pct:-}"
five_reset="${live_five_reset:-}"
seven_pct="${live_seven_pct:-}"
seven_reset="${live_seven_reset:-}"
live_rate_limits_present=0
if { [ "$five_pct" != "null" ] && [ -n "$five_pct" ]; } \
  || { [ "$seven_pct" != "null" ] && [ -n "$seven_pct" ]; }; then
  live_rate_limits_present=1
fi

# If rate_limits missing from live input, read from cache
if [ "$five_pct" = "null" ] || [ -z "$five_pct" ]; then
  if [ -f "$CACHE_FILE" ]; then
    cache_mtime=$(cache_file_mtime "$CACHE_FILE")
    cache_age=$(( $(date +%s) - cache_mtime ))
    if [ "$cache_age" -lt "$CACHE_MAX_AGE" ]; then
      cached=$(jq -r "$jq_rl" "$CACHE_FILE" 2>/dev/null)
      IFS="$tab" read -r five_pct five_reset seven_pct seven_reset <<EOF
$cached
EOF
    fi
  fi
fi

# Persist live rate_limits only when present (atomic write)
if [ "${live_five_pct:-}" != "null" ] && [ -n "${live_five_pct:-}" ] && [ -n "$input" ]; then
  mkdir -p "$CACHE_DIR"
  if ! {
    printf '%s' "$input" | jq '{rate_limits: .rate_limits}' \
      > "${CACHE_FILE}.tmp" 2>/dev/null \
      && mv "${CACHE_FILE}.tmp" "$CACHE_FILE" 2>/dev/null
  }; then
    :
  fi
fi

new_hw_5h_pct=""
new_hw_5h_reset=""
new_hw_7d_pct=""
new_hw_7d_reset=""
if acquire_highwater_lock; then
  apply_highwater_all
  write_highwater
  release_highwater_lock
else
  apply_highwater_all
fi

# --- Colors ---
RESET="\033[0m"
DIM="\033[2m"
GREEN="\033[32m"
YELLOW="\033[33m"
RED="\033[31m"
BLUE="\033[94m"
MAGENTA="\033[95m"

# Format seconds remaining as "4h23m" or "1d21h"
format_reset() {
  local ts="$1"
  [ -z "$ts" ] && return
  local epoch now diff
  epoch=$(printf '%s' "$ts" | tr -dc '0-9')
  [ -z "$epoch" ] && return
  now=$(date +%s)
  diff=$((epoch - now))
  [ "$diff" -le 0 ] && return
  local mins=$(( diff / 60 ))
  local hours=$(( mins / 60 ))
  local days=$(( hours / 24 ))
  if [ "$days" -ge 1 ]; then
    printf "%dd%dh" "$days" $(( hours % 24 ))
  elif [ "$hours" -ge 1 ]; then
    printf "%dh%dm" "$hours" $(( mins % 60 ))
  else
    printf "%dm" "$mins"
  fi
}

# Context %
ctx_pct=0
if [ "$window_size" -gt 0 ] 2>/dev/null; then
  ctx_pct=$(awk -v u="${used_tokens:-0}" -v t="$window_size" 'BEGIN { printf "%d", (u/t)*100 }')
fi
if [ "$ctx_pct" -ge 85 ] 2>/dev/null; then
  ctx_color="$RED"
elif [ "$ctx_pct" -ge 70 ] 2>/dev/null; then
  ctx_color="$YELLOW"
else
  ctx_color="$GREEN"
fi
context_part="${DIM}Context${RESET} ${ctx_color}${ctx_pct}%${RESET}"

# Usage color
usage_color() {
  local pct="$1"
  if [ "$pct" -ge 90 ] 2>/dev/null; then printf "%s" "$RED"
  elif [ "$pct" -ge 70 ] 2>/dev/null; then printf "%s" "$MAGENTA"
  else printf "%s" "$BLUE"
  fi
}

# 5h part
if [ "$five_pct" != "null" ] && [ -n "$five_pct" ]; then
  color=$(usage_color "$five_pct")
  reset_str=$(format_reset "$five_reset")
  if [ -n "$reset_str" ]; then
    five_part="${DIM}5h:${RESET} ${color}${five_pct}%${RESET} ${DIM}(${reset_str})${RESET}"
  else
    five_part="${DIM}5h:${RESET} ${color}${five_pct}%${RESET}"
  fi
else
  five_part="${DIM}5h: --${RESET}"
fi

# 7d part
if [ "$seven_pct" != "null" ] && [ -n "$seven_pct" ]; then
  color=$(usage_color "$seven_pct")
  reset_str=$(format_reset "$seven_reset")
  if [ -n "$reset_str" ]; then
    seven_part="${DIM}7d:${RESET} ${color}${seven_pct}%${RESET} ${DIM}(${reset_str})${RESET}"
  else
    seven_part="${DIM}7d:${RESET} ${color}${seven_pct}%${RESET}"
  fi
else
  seven_part="${DIM}7d: --${RESET}"
fi

printf "%b | %b | %b\n" "$context_part" "$five_part" "$seven_part"
