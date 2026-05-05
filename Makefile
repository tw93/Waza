PROJECT_KEY := $(shell printf '%s' "$(CURDIR)" | sed 's|[/_]|-|g; s|^-||')

.PHONY: test verify-docs verify-scripts smoke-statusline smoke-statusline-installer smoke-english-coaching-installer smoke-anti-patterns-installer smoke-verify-skills smoke-package smoke-health package

test: verify-docs verify-scripts smoke-statusline smoke-statusline-installer smoke-english-coaching-installer smoke-anti-patterns-installer smoke-verify-skills smoke-package smoke-health

verify-docs:
	./scripts/verify-skills.sh

verify-scripts:
	git diff --check
	bash -n scripts/statusline.sh skills/health/scripts/collect-data.sh skills/read/scripts/fetch.sh scripts/setup-statusline.sh scripts/setup-english-coaching.sh scripts/setup-anti-patterns.sh skills/check/scripts/run-tests.sh scripts/package-skill.sh
	echo "bash -n: ok"
	@if command -v shellcheck >/dev/null 2>&1; then \
	  shellcheck scripts/*.sh skills/*/scripts/*.sh && echo "shellcheck: ok"; \
	else \
	  echo "shellcheck: skipped (not installed)"; \
	fi
	python3 -m py_compile skills/read/scripts/fetch_feishu.py skills/read/scripts/fetch_weixin.py
	echo "py_compile: ok"
	bash skills/health/scripts/collect-data.sh auto >/tmp/waza-collect-data.out
	echo "collect-data: ok"
	rg -n "^=== CONVERSATION SIGNALS ===$$|^=== CONVERSATION EXTRACT ===$$|^=== MCP ACCESS DENIALS ===$$" /tmp/waza-collect-data.out

smoke-statusline:
	@set -e; \
	tmpdir=$$(mktemp -d); \
	json1='{"context_window":{"current_usage":{"input_tokens":10},"context_window_size":100},"rate_limits":{"five_hour":{"used_percentage":12,"resets_at":2000000000},"seven_day":{"used_percentage":34,"resets_at":2000003600}}}'; \
	json2='{"context_window":{"current_usage":{"input_tokens":20},"context_window_size":100}}'; \
	json_high='{"context_window":{"current_usage":{"input_tokens":30},"context_window_size":100},"rate_limits":{"five_hour":{"used_percentage":61,"resets_at":2000000000},"seven_day":{"used_percentage":63,"resets_at":2000003600}}}'; \
	json_low='{"context_window":{"current_usage":{"input_tokens":40},"context_window_size":100},"rate_limits":{"five_hour":{"used_percentage":1,"resets_at":2000000000},"seven_day":{"used_percentage":61,"resets_at":2000003600}}}'; \
	printf '%s' "$$json1" | HOME="$$tmpdir" bash scripts/statusline.sh >/dev/null; \
	printf '%s' "$$json2" | HOME="$$tmpdir" bash scripts/statusline.sh >"$$tmpdir/out2"; \
	printf '%s' "$$json2" | HOME="$$tmpdir" bash scripts/statusline.sh >"$$tmpdir/out3"; \
	grep -q '"used_percentage": 12' "$$tmpdir/.cache/waza-statusline/last.json"; \
	printf '%s' "$$json_high" | HOME="$$tmpdir" bash scripts/statusline.sh >/dev/null; \
	printf '%s' "$$json_low" | HOME="$$tmpdir" bash scripts/statusline.sh >"$$tmpdir/out4"; \
	grep -q '5h:' "$$tmpdir/out2"; \
	grep -q '7d:' "$$tmpdir/out2"; \
	grep -q '12%' "$$tmpdir/out2"; \
	grep -q '34%' "$$tmpdir/out3"; \
	grep -q '61%' "$$tmpdir/out4"; \
	grep -q '63%' "$$tmpdir/out4"; \
	tmpdir2=$$(mktemp -d); \
	mkdir -p "$$tmpdir2/.cache/waza-statusline"; \
	printf '%s\n' '{"seven_day":{"used_percentage":63,"resets_at":2000003600}}' > "$$tmpdir2/.cache/waza-statusline/highwater.json"; \
	printf '%s' "$$json1" | HOME="$$tmpdir2" bash scripts/statusline.sh >"$$tmpdir2/out"; \
	grep -q '12%' "$$tmpdir2/out"; \
	grep -q '63%' "$$tmpdir2/out"; \
	echo "statusline smoke: ok"

smoke-statusline-installer:
	@set -e; \
		tmpdir=$$(mktemp -d); \
		home_dir="$$tmpdir/home"; \
		bin_dir="$$tmpdir/bin"; \
		mkdir -p "$$home_dir/.claude" "$$bin_dir"; \
		ln -s "$$(command -v python3)" "$$bin_dir/python3"; \
		ln -s "$$(command -v jq)" "$$bin_dir/jq"; \
		ln -s /bin/chmod "$$bin_dir/chmod"; \
		ln -s /bin/mkdir "$$bin_dir/mkdir"; \
		printf '%s\n' '#!/bin/bash' \
			'outfile=""' \
			'while [ "$$#" -gt 0 ]; do' \
			'  if [ "$$1" = "-o" ]; then outfile="$$2"; shift 2; else shift; fi' \
			'done' \
			'printf "%s\n" "#!/bin/bash" "echo statusline" > "$$outfile"' \
			> "$$bin_dir/curl"; \
		printf '%s\n' '#!/bin/bash' \
			'echo "brew should not be called" >&2' \
			'echo "$$*" >>"$$BREW_LOG"' \
			'exit 99' \
			> "$$bin_dir/brew"; \
		chmod +x "$$bin_dir/curl" "$$bin_dir/brew"; \
		printf '%s\n' '{invalid json' > "$$home_dir/.claude/settings.json"; \
		if BREW_LOG="$$tmpdir/brew.log" PATH="$$bin_dir" HOME="$$home_dir" /bin/bash scripts/setup-statusline.sh >"$$tmpdir/install.out" 2>"$$tmpdir/install.err"; then \
			echo "setup-statusline should refuse invalid JSON"; exit 1; \
		fi; \
		grep -q 'Refusing to modify it' "$$tmpdir/install.err"; \
		grep -q 'invalid json' "$$home_dir/.claude/settings.json"; \
		test ! -f "$$tmpdir/brew.log"; \
		printf '%s\n' '{"theme":"dark"}' > "$$home_dir/.claude/settings.json"; \
		BREW_LOG="$$tmpdir/brew.log" PATH="$$bin_dir" HOME="$$home_dir" /bin/bash scripts/setup-statusline.sh >"$$tmpdir/install-valid.out" 2>"$$tmpdir/install-valid.err"; \
		python3 -c "import json, sys; data=json.load(open(sys.argv[1])); assert data['theme'] == 'dark'; assert data['statusLine']['command'] == 'bash ~/.claude/statusline.sh'" "$$home_dir/.claude/settings.json"; \
		test -x "$$home_dir/.claude/statusline.sh"; \
		test ! -f "$$tmpdir/brew.log"; \
		printf '%s\n' '{"statusLine":{"type":"command","command":"bash ~/foreign.sh"}}' > "$$home_dir/.claude/settings.json"; \
		PATH="$$bin_dir" HOME="$$home_dir" /bin/bash scripts/setup-statusline.sh </dev/null >"$$tmpdir/install-foreign.out" 2>"$$tmpdir/install-foreign.err"; \
		grep -q 'keeping existing statusline' "$$tmpdir/install-foreign.out"; \
		python3 -c "import json, sys; data=json.load(open(sys.argv[1])); assert data['statusLine']['command'] == 'bash ~/foreign.sh', data" "$$home_dir/.claude/settings.json"; \
		echo "statusline installer smoke: ok"

smoke-english-coaching-installer:
	@set -e; \
		tmpdir=$$(mktemp -d); \
		home_dir="$$tmpdir/home"; \
		bin_dir="$$tmpdir/bin"; \
		mkdir -p "$$home_dir/.codex" "$$bin_dir"; \
		ln -s "$$(command -v python3)" "$$bin_dir/python3"; \
		ln -s /bin/mkdir "$$bin_dir/mkdir"; \
		ln -s "$$(command -v mktemp)" "$$bin_dir/mktemp"; \
		ln -s /bin/rm "$$bin_dir/rm"; \
		printf '%s\n' '#!/bin/bash' \
			'outfile=""' \
			'while [ "$$#" -gt 0 ]; do' \
			'  if [ "$$1" = "-o" ]; then outfile="$$2"; shift 2; else shift; fi' \
			'done' \
			'printf "%s\n" "## English Coaching" "" "test rule" > "$$outfile"' \
			> "$$bin_dir/curl"; \
		chmod +x "$$bin_dir/curl"; \
		PATH="$$bin_dir" HOME="$$home_dir" /bin/bash scripts/setup-english-coaching.sh claude-code >"$$tmpdir/claude.out"; \
		grep -q 'test rule' "$$home_dir/.claude/rules/english.md"; \
		PATH="$$bin_dir" HOME="$$home_dir" /bin/bash scripts/setup-english-coaching.sh codex >"$$tmpdir/codex1.out"; \
		PATH="$$bin_dir" HOME="$$home_dir" /bin/bash scripts/setup-english-coaching.sh codex >"$$tmpdir/codex2.out"; \
		test "$$(grep -c '<!-- Waza English Coaching: start -->' "$$home_dir/.codex/AGENTS.md")" -eq 1; \
		grep -q 'test rule' "$$home_dir/.codex/AGENTS.md"; \
		echo "English Coaching installer smoke: ok"

smoke-anti-patterns-installer:
	@set -e; \
		tmpdir=$$(mktemp -d); \
		home_dir="$$tmpdir/home"; \
		bin_dir="$$tmpdir/bin"; \
		mkdir -p "$$home_dir/.codex" "$$bin_dir"; \
		ln -s "$$(command -v python3)" "$$bin_dir/python3"; \
		ln -s /bin/mkdir "$$bin_dir/mkdir"; \
		ln -s "$$(command -v mktemp)" "$$bin_dir/mktemp"; \
		ln -s /bin/rm "$$bin_dir/rm"; \
		printf '%s\n' '#!/bin/bash' \
			'outfile=""' \
			'while [ "$$#" -gt 0 ]; do' \
			'  if [ "$$1" = "-o" ]; then outfile="$$2"; shift 2; else shift; fi' \
			'done' \
			'printf "%s\n" "## Anti-Patterns" "" "anti-patterns rule" > "$$outfile"' \
			> "$$bin_dir/curl"; \
		chmod +x "$$bin_dir/curl"; \
		PATH="$$bin_dir" HOME="$$home_dir" /bin/bash scripts/setup-anti-patterns.sh claude-code >"$$tmpdir/claude.out"; \
		grep -q 'anti-patterns rule' "$$home_dir/.claude/rules/anti-patterns.md"; \
		PATH="$$bin_dir" HOME="$$home_dir" /bin/bash scripts/setup-anti-patterns.sh codex >"$$tmpdir/codex1.out"; \
		PATH="$$bin_dir" HOME="$$home_dir" /bin/bash scripts/setup-anti-patterns.sh codex >"$$tmpdir/codex2.out"; \
		test "$$(grep -c '<!-- Waza Anti-Patterns: start -->' "$$home_dir/.codex/AGENTS.md")" -eq 1; \
		grep -q 'anti-patterns rule' "$$home_dir/.codex/AGENTS.md"; \
		echo "Anti-Patterns installer smoke: ok"

smoke-verify-skills:
	@set -e; \
		tmpdir=$$(mktemp -d); \
		copy_repo() { mkdir -p "$$1"; tar --exclude './.git' --exclude '.git' -cf - . | (cd "$$1" && tar -xf -); }; \
		copy_repo "$$tmpdir/repo"; \
		python3 -c "from pathlib import Path; p=Path('$$tmpdir/repo/skills/check/SKILL.md'); t=p.read_text(); t=t.replace('---\n', '', 1); i=t.find('\n---\n'); p.write_text(t[:i] + t[i+5:])"; \
		if (cd "$$tmpdir/repo" && ./scripts/verify-skills.sh >"$$tmpdir/frontmatter.out" 2>"$$tmpdir/frontmatter.err"); then \
			echo "verify-skills should reject missing frontmatter delimiters"; exit 1; \
		fi; \
		grep -q 'INVALID FRONTMATTER' "$$tmpdir/frontmatter.err"; \
		copy_repo "$$tmpdir/repo2"; \
		python3 -c "import json; p='$$tmpdir/repo2/.claude-plugin/marketplace.json'; d=json.load(open(p)); d['plugins'].append({'name':'waza-ghost','description':'x','version':'1.0.0','category':'development','source':'./skills/ghost','homepage':'https://example.com'}); open(p,'w').write(json.dumps(d, indent=2) + '\n')"; \
		if (cd "$$tmpdir/repo2" && ./scripts/verify-skills.sh >"$$tmpdir/market.out" 2>"$$tmpdir/market.err"); then \
			echo "verify-skills should reject marketplace-only entries"; exit 1; \
		fi; \
		grep -q 'MISSING SKILL DIRECTORY: ghost' "$$tmpdir/market.err"; \
		copy_repo "$$tmpdir/repo3"; \
		python3 -c "import json; p='$$tmpdir/repo3/.claude-plugin/marketplace.json'; d=json.load(open(p)); [entry.update({'source':'./skills/read'}) for entry in d['plugins'] if entry['name']=='waza-check']; open(p,'w').write(json.dumps(d, indent=2) + '\n')"; \
		if (cd "$$tmpdir/repo3" && ./scripts/verify-skills.sh >"$$tmpdir/source.out" 2>"$$tmpdir/source.err"); then \
			echo "verify-skills should reject wrong source paths"; exit 1; \
		fi; \
		grep -q 'WRONG SOURCE: waza-check' "$$tmpdir/source.err"; \
		copy_repo "$$tmpdir/repo4"; \
		python3 -c "from pathlib import Path; p=Path('$$tmpdir/repo4/skills/check/SKILL.md'); p.write_text(p.read_text() + '\n[broken](missing-target.md)\n')"; \
		if (cd "$$tmpdir/repo4" && ./scripts/verify-skills.sh >"$$tmpdir/link.out" 2>"$$tmpdir/link.err"); then \
			echo "verify-skills should reject broken markdown links"; exit 1; \
		fi; \
		grep -q 'BROKEN MARKDOWN LINK' "$$tmpdir/link.err"; \
		copy_repo "$$tmpdir/repo5"; \
		printf '\n| trigger | skills/ghost/SKILL.md |\n' >> "$$tmpdir/repo5/skills/RESOLVER.md"; \
		if (cd "$$tmpdir/repo5" && ./scripts/verify-skills.sh >"$$tmpdir/resolver.out" 2>"$$tmpdir/resolver.err"); then \
			echo "verify-skills should reject stale RESOLVER references"; exit 1; \
		fi; \
		grep -q 'RESOLVER REFERENCES MISSING SKILL: ghost' "$$tmpdir/resolver.err"; \
		copy_repo "$$tmpdir/repo6"; \
		printf '\n| Col1 | Col2 |\n| --- | --- |\n| a | b | c |\n' >> "$$tmpdir/repo6/skills/check/SKILL.md"; \
		if (cd "$$tmpdir/repo6" && ./scripts/verify-skills.sh >"$$tmpdir/pipe.out" 2>"$$tmpdir/pipe.err"); then \
			echo "verify-skills should reject unescaped pipe in table data row"; exit 1; \
		fi; \
		grep -q 'UNESCAPED PIPE IN TABLE' "$$tmpdir/pipe.err"; \
		copy_repo "$$tmpdir/repo7"; \
		python3 -c "import json; p='$$tmpdir/repo7/.claude-plugin/marketplace.json'; d=json.load(open(p)); [e.update({'version':'3.0.0'}) for e in d['plugins'] if e['name']=='waza']; open(p,'w').write(json.dumps(d, indent=2) + '\n')"; \
		if (cd "$$tmpdir/repo7" && ./scripts/verify-skills.sh >"$$tmpdir/bundle.out" 2>"$$tmpdir/bundle.err"); then \
			echo "verify-skills should reject stale bundle version"; exit 1; \
		fi; \
		grep -q 'BUNDLE VERSION STALE' "$$tmpdir/bundle.err"; \
		echo "verify-skills smoke: ok"

package:
	./scripts/package-skill.sh

smoke-package:
	@set -e; \
		tmpdir=$$(mktemp -d); \
		./scripts/package-skill.sh "$$tmpdir/waza.zip" >/dev/null; \
		zipinfo -1 "$$tmpdir/waza.zip" >"$$tmpdir/manifest"; \
		grep -qx 'SKILL.md' "$$tmpdir/manifest"; \
		if grep -qiE '(^|/)skill\.md$$' "$$tmpdir/manifest" | grep -cv '^SKILL\.md$$' >/dev/null 2>&1; then true; fi; \
		test "$$(zipinfo -1 "$$tmpdir/waza.zip" | grep -ciE '(^|/)skill\.md$$')" -eq 1; \
		grep -qx 'skills/read/scripts/fetch.sh' "$$tmpdir/manifest"; \
		unzip -p "$$tmpdir/waza.zip" SKILL.md | grep -q 'SKILL: check'; \
		if unzip -p "$$tmpdir/waza.zip" SKILL.md | grep -q 'skills/check/SKILL.md'; then \
			echo "package root should not reference nested SKILL.md"; exit 1; \
		fi; \
		echo "package smoke: ok"

smoke-health:
	@set -e; \
		tmpdir=$$(mktemp -d); \
	convo_dir="$$tmpdir/.claude/projects/-$(PROJECT_KEY)"; \
	mkdir -p "$$convo_dir"; \
	printf '%s\n' '{"type":"user","message":{"content":"Please build a dashboard for sales data."}}' > "$$convo_dir/2-old.jsonl"; \
	printf '%s\n' '{"type":"user","message":{"content":"Please do not use em dashes next time."}}' >> "$$convo_dir/2-old.jsonl"; \
	printf '%s\n' '{"type":"user","message":{"content":"active session placeholder"}}' > "$$convo_dir/1-active.jsonl"; \
	HOME="$$tmpdir" bash skills/health/scripts/collect-data.sh auto > "$$tmpdir/health.out"; \
	grep -q '^=== CONVERSATION SIGNALS ===$$' "$$tmpdir/health.out"; \
	grep -q '^USER CORRECTION: Please do not use em dashes next time\.$$' "$$tmpdir/health.out"; \
	if grep -q '^USER CORRECTION: Please build a dashboard for sales data\.$$' "$$tmpdir/health.out"; then \
		echo "false positive correction detected"; exit 1; \
	fi; \
	echo "health smoke: ok"
