# colourful-research-charts · install guide

A chart maker for Copilot CLI. Point it at a CSV and it returns **one self-contained HTML file** with a real chart inside: a title, axis titles, tick marks, a legend, and the value printed on every bar, slice or point.

- **14 chart types**: bar, grouped bar, line, area, histogram, scatter, boxplot, radar, pie, donut, heatmap, funnel, flowchart, Gantt.
- **18 colour palettes and 6 font pairings**, drawn **at random** so no two people get the same looking chart from the same numbers.
- **Python standard library only.** No `pip install`, no matplotlib, no Node, no Chrome, no account, no API key, no internet needed after installing.

---

## Which route are you on?

| What you were given | What to do |
|---|---|
| **The whole `s7 tutorial folder`** | **Nothing to install.** Open a terminal in that folder, then jump to Step 3 |
| **A link to the GitHub repository** | `gh skill install hannaby-715/colourful-research-charts colourful-research-charts --scope user`, then Step 2. No GitHub CLI? Download the repository ZIP and use Step 1 on the `skills/colourful-research-charts` folder inside it |
| **Only this zip** | Follow Step 1, then Step 2 |

---

## Step 1 · Install it yourself (only if you got just the zip)

Unzip `colourful-research-charts.zip` into your personal skills folder. One line:

**macOS or Linux**

```
mkdir -p ~/.copilot/skills && unzip -o ~/Downloads/colourful-research-charts.zip -d ~/.copilot/skills && ls ~/.copilot/skills/colourful-research-charts
```

**Windows (PowerShell)** — the folder is `%USERPROFILE%\.copilot\skills`

```
New-Item -ItemType Directory -Force -Path $HOME\.copilot\skills | Out-Null
Expand-Archive -Path $HOME\Downloads\colourful-research-charts.zip -DestinationPath $HOME\.copilot\skills -Force
Get-ChildItem $HOME\.copilot\skills\colourful-research-charts
```

Change the `Downloads` path if you saved the zip somewhere else.

You should see **five files**:

```
SKILL.md   render.py   palettes.json   fonts.json   README.md
```

If you only see `SKILL.md`, the unzip went wrong. **All five are required**, and all five must sit in the same folder.

### Or let Copilot do it for you

If you would rather not type that, ask Copilot to do it. First make sure Copilot can read the zip: the safest place is the folder you launched it from. If the zip is in your Downloads folder, run `/add-dir ~/Downloads` first, then paste:

```
I have the skill zip at colourful-research-charts.zip
Unzip it so that I end up with ~/.copilot/skills/colourful-research-charts/
containing all five files: SKILL.md, render.py, palettes.json, fonts.json, README.md.
Do not use `copilot skill add` — that copies only SKILL.md and would leave the skill unable to draw anything.
Then run: ls ~/.copilot/skills/colourful-research-charts
```

Five files must come back. If Copilot proposes `copilot skill add`, say no and repeat the instruction.

### Or, if you already have GitHub CLI (gh 2.90.0 or later)

One command installs the whole folder, no unzipping and no checking:

```
gh skill install /path/to/colourful-research-charts --from-local --scope user --all
```

`--scope user` matters: the default is project scope, which ties the skill to one folder. This route copies every file in the folder, so the skill arrives complete. `gh skill` is in public preview, so check `gh --version` first.

### Copilot does not install skills by itself

Nothing happens if you simply mention the zip, or `@`-mention the `SKILL.md`, in a chat. Copilot only loads skills that already sit in one of its skill folders. There is no automatic install. So one of these must be true:

| | |
|---|---|
| The skill folder is in `~/.copilot/skills/` | personal, works in every folder |
| The skill folder is in `.github/skills/` inside the project you launched from | project, works in that folder |
| Someone ran an explicit install command, as above | |

---

## Step 2 · Check that Copilot loaded it

Open the Copilot CLI and type:

```
/skills info colourful-research-charts
```

It should print the location and the description. If the CLI was already open when you installed, run this first:

```
/skills reload
```

See everything at once with `/skills list`, or from a normal terminal with `copilot skill list`.

### If you were given the course folder instead

Nothing is installed on your machine, and nothing needs to be. The skill travels inside the folder at `.github/skills/colourful-research-charts/`, and Copilot picks it up as a **project skill** the moment you start a session in that folder. Just:

```
cd "s7 tutorial folder"
copilot
```

Then `/skills list` and look for it under **Project skills**. It keeps working if you `cd` into a subfolder such as `datasets/`, where it shows up as an **inherited** skill.

`.github` starts with a dot, so macOS Finder hides it. Press **Cmd + Shift + .** to show hidden files and confirm it is there.

---

## Step 3 · Draw your first chart

**Start the CLI in the folder that holds your CSV, or in its parent.** That matters: file paths are read relative to the folder you launched from.

Then paste this prompt (adjust the data path if your CSV sits elsewhere):

```
Use the /colourful-research-charts skill.

Data: datasets/s7_data_anova.csv (columns: ID, new_webpage, time_spent_read, sales_in_dollars).
Draw a bar chart of the mean time_spent_read for each new_webpage, label each bar with its mean,
and save it as an HTML file in outputs/.
Do not pick a palette or a font: let the skill choose both at random.
Then report the output path, the palette name and the font name it used.
```

Copilot will ask permission to run a terminal command. **Allow it.** Then open the HTML file it names in any browser.

### What you should see

| | |
|---|---|
| Three bars, for versions 2, 1 and 0 | tallest first |
| A number on every bar | **51.00**, **37.27**, **20.68** minutes |
| `n = 150` under every bar | 150 people per version |
| x axis title | "New webpage version" |
| y axis title | "Mean time spent reading (minutes)" |
| Colours and font | **different from everyone else's** |

The numbers come from the data and are identical for the whole class. Only the colours and the font are random. That is the point of the exercise.

---

## Step 4 · Look at what is possible

The course folder also carries a gallery. Open it in any browser:

```
gallery/index.html
```

| Page | What it shows |
|---|---|
| `gallery/all-types.html` | all 14 chart types, each on real data, with its axis titles and printed values |
| `gallery/palettes.html` | all 18 palettes as colour ramps, each applied to the same chart |

Use it to decide what to ask for before you ask. If you see a palette you like, name it in your prompt with `--palette <key>`.

Note that the gallery is a reference **for you**, not something Copilot reads by itself. If you want Copilot to look at a page, point at it: `@gallery/palettes.html`.

---

## Things that break it

| Mistake | Why it fails | Do this instead |
|---|---|---|
| `copilot skill add ./SKILL.md` | Copies **only** the `SKILL.md` and leaves `render.py` and both JSON files behind | Move the whole folder, as in Step 1 |
| Dropping `colourful-research-charts/` loose into the course folder | Copilot only looks inside `.github/skills/`, `.agents/skills/` or `.claude/skills/` in a project | Put it at `.github/skills/colourful-research-charts/` |
| Copying just `SKILL.md` somewhere | The skill needs its four neighbours | Keep all five files together |
| Editing the skill to pre-approve the shell | Lets any instruction run commands without asking | Approve the prompt by hand |
| Mentioning the zip, or `@`-mentioning the `SKILL.md`, and expecting it to install itself | Copilot never installs a skill from a chat message; it only loads skills that are already in a skill folder | Run Step 1, or paste the prompt in Step 1's "let Copilot do it" section |
| `copilot skill add https://…/SKILL.md` | The URL route also fetches **one** `SKILL.md` and nothing else | Move the whole folder, as in Step 1 |

Verified on 28 September 2026 with Copilot CLI 1.0.88: a plain folder (no git required) containing `.github/skills/colourful-research-charts/` is listed as a **project skill**; the same folder loose in the project root is **not** found.

---

## If something goes wrong

| What you see | What to do |
|---|---|
| `/skills info` finds nothing | Wrong folder. Confirm `~/.copilot/skills/colourful-research-charts/SKILL.md` exists, or that you are in the course folder |
| `Unknown palette` | Run `python3 <skill folder>/render.py list` and copy a name exactly |
| `command not found: python3` | Windows: tell Copilot to use `python` instead of `python3` |
| `No such file or directory: s7_data_anova.csv` | The CLI is not running in the right folder. `cd` there and start it again |
| Copilot used a different chart skill | Say the name out loud: `Use the /colourful-research-charts skill` |
| A permission prompt every time | Expected, and correct. Approve it |
| Two people got the same colours | Run it again. The draw is random, so it can repeat |

## Changing the look on purpose

Leave both flags out and you get a random pair. For a specific one instead:

```
--palette twilight-gold    # or any of the 18 keys
--font magazine            # or any of the 6 pairings
--seed 42                  # the same draw every time
```

There are 18 palettes, each shown on a real chart, in `outputs/demo/palettes.html`.

## Uninstalling

Personal install only:

```
copilot skill remove colourful-research-charts
```
