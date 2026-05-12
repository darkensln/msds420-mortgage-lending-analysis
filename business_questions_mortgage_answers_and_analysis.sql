-- Identify geographic and socio-economic areas where unequal lending practices are common and 
-- identify drivers of mortgage defaults.

-- STEP 1 — Quick Sanity Analytics
SELECT
    dc.county_name,
    COUNT(fl.loan_id) AS total_loans,
    AVG(fl.rate_orig) AS avg_interest_rate,
    AVG(fl.ltv) AS avg_ltv,
    AVG(fl.income_annual) AS avg_income
FROM fact_loans fl
JOIN dim_tract dt ON fl.tract_id = dt.tract_id
JOIN dim_county dc ON dt.county_id = dc.county_id
GROUP BY dc.county_name
ORDER BY total_loans DESC;
-- STEP 2 — Delinquency Trend by 
SELECT
    dc.county_name,
    fd.year_month,
    AVG(fd.delinquency_rate) AS avg_delinquency
FROM fact_delinquency fd
JOIN dim_county dc ON fd.county_id = dc.county_id
WHERE fd.delinquency_type = '90_plus'
GROUP BY dc.county_name, fd.year_month
ORDER BY fd.year_month;
-- STEP 3 — Minority % vs Interest Rate
SELECT
    dt.tract_minority_pct,
    AVG(fl.rate_orig) AS avg_rate
FROM fact_loans fl
JOIN dim_tract dt ON fl.tract_id = dt.tract_id
GROUP BY dt.tract_minority_pct
ORDER BY dt.tract_minority_pct;
-- BUSINESS QUESTIONS AND ANSWERS
-- SIMPLE QUESTIONS
/* ===========================================================
   BUSINESS QUESTION:
   Do formerly underserved census tracts in Chicago
   (area_concentrated_poverty = 1) have higher average
   loan-to-value (LTV) ratios compared to non-underserved tracts?

   INTERPRETATION LOGIC:
   Higher LTV suggests lower borrower equity and potentially
   higher financial risk at origination.
   =========================================================== */

SELECT
    dt.area_concentrated_poverty,
    COUNT(fl.loan_id) AS total_loans,
    ROUND(AVG(fl.ltv), 2) AS avg_ltv
FROM fact_loans fl
JOIN dim_tract dt ON fl.tract_id = dt.tract_id
GROUP BY dt.area_concentrated_poverty
ORDER BY dt.area_concentrated_poverty;

-- Non-underserved → Avg LTV ≈ 77.70
-- Underserved → Avg LTV ≈ 81.77

-- Interpretation:

-- Borrowers in underserved census tracts have materially higher loan-to-value ratios at origination. 
-- Higher LTV ratios indicate lower borrower equity and greater leverage at the time of purchase. 
-- This suggests that borrowers in historically disadvantaged areas are entering mortgage contracts 
-- with thinner financial buffers, increasing vulnerability to housing price shocks and financial stress. 
-- This structural difference reflects potential wealth inequality across geographic areas.

-- This is a strong redlining-consistent signal.


/* ===========================================================
   BUSINESS QUESTION:
   How do borrower income levels vary across census tracts?

   INTERPRETATION LOGIC:
   This evaluates spatial income distribution across Chicago.
   =========================================================== */

SELECT
    dt.tract_2020,
    ROUND(AVG(fl.income_annual), 2) AS avg_income,
    COUNT(fl.loan_id) AS total_loans
FROM fact_loans fl
JOIN dim_tract dt ON fl.tract_id = dt.tract_id
GROUP BY dt.tract_2020
ORDER BY avg_income DESC;



/* ===========================================================
   BUSINESS QUESTION:
   What is the racial composition of borrowers across tracts?

   INTERPRETATION LOGIC:
   Examines demographic distribution within geographic areas.
   =========================================================== */

SELECT
    dt.tract_2020,
    db.race1_borr,
    COUNT(fl.loan_id) AS total_loans
FROM fact_loans fl
JOIN dim_borrower db ON fl.borrower_id = db.borrower_id
JOIN dim_tract dt ON fl.tract_id = dt.tract_id
GROUP BY dt.tract_2020, db.race1_borr
ORDER BY dt.tract_2020;

/* ===========================================================
   BUSINESS QUESTION:
   Are DTI ratios higher in underserved census tracts?

   INTERPRETATION LOGIC:
   Higher DTI may indicate greater repayment stress.
   =========================================================== */

SELECT
    dt.area_concentrated_poverty,
    ROUND(AVG(fl.dti_cat), 2) AS avg_dti_category
FROM fact_loans fl
JOIN dim_tract dt ON fl.tract_id = dt.tract_id
GROUP BY dt.area_concentrated_poverty;

-- Result:

-- Non-underserved → 35.90
-- Underserved → 37.33

-- Interpretation:

-- Debt-to-income ratios are higher among borrowers in underserved tracts. 
-- Higher DTI indicates greater repayment burden relative to income. 
-- This suggests borrowers in disadvantaged areas may be financially more constrained at origination,
-- potentially increasing downstream default risk.

-- This reinforces financial stress disparities.

/* ===========================================================
   BUSINESS QUESTION:
   How do county-level delinquency rates vary across the region?

   INTERPRETATION LOGIC:
   Identifies geographic differences in mortgage distress.
   =========================================================== */

SELECT
    dc.county_name,
    fd.delinquency_type,
    ROUND(AVG(fd.delinquency_rate), 2) AS avg_delinquency
FROM fact_delinquency fd
JOIN dim_county dc ON fd.county_id = dc.county_id
GROUP BY dc.county_name, fd.delinquency_type
ORDER BY dc.county_name;

-- MEDIUM QUESTIONS
/* ===========================================================
   BUSINESS QUESTION:
   Do borrowers in underserved tracts face higher interest rates?

   INTERPRETATION LOGIC:
   Higher average rate may indicate less favorable lending terms.
   =========================================================== */

SELECT
    dt.area_concentrated_poverty,
    ROUND(AVG(fl.rate_orig), 3) AS avg_interest_rate
FROM fact_loans fl
JOIN dim_tract dt ON fl.tract_id = dt.tract_id
GROUP BY dt.area_concentrated_poverty;

-- Result:

-- Non-underserved → 6.788%
-- Underserved → 6.910%

-- Interpretation:

-- Borrowers in underserved census tracts face higher average mortgage interest rates. 
-- Even a 10–15 basis point difference can translate into substantial lifetime interest cost differences 
-- over 30 years. This suggests that geographic factors may influence pricing outcomes,
-- raising potential concerns about differential lending conditions across socioeconomically 
-- disadvantaged areas.

-- This supports the hypothesis of unequal lending conditions.

/* ===========================================================
   BUSINESS QUESTION:
   Are 90+ day delinquency rates higher in counties
   associated with underserved tracts?

   INTERPRETATION LOGIC:
   Compares long-term mortgage distress geographically.
   =========================================================== */

SELECT
    dc.county_name,
    ROUND(AVG(fd.delinquency_rate), 2) AS avg_90_plus_rate
FROM fact_delinquency fd
JOIN dim_county dc ON fd.county_id = dc.county_id
WHERE fd.delinquency_type = '90_plus'
GROUP BY dc.county_name
ORDER BY avg_90_plus_rate DESC;

-- Highest:

-- Cook County → 2.70%
-- Kendall → 2.21%
-- Will → 2.18%
-- Lowest: DuPage → 1.41%

-- Interpretation:

-- Serious delinquency rates (90+ days) are highest in Cook County, 
-- which contains a substantial number of historically disadvantaged and high-poverty tracts. 
-- Counties with stronger income profiles (e.g., DuPage) exhibit significantly lower serious delinquency 
-- rates. This geographic pattern aligns with socioeconomic stratification and supports the argument that structural 
-- disadvantages translate into higher mortgage distress outcomes.

/* ===========================================================
   BUSINESS QUESTION:
   Do lending terms differ between FNMA(2) and FHLMC(1)
   in underserved tracts?

   INTERPRETATION LOGIC:
   Compares enterprise-level lending behavior.
   =========================================================== */

SELECT
    fl.enterprise_id,
    dt.area_concentrated_poverty,
    ROUND(AVG(fl.rate_orig), 3) AS avg_rate,
    ROUND(AVG(fl.ltv), 2) AS avg_ltv
FROM fact_loans fl
JOIN dim_tract dt ON fl.tract_id = dt.tract_id
GROUP BY fl.enterprise_id, dt.area_concentrated_poverty
ORDER BY fl.enterprise_id;

-- In underserved tracts:

-- Enterprise 1 → Rate ≈ 6.921, LTV ≈ 82.63
-- Enterprise 2 → Rate ≈ 6.898, LTV ≈ 80.87

-- Interpretation:

-- Both enterprises exhibit higher LTV and interest rates in underserved tracts. 
-- Differences between enterprises are minor relative to geographic differences, 
-- suggesting that the primary driver of disparity appears to be tract-level socioeconomic conditions 
-- rather than enterprise-specific pricing behavior.

-- This is an important nuance.

-- COMPLEX (SQL-Ready Summary Support)
/* ===========================================================
   BUSINESS QUESTION:
   Which loan characteristics correlate with higher delinquency?

   INTERPRETATION LOGIC:
   Aggregates loan metrics by county-level delinquency averages.
   Supports later regression modeling.
   =========================================================== */

SELECT
    dc.county_name,
    ROUND(AVG(fl.ltv), 2) AS avg_ltv,
    ROUND(AVG(fl.dti_cat), 2) AS avg_dti,
    ROUND(AVG(fl.rate_orig), 3) AS avg_rate,
    ROUND(AVG(fd.delinquency_rate), 2) AS avg_90_plus_rate
FROM fact_loans fl
JOIN dim_tract dt ON fl.tract_id = dt.tract_id
JOIN dim_county dc ON dt.county_id = dc.county_id
JOIN fact_delinquency fd ON dc.county_id = fd.county_id
WHERE fd.delinquency_type = '90_plus'
GROUP BY dc.county_name
ORDER BY avg_90_plus_rate DESC;

