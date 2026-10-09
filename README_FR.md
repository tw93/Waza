<h4 align="right"><a href="README.md">English</a> | <a href="README_CN.md">中文</a> | <a href="README_TW.md">繁體</a> | <a href="README_JA.md">日本語</a> | <a href="README_KR.md">한국어</a> | <a href="README_DE.md">Deutsch</a> | <strong>Français</strong></h4>

<div align="center">
  <img src="https://gw.alipayobjects.com/zos/k/2h/waza.svg" width="120" />
  <h1>Waza</h1>
  <p><b>Les bonnes pratiques d'ingénierie transformées en compétences pour agents IA</b></p>
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

## Compétences (Skills)

Chaque réflexe d'ingénierie correspond à une compétence dédiée. Dans Claude Code, lancez la commande slash ; dans Codex, appelez la compétence directement par son nom

| Compétence | Quand l'utiliser | Ce qu'elle fait |
| :--- | :--- | :--- |
| [`/think`](skills/think/SKILL.md) | Avant d'écrire du code | Remet en question le problème et produit un plan d'action prêt à l'emploi |
| [`/ui`](skills/ui/SKILL.md) | Création d'interfaces frontend | Conçoit des interfaces soignées et itérées sur captures d'écran, loin des templates par défaut |
| [`/check`](skills/check/SKILL.md) | Avant merge ou release | Passe en revue les diffs selon les règles du projet et valide les résultats |
| [`/hunt`](skills/hunt/SKILL.md) | Bogues et régressions | Débogage méthodique pour identifier la cause racine avant d'appliquer un correctif |
| [`/write`](skills/write/SKILL.md) | Rédaction et révision | Récrit et polit les textes pour supprimer le ton robotique des IA |
| [`/learn`](skills/learn/SKILL.md) | Explorer un nouveau sujet | Recherche approfondie en 6 étapes pour maîtriser un sujet complexe |
| [`/read`](skills/read/SKILL.md) | Lire des URL ou des PDF | Extrait un résumé concis ou du Markdown propre pour référence ou sauvegarde |
| [`/health`](skills/health/SKILL.md) | Audit des agents IA | Audite la configuration des agents et les dérives d'instructions |

Chaque compétence est un dossier autonome contenant documentation, scripts et retours d'expérience du terrain

## Installation

**Claude Code, Codex, Cursor et autres agents**

```bash
npx skills add tw93/Waza -a claude-code codex cursor -g -y
```

Vous pouvez aussi demander directement à votre agent de l'installer :
> Install Waza for me by reading https://github.com/tw93/Waza/blob/main/llms.txt

Les compétences sont installées dans `~/.agents/skills`. Claude Code y accède via un lien symbolique ; Codex, Cursor, Gemini CLI, Copilot, Amp, Kimi Code CLI et tout autre agent lisant ce dossier chargent automatiquement les 8 compétences. Mise à jour via `npx skills update -g -y`

**En tant que plugin hôte** (les compétences sont préfixées, ex. `/waza:check`) :

```bash
# Claude Code (mise à jour : claude plugin update waza)
/plugin marketplace add tw93/Waza
/plugin install waza@waza

# Codex (mise à jour : codex plugin marketplace upgrade waza, puis codex plugin add waza@waza)
codex plugin marketplace add tw93/Waza
codex plugin add waza@waza
```

**Claude Desktop** : téléchargez [waza.zip](https://github.com/tw93/Waza/releases/latest/download/waza.zip), allez dans Customize > Skills > "+" > Create skill et chargez l'archive

**Pi** : `pi install npm:@tw93/waza`, mise à jour via `pi update npm:@tw93/waza`

## Enchaîner les compétences

Vous décidez comment combiner les compétences. Chaque compétence s'arrête une fois l'objectif atteint ; les flux autorisés s'enchaînent naturellement

**Flux courants :**

- **Nouvelle fonctionnalité** : `/think` pour cadrer → Implémentation → `/check` pour valider et fusionner
- **Correction de bogue** : `/hunt` pour trouver la cause → Correction → `/check` pour vérifier et publier
- **Recherche et rédaction** : `/read` pour collecter → `/learn` pour structurer → `/write` pour polir
- **Débogage et validation** : `/hunt` pour cibler la cause → Fix → `/check` pour revoir les diffs

## Contexte du projet

Waza n'embarque que des méthodes d'ingénierie universelles. `/check` lit au moment de l'exécution les fichiers publics du dépôt cible (README, manifestes, Makefile, CI) et vos contraintes, sans jamais accéder à des clés ou chemins privés

## Outils additionnels

### Barre d'état (Statusline)

Une barre d'état minimale pour Claude Code : fenêtre de contexte, quotas 5 heures et 7 jours avec code couleur sans encombrement

<div align="center">
  <img src="https://gw.alipayobjects.com/zos/k/y9/RUgevg.png" width="1000" />
</div>

```bash
(
  set -e
  WAZA_STATUSLINE_SCRIPT="$(mktemp -t waza-statusline.XXXXXX)"
  trap 'rm -f "$WAZA_STATUSLINE_SCRIPT"' EXIT
  curl -fL https://github.com/tw93/Waza/releases/latest/download/setup-statusline.sh -o "$WAZA_STATUSLINE_SCRIPT"
  bash "$WAZA_STATUSLINE_SCRIPT"
)
```

**Codex** intègre nativement ces indicateurs dans `~/.codex/config.toml` :

```toml
[tui]
status_line = ["model-with-reasoning", "current-dir", "context-used", "five-hour-limit", "weekly-limit"]
status_line_use_colors = true
```

### Règles optionnelles

Règles persistantes pour guider le comportement de votre agent :

```bash
(
  set -e
  WAZA_RULE_SCRIPT="$(mktemp -t waza-rule.XXXXXX)"
  trap 'rm -f "$WAZA_RULE_SCRIPT"' EXIT
  curl -fL https://github.com/tw93/Waza/releases/latest/download/setup-rule.sh -o "$WAZA_RULE_SCRIPT"

  # Coaching d'anglais : suggestions brèves en cas d'erreur de formulation
  bash "$WAZA_RULE_SCRIPT" english claude-code

  # Anti-patterns : garde-fous contre les modifications hâtives ou résumés superflus
  bash "$WAZA_RULE_SCRIPT" anti-patterns claude-code

  # Routage Waza : incite l'agent à préférer les compétences Waza
  bash "$WAZA_RULE_SCRIPT" waza-routing claude-code

  # Clarté d'expression : réponses directes et non ambiguës basées sur ASD-STE100
  WAZA_REF=main bash "$WAZA_RULE_SCRIPT" clarity claude-code
)
```

<div align="center">
  <img src="https://gw.alipayobjects.com/zos/k/24/vfkGOi.png" width="1000" />
</div>

## Pourquoi Waza

Waza (技, わざ) désigne dans les arts martiaux une technique répétée jusqu'à devenir un réflexe.

Un bon ingénieur fait bien plus qu'écrire du code : il challenge les besoins, cherche la cause racine et relit ses propres diffs. L'IA a la puissance brute, mais sans structure, elle produit des résultats banals. Waza définit le but et les limites, laissant le modèle libre de trouver la meilleure trajectoire.

Waza reste sobre : 8 compétences essentielles issues de plus de 300 sessions réelles. Fait partie d'une trilogie : [Kaku](https://github.com/tw93/Kaku) écrit le code, [Waza](https://github.com/tw93/Waza) ancre les réflexes, [Kami](https://github.com/tw93/Kami) produit les documents

## Désinstallation

```bash
npx skills remove tw93/Waza -g
rm -f ~/.claude/statusline.sh
rm -f ~/.claude/rules/english.md
rm -f ~/.claude/rules/anti-patterns.md
rm -f ~/.claude/rules/waza-routing.md
rm -f ~/.claude/rules/clarity.md
```

## Soutenir le projet

- Le moyen le plus direct est d'acheter [Mole for Mac](https://mole.fit), mon application de nettoyage pour Mac
- Si Waza vous est utile, n'hésitez pas à lui donner une étoile sur GitHub ou à le partager
- Vous pouvez aussi offrir une <a href="https://cats.tw93.fun?name=Waza" target="_blank">boîte de pâtée 🥩</a> à mes deux chats, TangYuan et Coke

<details>
<summary>Remerciements aux sponsors 🐱</summary>
<br/>
<div align="center">
  <a href="https://cats.tw93.fun?name=Waza"><img src="https://cdn.jsdelivr.net/gh/tw93/sponsors@main/assets/sponsors.svg" width="1000" loading="lazy" /></a>
</div>
</details>

## Licence

MIT License
