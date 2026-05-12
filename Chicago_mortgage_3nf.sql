/* ===========================================================
   CHICAGO MORTGAGE LENDING ANALYSIS DATABASE
   STRICT 3NF DESIGN WITH SURROGATE KEYS
   Scope: Illinois portion of Chicago CBSA (16980)
   =========================================================== */


/* ===========================================================
   DROP TABLES IF THEY EXIST (FOR CLEAN RE-RUN)
   =========================================================== */

DROP TABLE IF EXISTS fact_delinquency CASCADE;
DROP TABLE IF EXISTS fact_loans CASCADE;
DROP TABLE IF EXISTS dim_borrower CASCADE;
DROP TABLE IF EXISTS dim_tract CASCADE;
DROP TABLE IF EXISTS dim_county CASCADE;
DROP TABLE IF EXISTS dim_cbsa CASCADE;
DROP TABLE IF EXISTS dim_enterprise CASCADE;
DROP TABLE IF EXISTS dim_state CASCADE;


/* ===========================================================
   DIMENSION: STATE
   Represents U.S. state.
   Even though project is Chicago-only, we normalize properly.
   =========================================================== */

CREATE TABLE dim_state (
    state_id SERIAL PRIMARY KEY,
    state_fips INTEGER NOT NULL UNIQUE,
    state_name VARCHAR(50) NOT NULL
);


/* ===========================================================
   DIMENSION: CBSA (Metro Area)
   Chicago CBSA = 16980
   =========================================================== */

CREATE TABLE dim_cbsa (
    cbsa_id SERIAL PRIMARY KEY,
    cbsa_metro_code INTEGER NOT NULL UNIQUE,
    cbsa_metro_name VARCHAR(200) NOT NULL
);


/* ===========================================================
   DIMENSION: ENTERPRISE
   1 = FNMA
   2 = FHLMC
   =========================================================== */

CREATE TABLE dim_enterprise (
    enterprise_id SERIAL PRIMARY KEY,
    enterprise_code INTEGER NOT NULL UNIQUE
);


/* ===========================================================
   DIMENSION: COUNTY
   Each county belongs to a state.
   Surrogate key used (county_id).
   =========================================================== */

CREATE TABLE dim_county (
    county_id SERIAL PRIMARY KEY,
    state_id INTEGER NOT NULL,
    county_fips INTEGER NOT NULL,
    county_name VARCHAR(100),

    CONSTRAINT fk_county_state
        FOREIGN KEY (state_id)
        REFERENCES dim_state(state_id),

    CONSTRAINT unique_county UNIQUE (state_id, county_fips)
);


/* ===========================================================
   DIMENSION: TRACT
   Census tract belongs to a county.
   Stores socio-economic indicators.
   =========================================================== */

CREATE TABLE dim_tract (
    tract_id SERIAL PRIMARY KEY,
    county_id INTEGER NOT NULL,
    tract_2020 BIGINT NOT NULL,
    tract_minority_pct NUMERIC(6,2),
    tract_income_med NUMERIC(14,2),
    tract_income_ratio NUMERIC(8,4),
    area_concentrated_poverty INTEGER,
    area_high_opp INTEGER,

    CONSTRAINT fk_tract_county
        FOREIGN KEY (county_id)
        REFERENCES dim_county(county_id),

    CONSTRAINT unique_tract UNIQUE (county_id, tract_2020)
);


/* ===========================================================
   DIMENSION: BORROWER
   Borrower demographic attributes.
   Surrogate borrower_id used instead of record number.
   =========================================================== */

CREATE TABLE dim_borrower (
    borrower_id SERIAL PRIMARY KEY,
    race1_borr INTEGER,
    ethnicity_borr INTEGER,
    sex_borr INTEGER,
    age_borr_cat INTEGER,
    fthb INTEGER
);


/* ===========================================================
   FACT TABLE: LOANS
   Central transactional table.
   Each row represents a mortgage loan.
   References multiple dimensions.
   =========================================================== */

CREATE TABLE fact_loans (
    loan_id BIGSERIAL PRIMARY KEY,

    borrower_id INTEGER NOT NULL,
    tract_id INTEGER NOT NULL,
    cbsa_id INTEGER NOT NULL,
    enterprise_id INTEGER NOT NULL,

    income_annual NUMERIC(14,2),
    ltv NUMERIC(6,2),
    dti_cat INTEGER,
    rate_orig NUMERIC(6,3),
    upb_orig NUMERIC(16,2),
    property_value NUMERIC(16,2),
    term_orig INTEGER,
    purpose_ctf INTEGER,

    CONSTRAINT fk_fact_borrower
        FOREIGN KEY (borrower_id)
        REFERENCES dim_borrower(borrower_id),

    CONSTRAINT fk_fact_tract
        FOREIGN KEY (tract_id)
        REFERENCES dim_tract(tract_id),

    CONSTRAINT fk_fact_cbsa
        FOREIGN KEY (cbsa_id)
        REFERENCES dim_cbsa(cbsa_id),

    CONSTRAINT fk_fact_enterprise
        FOREIGN KEY (enterprise_id)
        REFERENCES dim_enterprise(enterprise_id)
);


/* ===========================================================
   FACT TABLE: DELINQUENCY
   Time-series data by county.
   Must be reshaped long format before loading.
   =========================================================== */

CREATE TABLE fact_delinquency (
    delinquency_id BIGSERIAL PRIMARY KEY,
    county_id INTEGER NOT NULL,
    year_month DATE NOT NULL,
    delinquency_rate NUMERIC(6,3),
    delinquency_type VARCHAR(20), -- '30_89' or '90_plus'

    CONSTRAINT fk_delinquency_county
        FOREIGN KEY (county_id)
        REFERENCES dim_county(county_id)
);


/* ===========================================================
   INSERT BASE DIMENSION VALUES
   =========================================================== */

/* Insert Illinois */
INSERT INTO dim_state (state_fips, state_name)
VALUES (17, 'Illinois');

/* Insert Chicago CBSA */
INSERT INTO dim_cbsa (cbsa_metro_code, cbsa_metro_name)
VALUES (16980, 'Chicago-Naperville-Elgin, IL-IN Metro Area');

/* Insert Enterprises */
INSERT INTO dim_enterprise (enterprise_code)
VALUES (1), (2);

