<div align="center">
  <img src="https://raw.githubusercontent.com/tw93/Waza/main/assets/logo.svg" width="120" />
  <h1>Waza</h1>
  <p><b>Tw93s Entwicklergewohnheiten, als Skills für deine Agenten</b></p>
  <p><a href="README.md">English</a> · <a href="README_CN.md">中文</a> · <a href="README_TW.md">繁體</a> · <a href="README_JA.md">日本語</a> · <a href="README_KR.md">한국어</a> · Deutsch · <a href="README_FR.md">Français</a></p>
  <a href="https://github.com/tw93/Waza/actions/workflows/test.yml"><img src="https://img.shields.io/github/actions/workflow/status/tw93/Waza/test.yml?branch=main&style=flat-square&label=tests" alt="Tests"></a>
  <a href="https://github.com/tw93/Waza/stargazers"><img src="https://img.shields.io/github/stars/tw93/Waza?style=flat-square" alt="Stars"></a>
  <a href="https://github.com/tw93/Waza/releases"><img src="https://img.shields.io/github/v/tag/tw93/Waza?label=version&style=flat-square" alt="Version"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square" alt="License"></a>
  <a href="https://twitter.com/HiTw93"><img src="https://img.shields.io/badge/follow-Tw93-red?style=flat-square&logo=Twitter" alt="Twitter"></a>
</div>

<br/>

<div align="center">
  <img src="assets/waza_skills.svg" width="1000" />
</div>

## Skills

Jede Entwicklergewohnheit entspricht einem eigenständigen Skill, einem Ordner mit Referenzdokumenten, Skripten und Fallstricken aus echten Fehlschlägen. In Claude Code rufst du ihn per Slash-Befehl auf, in Codex direkt über den Skill-Namen.

| Skill | Wann nutzen | Was er tut |
| :--- | :--- | :--- |
| [`/think`](skills/think/SKILL.md) | Vor neuem Code | Hinterfragt Anforderungen und erstellt direkt umsetzbare, entscheidungsreife Pläne. |
| [`/ui`](skills/ui/SKILL.md) | Frontend-UIs bauen | Entwickelt unverwechselbare UIs mit klarer gestalterischer Richtung statt Standard-Vorlagen, auf Wunsch auch mit Iteration anhand von Screenshots. |
| [`/check`](skills/check/SKILL.md) | Nach einer Aufgabe, vor Merge oder Release | Prüft Diffs gegen Projektvorgaben, verifiziert Ergebnisse und übernimmt freigegebene Release- und Maintainer-Aufgaben. |
| [`/hunt`](skills/hunt/SKILL.md) | Bugs und Regressionen | Systematisches Debugging: Ursache klären, bevor Code geändert wird, besonders wenn etwas vorher funktioniert hat. |
| [`/write`](skills/write/SKILL.md) | Texte schreiben oder feilen | Formuliert chinesische und englische Texte natürlich um, entfernt hölzernen KI-Ton. |
| [`/learn`](skills/learn/SKILL.md) | Unbekannte Themen erforschen | Recherche in sechs Phasen: sammeln, verdichten, gliedern, ausarbeiten, überarbeiten, dann selbst prüfen und veröffentlichen. |
| [`/read`](skills/read/SKILL.md) | Webseiten oder PDFs lesen | Erstellt prägnante Zusammenfassungen oder sauberes Markdown für Zitate und Notizen. |
| [`/health`](skills/health/SKILL.md) | Agenten-Konfiguration prüfen | Prüft Agenten-Konfiguration und Anweisungs-Drift, zuerst als ressourcenschonende Übersicht, dann im Detail. |

## Installation

**Claude Code, Codex, Cursor und andere Agenten**

```bash
npx skills add tw93/Waza -a claude-code codex cursor -g -y
```

Skills landen zentral in `~/.agents/skills`. Claude Code bindet sie per Symlink ein; Codex, Cursor, Gemini CLI, Copilot, Amp, Kimi Code CLI und alle Agenten, die dieses Verzeichnis nutzen, laden die 8 Skills automatisch. Agenten mit eigenem Skill-Verzeichnis gibst du nach `-a` mit ihrer ID an (zum Beispiel `antigravity-cli` oder `qwen-code`). Aktualisierung über `npx skills update -g -y`. Du kannst deinen Agenten auch direkt mit der Installation beauftragen:
> Lies https://github.com/tw93/Waza/blob/main/llms.txt und installiere Waza für mich

**Host-Plugin-Methode** (Skills erhalten einen Namespace-Präfix, z. B. `/waza:check`):

```bash
# Claude Code (Update: claude plugin update waza)
/plugin marketplace add tw93/Waza
/plugin install waza@waza

# Codex (Update: codex plugin marketplace upgrade waza, dann codex plugin add waza@waza)
codex plugin marketplace add tw93/Waza
codex plugin add waza@waza
```

**Claude Desktop**: Lade [waza.zip](https://github.com/tw93/Waza/releases/latest/download/waza.zip) herunter, öffne Customize > Skills > "+" > Create skill und lade die ZIP-Datei hoch. Zum Aktualisieren klickst du auf der Skill-Karte auf "...", wählst Replace und lädst die neueste ZIP-Datei hoch.

**Pi**: `pi install npm:@tw93/waza`, Update über `pi update npm:@tw93/waza`.

## Skill-Kombinationen

Du entscheidest, wie Skills kombiniert werden. Jeder Skill stoppt nach Erreichen des Zielergebnisses; autorisierte Workflows laufen nahtlos durch.

**Typische Workflows:**

- **Neues Feature**: `/think` prüft den Plan, nach Freigabe implementieren, dann mit `/check` prüfen und mergen
- **Bugfix**: `/hunt` findet die Ursache, dann beheben, dann mit `/check` die Diffs prüfen und bei Bedarf releasen
- **Recherche**: `/read` holt das Material, `/learn` strukturiert es, `/write` formuliert aus

## Projekt-Kontext

Waza liefert universelle Entwicklergewohnheiten. `/check` liest zur Laufzeit nur öffentliche Projektdateien (README, Paketdefinitionen, Makefile, CI-Workflows) und deine Vorgaben, niemals private Pfade, Zugangsdaten oder Tokens. Die Vorlage für den Review-Kontext findest du in [`skills/check/references/project-context.md`](skills/check/references/project-context.md).

## Extras

Die curl-URLs verwenden das neueste GitHub-Release-Asset. Für die neuesten Skripte von main setzt du `WAZA_REF=main` vor den Befehl.

### Statusleiste

Minimale Statusleiste für Claude Code: Kontext-Window, 5-Stunden- und 7-Tage-Kontingente farbcodiert, ohne Fortschrittsbalken und ohne Ablenkung.

<div align="center">
  <img src="https://raw.githubusercontent.com/tw93/Waza/main/assets/statusline.png" width="1000" />
</div>

```bash
(
  set -e
  WAZA_STATUSLINE_SCRIPT="$(mktemp -t waza-statusline.XXXXXX)"
  trap 'rm -f "$WAZA_STATUSLINE_SCRIPT"' EXIT
  curl -fL https://github.com/tw93/Waza/releases/latest/download/setup-statusline.sh -o "$WAZA_STATUSLINE_SCRIPT"
  # vorher prüfen: less "$WAZA_STATUSLINE_SCRIPT"
  bash "$WAZA_STATUSLINE_SCRIPT"
)
```

**Codex**-Statuszeile in `~/.codex/config.toml`:

```toml
[tui]
status_line = ["model-with-reasoning", "current-dir", "context-used", "five-hour-limit", "weekly-limit"]
status_line_use_colors = true
```

Codex zeigt das verbleibende Kontingent, die Claude-Code-Statusleiste oben den verbrauchten Anteil (upstream gibt es `five-hour-used` / `weekly-used` noch nicht).

### Optionale Regeln

Optionale Regeln wirken auch außerhalb von Skill-Aufrufen, sobald sie in den dauerhaften Anweisungen deines Agenten installiert sind. Die Installation der Waza-Skills allein aktiviert sie nicht. Kopiere die gewünschten Befehle (bei Codex oder Antigravity ersetzt du `claude-code` durch `codex` bzw. `antigravity-cli`):

```bash
(
  set -e
  WAZA_RULE_SCRIPT="$(mktemp -t waza-rule.XXXXXX)"
  trap 'rm -f "$WAZA_RULE_SCRIPT"' EXIT
  curl -fL https://github.com/tw93/Waza/releases/latest/download/setup-rule.sh -o "$WAZA_RULE_SCRIPT"
  # vorher prüfen: less "$WAZA_RULE_SCRIPT"

  # Englisch-Coaching: Kurze Korrekturhinweise bei Formulierungsfehlern
  bash "$WAZA_RULE_SCRIPT" english claude-code

  # Anti-Patterns: Verhindert voreilige Änderungen und überflüssige Zusammenfassungen
  bash "$WAZA_RULE_SCRIPT" anti-patterns claude-code

  # Skill-Routing: Bevorzugt Waza-Skills bei passenden Anfragen
  bash "$WAZA_RULE_SCRIPT" waza-routing claude-code

  # Klare Antworten: Verständliche Kommunikation basierend auf ASD-STE100
  # Clarity ist auf main verfügbar, aber noch nicht im aktuellen Release
  WAZA_REF=main bash "$WAZA_RULE_SCRIPT" clarity claude-code
)
```

[Clarity](rules/clarity.md) übernimmt Prinzipien für klares Schreiben aus ASD-STE100, ohne die Grammatik von kontrolliertem Englisch vorzuschreiben oder deinen Stil zu ändern. Führe den Befehl erneut aus, um die installierte Regel zu aktualisieren, und starte danach eine neue Sitzung. Codex installiert einen markierten Block in `~/.codex/AGENTS.md`; Claude Code und Antigravity installieren eine Regeldatei. Bei anderen Tools kopierst du die Regel in deren dauerhafte benutzerdefinierte Anweisungen.

<div align="center">
  <img src="https://raw.githubusercontent.com/tw93/Waza/main/assets/clarity.png" width="1000" />
</div>

## Warum Waza

Waza (技, わざ) bezeichnet in den Kampfkünsten eine Technik, die durch ständiges Üben zur instinktiven Gewohnheit wird. Gute Entwickler schreiben nicht nur Code. Sie hinterfragen Anforderungen, debuggen bis zur Ursache, prüfen ihre eigenen Diffs und lesen Primärquellen. KI kann all das leisten, driftet ohne Struktur aber ins Beliebige und Ungenaue ab. Jeder Waza-Skill legt das Ziel, die roten Linien und die Art der Überprüfung fest und überlässt den Lösungsweg dem Modell. Je besser die Modelle werden, desto mehr zahlt sich diese Zurückhaltung aus.

Tools wie Superpowers und gstack sind mächtig, aber schwer: zu viele Skills, zu viel Konfiguration. Waza bleibt klein, acht Skills für die Gewohnheiten, die wirklich zählen, jeder mit einer Aufgabe und einem klaren Auslöser. Waza ist aus echten Projekten entstanden und in über 300 Sitzungen über 7 Projekte hinweg verfeinert worden, jeder Fallstrick geht auf einen echten Fehlschlag zurück. Der `/health`-Skill ist aus dem sechsschichtigen Claude-Code-Framework aus [diesem Beitrag](https://tw93.fun/en/2026-03-12/claude.html) entstanden.

Teil einer Trilogie: [Kaku](https://github.com/tw93/Kaku) (書く) schreibt Code, [Waza](https://github.com/tw93/Waza) (技) trainiert Gewohnheiten, [Kami](https://github.com/tw93/Kami) (紙) liefert Dokumente. Als Familie gedacht ist Kaku der Vater, Waza die große Schwester und Kami die kleine Schwester.

## Deinstallation

```bash
npx skills remove tw93/Waza -g
rm -f ~/.claude/statusline.sh
rm -f ~/.claude/rules/english.md
rm -f ~/.claude/rules/anti-patterns.md
rm -f ~/.claude/rules/waza-routing.md
rm -f ~/.claude/rules/clarity.md
```

Für die Statusleiste entfernst du außerdem den Eintrag `statusLine` aus `~/.claude/settings.json`. In Claude Desktop löschst du Waza unter Customize > Skills. Bei Codex-Regelinstallationen entfernst du die markierten Waza-Blöcke aus `~/.codex/AGENTS.md`. Bei Antigravity entfernst du die gewählte Regeldatei aus `~/.gemini/antigravity-cli/rules/`. In anderen Tools entfernst du kopierte Regeln aus den benutzerdefinierten Anweisungen. Starte nach dem Entfernen einer Regel eine neue Sitzung.

## Unterstützung

- Die direkteste Unterstützung ist der Kauf meiner Mac-Bereinigungs-App [Mole for Mac](https://mole.fit)
- Wenn dir Waza hilft, freue ich mich über einen Stern, eine [Weiterempfehlung](https://twitter.com/intent/tweet?url=https://github.com/tw93/Waza&text=Waza%20-%20AI%20coding%20skills%20for%20the%20complete%20engineer.) oder ein Issue bzw. einen PR
- Du kannst auch meinen beiden Katzen TangYuan und Coke eine <a href="https://cats.tw93.fun?name=Waza" target="_blank">Dose Futter 🥩</a> spendieren

<details>
<summary>Diese lieben Menschen haben es schon getan 🐱</summary>
<br/>
<div align="center">
  <a href="https://cats.tw93.fun?name=Waza"><img src="https://cdn.jsdelivr.net/gh/tw93/sponsors@main/assets/sponsors.svg" width="1000" loading="lazy" /></a>
</div>
</details>

## Lizenz

MIT License. Please feel free to use and contribute to the development.
