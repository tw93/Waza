#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/test_helpers.sh"

tmpdir=$(make_tmpdir)
json1='{"context_window":{"current_usage":{"input_tokens":10},"context_window_size":100},"rate_limits":{"five_hour":{"used_percentage":12,"resets_at":2000000000},"seven_day":{"used_percentage":34,"resets_at":2000003600}}}'
json2='{"context_window":{"current_usage":{"input_tokens":20},"context_window_size":100}}'
json_high='{"context_window":{"current_usage":{"input_tokens":30},"context_window_size":100},"rate_limits":{"five_hour":{"used_percentage":61,"resets_at":2000000000},"seven_day":{"used_percentage":63,"resets_at":2000003600}}}'
json_low='{"context_window":{"current_usage":{"input_tokens":40},"context_window_size":100},"rate_limits":{"five_hour":{"used_percentage":1,"resets_at":2000000000},"seven_day":{"used_percentage":61,"resets_at":2000003600}}}'

printf '%s' "$json1" | HOME="$tmpdir" bash "$ROOT/scripts/statusline.sh" >/dev/null
printf '%s' "$json2" | HOME="$tmpdir" bash "$ROOT/scripts/statusline.sh" >"$tmpdir/out2"
printf '%s' "$json2" | HOME="$tmpdir" bash "$ROOT/scripts/statusline.sh" >"$tmpdir/out3"
grep -q '"used_percentage": 12' "$tmpdir/.cache/waza-statusline/last.json"
printf '%s' "$json_high" | HOME="$tmpdir" bash "$ROOT/scripts/statusline.sh" >/dev/null
printf '%s' "$json_low" | HOME="$tmpdir" bash "$ROOT/scripts/statusline.sh" >"$tmpdir/out4"
grep -q '5h:' "$tmpdir/out2"
grep -q '7d:' "$tmpdir/out2"
grep -q '12%' "$tmpdir/out2"
grep -q '34%' "$tmpdir/out3"
grep -q '61%' "$tmpdir/out4"
grep -q '63%' "$tmpdir/out4"

# Existing high-water mark survives a fresh session with lower live values.
tmpdir2=$(make_tmpdir)
mkdir -p "$tmpdir2/.cache/waza-statusline"
printf '%s\n' '{"seven_day":{"used_percentage":63,"resets_at":2000003600}}' > "$tmpdir2/.cache/waza-statusline/highwater.json"
printf '%s' "$json1" | HOME="$tmpdir2" bash "$ROOT/scripts/statusline.sh" >"$tmpdir2/out"
grep -q '12%' "$tmpdir2/out"
grep -q '63%' "$tmpdir2/out"

# A lower live value may reset high-water only after a fresh API activity in
# the same session. This catches Claude-side quota corrections where resets_at
# stays unchanged but the used percentage drops.
tmpdir2a=$(make_tmpdir)
mkdir -p "$tmpdir2a/.cache/waza-statusline"
printf '%s\n' '{"_last":{"session_id":"s1","api_duration_ms":100,"output_tokens":1000},"seven_day":{"used_percentage":80,"resets_at":2000003600}}' \
  > "$tmpdir2a/.cache/waza-statusline/highwater.json"
json_fresh_drop='{"session_id":"s1","cost":{"total_api_duration_ms":110},"context_window":{"total_output_tokens":1010,"current_usage":{"input_tokens":10},"context_window_size":100},"rate_limits":{"five_hour":{"used_percentage":12,"resets_at":2000000000},"seven_day":{"used_percentage":14,"resets_at":2000003600}}}'
printf '%s' "$json_fresh_drop" | HOME="$tmpdir2a" bash "$ROOT/scripts/statusline.sh" >"$tmpdir2a/out"
grep -q '14%' "$tmpdir2a/out"
jq -e '.seven_day.used_percentage == 14 and ._last.session_id == "s1" and ._last.api_duration_ms == 110' \
  "$tmpdir2a/.cache/waza-statusline/highwater.json" >/dev/null

# A tick without live rate_limits may use cached quota, but must not advance the
# freshness marker. The next live quota response still needs to count as fresh.
tmpdir2aa=$(make_tmpdir)
mkdir -p "$tmpdir2aa/.cache/waza-statusline"
printf '%s\n' '{"_last":{"session_id":"s1","api_duration_ms":100,"output_tokens":1000},"seven_day":{"used_percentage":80,"resets_at":2000003600}}' \
  > "$tmpdir2aa/.cache/waza-statusline/highwater.json"
printf '%s\n' '{"rate_limits":{"five_hour":{"used_percentage":12,"resets_at":2000000000},"seven_day":{"used_percentage":80,"resets_at":2000003600}}}' \
  > "$tmpdir2aa/.cache/waza-statusline/last.json"
json_no_live_rate_limits='{"session_id":"s1","cost":{"total_api_duration_ms":110},"context_window":{"total_output_tokens":1010,"current_usage":{"input_tokens":10},"context_window_size":100}}'
printf '%s' "$json_no_live_rate_limits" | HOME="$tmpdir2aa" bash "$ROOT/scripts/statusline.sh" >"$tmpdir2aa/out1"
grep -q '80%' "$tmpdir2aa/out1"
jq -e '._last.api_duration_ms == 100 and ._last.output_tokens == 1000' \
  "$tmpdir2aa/.cache/waza-statusline/highwater.json" >/dev/null
printf '%s' "$json_fresh_drop" | HOME="$tmpdir2aa" bash "$ROOT/scripts/statusline.sh" >"$tmpdir2aa/out2"
grep -q '14%' "$tmpdir2aa/out2"
jq -e '.seven_day.used_percentage == 14 and ._last.api_duration_ms == 110' \
  "$tmpdir2aa/.cache/waza-statusline/highwater.json" >/dev/null

# Small fresh dips are treated as jitter, not a reset/correction.
tmpdir2b=$(make_tmpdir)
mkdir -p "$tmpdir2b/.cache/waza-statusline"
printf '%s\n' '{"_last":{"session_id":"s1","api_duration_ms":100,"output_tokens":1000},"seven_day":{"used_percentage":63,"resets_at":2000003600}}' \
  > "$tmpdir2b/.cache/waza-statusline/highwater.json"
json_small_dip='{"session_id":"s1","cost":{"total_api_duration_ms":110},"context_window":{"total_output_tokens":1010,"current_usage":{"input_tokens":10},"context_window_size":100},"rate_limits":{"five_hour":{"used_percentage":12,"resets_at":2000000000},"seven_day":{"used_percentage":61,"resets_at":2000003600}}}'
printf '%s' "$json_small_dip" | HOME="$tmpdir2b" bash "$ROOT/scripts/statusline.sh" >"$tmpdir2b/out"
grep -q '63%' "$tmpdir2b/out"
jq -e '.seven_day.used_percentage == 63 and ._last.api_duration_ms == 110' \
  "$tmpdir2b/.cache/waza-statusline/highwater.json" >/dev/null

# Empty input must not crash; both rate-limit slots fall back to "--".
tmpdir3=$(make_tmpdir)
printf '' | HOME="$tmpdir3" bash "$ROOT/scripts/statusline.sh" >"$tmpdir3/out"
grep -q '5h: --' "$tmpdir3/out"
grep -q '7d: --' "$tmpdir3/out"

# Context >= 85% must render with red ANSI (\033[31m); usage >= 90% likewise red.
tmpdir4=$(make_tmpdir)
json_hot='{"context_window":{"current_usage":{"input_tokens":90},"context_window_size":100},"rate_limits":{"five_hour":{"used_percentage":95,"resets_at":2000000000},"seven_day":{"used_percentage":10,"resets_at":2000003600}}}'
printf '%s' "$json_hot" | HOME="$tmpdir4" bash "$ROOT/scripts/statusline.sh" >"$tmpdir4/out"
grep -q $'\033\[31m90%' "$tmpdir4/out"
grep -q $'\033\[31m95%' "$tmpdir4/out"

# resets_at in the past must clear the rate-limit slot, no stale "(0m)" output.
tmpdir5=$(make_tmpdir)
json_expired='{"context_window":{"current_usage":{"input_tokens":5},"context_window_size":100},"rate_limits":{"five_hour":{"used_percentage":42,"resets_at":1000000000},"seven_day":{"used_percentage":50,"resets_at":1000003600}}}'
printf '%s' "$json_expired" | HOME="$tmpdir5" bash "$ROOT/scripts/statusline.sh" >"$tmpdir5/out"
grep -q '5h: --' "$tmpdir5/out"
grep -q '7d: --' "$tmpdir5/out"

# Stale cache (older than CACHE_MAX_AGE = 6h) must not surface as live values
# when the current input lacks rate_limits.
tmpdir6=$(make_tmpdir)
mkdir -p "$tmpdir6/.cache/waza-statusline"
printf '%s\n' '{"rate_limits":{"five_hour":{"used_percentage":77,"resets_at":2000000000},"seven_day":{"used_percentage":88,"resets_at":2000003600}}}' \
  > "$tmpdir6/.cache/waza-statusline/last.json"
touch -t 200001010000 "$tmpdir6/.cache/waza-statusline/last.json"
printf '%s' "$json2" | HOME="$tmpdir6" bash "$ROOT/scripts/statusline.sh" >"$tmpdir6/out"
grep -q '5h: --' "$tmpdir6/out"
grep -q '7d: --' "$tmpdir6/out"

echo "statusline smoke: ok"
