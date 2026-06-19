"""Unit tests for build_metadata codegen helpers.

These are the pure functions inside the codegen pipeline. Full drift detection
is covered by the shell smoke (tests/test_codegen.sh); here we test the small
transforms.
"""

import build_metadata as bm


def test_render_readme_rewrites_main_to_latest_asset():
    body = "curl https://raw.githubusercontent.com/tw93/Waza/main/scripts/setup-rule.sh"
    out = bm.render_readme(body, "9.9.9")
    assert "https://github.com/tw93/Waza/releases/latest/download/setup-rule.sh" in out
    assert "raw.githubusercontent.com" not in out


def test_render_readme_rewrites_pinned_version_to_latest_asset():
    body = "curl https://raw.githubusercontent.com/tw93/Waza/v1.2.3/scripts/setup-rule.sh"
    out = bm.render_readme(body, "9.9.9")
    assert "https://github.com/tw93/Waza/releases/latest/download/setup-rule.sh" in out
    assert "v1.2.3" not in out


def test_render_readme_no_change_when_already_latest_asset():
    body = "curl https://github.com/tw93/Waza/releases/latest/download/setup-rule.sh"
    assert bm.render_readme(body, "9.9.9") == body


def test_render_script_ref_pins_main():
    body = 'WAZA_REF="${WAZA_REF:-main}"'
    out = bm.render_script_ref(body, "9.9.9")
    assert out == 'WAZA_REF="${WAZA_REF:-v9.9.9}"'


def test_render_script_ref_repins_old_version():
    body = 'WAZA_REF="${WAZA_REF:-v1.2.3}"'
    out = bm.render_script_ref(body, "9.9.9")
    assert out == 'WAZA_REF="${WAZA_REF:-v9.9.9}"'


def test_render_dispatcher_injects_table():
    template = """# Header

## Routing

<!-- routing-table:start -->
<!-- routing-table:end -->

## Footer
"""
    skills = [
        {"name": "alpha", "dispatch_intent": "first thing"},
        {"name": "beta", "dispatch_intent": "second thing"},
    ]
    out = bm.render_dispatcher(template, skills)
    assert "| first thing | alpha | `skills/alpha/SKILL.md` |" in out
    assert "| second thing | beta | `skills/beta/SKILL.md` |" in out
    assert "<!-- routing-table:start -->" in out
    assert "<!-- routing-table:end -->" in out
    # Original Header and Footer preserved.
    assert "# Header" in out
    assert "## Footer" in out


def test_render_dispatcher_alphabetical():
    template = "<!-- routing-table:start -->\n<!-- routing-table:end -->"
    skills = [
        {"name": "zebra", "dispatch_intent": "z"},
        {"name": "apple", "dispatch_intent": "a"},
    ]
    out = bm.render_dispatcher(template, skills)
    apple_idx = out.index("apple")
    zebra_idx = out.index("zebra")
    assert apple_idx < zebra_idx


def test_build_codex_plugin_manifest_shape():
    manifest = bm.build_codex_plugin("9.9.9")
    assert manifest["name"] == "waza"
    assert manifest["version"] == "9.9.9"
    assert manifest["skills"] == "./skills/"
    assert manifest["interface"]["displayName"] == "Waza"
    assert manifest["interface"]["category"] == "Developer Tools"
    assert len(manifest["interface"]["defaultPrompt"]) <= 3


def test_build_codex_marketplace_points_at_plugin_root():
    marketplace = bm.build_codex_marketplace()
    assert marketplace["name"] == "waza"
    entry = marketplace["plugins"][0]
    assert entry["name"] == "waza"
    assert entry["source"] == {"source": "local", "path": "./plugins/waza"}
    assert entry["policy"] == {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL",
    }
    assert entry["category"] == "Developer Tools"


def test_collect_codex_plugin_tree_ignores_local_cache_files(tmp_path):
    skill_script_dir = tmp_path / "skills" / "check" / "scripts"
    skill_script_dir.mkdir(parents=True)
    (skill_script_dir / "run.py").write_text("print('ok')\n")
    cache_dir = skill_script_dir / "__pycache__"
    cache_dir.mkdir()
    (cache_dir / "run.cpython-314.pyc").write_bytes(b"cache")

    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()
    (rules_dir / "waza-routing.md").write_text("routing\n")
    (rules_dir / ".DS_Store").write_bytes(b"noise")

    tree = bm.collect_codex_plugin_tree(tmp_path, "{}\n", {})

    assert "plugins/waza/skills/check/scripts/run.py" in tree
    assert "plugins/waza/rules/waza-routing.md" in tree
    assert all("__pycache__" not in path for path in tree)
    assert all(not path.endswith((".pyc", ".DS_Store")) for path in tree)


def test_collect_skill_update_scripts_copies_checker_to_each_skill(tmp_path):
    for name in ("check", "think"):
        skill_dir = tmp_path / "skills" / name
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("---\nname: x\n---\n")

    tree = bm.collect_skill_update_scripts(tmp_path, "checker\n")

    assert tree == {
        "skills/check/scripts/check-update.sh": b"checker\n",
        "skills/think/scripts/check-update.sh": b"checker\n",
    }
