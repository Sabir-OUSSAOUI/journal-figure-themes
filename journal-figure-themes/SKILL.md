---
name: journal-figure-themes
description: Journal-named figure templates for scientific figures (Nature, Nature Biomedical Engineering, Nature Biotechnology, Cell Metabolism, Advanced Science, and more). A template fixes the whole chart style, not only colours - palette, typography, panel badges, grid, line and marker weights, violin and heatmap construction, legends. The user picks one template by journal name and it is then applied to EVERY figure produced in the rest of the conversation. Use this skill whenever the user asks for a scientific or publication figure, plot, chart, heatmap, UMAP, violin, dose-response curve or multi-panel figure; whenever they mention a journal style, "Nature-style", a figure template, theme or colour palette for a paper, poster or slides; and on every later plotting request in a conversation where a template was already chosen, even if the user does not repeat the template name. Also triggers in French, e.g. "figure scientifique", "palette de couleurs", "style Nature", "template de journal", "appliquer le template".
---

# Journal figure templates

Give every figure in a conversation one consistent, journal-inspired look. The user chooses a
template once; from then on all figures share it, so a whole paper's worth of panels looks like it
came from one hand.

A template is the full set of chart characteristics, not a palette swap: colours, title typeface,
panel-letter style, grid, line/marker/error-bar weights, scatter density and cluster outlines, how
violins and heatmaps are built, where legends sit. Two figures with the same colours but different
title fonts, marker sizes or legend positions do not look like a set — which is why the helpers
below exist and why you should prefer them over hand-styling each chart.

The templates are *inspired by* journal cover art. They are not official journal style guides; say
so if the user asks whether a figure "meets Nature's requirements".

## Templates

| Key | Inspired by | Colours | Chart characteristics |
|---|---|---|---|
| `nature-lavender` | Nature | indigo, lavender, pink, teal | serif titles, multicolour letter badges, thin lines + small markers, tiny scatter points, white-gapped heatmap cells, legend outside right |
| `nature-biomedical-engineering` | Nature Biomedical Engineering | ocean blues, teal, grey control | serif titles, blue badges, heavy lines + large markers, wide error caps, large points with dashed cluster ellipses, seamless heatmap, legend inside |
| `nature-microbial` | Nature (microbiome cover) | warm pastels, 6 hues | cream background, serif titles, warm badges, light full grid, filled cluster ellipses, gapped heatmap |
| `nature-dark` | Nature (dark cover) | vivid multicolour on dark navy | sans titles, cyan badges with dark letter, heavier lines, gapped heatmap — for slides and posters |
| `nature-biomedchem` | Nature (Bio & Med Chem) | navy, cyan, purple, gold accent | serif titles, gold/blue/purple badges, light grid, fine lines, widest heatmap gaps |
| `cell-metabolism` | Cell Metabolism | blue vs orange, yellow | sans bold titles, orange/blue badges, light full grid, medium points, seamless heatmap |
| `nature-biotechnology` | Nature Biotechnology | teal, orange, purple (6) | minimal: accent bar + lower-case letter instead of badge, hollow markers, no error caps, violins with line + dot, thin donut, legend inside |
| `advanced-science` | Advanced Science | leaf green, lilac | serif titles, green badges, quiet thin lines, gapped heatmap |

`assets/theme_gallery.png` shows every palette; `assets/previews/<key>.png` shows each template on
eight chart types (line, bars, scatter, violin, two heatmaps, dose–response, donut). Show the user
the relevant preview when they are choosing. Loose names resolve automatically: "Nature", "NBE",
"NBT", "Cell", "adv sci", "dark", "sombre"…

## Workflow

### 1. Establish the active template

Look back through the conversation first. If a template was already chosen, keep using it — do
not ask again. Re-asking on every figure defeats the point of the skill.

If none was chosen:
- The user named a journal → resolve it to a key and proceed. "Nature" alone maps to
  `nature-lavender`; mention the other Nature variants in one line so they can switch.
- The user named a journal that has no template → say so, offer the closest by colour or field,
  and proceed with it rather than blocking.
- The user named nothing → show the list (and the gallery image if you can display files) and ask
  which they want. If they would rather not choose, use `nature-lavender`.

Then state the active template in one short line, e.g. *"Template: cell-metabolism — applied to
all figures in this chat."* On each later figure, a brief mention is enough.

The user can switch any time ("switch to NBT", "passe en sombre"). Switching applies to new
figures; offer to re-render earlier ones, since a mixed set is usually not what they want.

### 2. Apply it in code

Start every plotting script with the helper. Scripts usually run in fresh processes, so the
template does not survive between runs — call it each time. Copy `scripts/journal_theme.py` next
to the user's script (or add its folder to `sys.path`) so the script they receive runs on their
machine without an absolute path into the skill.

```python
from journal_theme import apply_theme
t = apply_theme("cell-metabolism")     # context="talk" or "poster" scales fonts, lines, markers
colors = t.assign(["Metformin", "Rapamycin", "Vehicle"])   # stable label -> colour; controls grey
```

`apply_theme` sets matplotlib rcParams (so seaborn and pandas plots inherit colours, fonts, spines,
grid, line and marker weights, export settings) and returns the template object. Draw with its
helpers so the template's chart characteristics are applied the same way every time:

| Helper | Draws | Template decides |
|---|---|---|
| `t.panel(ax, "a", "Title")` | panel letter + title | badge vs accent bar, badge colours, letter case, title typeface |
| `t.lineplot(ax, x, y, yerr=, label=, color=, band=, marker=)` | line + markers + error bars or band | line width, marker size, solid vs hollow markers, cap size |
| `t.curve(ax, x, y, color=)` / `t.points(ax, x, y, yerr=, label=, color=)` | smooth marker-free line / markers without a line | same weights; use together for "fit + data" |
| `t.bars(ax, cats, {series: values}, yerr=, colors=, stacked=, horizontal=, points=)` | grouped or stacked bars, optional replicate dots | group width, error-bar style, value-axis grid |
| `t.scatter(ax, x, y, labels, colors=)` | points coloured by group | point size, alpha, dashed/filled cluster ellipses |
| `t.violin(ax, data, labels=, colors=)` | violins | inner mark: white mini box, or line + median dot |
| `t.heatmap(ax, data, kind="seq"\|"div", xticklabels=, yticklabels=, vmin=, vmax=, cbar_label=, annotate=)` | heatmap + colourbar | cell gaps, frameless slim colourbar; `div` sets symmetric limits around zero by itself |
| `t.donut(ax, values, labels, colors=, center_text=)` | ring chart | ring thickness, gaps, centre typeface |
| `t.legend(ax, outside=, **legend_kwargs)` | legend | outside-right vs inside; passing `loc=` puts it inside |
| `t.suptitle(fig, "…")` | figure title | typeface, left alignment |
| `t.figsize(columns=1\|2, aspect=, legend_outside=)` | figure size in inches | scales with `context` so poster fonts keep their proportions |

Use `t.panel` instead of `ax.set_title`, and `t.legend` instead of `ax.legend`, even on charts you
draw with plain matplotlib or seaborn — titles, badges and legend placement are the most visible
part of a template. Use `constrained_layout=True` so badges and outside legends get room. The
helpers pass extra keyword arguments through to matplotlib (`marker="s"`, `ls="--"`,
`ncols=3`…), so a variation never requires dropping back to unstyled calls.

Common situations:

- **Fit + data (dose–response, kinetics, calibration).** `t.curve` for the fitted line on a fine
  grid, `t.points` with `yerr` for the measurements, same colour for both. Plain `ax.plot` picks
  up the template's markers; pass `marker="none"` if you use it.
- **A later figure shows only some of the groups.** Call `t.assign` with the full group list from
  the first figure and plot the subset — colours are handed out in order, so assigning from the
  subset would give a remaining group the absent group's colour. If the earlier script is gone,
  read the mapping off the earlier figure's legend.
- **Two categorical variables in one figure** (conditions in panels a–c, edit types in a donut):
  `t.assign(conditions)` for the first, `t.assign(types, skip=len(non-control conditions))` for
  the second, so one colour never means two things. A second "none/unedited" category takes a
  lighter grey than the control.
- **Outside legend in a single column.** It costs about a quarter of the width; use
  `t.figsize(1, legend_outside=True)` or put it inside with `t.legend(ax, loc="upper left")`.
- **Poster or slides.** `apply_theme(key, context="poster")` with `t.figsize(...)`, otherwise the
  doubled fonts crowd a journal-sized canvas.
- **Panel letters.** Each separate figure starts again at "a". The template decides badge vs bar
  and upper vs lower case, but the user's own wording wins: if they wrote "(a)" and "(b)", pass
  `upper=False` to `t.panel` (or `upper=True` for "A", "B") and keep that choice for the rest of
  the conversation. A single-panel figure needs no letter: `t.panel(ax, title="…")`.
- **Language of labels.** Follow the manuscript's language (usually English for these journals)
  even when the conversation is in another language, and say that you did.

For chart types without a helper (box plots, histograms, networks, Sankey, radar…), draw them
normally and take the values from the template so they still match:

| Need | Use |
|---|---|
| categorical colours | `t.assign(labels)`, `t.colors`, `t.n_colors(n)` |
| continuous low→high | `cmap=t.seq` (also the default `image.cmap`) |
| signed / centred data | `cmap=t.div` with symmetric limits |
| the one thing to notice / things that recede | `t.highlight` / `t.neutral`, `t.muted` |
| text, axes, gridlines, background | `t.text`, `t.muted`, `t.grid`, `t.bg` |
| weights and construction | `t.style` — `lw`, `ms`, `marker_face`, `capsize`, `scatter_s`, `scatter_alpha`, `ellipse`, `violin`, `heat_gap`, `bar_width`, `grid`, `legend`, `donut_width`, multiplied by `t.scale` |
| title typeface | `family=t.title_fonts` |

Seaborn: pass `palette=t.assign(labels)` and do not call `sns.set_theme()` after `apply_theme`,
because it resets the rcParams. Then finish the axes with `t.panel` and `t.legend`.

Plotly: `fig.update_layout(template=plotly_template("cell-metabolism"))` carries colours, fonts,
grid, line/marker weights, violin inner box, heatmap gaps and donut hole.

Anything else (R/ggplot2, SVG, HTML, D3, TikZ): run `python scripts/journal_theme.py show <key>`
and reproduce both halves of the JSON — the colours *and* the `style` block (title font, grid,
line width, marker size, hollow markers, heatmap gap, legend position). In ggplot2 that is
`scale_*_manual(values = …)` / `scale_*_gradientn(colours = …)` on `theme_classic(base_size = 8)`
with `legend.position`, `panel.grid.major`, `plot.title` family and `geom_*` sizes set from `style`.

### 3. Keep the set consistent

The template sets defaults; these choices are still yours, and they are what make several figures
read as one set:

- **Stable colour meaning.** Once a condition, cluster or species has a colour, it keeps that
  colour in every panel and every later figure. Build the mapping once with `t.assign(...)` and
  reuse it (put it in a small shared module if the figures are separate scripts); relying on
  plotting order silently reshuffles colours when a group is missing.
- **Controls are neutral.** `t.assign` already draws Control / Vehicle / WT / Other / Témoin in
  grey so the treated conditions carry the colour. Pass `control=[...]` when the labels are unusual.
- **Take colours in palette order.** The first N are the most distinguishable N. For more groups
  than the palette holds, fold the tail into "Other" in `t.neutral` — a dozen near-identical hues
  cannot be read anyway.
- **Match the colormap to the data.** Sequential for magnitudes, diverging only when zero (or a
  reference) is meaningful. Never use the categorical palette for ordered values.
- **Nothing off-template.** No matplotlib default colours, `"red"`, `viridis`, boxed legends,
  centred titles, or one-off line widths and marker sizes. If something needs emphasis, use
  `t.highlight`; if it needs to recede, `t.muted`.
- **Same chart, same construction.** If the first violin in the conversation had the white mini
  box, so does the tenth. This is automatic with the helpers and easy to break without them.
- **Dark template.** `nature-dark` is for screens. If the figure is going into a manuscript,
  mention that journals expect a white background and offer a light template.
- **Colour is not the only channel.** Several palettes are pastel or single-hue; where series must
  be told apart in greyscale or by colour-blind readers, add marker shapes, line styles or direct
  labels.
- **The template never outranks legibility.** It decides how things look, not what is shown. Keep
  the habits of a careful figure: show individual replicates when n is small (`points=` on bars),
  fit curves to the data rather than drawing the generating model, label clusters or segments
  directly when that reads faster than a legend, share one legend across panels that use the same
  groups, give series that start at the same value a small x-offset so markers do not stack, and
  state the figure width and what the error bars are. If a template choice hides data (hollow
  markers piling up, a violin too narrow to show its inner mark), adjust that element and say so.

Shared conventions across all templates: sans-serif 8 pt body text, no top/right spines, no legend
frame, axis labels with units. Size figures for the destination (single column ≈ 3.5 in / 89 mm,
double ≈ 7.2 in / 183 mm) and save vector (`.pdf`/`.svg`) plus a 300 dpi `.png`.

### 4. Check before delivering

Open the rendered image. Confirm the template is visibly applied — background, text colour,
palette, *and* panel badges, title typeface, grid, legend position — that nothing fell back to
matplotlib defaults, labels and legends do not overlap data, error bars are actually visible (not
hidden behind markers), panel titles line up, and colours mean the same thing as in earlier
figures of this conversation. Fix and re-render before showing the user, and look again after the
last edit. Put the script in a code file rather than pasting it whole into the reply.

## Helper CLI

```
python scripts/journal_theme.py list                  # keys + one-line descriptions
python scripts/journal_theme.py show <key>            # colours + style as JSON
python scripts/journal_theme.py gallery out.png       # palette sheet of all templates
python scripts/journal_theme.py demo <key> out.png    # eight chart types in that template
```

## Adding or adjusting a template

Edit `THEMES` in `scripts/journal_theme.py`: colour fields (`bg`, `panel`, `text`, `muted`, `grid`,
`categorical`, `sequential`, `diverging`, `highlight`, `neutral`) plus a `style` dict overriding
any key of `STYLE_DEFAULT` (documented at the top of the file). Keep grey out of `categorical`
(it belongs in `neutral`), order `categorical` so neighbours contrast, add aliases, regenerate the
gallery and the preview, and add a row to the table above. When a user asks for a lasting change to
a template's look ("thicker lines in NBT", "no grid for Cell"), change the `style` entry rather
than patching individual figures.
