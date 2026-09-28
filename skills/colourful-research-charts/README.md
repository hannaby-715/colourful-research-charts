# colourful-research-charts

A chart maker for people who do not want to fight a chart library.

Point it at a CSV, pick a chart type, get **one self-contained HTML file** with a hand-built SVG chart: real axes, real tick labels, axis titles, a title, a caption, and the value or count printed on every mark.

- **Python standard library only.** No matplotlib, no Node, no Chrome, no API key, no network.
- **14 chart types.** bar, grouped-bar, line, area, histogram, scatter, boxplot, radar, pie, donut, heatmap, funnel, flowchart, gantt.
- **18 palettes, 6 font pairings**, all light-ground. Both are drawn **at random unless you name one**, so the same data can look different every time and the numbers still never move.

## Install

Drop this folder into your skills directory:

```
~/.copilot/skills/colourful-research-charts/
```

## Use

```
python3 ~/.copilot/skills/colourful-research-charts/render.py bar \
  --data s7_data_anova.csv --x new_webpage --y time_spent_read --agg mean --show-n \
  --xlabel "New webpage version" --ylabel "Mean time spent reading (minutes)" \
  --title "Which webpage version kept readers longest?" \
  --out outputs/my_chart.html
```

No `--palette`, no `--font`: one of each is drawn at random and reported in the output.

See the menus:

```
python3 ~/.copilot/skills/colourful-research-charts/render.py list
```

Full instructions, every flag and a classroom exercise live in `SKILL.md`.

## Files

| File | What it holds |
|---|---|
| `SKILL.md` | the instructions the assistant reads |
| `render.py` | the renderer |
| `palettes.json` | eighteen colour palettes |
| `fonts.json` | six heading and body font pairings |
| `README.md` | this file |

## Output

The deliverable is the HTML. Open it in any browser. If a picture is needed, print it to PDF from the browser, or take a screenshot.
