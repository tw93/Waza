PROJECT_KEY := $(shell printf '%s' "$(CURDIR)" | sed 's|[/_]|-|g; s|^-||')

# Discover test_*.sh files automatically; test_helpers.sh is a shared library,
# not a runnable test, so it's filtered out before turning the path into a
# smoke-<name> target.
TEST_FILES := $(filter-out tests/test_helpers.sh,$(wildcard tests/test_*.sh))
SMOKE_TESTS := $(patsubst tests/test_%.sh,smoke-%,$(TEST_FILES))

.PHONY: test verify-docs verify-generated verify-scripts verify-routing verify-unit package regenerate $(SMOKE_TESTS)

test: verify-docs verify-generated verify-routing verify-scripts verify-unit $(SMOKE_TESTS)

verify-docs:
	python3 scripts/verify_skills.py --root .

# Python unit tests. Live in tests/python/ and target the small pure-logic
# pieces of verify_skills and build_metadata that the shell smoke tests
# cannot exercise directly. Skipped gracefully if pytest is not installed.
verify-unit:
	@if python3 -c "import pytest" 2>/dev/null; then \
	  python3 -m pytest tests/python/ -q; \
	else \
	  echo "verify-unit: skipped (pytest not installed; run: pip install --user pytest)"; \
	fi

# Regenerate marketplace.json (and any future generated files) from VERSION +
# SKILL.md frontmatter. Single source of truth lives there.
regenerate:
	python3 scripts/build_metadata.py

verify-generated:
	python3 scripts/build_metadata.py --check

verify-routing:
	python3 scripts/check_routing_drift.py --root .

verify-scripts:
	git diff --check
	bash -n scripts/statusline.sh scripts/check-update.sh skills/*/scripts/check-update.sh skills/health/scripts/collect-data.sh skills/health/scripts/check-agent-context.sh skills/health/scripts/check-doc-refs.sh skills/health/scripts/check-maintainability.sh skills/health/scripts/check-verifier-output.sh skills/read/scripts/fetch.sh scripts/setup-statusline.sh scripts/setup-rule.sh skills/check/scripts/run-tests.sh skills/write/scripts/check-punctuation.sh scripts/package-skill.sh
	echo "bash -n: ok"
	bash -n $(TEST_FILES) tests/test_helpers.sh
	echo "bash -n tests/: ok"
	@if command -v shellcheck >/dev/null 2>&1; then \
	  shellcheck scripts/*.sh skills/*/scripts/*.sh && echo "shellcheck: ok"; \
	else \
	  echo "shellcheck: skipped (not installed)"; \
	fi
	python3 -m py_compile \
	  scripts/verify_skills.py \
	  scripts/skill_frontmatter.py \
	  scripts/skill_checks.py \
	  scripts/build_metadata.py \
	  scripts/packaging_filter.py \
	  scripts/check_routing_drift.py \
	  scripts/validate_package.py \
	  skills/read/scripts/fetch_feishu.py \
	  skills/read/scripts/fetch_weixin.py \
	  skills/read/scripts/fetch_local.py \
	  skills/check/scripts/audit_signals.py \
	  skills/health/scripts/check_doc_refs.py \
	  skills/health/scripts/check_verifier_output.py \
	  skills/health/scripts/check_agent_context.py \
	  skills/health/scripts/check_maintainability.py \
	  skills/write/scripts/check_punctuation.py
	echo "py_compile: ok"
	bash skills/health/scripts/collect-data.sh auto >/tmp/waza-collect-data.out
	echo "collect-data: ok"
	rg -n "^=== CONVERSATION SIGNALS ===$$|^=== CONVERSATION EXTRACT ===$$|^=== MCP ACCESS DENIALS ===$$" /tmp/waza-collect-data.out
	rg -n "^=== AGENT CONFIG SUMMARY ===$$|^=== AGENT INSTRUCTION SURFACE ===$$|^=== CODEX SURFACE ===$$" /tmp/waza-collect-data.out
	rg -n "^=== AI MAINTAINABILITY SUMMARY ===$$|^maintainability_status: " /tmp/waza-collect-data.out

# Static pattern rule binds every smoke-<name> phony target to its sibling
# tests/test_<name>.sh script. Each script is self-contained, sources
# test_helpers.sh for tmpdir/copy_repo, and echoes its own "ok" line at the
# end. Static pattern rules behave correctly with .PHONY on GNU Make 3.81
# (which macOS still ships); a plain `smoke-%:` pattern rule does not.
$(SMOKE_TESTS): smoke-%: tests/test_%.sh
	bash $<

package:
	./scripts/package-skill.sh
