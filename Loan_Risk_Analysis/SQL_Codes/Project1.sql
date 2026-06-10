USE Project1;

SELECT * FROM ext_cibil_data;
SELECT * FROM int_bank_data;

-- *** DATA AUDIT ***
DESCRIBE ext_cibil_data;
DESCRIBE int_bank_data;


-- Checking the no of rows 
SELECT COUNT(*) AS Cibil_rows FROM ext_cibil_data; -- 51336 rows
SELECT COUNT(*) AS Internal_rows FROM int_bank_data; -- 51336 rows

-- Check duplicate prospectID

SELECT PROSPECTID, COUNT(*) AS CNT FROM ext_cibil_data
GROUP BY PROSPECTID
HAVING COUNT(*) > 1;                    -- NO DUPLICATES

SELECT PROSPECTID, COUNT(*) AS CNT FROM int_bank_data
group by PROSPECTID
HAVING COUNT(*) >1;                     -- NO DUPLICATES

-- Missing value checks

SELECT 
SUM(CASE WHEN PROSPECTID  is null then 1 ELSE 0 END) AS null_PROSPECTID,
    SUM(CASE WHEN time_since_recent_payment   is null then 1 else 0 end) AS null_time_since_recent_payment,
    SUM(CASE WHEN time_since_first_deliquency is null then 1 else 0 end) AS null_time_since_first_deliquency,
    SUM(CASE WHEN num_times_delinquent  is null then 1 else 0 end) AS null_num_times_delinquent,
    SUM(CASE WHEN Credit_Score  is null then 1 else 0 end) AS null_Credit_Score,
    SUM(CASE WHEN Approved_Flag  is null then 1 else 0 end) AS null_Approved_Flag,
    SUM(CASE WHEN AGE  is null then 1 else 0 end) AS null_AGE,
    SUM(CASE WHEN GENDER  is null then 1 else 0 end) AS null_GENDER,
    SUM(CASE WHEN MARITALSTATUS  is null then 1 else 0 end) AS null_MARITALSTATUS,
    SUM(CASE WHEN EDUCATION  is null then 1 else 0 end) AS null_EDUCATION,
    SUM(CASE WHEN NETMONTHLYINCOME  is null then 1 else 0 end) AS null_NETMONTHLYINCOME,
    SUM(CASE WHEN CC_utilization  is null then 1 else 0 end) AS null_CC_utilization,
    SUM(CASE WHEN PL_utilization  is null then 1 else 0 end) AS null_PL_utilization
from ext_cibil_data; 					-- NO Null values

SELECT 
SUM(CASE WHEN PROSPECTID  is null then 1 else 0 end) AS null_PROSPECTID,
    SUM(CASE WHEN Total_TL is null then 1 else 0 end) AS null_Total_TL,
    SUM(CASE WHEN Tot_Closed_TL is null then 1 else 0 end) AS null_Tot_Closed_TL,
    SUM(CASE WHEN Tot_Active_TL  is null then 1 else 0 end) AS null_Tot_Active_TL,
    SUM(CASE WHEN Tot_Missed_Pmnt is null then 1 else 0 end) AS null_Tot_Missed_Pmnt,
    SUM(CASE WHEN Age_Oldest_TL is null then 1 else 0 end) AS null_Age_Oldest_TL,
    SUM(CASE WHEN Age_Newest_TL is null then 1 else 0 end) AS null_Age_Newest_TL
from int_bank_data; 				   -- No Null values


-- Checking that IDs are present in both datas

SELECT c.PROSPECTID
FROM ext_cibil_data c
join int_bank_data i on c.PROSPECTID = i.PROSPECTID
where i.PROSPECTID is null;

SELECT i.PROSPECTID
FROM int_bank_data i
join ext_cibil_data c on i.PROSPECTID = c.PROSPECTID
where c.PROSPECTID is null;
-- Yes its present in both

-- Invalid value checks

SELECT * FROM ext_cibil_data
where NETMONTHLYINCOME < 0
or Credit_Score < 0
or num_times_delinquent < 0; -- No Negative values present

SELECT * FROM ext_cibil_data
where age < 18 or age > 100; -- No age discripensies

-- Logical consistancy check

select * from int_bank_data
where Tot_Closed_TL + Tot_Active_TL > Total_TL; -- Active and closed doesn't exceed total

SELECT * FROM int_bank_data
WHERE pct_active_tl >100
OR pct_closed_tl >100;            		-- percentages are <= 100

-- Categorical value checks
SELECT DISTINCT GENDER
FROM ext_cibil_data; 					-- No Inconsistencies

SELECT DISTINCT EDUCATION
FROM ext_cibil_data;

-- ** SUMMARY AUDIT **
SELECT
MIN(Credit_Score),                  -- 469
MAX(Credit_Score), 					-- 811
AVG(Credit_Score),					-- 679.8
MIN(AGE),							-- 21
MAX(AGE),							-- 77
AVG(NETMONTHLYINCOME)				-- 26,424
FROM ext_cibil_data;


-- Create merged dataset
CREATE TABLE merged_data AS
SELECT 
    e.*,
    i.PROSPECTID AS bank_prospect_id,
    i.*
FROM ext_cibil_data e
JOIN int_bank_data i
ON e.PROSPECTID = i.PROSPECTID;


-- Merging both the columns and creating a new table Merged data

SHOW COLUMNS FROM int_bank_data;

CREATE TABLE merged_data AS
SELECT 
    e.*,
    i.Total_TL,
    i.Tot_Closed_TL,
    i.Tot_Active_TL,
    i.Total_TL_opened_L6M,
    i.Tot_TL_closed_L6M,
    i.pct_tl_open_L6M,
    i.pct_tl_closed_L6M,
    i.pct_active_tl,
    i.pct_closed_tl,
    i.Total_TL_opened_L12M,
    i.Tot_TL_closed_L12M,
    i.pct_tl_open_L12M,
    i.pct_tl_closed_L12M,
    i.Tot_Missed_Pmnt,
    i.Auto_TL,
    i.CC_TL,
    i.Consumer_TL,
    i.Gold_TL,
    i.Home_TL,
    i.PL_TL,
    i.Secured_TL,
    i.Unsecured_TL,
    i.Other_TL,
    i.Age_Oldest_TL,
    i.Age_Newest_TL
FROM ext_cibil_data e
JOIN int_bank_data i
ON e.PROSPECTID = i.PROSPECTID;

SHOW COLUMNS FROM merged_data;					-- 88 Columns
SELECT COUNT(*) FROM merged_data;				-- 51336 rows

-- Checking for sentinel values and handling them
select * from merged_data;

select 
sum(case when time_since_recent_payment = -99999 then 1 else 0 end) * 100 / count(*) as Time_since_recent_payment_sentinel,
sum(case when time_since_first_deliquency = -99999 then 1 else 0 end)* 100 / count(*) as time_since_first_deliquency_sentinel,
sum(case when time_since_recent_deliquency = -99999 then 1 else 0 end)* 100 / count(*) as time_since_recent_deliquency_sentinel,
sum(case when max_delinquency_level = -99999 then 1 else 0 end)* 100 / count(*) as max_delinquency_level_sentinel,
sum(case when max_deliq_6mts = -99999 then 1 else 0 end)* 100 / count(*) as max_deliq_6mts_sentinel,
sum(case when max_deliq_12mts = -99999 then 1 else 0 end)* 100 / count(*) as max_deliq_12mts_sentinel,
sum(case when tot_enq = -99999 then 1 else 0 end)* 100 / count(*) as tot_enq_sentinel,
sum(case when CC_enq = -99999 then 1 else 0 end)* 100 / count(*) as CC_enq_sentinel,
sum(case when CC_enq_L6m = -99999 then 1 else 0 end)* 100 / count(*) as CC_enq_L6m_sentinel,
sum(case when CC_enq_L12m = -99999 then 1 else 0 end)* 100 / count(*) as CC_enq_L12m_sentinel,
sum(case when PL_enq = -99999 then 1 else 0 end)* 100 / count(*) as PL_enq_sentinel,
sum(case when PL_enq_L6m = -99999 then 1 else 0 end)* 100 / count(*) as PL_enq_L6m_sentinel,
sum(case when PL_enq_L12m = -99999 then 1 else 0 end)* 100 / count(*) as PL_enq_L12m_sentinel,
sum(case when time_since_recent_enq = -99999 then 1 else 0 end)* 100 / count(*) as time_since_recent_enq_sentinel,
sum(case when enq_L12m = -99999 then 1 else 0 end)* 100 / count(*) as enq_L12m_sentinel,
sum(case when enq_L6m = -99999 then 1 else 0 end)* 100 / count(*) as enq_L6m_sentinel,
sum(case when enq_L3m = -99999 then 1 else 0 end)* 100 / count(*) as enq_L3m_sentinel,
sum(case when CC_utilization = -99999 then 1 else 0 end)* 100 / count(*) as CC_utilization_sentinel,
sum(case when PL_utilization = -99999 then 1 else 0 end)* 100 / count(*) as PL_utilization_sentinel,
sum(case when max_unsec_exposure_inPct = -99999 then 1 else 0 end)* 100 / count(*) as max_unsec_exposure_inPct_sentinel
from merged_data;


-- Dropping columns with high sentinel values
alter table merged_data
drop column time_since_first_deliquency,
drop column time_since_recent_deliquency,
drop column max_delinquency_level,
drop column CC_utilization,
drop column PL_utilization;

alter table merged_data drop column max_unsec_exposure_inPct;

-- relacing the remaing columns with null values
SET SQL_SAFE_UPDATES = 0;
update merged_data 
set
	max_deliq_6mts = nullif(max_deliq_6mts,-99999),
    max_deliq_12mts = nullif(max_deliq_12mts,-99999),
    time_since_recent_enq = nullif(time_since_recent_enq,-99999),
    enq_L3m = nullif(enq_L3m,-99999),
    enq_L6m = nullif(enq_L6m,-99999),
    enq_L12m = nullif(enq_L12m,-99999),
    PL_enq_L6m = nullif(PL_enq_L6m,-99999),
    PL_enq = nullif(PL_enq,-99999),
    CC_enq_L6m = nullif(CC_enq_L6m,-99999),
    CC_enq_L12m = nullif(CC_enq_L12m,-99999),
    CC_enq = nullif(CC_enq,-99999),
    time_since_recent_payment = nullif(time_since_recent_payment,-99999),
    Age_Oldest_TL = nullif(Age_Oldest_TL,-99999),
    Age_Newest_TL= nullif(Age_Newest_TL,-99999),
    pct_currentBal_all_TL = nullif(pct_currentBal_all_TL,-99999)
WHERE PROSPECTID IS NOT NULL;
SET SQL_SAFE_UPDATES = 1;

SHOW COLUMNS FROM merged_data;
select * from merged_data;
-- ** FEATURE ENGINEERING **
-- 1. Set income band

ALTER TABLE merged_data ADD COLUMN income_band VARCHAR(10);
ALTER TABLE merged_data 
MODIFY income_band VARCHAR(20);

SET SQL_SAFE_UPDATES = 0;
UPDATE merged_data
set income_band = 
CASE
	WHEN NETMONTHLYINCOME < 20000 THEN 'Low'
    WHEN NETMONTHLYINCOME < 50000 THEN 'Lower Middle'
    WHEN NETMONTHLYINCOME < 100000 THEN 'Upper Middle'
    ELSE 'High'
END;
SET SQL_SAFE_UPDATES = 1;

 -- 2. Risk segmentation   
ALTER TABLE merged_data ADD COLUMN risk_segment VARCHAR(20);

SET SQL_SAFE_UPDATES = 0;

UPDATE merged_data
SET risk_segment = 
CASE 
    WHEN credit_score >= 750 THEN 'Low Risk'
    WHEN credit_score >= 650 THEN 'Medium Risk'
    ELSE 'High Risk'
END;

SET SQL_SAFE_UPDATES = 1;

-- Delinquency flag

ALTER TABLE merged_data ADD COLUMN delinquency_flag INT;
SET SQL_SAFE_UPDATES = 0;
UPDATE merged_data
SET delinquency_flag = 
CASE 
	WHEN num_deliq_12mts > 30 then 1
    else 0
end;
SET SQL_SAFE_UPDATES = 1;


-- ** KPI Definitions **

-- 1. Default rate - % of customers who defaulted
SELECT 
    COUNT(CASE WHEN delinquency_flag = 1 THEN 1 END) * 100.0 / COUNT(*) AS default_rate
FROM merged_data;

-- 2. Average credit score - 

SELECT AVG(credit_score) as avgcredit_score from merged_data; -- 679.8

-- 3. Delinquency rate
-- 30+ DPD rate
SELECT COUNT(CASE WHEN num_times_30p_dpd > 0 then 1 end) *100 / count(*) as dpd_30_rate
from merged_data;       -- 15.5

 -- 60+ dpd rate
 select count(case when num_times_60p_dpd >0 then 1 end) * 100 / count(*) as dpd_60_rate
 from merged_data;             -- 9.52
 
 -- 4. Payment history
 
 select avg(num_times_delinquent) as avg_delinquency,			-- 1.57
		avg(num_deliq_12mts) as avg_12m_delinquency				-- 0.48
from merged_data;

-- Missed payment rate

select count(case when num_deliq_12mts > 0 then 1 end) * 100 / count(*) as missed_payment_rate
from merged_data;												-- 16.41

-- Inquiry intensity

select avg(enq_L3m) as avg_enq_3m,
		avg(enq_L6m) as avg_enq_6m,
        avg(enq_L12m) as avg_enq_12m
from merged_data;


