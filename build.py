#!/usr/bin/env python3
"""
build.py  --  H-1B dashboard refresh script
============================================

Regenerates the two FY-quarter sections of index.html (the national
"FY2026 Snapshot" and the "MA FYxxxx Qx Deep Dive") from raw government
data files. Everything else in index.html is left untouched.

HOW TO USE
----------
1. Each quarter, download three files and put them in the `data/` folder
   next to this script:

     data/LCA_Disclosure_Data_FYxxxx_Qx.xlsx   <- DOL FLAG quarterly LCA file
     data/Approvals_Receipts_MA.xlsx           <- USCIS Data Hub, MA filtered
     data/Approvals_Receipts_National.xlsx     <- USCIS Data Hub, national

   Keep the DOL filename exactly as downloaded -- the fiscal year and
   quarter are read from it (e.g. ..._FY2026_Q2.xlsx).

2. Run:   python build.py

3. The script rewrites index.html in place and prints a summary of every
   number it changed. Commit index.html and you are done.

If a data file is missing, the script simply skips the charts that depend
on it and leaves them as they were -- so you can refresh one source at a
time.

Requires: python 3.8+, pandas, openpyxl   (pip install pandas openpyxl)
"""

import os
import re
import sys
import glob
import statistics

try:
    import openpyxl
except ImportError:
    sys.exit("Missing dependency. Run:  pip install pandas openpyxl")
try:
    import pandas as pd
except ImportError:
    sys.exit("Missing dependency. Run:  pip install pandas openpyxl")

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "data")
INDEX = os.path.join(HERE, "index.html")

# ---------------------------------------------------------------------------
# CLASSIFICATION TABLES  --  this is the only part you may need to hand-edit.
# When a new company shows up in the data the script will print a warning;
# add it to the right list below so it gets coloured correctly next quarter.
# ---------------------------------------------------------------------------

# National petitioner categories for the colour-coded charts.
# 1 = Indian IT outsourcer, 2 = U.S. Big Tech, 3 = Finance, 4 = Consulting/Big4
INDIAN_IT = {  # keyword in name : canonical short name
    "TATA CONSULTANCY": "TCS", "INFOSYS": "Infosys", "COGNIZANT": "Cognizant",
    "WIPRO": "Wipro", "HCL": "HCL", "TECH MAHINDRA": "Tech Mahindra",
    "LTIMINDTREE": "LTIMindtree", "MINDTREE": "LTIMindtree", "MPHASIS": "Mphasis",
    "SYNTEL": "Syntel", "HEXAWARE": "Hexaware", "BIRLASOFT": "Birlasoft",
    "COFORGE": "Coforge", "ZENSAR": "Zensar", "PERSISTENT SYSTEMS": "Persistent",
}
BIG_TECH = [
    "AMAZON", "MICROSOFT", "GOOGLE", "APPLE INC", "META PLATFORM", "TESLA",
    "ORACLE", "NVIDIA", "INTEL", "CISCO", "SALESFORCE", "ADOBE", "QUALCOMM",
    "MICRON", "BROADCOM", "PAYPAL", "INTUIT", "VMWARE", "UBER", "EXPEDIA",
    "LINKEDIN", "SNAP INC", "PINTEREST", "DOORDASH", "EBAY", "SERVICENOW",
    "PALO ALTO", "WORKDAY", "DATABRICKS", "SNOWFLAKE", "IBM", "TEXAS INSTRUMENTS",
    "APPLIED MATERIALS",
]
FINANCE = [
    "JPMORGAN", "FIDELITY", "GOLDMAN", "MORGAN STANLEY", "BANK OF AMERICA",
    "CITIGROUP", "CITIBANK", "WELLS FARGO", "CAPITAL ONE", "STATE STREET",
    "BLACKROCK", "MASTERCARD", "VISA INC", "AMERICAN EXPRESS", "BARCLAYS",
    "DEUTSCHE BANK", "BLOOMBERG", "CHARLES SCHWAB", "BNY MELLON", "PNC BANK",
]
CONSULTING = [
    "CAPGEMINI", "ACCENTURE", "DELOITTE", "ERNST AND YOUNG", "ERNST & YOUNG",
    "KPMG", "PRICEWATERHOUSE", "MCKINSEY", "BOSTON CONSULTING", "BAIN AND COMPANY",
    "BAIN & COMPANY", "BOOZ ALLEN", "SLALOM", "PWC", "GUIDEHOUSE",
]

# MA employer chart: which firms are outsourcing/consulting (orange) vs direct (blue)
OUTSOURCING_MA = [
    "RANDSTAD", "VIRTUSA", "CONSULTING GROUP", "BAIN AND COMPANY", "BAIN & COMPANY",
    "INFOSYS", "TATA CONSULTANCY", "COGNIZANT", "WIPRO", "HCL", "ACCENTURE",
    "DELOITTE", "CAPGEMINI", "LTIMINDTREE", "TECH MAHINDRA", "KFORCE", "COMPUNNEL",
    "MCKINSEY", "ERNST AND YOUNG", "KPMG", "PRICEWATERHOUSE", "MPHASIS", "SAPIENT",
    "COLLABERA", "MINDTREE", "SYNTEL", "PERSISTENT", "STAFFING", "TEK SYSTEMS",
    "TEKSYSTEMS", "APEX SYSTEMS",
]

# Friendly display names. Anything not listed falls back to an automatic cleaner.
SHORT_SOC = {
    "Software Quality Assurance Analysts and Testers": "Software QA Analysts/Testers",
    "Medical Scientists, Except Epidemiologists": "Medical Scientists",
    "Biochemists and Biophysicists": "Biochemists & Biophysicists",
    "Biological Scientists, All Other": "Biological Scientists",
    "Computer and Information Systems Managers": "Computer & IS Managers",
    "Information Technology Project Managers": "IT Project Managers",
    "Molecular and Cellular Biologists": "Molecular & Cellular Biologists",
    "Computer Systems Engineers/Architects": "Computer Systems Engineers",
    "Accountants and Auditors": "Accountants & Auditors",
}
SHORT_EMPLOYER = {
    "FIDELITY TECHNOLOGY GROUP": "Fidelity Technology Group",
    "RANDSTAD DIGITAL": "Randstad Digital LLC",
    "VIRTUSA CORPORATION": "Virtusa Corporation",
    "ANALOG DEVICES": "Analog Devices Inc",
    "BOSTON CONSULTING GROUP": "Boston Consulting Group",
    "STATE STREET BANK": "State Street Bank & Trust",
    "MATHWORKS": "The MathWorks Inc",
    "BAIN AND COMPANY": "Bain & Company Inc",
    "THERMO FISHER": "Thermo Fisher Scientific",
    "SCHNEIDER ELECTRIC": "Schneider Electric USA",
    "VERTEX PHARMACEUTICALS": "Vertex Pharmaceuticals",
    "MASS GENERAL": "Mass General Hospital",
    "GENERAL HOSP": "Mass General Hospital",
    "AKAMAI": "Akamai Technologies",
    "STAPLES": "Staples Inc",
    "HARVARD": "Harvard University",
    "BRIGHAM AND WOMEN": "Brigham & Women's Hospital",
    "DANA-FARBER": "Dana-Farber Cancer Inst",
    "MASSACHUSETTS INSTITUTE OF TECHNOLOGY": "MIT",
    "WAYFAIR": "Wayfair LLC",
    "UMASS CHAN": "UMass Chan Medical",
    "UNIVERSITY OF MASSACHUSETTS CHAN": "UMass Chan Medical",
}
SHORT_NATIONAL = {
    "AMAZON COM SERVICES": "Amazon.com Services", "AMAZON.COM SERVICES": "Amazon.com Services",
    "TATA CONSULTANCY": "Tata Consultancy Svcs", "MICROSOFT": "Microsoft",
    "INFOSYS": "Infosys", "GOOGLE": "Google", "APPLE INC": "Apple",
    "COGNIZANT": "Cognizant", "META PLATFORM": "Meta Platforms", "TESLA": "Tesla",
    "WAL-MART ASSOCIATES": "Wal-Mart Associates", "WALMART ASSOCIATES": "Wal-Mart Associates",
    "JPMORGAN": "JPMorgan Chase", "CAPGEMINI": "Capgemini America",
    "ACCENTURE": "Accenture LLP", "ORACLE": "Oracle America",
    "DELOITTE": "Deloitte Consulting", "HCL AMERICA": "HCL America",
    "FIDELITY TECHNOLOGY": "Fidelity Tech (MA)", "ERNST AND YOUNG": "Ernst & Young",
    "LTIMINDTREE": "LTIMindtree", "NVIDIA": "NVIDIA", "WIPRO": "Wipro",
}
SHORT_UNIVERSITY = {
    "HARVARD UNIVERSITY": "Harvard University",
    "MASSACHUSETTS INSTITUTE OF TECHNOLOGY": "MIT",
    "UNIVERSITY OF MASSACHUSETTS CHAN MEDICAL SCHOOL": "UMass Chan Medical",
    "TRUSTEES OF BOSTON UNIVERSITY": "Trustees of Boston U",
    "NORTHEASTERN UNIVERSITY": "Northeastern U",
    "TUFTS UNIVERSITY": "Tufts University",
    "UNIVERSITY OF MASSACHUSETTS AMHERST": "UMass Amherst",
    "BOSTON COLLEGE": "Boston College",
    "UNIVERSITY OF MASSACHUSETTS LOWELL": "UMass Lowell",
    "BRANDEIS UNIVERSITY": "Brandeis University",
}
NAICS2_NAMES = {
    "54": "Prof/Sci/Tech (54)", "62": "Healthcare (62)", "61": "Education (61)",
    "51": "Information (51)", "52": "Finance (52)", "33": "Mfg (33)",
    "32": "Mfg (32)", "31": "Mfg (31)", "44-45": "Retail (44-45)",
    "42": "Wholesale (42)", "56": "Admin/Support (56)", "23": "Construction (23)",
    "81": "Other Services (81)", "53": "Real Estate (53)", "48-49": "Transport (48-49)",
    "92": "Public Admin (92)", "21": "Mining (21)", "22": "Utilities (22)",
    "11": "Agriculture (11)", "55": "Mgmt of Companies (55)", "71": "Arts/Rec (71)",
    "72": "Hospitality (72)",
}

WAGE_MULT = {"year": 1, "hour": 2080, "week": 52, "bi-weekly": 26,
             "biweekly": 26, "month": 12, "monthly": 12}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def log(msg):
    print(msg, flush=True)


def jsarr(values):
    """Render a Python list as a compact JS array literal."""
    out = []
    for v in values:
        if isinstance(v, str):
            out.append('"' + v.replace('"', "'") + '"')
        else:
            out.append(str(v))
    return "[" + ",".join(out) + "]"


def title_clean(name):
    """Generic 'SOME COMPANY LLC' -> 'Some Company' cleaner."""
    n = re.sub(r"\bD B A\b.*$", "", str(name), flags=re.I).strip()
    n = re.sub(r"\b(LLC|INC|CORP|CORPORATION|LTD|LIMITED|CO|LP|LLP|PC|PLLC|"
               r"COMPANY|INCORPORATED)\b\.?", "", n, flags=re.I).strip(" ,.")
    return n.title() if n else str(name).title()


def short_name(raw, table, fallback=None):
    u = str(raw).upper().strip()
    for key, val in table.items():
        if key in u:
            return val
    return fallback if fallback is not None else title_clean(raw)


def category(name):
    u = str(name).upper()
    for kw in INDIAN_IT:
        if kw in u:
            return 1
    if any(kw in u for kw in BIG_TECH):
        return 2
    if any(kw in u for kw in FINANCE):
        return 3
    if any(kw in u for kw in CONSULTING):
        return 4
    return 5


def is_outsourcing(name):
    u = str(name).upper()
    return 1 if any(kw in u for kw in OUTSOURCING_MA) else 0


def median_int(seq):
    seq = [x for x in seq if x is not None and x == x]
    return int(round(statistics.median(seq))) if seq else 0


# ---------------------------------------------------------------------------
# Data loaders
# ---------------------------------------------------------------------------

def find_file(*patterns):
    for pat in patterns:
        hits = sorted(glob.glob(os.path.join(DATA_DIR, pat)))
        if hits:
            return hits[0]
    return None


def load_lca_ma(path):
    """Stream the DOL LCA workbook (large) and keep only MA-worksite rows."""
    want = ["CASE_STATUS", "VISA_CLASS", "SOC_TITLE", "WORKSITE_CITY",
            "WORKSITE_STATE", "NAICS_CODE", "EMPLOYER_NAME",
            "WAGE_RATE_OF_PAY_FROM", "WAGE_UNIT_OF_PAY", "PW_WAGE_LEVEL"]
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    rows = ws.iter_rows(values_only=True)
    header = [str(c).strip() if c is not None else "" for c in next(rows)]
    idx = {c: header.index(c) for c in want if c in header}
    if "WORKSITE_STATE" not in idx:
        wb.close()
        raise ValueError("DOL file has no WORKSITE_STATE column")
    st = idx["WORKSITE_STATE"]
    vc = idx.get("VISA_CLASS")
    recs = []
    for r in rows:
        # MA worksite, H-1B family only (excludes E-3 Australia visas)
        if r[st] == "MA" and (vc is None or str(r[vc]).startswith("H-1B")):
            recs.append({c: r[i] for c, i in idx.items()})
    wb.close()
    df = pd.DataFrame(recs)
    # annualised offered wage
    w = pd.to_numeric(df["WAGE_RATE_OF_PAY_FROM"], errors="coerce")
    unit = df["WAGE_UNIT_OF_PAY"].astype(str).str.strip().str.lower()
    df["ANN"] = w * unit.map(WAGE_MULT).fillna(1)
    return df


def parse_uscis(path):
    """USCIS Data Hub employer export -> [(name, count), ...] sorted desc."""
    x = pd.read_excel(path, header=None)
    recs = []
    for i in range(2, len(x)):
        name = x.iloc[i, 0]
        nums = [v for v in x.iloc[i, 1:].tolist() if pd.notna(v)]
        if isinstance(name, str) and name.strip() and nums:
            try:
                recs.append((name.strip(), int(float(nums[0]))))
            except (ValueError, TypeError):
                pass
    recs.sort(key=lambda t: -t[1])
    return recs


# ---------------------------------------------------------------------------
# index.html patching
# ---------------------------------------------------------------------------

def set_const(html, var, values):
    pat = re.compile(r"(const\s+" + re.escape(var) + r"\s*=\s*)\[[^\]]*\]")
    new, n = pat.subn(lambda m: m.group(1) + jsarr(values), html, count=1)
    if n == 0:
        log("  ! could not find JS variable: const %s" % var)
    return new


def set_html_marker(html, key, value):
    pat = re.compile(r"(<!--A:" + re.escape(key) + r"-->).*?(<!--/A-->)", re.S)
    new, n = pat.subn(lambda m: m.group(1) + str(value) + m.group(2), html, count=1)
    if n == 0:
        log("  ! could not find HTML marker: %s" % key)
    return new


def set_js_marker(html, key, value):
    """Replace the numeric/array token immediately before /*A:key*/."""
    pat = re.compile(r"(?:\[[\d.,\s]*\]|[\d.]+)(/\*A:" + re.escape(key) + r"\*/)")
    new, n = pat.subn(lambda m: str(value) + m.group(1), html, count=1)
    if n == 0:
        log("  ! could not find JS marker: %s" % key)
    return new


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if not os.path.isfile(INDEX):
        sys.exit("index.html not found next to build.py")
    html = open(INDEX, encoding="utf-8").read()
    changed = []

    lca_path = find_file("LCA_Disclosure_Data*.xls*", "LCA_Disclosure*.xls*")
    ma_path = find_file("Approvals_Receipts_MA.xls*", "*_MA.xls*")
    nat_path = find_file("Approvals_Receipts_National.xls*", "*_National.xls*")

    # ---- DOL LCA  -> Massachusetts deep-dive (8 charts + KPIs) -------------
    if lca_path:
        log("Reading DOL LCA file: %s" % os.path.basename(lca_path))
        m = re.search(r"FY(\d{4})[_-]?Q([1-4])", os.path.basename(lca_path), re.I)
        fy, q = (m.group(1), m.group(2)) if m else (None, None)
        df = load_lca_ma(lca_path)
        total = len(df)
        log("  MA worksite LCAs: %d" % total)

        levels = ["I", "II", "III", "IV"]
        lvl = df["PW_WAGE_LEVEL"].astype(str).str.strip()
        wlC = [int((lvl == L).sum()) for L in levels]
        wlMed = [median_int(df.loc[lvl == L, "ANN"]) for L in levels]
        html = set_const(html, "wlC", wlC)
        html = set_const(html, "wlMed", wlMed)
        html = set_js_marker(html, "maWlTotal", sum(wlC))

        # SOC occupations (top 15)
        soc = df.groupby(df["SOC_TITLE"].astype(str).str.strip())
        soc_rank = soc.size().sort_values(ascending=False).head(15)
        socN, socC, socW = [], [], []
        for title, cnt in soc_rank.items():
            socN.append(SHORT_SOC.get(title, title if len(title) <= 34
                                      else title[:32] + "..."))
            socC.append(int(cnt))
            socW.append(median_int(df.loc[df["SOC_TITLE"].astype(str).str.strip()
                                          == title, "ANN"]))
        html = set_const(html, "socN", socN)
        html = set_const(html, "socC", socC)
        html = set_const(html, "socW", socW)

        # Cities (top 15)
        city = df["WORKSITE_CITY"].astype(str).str.strip().str.upper()
        city_rank = city.value_counts().head(15)
        cityN, cityC, cityW = [], [], []
        for name, cnt in city_rank.items():
            cityN.append(name.title())
            cityC.append(int(cnt))
            cityW.append(median_int(df.loc[city == name, "ANN"]))
        html = set_const(html, "cityN", cityN)
        html = set_const(html, "cityC", cityC)
        html = set_const(html, "cityW", cityW)

        # NAICS sectors (top 8 + Other)
        n2 = df["NAICS_CODE"].astype(str).str[:2].replace(
            {"44": "44-45", "45": "44-45"})
        sec_counts = n2.value_counts()
        top8 = sec_counts.head(8)
        secN = [NAICS2_NAMES.get(code, "NAICS " + code) for code in top8.index]
        secV = [int(v) for v in top8.values]
        other = total - sum(secV)
        if other > 0:
            secN.append("Other")
            secV.append(other)
        html = set_const(html, "secN", secN)
        html = set_const(html, "secV", secV)

        # Software developer wage-level mix
        sw = df[df["SOC_TITLE"].astype(str).str.strip() == "Software Developers"]
        swlvl = sw["PW_WAGE_LEVEL"].astype(str).str.strip()
        swC = [int((swlvl == L).sum()) for L in levels]
        html = set_const(html, "swC", swC)
        html = set_js_marker(html, "maSwTotal", sum(swC))

        # Biotech / pharma hubs (NAICS 3254 pharma mfg + 5417 R&D sciences)
        na = df["NAICS_CODE"].astype(str)
        bio = df[na.str.startswith("3254") | na.str.startswith("5417")]
        bio_city = bio["WORKSITE_CITY"].astype(str).str.strip().str.upper()
        bio_rank = bio_city.value_counts().head(10)
        bioN = [c.title() for c in bio_rank.index]
        bioC = [int(v) for v in bio_rank.values]
        html = set_const(html, "bioN", bioN)
        html = set_const(html, "bioC", bioC)
        html = set_js_marker(html, "maBioTotal", len(bio))

        # Academia footprint
        emp = df["EMPLOYER_NAME"].astype(str).str.upper()
        acad_mask = emp.str.contains(
            "UNIVERSITY|COLLEGE|INSTITUTE OF TECHNOLOGY", regex=True, na=False)
        acad = df[acad_mask]
        acad_emp = acad["EMPLOYER_NAME"].astype(str).str.upper().str.strip()
        acad_rank = acad_emp.value_counts().head(10)
        acN = [SHORT_UNIVERSITY.get(n, n.title()) for n in acad_rank.index]
        acC = [int(v) for v in acad_rank.values]
        html = set_const(html, "acN", acN)
        html = set_const(html, "acC", acC)

        # KPIs / headline numbers
        med_all = median_int(df["ANN"])
        uniq_emp = int(df["EMPLOYER_NAME"].nunique())
        bio_pct = round(len(bio) / total * 100, 1)
        html = set_html_marker(html, "maLca", "{:,}".format(total))
        html = set_html_marker(html, "maMedWage", "${:,}".format(med_all))
        html = set_html_marker(html, "maEmployers", "{:,}".format(uniq_emp))
        html = set_html_marker(html, "maBiotech", "{:,}".format(len(bio)))
        html = set_html_marker(html, "maBiotechLbl",
                               "LCAs ({}%)".format(bio_pct))
        if fy and q:
            html = set_html_marker(html, "maQuarter1", "FY%s Q%s" % (fy, q))
            html = set_html_marker(html, "maQuarter2", "FY%s Q%s" % (fy[2:], q))
        changed.append("MA deep-dive: %d LCAs, median $%s, %d employers, "
                        "%d biotech" % (total, "{:,}".format(med_all),
                                        uniq_emp, len(bio)))
    else:
        log("No DOL LCA file in data/ -- MA deep-dive charts left unchanged.")

    # ---- USCIS MA employers ----------------------------------------------
    if ma_path:
        log("Reading USCIS MA file: %s" % os.path.basename(ma_path))
        recs = parse_uscis(ma_path)[:20]
        f26eN = [short_name(n, SHORT_EMPLOYER) for n, _ in recs]
        f26eC = [c for _, c in recs]
        f26eO = [is_outsourcing(n) for n, _ in recs]
        html = set_const(html, "f26eN", f26eN)
        html = set_const(html, "f26eC", f26eC)
        html = set_const(html, "f26eO", f26eO)
        if recs:
            html = set_html_marker(html, "maTopEmp", "{:,}".format(recs[0][1]))
            top_short = short_name(recs[0][0], SHORT_EMPLOYER).split(" Group")[0]
            html = set_html_marker(html, "maTopEmpLbl",
                                   "%s FY26" % top_short)
        changed.append("MA employers: #1 %s (%d)" % (f26eN[0], f26eC[0]))
    else:
        log("No USCIS MA file in data/ -- MA employer chart left unchanged.")

    # ---- USCIS national ---------------------------------------------------
    if nat_path:
        log("Reading USCIS national file: %s" % os.path.basename(nat_path))
        recs = parse_uscis(nat_path)
        nat_total = sum(c for _, c in recs)
        top20 = recs[:20]
        t20N = [short_name(n, SHORT_NATIONAL) for n, _ in top20]
        t20C = [c for _, c in top20]
        t20K = [category(n) for n, _ in top20]
        html = set_const(html, "t20N", t20N)
        html = set_const(html, "t20C", t20C)
        html = set_const(html, "t20K", t20K)

        # category block totals across all 100
        block = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for n, c in recs:
            block[category(n)] += c
        blkV = [block[2], block[1], block[3], block[4] + block[5]]
        html = set_js_marker(html, "blkV", jsarr(blkV))
        html = set_js_marker(html, "natTotal", nat_total)

        # Indian IT single-year breakdown
        ii = {}
        for n, c in recs:
            if category(n) == 1:
                for kw, short in INDIAN_IT.items():
                    if kw in n.upper():
                        ii[short] = ii.get(short, 0) + c
                        break
        ii_sorted = sorted(ii.items(), key=lambda t: -t[1])[:8]
        iiN = [k for k, _ in ii_sorted]
        iiC = [v for _, v in ii_sorted]
        html = set_const(html, "iiN", iiN)
        html = set_const(html, "iiC", iiC)

        # KPIs
        def pct(x):
            return round(x / nat_total * 100, 1) if nat_total else 0
        html = set_html_marker(html, "natAmazon", "{:,}".format(top20[0][1]))
        html = set_html_marker(html, "natIndianIT", "{:,}".format(block[1]))
        html = set_html_marker(html, "natBigTech", "{:,}".format(block[2]))
        html = set_html_marker(html, "natFinance", "{:,}".format(block[3]))
        html = set_html_marker(html, "natIndianITpct",
                               "({}% of Top 100)".format(pct(block[1])))
        html = set_html_marker(html, "natBigTechpct",
                               "({}% of Top 100)".format(pct(block[2])))
        html = set_html_marker(html, "natFinancepct",
                               "({}% of Top 100)".format(pct(block[3])))
        changed.append("National: %d firms, %s approvals; Big Tech %s / "
                        "Indian IT %s / Finance %s"
                        % (len(recs), "{:,}".format(nat_total),
                           "{:,}".format(block[2]), "{:,}".format(block[1]),
                           "{:,}".format(block[3])))

        # warn about unknown companies (default-classified as Other)
        unknown = [n for n, _ in recs if category(n) == 5]
        if unknown:
            log("  Note: %d firm(s) classified as 'Other' (review if needed):"
                % len(unknown))
            for n in unknown[:15]:
                log("    - " + n)
    else:
        log("No USCIS national file in data/ -- national charts left unchanged.")

    # ---- write ------------------------------------------------------------
    if not changed:
        log("\nNo recognised data files in the data/ folder -- nothing to "
            "rebuild. index.html left unchanged.")
        log("See the comments at the top of build.py for file names.")
        return
    open(INDEX, "w", encoding="utf-8").write(html)
    log("\nUpdated index.html:")
    for c in changed:
        log("  - " + c)
    log("\nDone. Review index.html, then commit it.")


if __name__ == "__main__":
    main()
