---
name: colourful-research-charts
description: Draw publication-style charts as self-contained HTML files, computing every value with Python from a CSV. Use for bar, grouped bar, line, area, histogram, scatter, boxplot, radar, pie, donut, heatmap, funnel, flowchart and Gantt charts with titles, axis labels, tick marks and the value printed on every mark. Eighteen warm palettes and six font pairings, drawn at random unless a specific one is named.
license: For course use in PMGM 7023.
version: 3.0.0
---

# colourful-research-charts

Turn a CSV into **one self-contained HTML file** holding a hand-built SVG chart. Python computes every number, so nothing is invented and nothing is guessed.

## What it is, and what it is not

| It is | It is not |
|---|---|
| Python standard library only | matplotlib, seaborn, plotly, pandas |
| One HTML file you can open offline | a notebook, a script you must debug |
| Real axes, tick labels, axis titles, a printed value on every mark | a chart library's default output |
| Light backgrounds and warm palettes | a dark theme |

**No pip install. No Node. No Chrome. No API key. No network.** Only the Google Fonts link is external, and the chart still renders without it.

## How to run it

The renderer sits next to this file:

```
python3 ~/.copilot/skills/colourful-research-charts/render.py <chart-type> --data <file.csv> [options] --out <path.html>
```

See the palette and font menus:

```
python3 ~/.copilot/skills/colourful-research-charts/render.py list
```

Run the whole thing as one shell command and show the user the output path. Nothing else is needed.

## Chart types

Pick the type that answers the question, then pass the columns it needs.

| Command | Use it for | Requires |
|---|---|---|
| `bar` | one value per category, ranked | `--x` category, optional `--y` number |
| `grouped-bar` | two or more series side by side | `--x`, `--y`, `--series` |
| `line` | a value over an ordered x | `--x`, `--y`, optional `--group` |
| `area` | same as line, filled to the baseline | `--x`, `--y`, optional `--group` |
| `histogram` | the distribution of one number | `--x`, optional `--bins` |
| `scatter` | the relationship between two numbers | `--x`, `--y`, optional `--group` |
| `boxplot` | spread of a number within groups | `--x` group, `--y` number |
| `radar` | a profile across three or more dimensions | `--x` dimension, `--y`, optional `--group` |
| `pie` | each category's share of a total | `--x`, optional `--y` |
| `donut` | the same, with a total in the middle | `--x`, optional `--y`, `--center-label` |
| `heatmap` | a value across two categories at once | `--x` row, `--series` column, `--y` value |
| `funnel` | drop-off through ordered stages | `--x` stage, optional `--y` |
| `flowchart` | a process, step by step | `--data --x` step, or `--labels` |
| `gantt` | tasks against a timeline | `--x` task, `--start`, `--end` or `--duration` |

Rules of thumb:

- One number per category, one bar each: `bar`.
- A number over time or over an ordered sequence: `line` or `area`.
- Two numbers, one plotted against the other: `scatter`. Add `--group` to colour by a third column.
- Parts of a whole: `pie` or `donut`. Keep it to five slices or fewer, or the labels collide.
- Two categories crossed with a number in the middle: `heatmap`.
- Stages that shrink: `funnel`. Steps that do not shrink: `flowchart`.
- A schedule: `gantt`.

## Shared options

| Flag | Meaning |
|---|---|
| `--data PATH` | the CSV to read |
| `--x`, `--y` | column names |
| `--group` / `--series` | split the chart into coloured series |
| `--title "..."` | the question the chart answers |
| `--subtitle "..."` | one clarifying line under the title |
| `--xlabel`, `--ylabel` | **axis titles. Always set these.** |
| `--caption "..."` | the figure caption |
| `--palette NAME` | a palette key. **Leave it out and one is drawn at random, which is the preferred default** |
| `--font NAME` | a font pairing name. **Leave it out and one is drawn at random** |
| `--agg mean\|sum\|count\|median` | how to combine `--y` (bar, grouped-bar, radar, pie, donut, heatmap, funnel) |
| `--order desc\|asc\|asis` | category order (bar, pie, donut default `desc`; funnel default `asis`) |
| `--show-n` | print `n=` under each bar |
| `--bins N` | histogram bin count |
| `--ticks N` | how many grid lines (default 5) |
| `--labels "A,B,C"` | inline steps instead of a CSV (flowchart) |
| `--cols N` | boxes per row (flowchart, default 4) |
| `--start`, `--end`, `--duration` | timeline columns (gantt) |
| `--center-label "..."` | the text inside a donut hole |
| `--out PATH` | where to write the HTML (default `outputs/chart.html`) |
| `--seed N` | makes a random palette and font reproducible |

Charts with no axes: `pie`, `donut`, `funnel`, `flowchart`. They still need a `--title` and a `--caption`.

## The workflow

1. **Read the data before choosing any flag.** Print the column names and a few rows with Python. Never guess a column name, and never rename one.
2. **Choose the chart type** from the table above.
3. **Always pass `--xlabel` and `--ylabel`** where the chart has axes. A chart without axis titles is incomplete.
4. **Always pass a `--title`** phrased as the question the chart answers, for example "Which webpage version kept readers longest?".
5. **Say nothing about the palette or the font.** Both are drawn at random when the flags are omitted, and that is the house rule: the numbers are fixed by the data, the styling varies. Only pass `--palette` or `--font` when the user names one, or when the chart must match a specific deck (`blue-mist-mocha` is the MA7 slide style).
6. **Run the command**, then report the output path, the palette and font that came up, and the sample size from the printed figure note. The tool prints `drawn at random` next to whichever was picked for you, so quote it.

## Palettes

Eighteen, all on light grounds, defined in `palettes.json`. Omitting `--palette` picks one at random.

**Warm and soft:** `blue-mist-mocha` (the MA7 house style) · `sunset` · `peach-mist` · `pear-breeze` · `pine-ceramic` · `berry-mist` · `twilight-gold` · `sea-mist-coral` · `contrast-cream-blue` · `contrast-blush-navy`

**Cool and journal-like:** `slate-mauve` · `harbour-ochre` · `indigo-blossom` · `lagoon-apricot` · `magenta-teal` · `candy-pastel`

**Special purpose:** `journal-blue-ember` (an ordered cool-to-warm ramp, for a colour scale rather than unrelated groups) · `amber-lilac` (eight colours, for charts with many series)

Forcing one is rarely needed. If the user wants a particular flavour, the safe picks are `twilight-gold` or `slate-mauve` for a paper figure, `harbour-ochre` or `indigo-blossom` for a slide, `candy-pastel` or `sunset` for a first lesson.

## Fonts

Six heading plus body pairings, defined in `fonts.json`:

`warm-academic` (Georgia + Quicksand) · `soft-rounded` · `elegant-paper` (Cormorant + Open Sans) · `magazine` (Playfair + Lato) · `modern-editorial` (Zilla Slab + Inter) · `data-journalism` (Fraunces + Source Sans)

## Hard rules

1. **Never invent a number.** Every value comes from the CSV through the renderer. If the renderer errors, fix the flags; never edit the HTML by hand.
2. **Always label both axes**, and always write a title.
3. **No p-values, no effect sizes, no assumption checks** unless the user explicitly asks for them.
4. **Light backgrounds only.** Every palette already is.
5. **One HTML file, self-contained.** Only the Google Fonts link is external.
6. **No PNG, no screenshots, no extra files.** The deliverable is the HTML. It opens in any browser and can be printed to PDF from there if someone wants that.
7. **Report the sample size.** It is in the figure note the renderer writes.
8. **Never load a chart library.** The renderer writes the SVG itself.
9. **Never pass `--palette` or `--font` unless the user asked for a specific one.** The random draw is the point: same numbers, different look each time.

## Classroom exercise: the reading-time bar chart

**The task.** Using `s7_data_anova.csv` (columns `ID`, `new_webpage`, `time_spent_read`, `sales_in_dollars`), draw a bar chart of the mean `time_spent_read` for each `new_webpage`, label each bar with its mean, and save it as HTML. Let the palette and the font be chosen at random so no two students get the same looking chart.

**The one command to copy:**

```
python3 ~/.copilot/skills/colourful-research-charts/render.py bar \
  --data s7_data_anova.csv --x new_webpage --y time_spent_read --agg mean --show-n \
  --xlabel "New webpage version" --ylabel "Mean time spent reading (minutes)" \
  --title "Which webpage version kept readers longest?" \
  --out outputs/my_chart.html
```

Notice there is no `--palette` and no `--font`. That is deliberate: leave both out and the renderer draws one of the eighteen palettes and one of the six fonts at random, so every student gets a different looking chart from identical numbers. The tool prints `drawn at random` next to each, and the student should be asked to report which came up.

**What must come out, whatever the styling:** three bars, means **20.68**, **37.27** and **51.00** minutes, `n = 150` under each bar, N = 450. Palette and font differ from student to student; the numbers never do. That is the lesson: the data fixes the numbers, only the styling varies.

**Marking checklist**

| Check | Pass |
|---|---|
| Three bars, in the order 2, 1, 0 | |
| Each bar labelled with its mean | |
| `n = 150` under each bar | |
| x axis titled "New webpage version" | |
| y axis titled "Mean time spent reading (minutes)" | |
| A title written as a question or a finding | |
| A caption and a note naming the file and the sample size | |
| One `.html` file that opens on its own | |

## Recipes

One line each. No `--palette` or `--font` anywhere, because both default to a random draw. Swap the columns for your own data.

```
# bars: counts per category, no --y needed
render.py bar --data f.csv --x group --xlabel "Group" --ylabel "Number of records" --title "How many records per group?" --out out/bars.html

# grouped bars: two series side by side (long format: group, series, value)
render.py grouped-bar --data long.csv --x condition --y steps --series wave --agg mean --xlabel "Condition" --ylabel "Mean daily steps" --title "Did steps rise in each condition?" --out out/grouped.html

# line and area over an ordered x
render.py line --data f.csv --x month --y sales --xlabel "Month" --ylabel "Sales" --title "How did sales move over the year?" --out out/line.html
render.py area --data f.csv --x month --y sales --xlabel "Month" --ylabel "Sales" --title "How did sales build up over the year?" --out out/area.html

# histogram of one number
render.py histogram --data f.csv --x score --bins 9 --xlabel "Score" --ylabel "Number of people" --title "How are the scores distributed?" --out out/hist.html

# scatter, coloured by a third column
render.py scatter --data f.csv --x height --y weight --group sex --xlabel "Height (cm)" --ylabel "Weight (kg)" --title "How do height and weight relate?" --out out/scatter.html

# boxplot of a number within groups
render.py boxplot --data f.csv --x group --y score --xlabel "Group" --ylabel "Score" --title "How does the score spread by group?" --out out/box.html

# radar: needs 3 or more dimensions
render.py radar --data f.csv --x dimension --y score --group method --xlabel "Dimension" --ylabel "Mean score" --title "Which method is strongest on each dimension?" --out out/radar.html

# pie and donut of a share
render.py pie --data f.csv --x group --xlabel "Group" --title "How do the records split by group?" --out out/pie.html
render.py donut --data f.csv --x group --center-label "150 people" --xlabel "Group" --title "How are the 150 people divided?" --out out/donut.html

# heatmap: long format is row / column / value
render.py heatmap --data long.csv --x row --series col --y value --agg mean --xlabel "Column" --ylabel "Row" --title "Where are the values highest?" --out out/heatmap.html

# heatmap: wide format, one numeric column per grid column (no --series)
render.py heatmap --data wide.csv --x name --xlabel "Variable" --ylabel "Record" --title "Where are the values highest?" --out out/heatmap_wide.html

# funnel: stages in the order they happen
render.py funnel --data f.csv --x stage --y people --xlabel "Stage" --title "Where did the people drop off?" --out out/funnel.html

# flowchart: inline steps, or a step column in a CSV
render.py flowchart --labels "Collect,Clean,Analyse,Report" --cols 4 --title "How does the pipeline flow?" --out out/flow.html

# gantt: dates as YYYY-MM-DD, or plain numbers
render.py gantt --data f.csv --x task --start begin --end finish --group phase --xlabel "Date" --ylabel "Task" --title "What is the schedule?" --out out/gantt.html
```

To force a look, add `--palette slate-mauve --font magazine`, or pin a reproducible draw with `--seed 42`.

## When something goes wrong

| Message | Fix |
|---|---|
| `Unknown palette` / `Unknown font` | run `render.py list` and copy a name exactly |
| `argument cmd: invalid choice` | the chart type is misspelled; the list of valid ones is in the error |
| `Column ... has no numeric values` | that column is text, not numbers; pick the right one |
| `A radar chart needs at least 3 dimensions` | radar needs three or more spokes; use a bar chart instead |
| `A Gantt chart needs --start` | pass `--start`, plus `--end` or `--duration` |
| `No complete pairs` | the two columns never both have a number in the same row |
| `Every value is zero` | the pie or donut has nothing to divide |
| Two category labels overlap | shorten them, or use `bar` instead of `pie` |
| The y axis is squeezed | reduce `--ticks` |
| The bars are in the wrong order | use `--order asis` to keep the file's order |
| Must have the same colours twice | pass `--seed 42` with `random` |
| Someone wants a picture file | open the HTML and use the browser's own print or screenshot. This tool does not make PNGs |
