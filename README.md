# MSDS 420 — Mortgage Lending Analysis of Redlined Zones in Chicago

> Data warehouse + regression analysis of mortgage lending disparities in Chicago's formerly redlined zones using FHFA/CFPB federal datasets

**Course**: MSDS 420 — Database Systems and Data Preparation  
**Team**: Selin Altiparmak · Abdullah Abdul Sami · Qifan Yang  
**Institution**: Northwestern University, School of Professional Studies  

---

## Project Overview

Formerly redlined zones in the Midwest are among the most segregated areas in the country. This project investigates whether unequal mortgage lending practices persist today in Chicago's historically redlined census tracts — and identifies the key drivers of mortgage delinquency across the Chicago MSA.

Using federal mortgage performance data from the FHFA (Freddie Mac FHLMC + Fannie Mae FNMA), we built a full data warehouse, conducted exploratory and regression analysis, and developed an interactive Plotly/Dash dashboard to surface geographic and demographic lending disparities.

---

## Key Findings

- **Census tract minority percentage is a statistically significant predictor of mortgage interest rates** (coef = 0.071, p < 0.001) — even after controlling for income, DTI, and LTV ratio
- **Underserved tract status is the 2nd strongest predictor of county-level delinquency**, after credit-related factors
- **Cook County** (highest % underserved tracts in the Chicago MSA) has the highest 90+ day delinquency rates — lending disparities and delinquency are positively correlated
- Borrowers in high-minority census tracts face measurably worse loan terms independent of their financial profile

---

## Data Sources

| Source | Description |
|--------|-------------|
| [FHFA PUDB](https://www.fhfa.gov/data/datasets) | Freddie Mac (FHLMC) + Fannie Mae (FNMA) single-family loan-level data, 2024 |
| [CFPB Mortgage Performance](https://www.consumerfinance.gov/data-research/mortgage-performance-trends/download-the-data/) | County-level delinquency rates (30–89 day and 90+ day), through March 2025 |
| US Census 2020 tract shapefiles | For census tract minority ratio, income, and poverty concentration flags |

Raw FHLMC and FNMA files are not included in this repo due to size (200MB+ each). Download links above.

---

## Repository Structure

```
msds420-mortgage-lending-analysis/
│
├── business_schema_and_questions/
│   ├── final_project.ipynb                          # ETL pipeline + data warehouse construction
│   ├── regression_analysis.ipynb                    # Statistical analysis + complex business questions
│   ├── Chicago_mortgage_3nf.sql                     # 3NF normalized schema DDL
│   ├── business_questions_mortgage_answers.sql      # Analytical SQL queries
│   └── Mortgage_warehouse_validation.sql            # Schema validation queries
│
├── dashboard_run/
│   ├── dashboard.py                                 # Plotly/Dash interactive dashboard
│   ├── run_all.py                                   # Full pipeline runner
│   ├── fact_loans_chicago_fhlmc.csv                 # Processed FHLMC fact table
│   ├── fact_loans_chicago_fnma.csv                  # Processed FNMA fact table
│   ├── fact_delinquency_30_89_final.csv             # 30–89 day delinquency rates
│   ├── fact_delinquency_90_plus_final.csv           # 90+ day delinquency rates
│   ├── dim_tract_chicago.csv                        # Census tract dimension table
│   └── dim_county_with_ids.csv                      # County dimension table
│
├── dashboard_screenshots/
│   └── *.png                                        # Dashboard UI screenshots
│
└── README.md
```

---

## Data Warehouse Design

The project implements a **3NF-normalized star schema** warehouse with separate fact and dimension tables:

**Fact Tables**
- `fact_loans_chicago_fhlmc` — Freddie Mac loan records filtered to Chicago MSA (state FIPS 17, CBSA 16980)
- `fact_loans_chicago_fnma` — Fannie Mae loan records (same filter)
- `fact_delinquency_30_89` — County-level 30–89 day late mortgage percentages
- `fact_delinquency_90_plus` — County-level 90+ day late mortgage percentages

**Dimension Tables**
- `dim_tract_chicago` — Census tract attributes: minority %, median income, income ratio, poverty concentration flag, high-opportunity flag
- `dim_borrower_chicago` — Borrower demographics: race, ethnicity, sex, age category, first-time homebuyer flag
- `dim_county` — County FIPS codes and names

---

## Analysis Performed

### 1. ETL Pipeline (`final_project.ipynb`)
- Filtered 400M+ bytes of raw FHFA data to Chicago MSA
- Constructed normalized fact and dimension tables
- Joined census tract demographic attributes to loan records

### 2. Regression & Business Questions (`regression_analysis.ipynb`)

| Question | Method | Finding |
|----------|--------|---------|
| Does tract location predict mortgage rate after controlling for income/DTI/LTV? | OLS Regression | YES — coef=0.071, p<0.001 |
| Which borrower/loan characteristics predict delinquency? | Feature importance analysis | Underserved tract status = 2nd strongest predictor |
| Is 90+ day delinquency concentrated in underserved counties? | County-level aggregation | YES — Cook County leads |
| Do lending disparities correlate with higher delinquency? | Correlation analysis | YES — positive correlation confirmed |

### 3. Interactive Dashboard (`dashboard.py`)
Built with **Plotly Dash** — visualizes:
- Interest rate distributions by tract minority percentage
- Delinquency rates by county and underserved status
- Loan-to-value and DTI distributions across demographic groups
- Geographic heatmaps of lending activity across the Chicago MSA

---

## How to Run the Dashboard

```bash
# 1. Install dependencies
pip install dash plotly pandas numpy

# 2. Ensure processed CSV files are in dashboard_run/
# (or run final_project.ipynb first to generate them)

# 3. Launch the dashboard
cd dashboard_run
python dashboard.py

# Open http://127.0.0.1:8050 in your browser
```

---

## Tech Stack

| Category | Tools |
|----------|-------|
| Languages | Python, SQL |
| Data Processing | pandas, numpy |
| Visualization | Plotly, Dash |
| Database Design | 3NF normalization, star schema |
| Statistical Analysis | scipy, statsmodels, OLS regression |
| Environment | Google Colab, Jupyter Notebook |
| Data Sources | FHFA PUDB, CFPB Mortgage Performance Trends |

---

## Policy Implications

This analysis provides evidence-based support for local government officials and community leaders seeking to:
- Identify census tracts where unequal lending practices persist
- Understand the relationship between neighborhood demographics and loan terms
- Target intervention programs at high-delinquency, underserved counties
- Hold lenders accountable using publicly available federal data

---

## References

1. Best, Ryan, and Elena Mejía. "The Lasting Legacy of Redlining." FiveThirtyEight, February 9, 2022.
2. FHFA Public Use Database (PUDB) — Single-Family, 2024. https://www.fhfa.gov/data/datasets
3. CFPB Mortgage Performance Trends. https://www.consumerfinance.gov/data-research/mortgage-performance-trends/
