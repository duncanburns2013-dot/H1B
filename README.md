# H-1B Visa & U.S. Offshoring Analysis (2000–2025)

Interactive data visualization tracking the migration of American jobs, businesses, and investment to India over 25 years. 50 charts across 10 tabs. Built from 844,054 official USCIS filings.

**[View the live dashboard](https://duncanburns2013-dot.github.io/H1B/)**

## Data Sources

All data comes from official U.S. government sources and peer-reviewed research:

- **USCIS H-1B Employer Data Hub** — 844,054 individual filings across all 50 states & territories (FY2009–2026)
- **DOL Foreign Labor Certification LCA Disclosure Data** — 7,629 Massachusetts labor condition applications with actual job titles, wages, and prevailing wage levels (FY2020 & FY2024)
- **USCIS H-1B Characteristics Congressional Reports** (FY2003–2024)
- **Bureau of Labor Statistics (BLS)** — Labor force participation, manufacturing employment
- **Federal Reserve Economic Data (FRED)**
- **NASSCOM Annual Reports** — India IT industry revenue, GCC data
- **NBER Working Paper #23153** (Bound et al.) — H-1B wage and employment impact
- **EPI** — H-1B prevailing wage analysis
- **Goldman Sachs, McKinsey** — AI automation and labor displacement projections
- **a16z, Business Standard** — BPO industry transformation data

## Dashboard Tabs

| Tab | What It Shows |
|-----|---------------|
| **Overview** | National labor trends, India IT revenue growth, GCC expansion, U.S. company India headcount, sector evolution |
| **H-1B Visas** | Top 20 employers, India's share over time, Indian IT firms breakdown |
| **50-State Data** | State search, all states ranked by H-1B approvals, national approval/denial trends |
| **Massachusetts** | Deep dive into 245K+ approvals, industries, cities, top 20 employers, outsourcing trends, NAICS 54 |
| **Real Jobs & Wages** | DOL LCA data — actual job titles and wages, human services employers, lowest-paid H-1B jobs in MA |
| **Questionable Usage** | IT outsourcing firms, hotels, pizza shops, fast food chains. Dunkin' Brands case study. Household brands (Starbucks, McDonald's, Marriott, Hilton) |
| **The Pipeline** | "Change of Employer" analysis — how H-1B workers get recycled, top recycler companies |
| **The Law** | 36 years of H-1B legislation (1990–2025), visa cap history, fee explosion, wage suppression math, NBER research |
| **The AI Era** | Why H-1B demand is collapsing — AI productivity, Indian IT layoffs, BPO collapse, automation of H-1B tasks |
| **Sources** | Full methodology and citation list |

## Key Findings

- **4.78 million** H-1B approvals nationally (FY2009–2026), with **326,945 denials** (6.4% rate)
- **576,625** approvals (12.1%) went to IT outsourcing firms
- **797,541** "Change of Employer" approvals — companies recruiting from a captive H-1B labor pool
- Indian IT firms account for **39.7%** of all approvals among the top 100 employers
- **18.9%** of Massachusetts H-1B positions are at **entry-level wages** (Level I = 36% below median)
- Direct Care Professionals hired on H-1B at **$30,160/year** — Wage Level I
- Dunkin' Brands: 74 approvals, **57% were "Change of Employer"** transfers (poached from H-1B pool)
- McDonald's: 323 approvals, **48% Change of Employer**
- Starbucks: 1,485 approvals, Marriott: 771, Hilton: 661, Domino's: 443
- NBER research: H-1B suppressed CS wages by **2.6–5.1%** and employment by **6.1–10.8%**
- Indian IT firms (TCS, Infosys, Wipro) cut **64,759 jobs in FY2024** while profits increased
- India BPO employment projected to collapse from **4M to <1M by 2030**

## Technical

Single-file HTML dashboard using Chart.js 4.4.1 with chartjs-plugin-annotation. No build tools needed — just open `index.html` or deploy to GitHub Pages. 50 interactive charts, ~117KB.

## Deployment

1. Push `index.html` and `README.md` to the `main` branch
2. Go to Settings → Pages → Source: Deploy from branch → `main` / `/ (root)`
3. Site goes live at `https://duncanburns2013-dot.github.io/H1B/`

## Notes

- California data is partially incomplete due to USCIS download portal limitations
- DOL LCA analysis covers FY2020 and FY2024 (other years exceeded processing limits)
- Where exact yearly figures were unavailable, values were interpolated from nearest confirmed data points
- Multiple USCIS entity names for the same parent company have been consolidated
- AI automation percentages based on McKinsey, Goldman Sachs, and industry analysis
