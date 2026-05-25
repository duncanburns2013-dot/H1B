# Automating the quarterly dashboard refresh

This repo can now rebuild the two FY-quarter sections of the dashboard
automatically — the **national FY2026 Snapshot** and the
**Massachusetts FY-quarter Deep Dive** — from raw government data files.
Everything else in `index.html` (the original 50 charts, styling, tabs)
is never touched.

There are two ways to run it. You only need one.

---

## How it works

`build.py` reads up to three data files from the `data/` folder,
recomputes the chart numbers, and rewrites the marked sections of
`index.html`. The numbers live inside tiny invisible markers in the HTML,
so the script knows exactly where to write and leaves everything else
alone.

---

## The three data files

Each quarter you download three files and rename them exactly like this:

| File in `data/`                          | Where to get it |
|-------------------------------------------|-----------------|
| `LCA_Disclosure_Data_FY2026_Q2.xlsx`      | DOL FLAG site — Performance Data — quarterly **LCA Disclosure Data**. Keep the original filename; the script reads the fiscal year and quarter from it. |
| `Approvals_Receipts_MA.xlsx`              | USCIS H-1B Employer Data Hub — filter to **Massachusetts**, current fiscal year — Export to Excel. |
| `Approvals_Receipts_National.xlsx`        | USCIS H-1B Employer Data Hub — **all states**, current fiscal year — Export to Excel. |

You can refresh just one source if you want — the script updates whatever
charts it has data for and leaves the rest unchanged.

---

## Option A — let GitHub do it (no software needed)

1. On github.com, open your H1B repo and go into the `data/` folder.
2. Click **Add file -> Upload files** and drop in the three files above
   (replacing last quarter's files). Commit the change.
3. That's it. The **Rebuild H-1B dashboard** workflow (under the
   **Actions** tab) runs automatically, regenerates `index.html`, and
   commits it. GitHub Pages redeploys a minute or two later.

If you ever want to run it manually: Actions tab -> **Rebuild H-1B
dashboard** -> **Run workflow**.

---

## Option B — run it on your own computer

1. Install Python 3, then once: `pip install pandas openpyxl`
2. Put the three data files in the `data/` folder.
3. From the repo folder, run: `python build.py`
4. It prints a summary of every number it changed. Commit `index.html`
   and push.

---

## What the script prints

`build.py` reports the new headline numbers and lists any company it
could not categorize (it falls back to "Other"). Example:

```
Updated index.html:
  - MA deep-dive: 2799 LCAs, median $127,300, 1100 employers, 407 biotech
  - MA employers: #1 Fidelity Technology Group (404)
  - National: 100 firms, 25,328 approvals; Big Tech 10,631 / ...
```

---

## Keeping the categories accurate

The colour-coding of national employers (Indian IT / Big Tech / Finance /
Consulting) and the orange/blue split of MA employers comes from keyword
lists near the top of `build.py`. When a brand-new company appears in the
data, the script prints a note. To fix its colour, open `build.py` and add
the company to the right list (`INDIAN_IT`, `BIG_TECH`, `FINANCE`,
`CONSULTING`, or `OUTSOURCING_MA`). This is the only part you may ever need
to hand-edit.

---

## What stays manual

The script updates the chart data and the headline KPI numbers. The
descriptive sentences under each chart (e.g. "Software Developers alone:
594 filings") are left as-is — glance over them after a refresh and tweak
any wording that has gone stale. The script's printout gives you the new
figures to use.
