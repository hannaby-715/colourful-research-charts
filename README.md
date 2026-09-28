# colourful-research-charts

An agent skill that turns a CSV into **one self-contained HTML chart**: real axes, tick labels, axis titles, a legend, and the value or count printed on every mark.

Built for teaching data analysis in PMGM 7023 at HKU Business School, where the audience does not write code.

- **14 chart types** — bar, grouped bar, line, area, histogram, scatter, boxplot, radar, pie, donut, heatmap, funnel, flow chart, Gantt
- **18 colour palettes and 6 font pairings**, drawn **at random** unless you name one, so the same data looks different for every student while the numbers stay identical
- **Python standard library only** — no `pip install`, no matplotlib, no Node, no Chrome, no API key, no network. Tested on Python 3.9 and 3.13

## Install

With GitHub CLI 2.90.0 or later:

```
gh skill install hannaby-715/colourful-research-charts colourful-research-charts --scope user
```

`--scope user` matters: the default is project scope, which ties the skill to a single folder.

Without GitHub CLI, download this repository as a ZIP and unzip the `skills/colourful-research-charts` folder into `~/.copilot/skills/`. All five files must arrive together. See [INSTALL.md](INSTALL.md).

Then, in the Copilot CLI:

```
/skills info colourful-research-charts
```

## Use

```
Use the /colourful-research-charts skill.

Data: s7_data_anova.csv (columns: ID, new_webpage, time_spent_read, sales_in_dollars).
Draw a bar chart of the mean time_spent_read for each new_webpage, label each bar with its mean,
and save it as an HTML file in outputs/.
Do not pick a palette or a font: let the skill choose both at random.
Then report the output path, the palette name and the font name it used.
```

Expected result: three bars at **51.00**, **37.27** and **20.68** minutes, `n = 150` each. The palette and font vary by student; the numbers never do.

## Gallery

Open [`gallery/index.html`](gallery/index.html) in a browser:

| Page | Shows |
|---|---|
| [`gallery/all-types.html`](gallery/all-types.html) | all 14 chart types on real data |
| [`gallery/palettes.html`](gallery/palettes.html) | all 18 palettes as colour ramps, each applied to the same chart |

The palettes were extracted from photographs of colour reference cards in `IMG_3884–3889` and `IMG_3996–4004`. Palette swatches in the gallery are read straight from `palettes.json`, so the gallery cannot drift from what the renderer actually uses.

## Repository layout

```
skills/colourful-research-charts/   the skill: SKILL.md, render.py, palettes.json, fonts.json
gallery/                            what every chart type and palette looks like
INSTALL.md                          step-by-step install guide
```

## Licence

For course use in PMGM 7023. There is no open source licence file, so the default applies: all rights reserved. Ask before redistributing.

## A note on trust

Agent skills are **not verified by GitHub** and may contain prompt injections, hidden instructions or malicious scripts.

This one is deliberately auditable. `render.py` is a single Python file using only the standard library. It makes no network calls, reads only the CSV you name, and writes only the HTML path you give it. There is nothing to `pip install`. Read it before you run it.

Note also that this skill does **not** include the `allowed-tools` frontmatter field, so your agent will ask permission before running the renderer. That is intentional: pre-approving shell access removes a confirmation step that is worth keeping.
