-- DataFlow — Data Quality SQL
-- --------------------------------------------------------
-- Demonstrates how data quality checks would be implemented directly in SQL
-- if we were validating data already sitting in a staging table.

-- 1. Detect duplicate transactions
SELECT 
    transaction_id, 
    COUNT(*) AS occurrence_count
FROM transactions_staging
GROUP BY transaction_id
HAVING COUNT(*) > 1;

-- 2. Detect missing required fields
SELECT *
FROM transactions_staging
WHERE transaction_id IS NULL 
   OR customer_id IS NULL 
   OR amount IS NULL;

-- 3. Detect orphan customer IDs (Referential Integrity Check)
SELECT t.transaction_id, t.customer_id
FROM transactions_staging t
LEFT JOIN customers c ON t.customer_id = c.customer_id
WHERE c.customer_id IS NULL;

-- 4. Detect invalid amounts
SELECT transaction_id, amount
FROM transactions_staging
WHERE amount <= 0;

-- 5. Detect invalid categories
SELECT transaction_id, category
FROM transactions_staging
WHERE category NOT IN (
    'groceries', 'utilities', 'entertainment', 'healthcare',
    'education', 'travel', 'dining', 'shopping', 'fuel',
    'insurance', 'rent', 'salary', 'investment', 'transfer', 'subscription'
);

-- 6. Detect invalid or unreasonable dates
SELECT transaction_id, transaction_date
FROM transactions_staging
WHERE transaction_date > CURRENT_TIMESTAMP 
   OR transaction_date < '2000-01-01';
