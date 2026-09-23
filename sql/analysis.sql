-- DataFlow — SQL Analytics
-- --------------------------------------------------------
-- Demonstrates proficiency in aggregations, JOINs, CTEs,
-- and Window Functions.

-- 1. Total transaction value by month (Successful transactions only)
SELECT 
    DATE_TRUNC('month', transaction_date) AS txn_month,
    COUNT(transaction_id) AS total_transactions,
    SUM(amount) AS total_value
FROM transactions
WHERE transaction_status = 'success'
GROUP BY 1
ORDER BY 1;

-- 2. Number of transactions by category
SELECT 
    category,
    COUNT(transaction_id) AS transaction_count,
    SUM(amount) AS total_value,
    ROUND(AVG(amount), 2) AS average_value
FROM transactions
GROUP BY 1
ORDER BY total_value DESC;

-- 3. Average transaction value by account type (Requires JOIN)
SELECT 
    c.account_type,
    COUNT(t.transaction_id) AS transaction_count,
    ROUND(AVG(t.amount), 2) AS avg_transaction_value
FROM transactions t
JOIN customers c ON t.customer_id = c.customer_id
WHERE t.transaction_status = 'success'
GROUP BY 1
ORDER BY 3 DESC;

-- 4 & 5. Top 10 customers by total transaction amount and volume
SELECT 
    c.customer_id,
    c.first_name,
    c.last_name,
    COUNT(t.transaction_id) AS total_volume,
    SUM(t.amount) AS total_amount
FROM customers c
JOIN transactions t ON c.customer_id = t.customer_id
WHERE t.transaction_status = 'success'
GROUP BY 1, 2, 3
ORDER BY total_amount DESC
LIMIT 10;

-- 6. Failed transaction rate by payment method
SELECT 
    payment_method,
    COUNT(*) AS total_attempts,
    SUM(CASE WHEN transaction_status = 'failed' THEN 1 ELSE 0 END) AS failed_count,
    ROUND((SUM(CASE WHEN transaction_status = 'failed' THEN 1 ELSE 0 END)::DECIMAL / COUNT(*)) * 100, 2) AS failure_rate_pct
FROM transactions
GROUP BY 1
ORDER BY failure_rate_pct DESC;

-- 7. Transactions by city
SELECT 
    c.city,
    COUNT(t.transaction_id) AS transaction_count,
    SUM(t.amount) AS total_value
FROM transactions t
JOIN customers c ON t.customer_id = c.customer_id
GROUP BY 1
ORDER BY total_value DESC;

-- 8 & 12. Month-over-month transaction growth (Using CTE and Window Functions)
WITH monthly_stats AS (
    SELECT 
        DATE_TRUNC('month', transaction_date) AS month,
        SUM(amount) AS total_revenue
    FROM transactions
    WHERE transaction_status = 'success'
    GROUP BY 1
)
SELECT 
    month,
    total_revenue,
    LAG(total_revenue) OVER (ORDER BY month) AS prev_month_revenue,
    ROUND(((total_revenue - LAG(total_revenue) OVER (ORDER BY month)) / 
           LAG(total_revenue) OVER (ORDER BY month)) * 100, 2) AS mom_growth_pct
FROM monthly_stats
ORDER BY month;

-- 10. Customers with unusually high transaction frequency (Potential fraud / anomaly detection)
-- (More than 3 std deviations above average frequency)
WITH customer_counts AS (
    SELECT customer_id, COUNT(*) AS txn_count
    FROM transactions
    GROUP BY customer_id
),
global_stats AS (
    SELECT 
        AVG(txn_count) AS avg_txn,
        STDDEV(txn_count) AS std_txn
    FROM customer_counts
)
SELECT 
    c.customer_id,
    c.txn_count,
    g.avg_txn
FROM customer_counts c
CROSS JOIN global_stats g
WHERE c.txn_count > (g.avg_txn + (3 * g.std_txn))
ORDER BY c.txn_count DESC;
