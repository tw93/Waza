PROJECT_KEY := $(shell printf '%s' "$(CURDIR)" | sed 's|[/_]|-|g; s|^-||')

.PHONY: test verify-docs verify-scripts smoke-statusline smoke-statusline-installer smoke-verify-skills smoke-health

test: verify-docs verify-scripts smoke-statusline smoke-statusline-installer smoke-verify-skills smoke-health

verify-docs:
	./scripts/verify-skills.sh

verify-scripts:
	git diff --check
	bash -n scripts/statusline.sh skills/health/scripts/collect-data.sh skills/read/scripts/fetch.sh scripts/setup-statusline.sh skills/check/scripts/run-tests.sh
	echo "bash -n: ok"
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
	printf '%s' "$$json1" | HOME="$$tmpdir" bash scripts/statusline.sh >/dev/null; \
	printf '%s' "$$json2" | HOME="$$tmpdir" bash scripts/statusline.sh >"$$tmpdir/out2"; \
	printf '%s' "$$json2" | HOME="$$tmpdir" bash scripts/statusline.sh >"$$tmpdir/out3"; \
	grep -q '"used_percentage": 12' "$$tmpdir/.cache/waza-statusline/last.json"; \
	grep -q '5h:' "$$tmpdir/out2"; \
	grep -q '7d:' "$$tmpdir/out2"; \
	grep -q '12%' "$$tmpdir/out2"; \
	grep -q '34%' "$$tmpdir/out3"; \
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
		echo "statusline installer smoke: ok"

smoke-verify-skills:
	@set -e; \
		tmpdir=$$(mktemp -d); \
		cp -R . "$$tmpdir/repo"; \
		python3 -c "from pathlib import Path; p=Path('$$tmpdir/repo/skills/check/SKILL.md'); t=p.read_text(); t=t.replace('---\n', '', 1); i=t.find('\n---\n'); p.write_text(t[:i] + t[i+5:])"; \
		if (cd "$$tmpdir/repo" && ./scripts/verify-skills.sh >"$$tmpdir/frontmatter.out" 2>"$$tmpdir/frontmatter.err"); then \
			echo "verify-skills should reject missing frontmatter delimiters"; exit 1; \
		fi; \
		grep -q 'INVALID FRONTMATTER' "$$tmpdir/frontmatter.err"; \
		cp -R . "$$tmpdir/repo2"; \
		python3 -c "import json; p='$$tmpdir/repo2/.claude-plugin/marketplace.json'; d=json.load(open(p)); d['plugins'].append({'name':'ghost','description':'x','version':'1.0.0','category':'development','source':'./skills/ghost','homepage':'https://example.com'}); open(p,'w').write(json.dumps(d, indent=2) + '\n')"; \
		if (cd "$$tmpdir/repo2" && ./scripts/verify-skills.sh >"$$tmpdir/market.out" 2>"$$tmpdir/market.err"); then \
			echo "verify-skills should reject marketplace-only entries"; exit 1; \
		fi; \
		grep -q 'MISSING SKILL DIRECTORY: ghost' "$$tmpdir/market.err"; \
		cp -R . "$$tmpdir/repo3"; \
		python3 -c "import json; p='$$tmpdir/repo3/.claude-plugin/marketplace.json'; d=json.load(open(p)); [entry.update({'source':'./skills/read'}) for entry in d['plugins'] if entry['name']=='check']; open(p,'w').write(json.dumps(d, indent=2) + '\n')"; \
		if (cd "$$tmpdir/repo3" && ./scripts/verify-skills.sh >"$$tmpdir/source.out" 2>"$$tmpdir/source.err"); then \
			echo "verify-skills should reject wrong source paths"; exit 1; \
		fi; \
		grep -q 'WRONG SOURCE: check' "$$tmpdir/source.err"; \
		cp -R . "$$tmpdir/repo4"; \
		python3 -c "import re; from pathlib import Path; p=Path('$$tmpdir/repo4/skills/check/SKILL.md'); lines=p.read_text().splitlines(); out=[]; injected=False;\
[(out.append(l), out.append('| broken | cell with | extra pipe | bad |')) if (not injected and re.match(r'^[\s|:\-]+\$$', l.strip()) and '---' in l and '|' in l) else out.append(l) for l in lines]; injected=True if any('extra pipe' in o for o in out) else False; p.write_text('\n'.join(out) + '\n')"; \
		if (cd "$$tmpdir/repo4" && ./scripts/verify-skills.sh >"$$tmpdir/pipe.out" 2>"$$tmpdir/pipe.err"); then \
			echo "verify-skills should reject unescaped pipe in table data row"; exit 1; \
		fi; \
		grep -q 'UNESCAPED PIPE IN TABLE' "$$tmpdir/pipe.err"; \
		cp -R . "$$tmpdir/repo5"; \
		printf '\n| trigger | skills/ghost/SKILL.md |\n' >> "$$tmpdir/repo5/skills/RESOLVER.md"; \
		if (cd "$$tmpdir/repo5" && ./scripts/verify-skills.sh >"$$tmpdir/resolver.out" 2>"$$tmpdir/resolver.err"); then \
			echo "verify-skills should reject stale RESOLVER references"; exit 1; \
		fi; \
		grep -q 'RESOLVER REFERENCES MISSING SKILL: ghost' "$$tmpdir/resolver.err"; \
		cp -R . "$$tmpdir/repo6"; \
		python3 -c "from pathlib import Path; p=Path('$$tmpdir/repo6/skills/check/SKILL.md'); p.write_text(p.read_text() + '\n[broken](missing-target.md)\n')"; \
		if (cd "$$tmpdir/repo6" && ./scripts/verify-skills.sh >"$$tmpdir/link.out" 2>"$$tmpdir/link.err"); then \
			echo "verify-skills should reject broken markdown links"; exit 1; \
		fi; \
		grep -q 'BROKEN MARKDOWN LINK' "$$tmpdir/link.err"; \
		echo "verify-skills smoke: ok"

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
