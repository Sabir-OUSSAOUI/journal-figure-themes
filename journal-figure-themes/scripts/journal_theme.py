"""Journal-inspired templates for scientific figures: palette + chart styling.

A template is more than colours. Each one fixes typography, panel-label style, grid,
line/marker/error-bar weights, scatter density, violin and heatmap construction and
legend placement, so every figure in a conversation looks like part of one set.

Usage (top of every plotting script):

    import sys; sys.path.insert(0, "<skill-dir>/scripts")
    from journal_theme import apply_theme
    t = apply_theme("cell-metabolism")            # rcParams + colormaps
    colors = t.assign(["Drug A", "Drug B", "Control"])   # stable label -> colour, control = neutral

    fig, axs = plt.subplots(1, 3, figsize=(7.2, 2.4), constrained_layout=True)
    t.lineplot(axs[0], x, y, yerr=e, label="Drug A", color=colors["Drug A"])
    t.heatmap(axs[1], z, kind="div", xticklabels=cols, yticklabels=rows, cbar_label="z-score")
    t.violin(axs[2], [a, b, c], labels=["A", "B", "C"])
    for ax, L, title in zip(axs, "abc", ["Dose response", "Expression", "Distribution"]):
        t.panel(ax, L, title)
    t.legend(axs[0])

CLI:
    python journal_theme.py list
    python journal_theme.py show <theme>            # JSON (colours + style), for other tools
    python journal_theme.py gallery out.png         # swatch sheet of every theme
    python journal_theme.py demo <theme> out.png    # 8-panel sample figure

Templates are *inspired by* journal cover art. They are not official journal style
guides and carry no endorsement.
"""
from __future__ import annotations

import json
import re
import sys
import warnings

SERIF = ["Georgia", "Times New Roman", "Liberation Serif", "DejaVu Serif"]
SANS = ["Arial", "Helvetica", "Liberation Sans", "DejaVu Sans"]

# Style keys (chart characteristics, per template):
#   title_font   "serif" | "sans"        font of panel titles and figure title
#   label        "badge" | "bar" | "plain"   panel-letter style
#   badge        list of colours cycled over panels (badge) / accent colour (bar)
#   badge_text   letter colour inside the badge
#   upper        panel letters upper-case (A, B, C) or lower-case (a, b, c)
#   grid         "none" | "y" | "both"
#   lw, ms       line width, marker size (pt)
#   marker_face  "fill" (solid marker) | "bg" (hollow, background-filled)
#   capsize      error-bar cap (pt)
#   scatter_s, scatter_alpha
#   ellipse      "none" | "dashed" | "filled"   cluster outline on scatter plots
#   violin       "box" (white mini box plot) | "line" (thin line + median dot)
#   heat_gap     width of the gap between heatmap cells (0 = seamless)
#   bar_width    total width of a bar group (0-1)
#   legend       "right" (outside, dot handles) | "inside"
#   donut_width  ring thickness (fraction of radius)
STYLE_DEFAULT = dict(title_font="serif", label="badge", badge_text="#FFFFFF", upper=True, grid="none",
                     lw=1.5, ms=4.0, marker_face="fill", capsize=2.5, scatter_s=9, scatter_alpha=0.85,
                     ellipse="none", violin="box", heat_gap=0.6, bar_width=0.78, legend="right",
                     donut_width=0.36)

# categorical: ordered so that the first N colours are the most distinguishable N.
# sequential:  low -> high. diverging: negative -> neutral -> positive.
THEMES = {
    "nature-lavender": {
        "label": "Nature — lavender / pink / teal",
        "mood": "soft, molecular, pastel-cool",
        "dark": False,
        "bg": "#FFFFFF", "panel": "#FFFFFF", "text": "#3B4A7A", "muted": "#8D98B3", "grid": "#E6EAF2",
        "categorical": ["#4A5B9A", "#D881B7", "#7AC5B6", "#8D7CC6", "#5FB7E0", "#5CAB6B", "#C56DAE", "#A7D9E5"],
        "sequential": ["#F1EEFA", "#CFC6EE", "#8D7CC6", "#4A5B9A", "#2A335E"],
        "diverging": ["#3F9C8C", "#7AC5B6", "#F3F1F8", "#D881B7", "#A8478C"],
        "highlight": "#D881B7", "neutral": "#A3AAC0",
        "style": dict(badge=["#D881B7", "#8D7CC6", "#7AC5B6", "#5FB7E0"], lw=1.3, ms=3.2, capsize=2,
                      scatter_s=7, scatter_alpha=0.8, heat_gap=0.8),
    },
    "nature-biomedical-engineering": {
        "label": "Nature Biomedical Engineering — ocean blues + teal",
        "mood": "clean, clinical, monochrome blue",
        "dark": False,
        "bg": "#FFFFFF", "panel": "#FFFFFF", "text": "#0B3F6A", "muted": "#6A8CAF", "grid": "#DCEAF5",
        "categorical": ["#0B4F8A", "#3BBC9F", "#3FA0E8", "#96D6F2", "#1670B8", "#9CDCC7", "#71C0E8"],
        "sequential": ["#EAF6FD", "#C0E6FA", "#71C0E8", "#1670B8", "#0B3F6A"],
        "diverging": ["#1F8F78", "#9CDCC7", "#F4F8FA", "#71C0E8", "#0B4F8A"],
        "highlight": "#3BBC9F", "neutral": "#98A4B3",
        "style": dict(badge=["#1670B8", "#3FA0E8", "#3BBC9F"], lw=1.8, ms=5, capsize=3.5, scatter_s=24,
                      scatter_alpha=0.95, ellipse="dashed", heat_gap=0, legend="inside", bar_width=0.72),
    },
    "nature-microbial": {
        "label": "Nature (microbiome) — warm pastels",
        "mood": "warm, friendly, many categories",
        "dark": False,
        "bg": "#FFFDF9", "panel": "#FFFDF9", "text": "#555555", "muted": "#9A938C", "grid": "#EFE7DF",
        "categorical": ["#E07B56", "#8BB7D9", "#F0D86B", "#C7A5D6", "#9CBF8F", "#E89AB5"],
        "sequential": ["#FFF3E6", "#FAD3B5", "#F0A77F", "#E07B56", "#A84E30"],
        "diverging": ["#4F92C4", "#A9CCE6", "#FFF6E0", "#F0A77F", "#D9603A"],
        "highlight": "#E07B56", "neutral": "#B0ABA5",
        "style": dict(badge=["#E07B56", "#E89AB5", "#C7A5D6", "#D9736B"], grid="both", lw=1.5, ms=4,
                      scatter_s=10, scatter_alpha=0.85, ellipse="filled", heat_gap=0.5),
    },
    "nature-dark": {
        "label": "Nature — dark background, vivid multicolour",
        "mood": "high contrast, slides and posters",
        "dark": True,
        "bg": "#0B1C24", "panel": "#0B1C24", "text": "#EAEFF2", "muted": "#B0BEC5", "grid": "#1E2A35",
        "categorical": ["#4FA7C9", "#F26B38", "#3BB354", "#8E63CE", "#DCE775", "#E57373", "#7FD1E3"],
        "sequential": ["#12303C", "#1F5F78", "#4FA7C9", "#7FD1E3", "#DCE775"],
        "diverging": ["#7FD1E3", "#2F7F9E", "#16252E", "#B4532C", "#F26B38"],
        "highlight": "#F26B38", "neutral": "#6B7C86",
        "style": dict(title_font="sans", badge=["#4FA7C9"], badge_text="#0B1C24", lw=1.8, ms=4,
                      scatter_s=8, scatter_alpha=0.9, heat_gap=0.5),
    },
    "nature-biomedchem": {
        "label": "Nature (Bio & Med Chem) — navy / cyan / gold",
        "mood": "deep, formal, gold accent",
        "dark": False,
        "bg": "#FFFFFF", "panel": "#FFFFFF", "text": "#0B2A6B", "muted": "#5F6B8D", "grid": "#E6EAF2",
        "categorical": ["#0B2A6B", "#D4AF37", "#00B4D8", "#6A3FB1", "#3BC7A5", "#1F54B8", "#A78EDB", "#5CC8F1"],
        "sequential": ["#EAF7FD", "#5CC8F1", "#1F54B8", "#0B2A6B", "#06153A"],
        "diverging": ["#00A3C4", "#8FD9EC", "#F7F5EF", "#E3C873", "#B8901F"],
        "highlight": "#D4AF37", "neutral": "#989FB5",
        "style": dict(badge=["#D4AF37", "#1F54B8", "#6A3FB1"], grid="both", lw=1.3, ms=3, capsize=2,
                      scatter_s=8, heat_gap=1.0),
    },
    "cell-metabolism": {
        "label": "Cell Metabolism — blue / orange / yellow",
        "mood": "vivid, strong warm-cool contrast",
        "dark": False,
        "bg": "#FFFFFF", "panel": "#FFFFFF", "text": "#1F2A5C", "muted": "#6B7280", "grid": "#E3ECF7",
        "categorical": ["#3B79C4", "#F05A28", "#FFD469", "#B9A9E5", "#9EC6EB", "#F78B4C", "#5A9BD6", "#FDBD7C"],
        "sequential": ["#F1F7FD", "#DDECF9", "#9EC6EB", "#5A9BD6", "#3B79C4", "#1F2A5C"],
        "diverging": ["#3B79C4", "#9EC6EB", "#FFFFFF", "#FDBD7C", "#F05A28"],
        "highlight": "#F05A28", "neutral": "#9AA1AE",
        "style": dict(title_font="sans", badge=["#F05A28", "#3B79C4"], grid="both", lw=1.6, ms=4,
                      scatter_s=16, scatter_alpha=0.9, heat_gap=0),
    },
    "nature-biotechnology": {
        "label": "Nature Biotechnology — teal / orange / purple",
        "mood": "compact six-colour set, minimal, one warm accent",
        "dark": False,
        "bg": "#FFFFFF", "panel": "#FFFFFF", "text": "#0B4A5F", "muted": "#6F8A95", "grid": "#E4EEF1",
        "categorical": ["#0B5F7A", "#F4A261", "#8B5C9A", "#36B2D1", "#C9B0D6", "#8ED4E3"],
        "sequential": ["#EEF8FB", "#8ED4E3", "#36B2D1", "#0B5F7A", "#073B4C"],
        "diverging": ["#0B5F7A", "#8ED4E3", "#F8F6F3", "#F4A261", "#C8702A"],
        "highlight": "#F4A261", "neutral": "#A0AFB8",
        "style": dict(label="bar", badge=["#0B5F7A"], lw=1.5, ms=5, marker_face="bg", capsize=0,
                      scatter_s=16, scatter_alpha=0.9, violin="line", heat_gap=0, legend="inside",
                      donut_width=0.30),
    },
    "advanced-science": {
        "label": "Advanced Science — leaf green / lilac",
        "mood": "natural, quiet, botanical",
        "dark": False,
        "bg": "#FFFFFF", "panel": "#FFFFFF", "text": "#1F3D2A", "muted": "#7A9080", "grid": "#E3EFE4",
        "categorical": ["#2F6B3E", "#B79BE0", "#7FAF6B", "#7A5BB5", "#B8D9B7", "#DCCBF5"],
        "sequential": ["#F1F9F1", "#D6EED8", "#B8D9B7", "#7FAF6B", "#2F6B3E", "#173A21"],
        "diverging": ["#8E6CC9", "#C9B3EE", "#F7F8F5", "#A9CFA3", "#2F6B3E"],
        "highlight": "#9B7AD6", "neutral": "#A6B2A9",
        "style": dict(badge=["#7FAF6B"], lw=1.4, ms=3.5, scatter_s=12, heat_gap=0.8),
    },
}

DEFAULT = "nature-lavender"

ALIASES = {
    "nature": "nature-lavender", "lavender": "nature-lavender", "nature-complex-system": "nature-lavender",
    "nbe": "nature-biomedical-engineering", "nature-biomed-eng": "nature-biomedical-engineering",
    "biomedical-engineering": "nature-biomedical-engineering", "nature-bme": "nature-biomedical-engineering",
    "microbial": "nature-microbial", "microbiome": "nature-microbial", "nature-microbiome": "nature-microbial",
    "nature-pastel": "nature-microbial", "pastel": "nature-microbial",
    "dark": "nature-dark", "nature-black": "nature-dark", "nature-sombre": "nature-dark", "sombre": "nature-dark",
    "biomedchem": "nature-biomedchem", "bio-med-chem": "nature-biomedchem", "nature-gold": "nature-biomedchem",
    "nature-navy": "nature-biomedchem", "gold": "nature-biomedchem",
    "cell": "cell-metabolism", "cell-metab": "cell-metabolism", "cell-press": "cell-metabolism",
    "nbt": "nature-biotechnology", "nature-biotech": "nature-biotechnology", "biotechnology": "nature-biotechnology",
    "adv-sci": "advanced-science", "advsci": "advanced-science", "green": "advanced-science",
}

_CONTROL = re.compile(
    r"\b(control|ctrl|contr[oô]le|t[eé]moin|vehicle|v[eé]hicule|untreated|baseline|mock|placebo|sham|dmso|"
    r"wt|wild[- ]?type|others?|autres?|unassigned|unknown|na)\b", re.I)


def _installed(names):
    """Keep only fonts present on this machine, so matplotlib does not warn on every draw."""
    from matplotlib import font_manager as fm
    have = {f.name for f in fm.fontManager.ttflist}
    return [n for n in names if n in have] or ["DejaVu Sans"]


def _slug(s: str) -> str:
    s = s.lower().replace("&", " ")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def resolve(name: str | None) -> str:
    """Map a user-typed journal/theme name to a theme key. Raises KeyError with the valid list."""
    if not name:
        return DEFAULT
    s = _slug(name)
    if s in THEMES:
        return s
    if s in ALIASES:
        return ALIASES[s]
    hits = [k for k in THEMES if s in k or k in s]
    if len(hits) == 1:
        return hits[0]
    raise KeyError(f"Unknown theme {name!r}. Choose one of: {', '.join(THEMES)}")


class Theme:
    """Resolved template: colours, style values and drawing helpers that apply them."""

    def __init__(self, key: str, scale: float = 1.0):
        d = THEMES[key]
        self.key = key
        self.__dict__.update({k: v for k, v in d.items() if k not in ("style", "panel")})
        self.panel_bg = d["panel"]  # axes background ("panel" is the method below)
        self.colors = list(d["categorical"])
        self.style = {**STYLE_DEFAULT, **d.get("style", {})}
        self.scale = scale
        self.seq, self.div, self.cat = f"{key}_seq", f"{key}_div", f"{key}_cat"
        self.body_fonts = _installed(SANS)
        self.title_fonts = _installed(SERIF) if self.style["title_font"] == "serif" else self.body_fonts
        self._n_panels = 0

    # ------------------------------------------------------------ colours
    def color(self, i: int) -> str:
        return self.colors[i % len(self.colors)]

    def n_colors(self, n: int) -> list[str]:
        """n categorical colours. Beyond the palette size, samples the sequential ramp
        instead of silently repeating hues (repeats make two groups indistinguishable)."""
        if n <= len(self.colors):
            return self.colors[:n]
        import matplotlib
        from matplotlib.colors import to_hex
        cmap = matplotlib.colormaps[self.seq]
        return [to_hex(cmap(0.15 + 0.85 * i / (n - 1))) for i in range(n)]

    def assign(self, labels, control=None, skip: int = 0) -> dict:
        """Stable {label: colour}. Control-like labels (Control, Vehicle, WT, Other, Témoin…)
        get the neutral grey so treated groups carry the colour. Pass control=[...] to name
        them explicitly, or control=[] to disable.

        Build this once from the FULL list of groups and reuse it in every figure, including
        figures that show only some of the groups: colours are handed out in list order, so
        assigning from a subset would shift them.

        skip=k starts after the first k palette colours. Use it for a second categorical
        variable in the same figure (e.g. edit types next to conditions) so its colours are
        not mistaken for the first variable's."""
        labels = list(dict.fromkeys(labels))
        is_ctrl = (lambda l: l in control) if control is not None else (lambda l: bool(_CONTROL.search(str(l))))
        rest = [l for l in labels if not is_ctrl(l)]
        pal = dict(zip(rest, self.n_colors(max(len(rest), 1) + skip)[skip:]))
        return {l: (self.neutral if is_ctrl(l) else pal[l]) for l in labels}

    def figsize(self, columns: int = 1, aspect: float = 0.72, legend_outside: bool = False):
        """(width, height) in inches for a single- (3.5 in) or double-column (7.2 in) figure,
        scaled up for talk/poster contexts so the larger fonts keep the same proportions.
        legend_outside=True adds room on the right for an outside legend."""
        w = (3.5 if columns == 1 else 7.2) * self.scale
        return (w * (1.28 if legend_outside else 1.0), w * aspect)

    # ------------------------------------------------------------ panel furniture
    def panel(self, ax, letter: str | None = None, title: str | None = None, upper: bool | None = None):
        """Panel letter + title in the template's style, above the top-left corner.
        Use instead of ax.set_title so titles, badges and fonts match across figures.
        The template picks the letter case; upper=True/False overrides it (keep one choice
        for the whole conversation)."""
        s, k = dict(self.style), self.scale
        if upper is not None:
            s["upper"] = upper
        import matplotlib
        fs = float(matplotlib.rcParams["axes.titlesize"])
        dy, x_title = 7 * k, 0.0
        kw = dict(xy=(0, 1), xycoords="axes fraction", textcoords="offset points", va="bottom", ha="left",
                  annotation_clip=False)
        if s["label"] == "badge" and letter:
            col = s["badge"][self._n_panels % len(s["badge"])]
            ax.annotate(letter.upper() if s["upper"] else letter.lower(), xytext=(1.5 * k, dy), fontsize=fs - 1,
                        fontweight="bold", color=s["badge_text"], family=self.body_fonts,
                        bbox=dict(boxstyle="round,pad=0.28,rounding_size=0.18", fc=col, ec="none"), **kw)
            x_title = fs * 1.75
        elif s["label"] == "bar":
            ax.annotate(" ", xytext=(0, dy), fontsize=fs, family=self.body_fonts,
                        bbox=dict(boxstyle="square,pad=0.08", fc=s["badge"][0], ec="none"), **kw)
            x_title = fs * 0.75
            if letter:
                letter = letter.upper() if upper else letter.lower()
                title = f"{letter}  {title}" if title else letter
        elif letter:
            ax.annotate(letter.upper() if s["upper"] else letter.lower(), xytext=(0, dy), fontsize=fs + 1,
                        fontweight="bold", color=self.text, family=self.body_fonts, **kw)
            x_title = fs * 1.4
        if title:
            ax.annotate(title, xytext=(x_title, dy), fontsize=fs, fontweight="bold", color=self.text,
                        family=self.title_fonts, **kw)
        self._n_panels += 1
        return ax

    panel_label = panel  # backwards-compatible name

    def suptitle(self, fig, text: str, **kw):
        kw = {**dict(x=0.01, ha="left", fontweight="bold", family=self.title_fonts, color=self.text), **kw}
        return fig.suptitle(text, **kw)

    def legend(self, ax, title: str | None = None, outside: bool | None = None, **kw):
        """Legend in the template's position: outside-right with compact handles, or inside.
        outside=True forces the outside-right position (donuts, dense scatters)."""
        if outside is None:
            outside = self.style["legend"] == "right" and "loc" not in kw  # an explicit loc means inside
        if outside:
            base = dict(loc="center left", bbox_to_anchor=(1.01, 0.5), handlelength=1.0, handletextpad=0.5,
                        labelspacing=0.55, borderaxespad=0.0)
        else:
            base = dict(loc="best", handlelength=1.6, labelspacing=0.4)
        from matplotlib.collections import PathCollection
        if (self.style["scatter_s"] < 12 and not ax.lines
                and any(isinstance(c, PathCollection) for c in ax.collections)):
            base["markerscale"] = 1.8  # scatter-only axes: tiny points would be unreadable as handles
        return ax.legend(title=title, **{**base, **kw})

    def _grid(self, ax, on: bool | None = None, axis: str | None = None):
        g = self.style["grid"]
        if on is False or (on is None and g == "none"):
            ax.grid(False)
        else:
            ax.grid(True, axis=axis or (g if g != "none" else "both"))

    # ------------------------------------------------------------ chart helpers
    def curve(self, ax, x, y, color=None, label=None, **kw):
        """Smooth line without markers (fitted curve, model, density). Plain ax.plot would
        inherit the template's markers. Pair with points(...) for 'fit + data' charts."""
        base = dict(color=color or ax._get_lines.get_next_color(), marker="none",
                    lw=self.style["lw"] * self.scale, label=label)
        base.update(kw)
        return ax.plot(x, y, **base)

    def points(self, ax, x, y, yerr=None, label=None, color=None, **kw):
        """Markers with optional error bars and no connecting line (data under a fitted curve)."""
        kw.setdefault("ls", "none")
        return self.lineplot(ax, x, y, yerr=yerr, label=label, color=color, **kw)

    def lineplot(self, ax, x, y, yerr=None, label=None, color=None, band=False, **kw):
        """Line with markers and optional error bars (or a shaded band) at the template's weights."""
        s, k = self.style, self.scale
        color = color or ax._get_lines.get_next_color()
        mfc = self.bg if s["marker_face"] == "bg" else color
        base = dict(color=color, marker="o", ms=s["ms"] * k, lw=s["lw"] * k, mfc=mfc, mec=color,
                    label=label)
        if s["marker_face"] == "bg":
            base["mew"] = 1.2 * k  # only for hollow markers: a zero edge width would also erase error caps
        base.update(kw)
        if yerr is not None and band:
            import numpy as np
            y_, e_ = np.asarray(y, float), np.asarray(yerr, float)
            ax.fill_between(x, y_ - e_, y_ + e_, color=color, alpha=0.18, lw=0)
            out = ax.plot(x, y, **base)
        elif yerr is not None:
            out = ax.errorbar(x, y, yerr=yerr, capsize=s["capsize"] * k, elinewidth=0.9 * k,
                              capthick=0.9 * k, **base)
        else:
            out = ax.plot(x, y, **base)
        self._grid(ax)
        return out

    def bars(self, ax, categories, groups: dict, yerr: dict | None = None, colors: dict | None = None,
             stacked=False, horizontal=False, points: dict | None = None):
        """Grouped (or stacked) bars. groups = {series label: values per category}.
        points = {series label: array (n_replicates, n_categories)} overlays the replicates."""
        import numpy as np
        s, k = self.style, self.scale
        colors = colors or self.assign(groups)
        n, x = len(groups), np.arange(len(categories))
        w = s["bar_width"] if stacked else s["bar_width"] / n
        bottom = np.zeros(len(categories))
        f = ax.barh if horizontal else ax.bar
        for i, (lab, vals) in enumerate(groups.items()):
            vals = np.asarray(vals, float)
            pos = x if stacked else x + (i - (n - 1) / 2) * w
            err = None if yerr is None else yerr.get(lab)
            ekw = dict(error_kw=dict(ecolor=self.text, elinewidth=0.9 * k, capsize=s["capsize"] * k,
                                     capthick=0.9 * k))
            if horizontal:
                bc = f(pos, vals, w, left=bottom if stacked else None, xerr=err, color=colors[lab], label=lab,
                       edgecolor=self.bg, linewidth=0.6 * k, **ekw)
            else:
                bc = f(pos, vals, w, bottom=bottom if stacked else None, yerr=err, color=colors[lab], label=lab,
                       edgecolor=self.bg, linewidth=0.6 * k, **ekw)
            if bc.errorbar is not None:
                # halo in the background colour: the half of the bar lying over a dark bar stays visible
                import matplotlib.patheffects as pe
                halo = [pe.Stroke(linewidth=2.4 * k, foreground=self.bg), pe.Normal()]
                _, caps, lines = bc.errorbar.lines
                for art in (*caps, *lines):
                    art.set_path_effects(halo)
            if stacked:
                bottom = bottom + vals
            elif points is not None and lab in points:
                reps = np.atleast_2d(np.asarray(points[lab], float))
                jit = np.linspace(-0.22, 0.22, reps.shape[0])[:, None] * w if reps.shape[0] > 1 else 0
                px, py = (pos[None, :] + jit) * np.ones_like(reps), reps
                ax.scatter(*((py, px) if horizontal else (px, py)), s=7 * k * k, facecolor=self.bg,
                           edgecolor=self.text, linewidths=0.6 * k, zorder=3)
        if horizontal:
            ax.set_yticks(x, categories); ax.invert_yaxis(); ax.tick_params(axis="y", length=0)
        else:
            ax.set_xticks(x, categories); ax.tick_params(axis="x", length=0)
        self._grid(ax, on=self.style["grid"] != "none", axis="x" if horizontal else "y")
        return ax

    def scatter(self, ax, x, y, labels=None, colors: dict | None = None, ellipse: str | None = None, **kw):
        """Scatter coloured by label (clusters, groups), with the template's point size and,
        where the template uses them, 2-sigma cluster outlines."""
        import numpy as np
        s, k = self.style, self.scale
        x, y = np.asarray(x, float), np.asarray(y, float)
        base = dict(s=s["scatter_s"] * k * k, alpha=s["scatter_alpha"], linewidths=0)
        base.update(kw)
        if labels is None:
            ax.scatter(x, y, **base)
        else:
            labels = np.asarray(labels)
            order = list(dict.fromkeys(labels.tolist()))
            colors = colors or self.assign(order)
            mode = ellipse or s["ellipse"]
            for lab in order:
                m = labels == lab
                ax.scatter(x[m], y[m], color=colors[lab], label=str(lab), **base)
                if mode != "none" and m.sum() > 3:
                    self._ellipse(ax, x[m], y[m], colors[lab], mode)
        self._grid(ax)
        return ax

    def _ellipse(self, ax, x, y, color, mode, n_std=2.2):
        import numpy as np
        from matplotlib.patches import Ellipse
        vals, vecs = np.linalg.eigh(np.cov(x, y))
        ang = np.degrees(np.arctan2(vecs[1, 1], vecs[0, 1]))
        w, h = 2 * n_std * np.sqrt(vals[::-1])
        kw = (dict(fc="none", ec=color, ls=(0, (4, 3)), lw=1.0 * self.scale) if mode == "dashed"
              else dict(fc=color, ec="none", alpha=0.16))
        ax.add_patch(Ellipse((x.mean(), y.mean()), w, h, angle=ang, zorder=0.5, **kw))

    def violin(self, ax, data, labels=None, colors=None):
        """Violins with the template's inner mark (white mini box, or thin line + median dot)."""
        import numpy as np
        s, k = self.style, self.scale
        n = len(data)
        cols = colors or self.n_colors(n)
        if isinstance(cols, dict):
            cols = [cols[l] for l in labels]
        pos = np.arange(1, n + 1)
        parts = ax.violinplot(data, positions=pos, showextrema=False, widths=0.78)
        for b, c in zip(parts["bodies"], cols):
            b.set_facecolor(c); b.set_edgecolor("none"); b.set_alpha(0.92)
        q = [np.percentile(d, [25, 50, 75]) for d in data]
        ink = "#1B2530" if self.dark else self.text  # box outline must read on the white box
        if s["violin"] == "box":
            for p, d, (q1, med, q3) in zip(pos, data, q):
                lo, hi = max(np.min(d), q1 - 1.5 * (q3 - q1)), min(np.max(d), q3 + 1.5 * (q3 - q1))
                ax.vlines(p, lo, hi, color=self.text, lw=0.8 * k, zorder=3)
                ax.bar(p, q3 - q1, 0.11, bottom=q1, color="#FFFFFF", edgecolor=ink, linewidth=0.8 * k, zorder=4)
                ax.hlines(med, p - 0.055, p + 0.055, color=ink, lw=1.1 * k, zorder=5)
        else:
            for p, (q1, med, q3) in zip(pos, q):
                ax.vlines(p, q1, q3, color="#FFFFFF", lw=1.3 * k, zorder=3)
                ax.scatter([p], [med], s=10 * k * k, color="#FFFFFF", zorder=4, linewidths=0)
        if labels is not None:
            ax.set_xticks(pos, labels)
        ax.tick_params(axis="x", length=0)
        self._grid(ax, on=self.style["grid"] != "none", axis="y")
        return ax

    def heatmap(self, ax, data, kind="seq", xticklabels=None, yticklabels=None, vmin=None, vmax=None,
                cbar=True, cbar_label=None, annotate=False, fmt="{:.1f}"):
        """Heatmap with the template's cell gaps and a slim frameless colourbar.
        kind="div" centres the diverging map on zero with symmetric limits."""
        import numpy as np
        k = self.scale
        data = np.asarray(data, float)
        if kind == "div":
            lim = max(abs(np.nanmin(data)), abs(np.nanmax(data))) if vmax is None else vmax
            vmin, vmax = (-lim, lim) if vmin is None else (vmin, vmax)
        gap = self.style["heat_gap"] * k
        mesh = ax.pcolormesh(data, cmap=self.div if kind == "div" else self.seq, vmin=vmin, vmax=vmax,
                             edgecolors=self.bg if gap else "face", linewidth=gap, rasterized=not gap)
        ax.invert_yaxis()
        ny, nx = data.shape
        ax.set_xticks(np.arange(nx) + 0.5, xticklabels if xticklabels is not None else [])
        ax.set_yticks(np.arange(ny) + 0.5, yticklabels if yticklabels is not None else [])
        ax.tick_params(length=0)
        for sp in ax.spines.values():
            sp.set_visible(False)
        ax.grid(False)
        if annotate:
            import matplotlib
            cmap, norm = mesh.get_cmap(), mesh.norm
            for (i, j), v in np.ndenumerate(data):
                r, g, b, _ = cmap(norm(v))
                ink = "#FFFFFF" if 0.299 * r + 0.587 * g + 0.114 * b < 0.5 else "#222222"
                ax.text(j + 0.5, i + 0.5, fmt.format(v), ha="center", va="center", color=ink,
                        fontsize=float(matplotlib.rcParams["font.size"]) - 2)
        if cbar:
            cb = ax.figure.colorbar(mesh, ax=ax, shrink=1.0, aspect=24, pad=0.03)
            cb.outline.set_visible(False)
            cb.ax.tick_params(length=2 * k, width=0.6 * k)
            if cbar_label:
                cb.set_label(cbar_label)
        return mesh

    def donut(self, ax, values, labels=None, colors=None, center_text=None):
        """Ring chart with background-coloured gaps and optional centre text."""
        cols = colors or self.n_colors(len(values))
        if isinstance(cols, dict):
            cols = [cols[l] for l in labels]
        wedges, _ = ax.pie(values, colors=cols, startangle=90, counterclock=False,
                           wedgeprops=dict(width=self.style["donut_width"], edgecolor=self.bg,
                                           linewidth=1.2 * self.scale))
        if labels is not None:
            for w, l in zip(wedges, labels):
                w.set_label(str(l))
        if center_text:
            ax.text(0, 0, center_text, ha="center", va="center", color=self.text, fontweight="bold",
                    family=self.title_fonts)
        ax.set_aspect("equal")
        ax.set_anchor("W")  # keep the ring flush left so its panel title aligns with the others
        return wedges

    def as_dict(self) -> dict:
        d = {k: v for k, v in THEMES[self.key].items() if k != "style"}
        return {"key": self.key, **d, "style": self.style,
                "fonts": {"body": SANS, "titles": self.title_fonts}}


def _register_cmaps(t: Theme):
    import matplotlib
    from matplotlib.colors import LinearSegmentedColormap, ListedColormap
    for name, cmap in (
        (t.seq, LinearSegmentedColormap.from_list(t.seq, t.sequential)),
        (t.div, LinearSegmentedColormap.from_list(t.div, t.diverging)),
        (t.cat, ListedColormap(t.colors, name=t.cat)),
    ):
        with warnings.catch_warnings():  # re-applying a theme re-registers its maps; that is fine
            warnings.simplefilter("ignore")
            matplotlib.colormaps.register(cmap, name=name, force=True)
            matplotlib.colormaps.register(cmap.reversed(), name=name + "_r", force=True)


def apply_theme(name: str | None = None, font_size: float = 8, context: str = "paper") -> Theme:
    """Apply a journal template to matplotlib (and therefore seaborn/pandas plots).

    context: "paper" (8 pt, thin lines); "talk" and "poster" scale fonts, lines and markers up.
    Returns the Theme: colours (.colors, .seq, .div, .highlight, .neutral, .assign) and the
    styled chart helpers (.panel, .lineplot, .bars, .scatter, .violin, .heatmap, .donut, .legend).
    """
    import matplotlib as mpl
    from cycler import cycler

    k = {"paper": 1.0, "talk": 1.5, "poster": 2.0}.get(context, 1.0)
    t = Theme(resolve(name), scale=k)
    _register_cmaps(t)
    s = t.style
    fs = font_size * k
    mpl.rcParams.update({
        "figure.facecolor": t.bg, "savefig.facecolor": t.bg, "axes.facecolor": t.panel_bg,
        "text.color": t.text, "axes.labelcolor": t.text, "axes.titlecolor": t.text,
        "axes.edgecolor": t.muted, "xtick.color": t.muted, "ytick.color": t.muted,
        "xtick.labelcolor": t.text, "ytick.labelcolor": t.text,
        "grid.color": t.grid, "grid.linewidth": 0.6 * k, "axes.axisbelow": True,
        "axes.grid": s["grid"] != "none", "axes.grid.axis": s["grid"] if s["grid"] != "none" else "both",
        "axes.prop_cycle": cycler(color=t.colors),
        "image.cmap": t.seq,
        "font.family": "sans-serif", "font.sans-serif": t.body_fonts, "font.serif": _installed(SERIF),
        "font.size": fs, "axes.labelsize": fs, "axes.titlesize": fs + 1,
        "xtick.labelsize": fs - 1, "ytick.labelsize": fs - 1, "legend.fontsize": fs - 1,
        "legend.title_fontsize": fs - 1, "figure.titlesize": fs + 3,
        "axes.titleweight": "bold", "axes.titlelocation": "left", "axes.titlepad": 6 * k,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.linewidth": 0.8 * k, "xtick.major.width": 0.8 * k, "ytick.major.width": 0.8 * k,
        "xtick.major.size": 3 * k, "ytick.major.size": 3 * k,
        "lines.linewidth": s["lw"] * k, "lines.markersize": s["ms"] * k, "errorbar.capsize": s["capsize"] * k,
        "scatter.marker": "o", "patch.linewidth": 0.6 * k, "patch.edgecolor": t.bg,
        "boxplot.medianprops.color": t.text, "boxplot.boxprops.color": t.text,
        "boxplot.whiskerprops.color": t.text, "boxplot.capprops.color": t.text,
        "boxplot.flierprops.markeredgecolor": t.muted,
        "legend.frameon": False, "legend.labelcolor": t.text,
        "figure.dpi": 120, "savefig.dpi": 300, "savefig.bbox": "tight",
        "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none",
    })
    return t


def plotly_template(name: str | None = None) -> dict:
    """Plotly layout template dict: fig.update_layout(template=plotly_template("nbt"))."""
    t = Theme(resolve(name))
    s = t.style
    n, m = len(t.sequential) - 1, len(t.diverging) - 1
    grid = s["grid"]
    title_font = ("Georgia, 'Times New Roman', serif" if s["title_font"] == "serif"
                  else "Arial, Helvetica, sans-serif")

    def axis(which):
        return dict(linecolor=t.muted, gridcolor=t.grid, zeroline=False, ticks="outside", tickcolor=t.muted,
                    showline=True, mirror=False, showgrid=grid == "both" or grid == which)
    return {"layout": {
        "colorway": t.colors, "paper_bgcolor": t.bg, "plot_bgcolor": t.panel_bg,
        "font": {"family": "Arial, Helvetica, sans-serif", "color": t.text, "size": 12},
        "title": {"font": {"family": title_font, "color": t.text, "size": 16}, "x": 0.02, "xanchor": "left"},
        "xaxis": axis("x"), "yaxis": axis("y"),
        "colorscale": {
            "sequential": [[i / n, c] for i, c in enumerate(t.sequential)],
            "diverging": [[i / m, c] for i, c in enumerate(t.diverging)],
        },
        "legend": {"bgcolor": "rgba(0,0,0,0)"},
    }, "data": {
        "scatter": [{"line": {"width": s["lw"] * 1.4}, "marker": {"size": s["ms"] * 1.8}}],
        "violin": [{"box": {"visible": s["violin"] == "box"}, "meanline": {"visible": False}}],
        "heatmap": [{"xgap": s["heat_gap"] * 2, "ygap": s["heat_gap"] * 2}],
        "pie": [{"hole": 1 - s["donut_width"], "marker": {"line": {"color": t.bg, "width": 2}}}],
    }}


# ---------------------------------------------------------------- previews
def gallery(out: str):
    """One row per theme: categorical swatches, sequential ramp, diverging ramp."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    plt.rcdefaults()
    keys = list(THEMES)
    fig, axes = plt.subplots(len(keys), 3, figsize=(11, 0.95 * len(keys)),
                             gridspec_kw={"width_ratios": [3, 1.3, 1.3], "wspace": 0.05, "hspace": 0.9})
    fig.patch.set_facecolor("white")
    grad = np.linspace(0, 1, 256)[None, :]
    for row, key in zip(axes, keys):
        t = Theme(key)
        _register_cmaps(t)
        ax = row[0]
        ax.set_facecolor(t.bg)
        for i, c in enumerate(t.colors):
            ax.add_patch(plt.Rectangle((i + 0.08, 0.12), 0.84, 0.76, color=c, lw=0))
        ax.set_xlim(0, 8); ax.set_ylim(0, 1)
        ax.set_title(f"{key}   ·   {t.label}", loc="left", fontsize=9, fontweight="bold", color="#222")
        row[1].imshow(grad, aspect="auto", cmap=t.seq)
        row[2].imshow(grad, aspect="auto", cmap=t.div)
        for a in row:
            a.set_xticks([]); a.set_yticks([])
            for sp in a.spines.values():
                sp.set_visible(True); sp.set_color("#DDD"); sp.set_linewidth(0.6)
    axes[0][1].set_title("sequential", fontsize=8, color="#666", loc="right")
    axes[0][2].set_title("diverging", fontsize=8, color="#666", loc="right")
    fig.savefig(out, dpi=170, bbox_inches="tight", facecolor="white")
    return out


def demo(name: str, out: str, dpi: int | None = None):
    """Eight-panel sample showing the template's chart characteristics."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    plt.rcdefaults()
    t = apply_theme(name)
    rng = np.random.default_rng(3)
    fig, axs = plt.subplots(2, 4, figsize=(12.5, 5.8), constrained_layout=True)
    fig.get_layout_engine().set(h_pad=0.14, w_pad=0.1)
    t.suptitle(fig, t.label)
    groups = ["Treated", "Partial", "Control"]
    gc = t.assign(groups)

    ax = axs[0, 0]; x = np.arange(6)
    for i, lab in enumerate(groups):
        y = (3 - i) * x * 0.6 + 2 + rng.normal(0, 0.3, 6)
        t.lineplot(ax, x, y, yerr=0.5 + 0.1 * x, label=lab, color=gc[lab])
    ax.set(xlabel="Time (d)", ylabel="Response"); t.legend(ax, loc="upper left")
    t.panel(ax, "a", "Line + error bars")

    ax = axs[0, 1]
    means = {g: rng.uniform(2, 9, 3) for g in groups}
    t.bars(ax, ["IFN-γ", "IL-2", "TNF-α"], means, yerr={g: rng.uniform(0.3, 0.9, 3) for g in groups},
           colors=gc, points={g: means[g] + rng.normal(0, 0.5, (4, 3)) for g in groups})
    ax.set(ylabel="Concentration"); t.panel(ax, "b", "Grouped bars")

    ax = axs[0, 2]
    cen = np.array([[-6, -2], [6, 0], [0, 6], [6, 8], [-5, 7]])
    lab = np.repeat([f"Cluster {i + 1}" for i in range(5)], 70)
    pts = np.repeat(cen, 70, axis=0) + rng.normal(0, 1.3, (350, 2))
    t.scatter(ax, pts[:, 0], pts[:, 1], lab)
    ax.set(xlabel="UMAP 1", ylabel="UMAP 2"); t.legend(ax); t.panel(ax, "c", "Scatter clusters")

    ax = axs[0, 3]
    t.violin(ax, [rng.normal(m, 1, 120) for m in (0, 0.6, 1.4, 0.9, 0.2)], labels=list("ABCDE"))
    ax.set(ylabel="Expression"); t.panel(ax, "d", "Violin")

    ax = axs[1, 0]
    t.heatmap(ax, rng.random((7, 8)).cumsum(1), xticklabels=[f"S{i + 1}" for i in range(8)],
              yticklabels=[f"Gene{c}" for c in "ABCDEFG"])
    t.panel(ax, "e", "Sequential heatmap")

    ax = axs[1, 1]
    m = np.corrcoef(rng.normal(size=(8, 30)) + rng.normal(size=(1, 30)) * np.linspace(-1, 1, 8)[:, None])
    t.heatmap(ax, m, kind="div", vmax=1); t.panel(ax, "f", "Diverging matrix")

    ax = axs[1, 2]
    xx = np.logspace(-2, 2, 9); fine = np.logspace(-2, 2, 100)
    for i, (labd, ec50) in enumerate([("Drug A", 0.3), ("Drug B", 2.0), ("Drug C", 12.0)]):
        f = lambda c: 100 / (1 + (ec50 / c) ** 1.2)
        t.curve(ax, fine, f(fine), color=t.color(i))
        t.points(ax, xx, f(xx) + rng.normal(0, 2, 9), yerr=4, label=labd, color=t.color(i))
    ax.set(xscale="log", xlabel="Concentration (nM)", ylabel="Response (%)"); t.legend(ax, loc="upper left")
    t.panel(ax, "g", "Dose–response")

    ax = axs[1, 3]
    names = ["Lipid", "Carbohydrate", "Amino acid", "Nucleotide", "Energy"]
    t.donut(ax, [30, 24, 20, 14, 12], names, colors=t.assign(names, control=[], skip=0), center_text="Pathways")
    t.legend(ax, outside=True); t.panel(ax, "h", "Donut")

    fig.savefig(out, dpi=dpi)
    return out


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    if cmd == "list":
        for k, d in THEMES.items():
            print(f"{k:32s} {d['label']}  [{d['mood']}]")
    elif cmd == "show":
        print(json.dumps(Theme(resolve(sys.argv[2])).as_dict(), indent=2, ensure_ascii=False))
    elif cmd == "gallery":
        print(gallery(sys.argv[2] if len(sys.argv) > 2 else "theme_gallery.png"))
    elif cmd == "demo":
        print(demo(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else f"demo_{resolve(sys.argv[2])}.png"))
    else:
        sys.exit(__doc__)
