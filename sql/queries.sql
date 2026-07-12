-- ============================================================================
-- queries.sql
-- Business-facing analytical queries for the Online Retail Analytics project.
-- Written for MySQL 8+ (uses window functions, CTEs, DATE_FORMAT, DATEDIFF).
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. Top 10 best-selling products by total revenue
-- ----------------------------------------------------------------------------
SELECT
    p.product_name,
    p.category,
    SUM(t.quantity)      AS units_sold,
    ROUND(SUM(t.revenue), 2) AS total_revenue
FROM transactions t
JOIN products p ON t.product_id = p.product_id
GROUP BY p.product_id, p.product_name, p.category
ORDER BY total_revenue DESC
LIMIT 10;


-- ----------------------------------------------------------------------------
-- 2. Monthly revenue trend (overall business trajectory)
-- ----------------------------------------------------------------------------
SELECT
    CONCAT(YEAR(order_date), '-', LPAD(MONTH(order_date), 2, '0')) AS order_month,
    COUNT(DISTINCT invoice_id)    AS num_orders,
    ROUND(SUM(revenue), 2)        AS monthly_revenue
FROM transactions
GROUP BY order_month
ORDER BY order_month;


-- ----------------------------------------------------------------------------
-- 3. Revenue by category (which product categories drive the business)
-- ----------------------------------------------------------------------------
SELECT
    p.category,
    COUNT(DISTINCT t.invoice_id) AS num_orders,
    ROUND(SUM(t.revenue), 2)     AS total_revenue,
    ROUND(AVG(t.revenue), 2)     AS avg_order_value
FROM transactions t
JOIN products p ON t.product_id = p.product_id
GROUP BY p.category
ORDER BY total_revenue DESC;


-- ----------------------------------------------------------------------------
-- 4. Revenue by country (geographic performance)
-- ----------------------------------------------------------------------------
SELECT
    c.country,
    COUNT(DISTINCT t.customer_id) AS num_customers,
    ROUND(SUM(t.revenue), 2)      AS total_revenue
FROM transactions t
JOIN customers c ON t.customer_id = c.customer_id
GROUP BY c.country
ORDER BY total_revenue DESC;


-- ----------------------------------------------------------------------------
-- 5. RFM Segmentation (Recency, Frequency, Monetary)
-- Identifies customer value tiers — a classic business analytics technique.
-- "Snapshot date" is the day after the last order in the dataset.
-- ----------------------------------------------------------------------------
WITH snapshot AS (
    SELECT DATE_ADD(MAX(order_date), INTERVAL 1 DAY) AS snapshot_date FROM transactions
),
rfm_base AS (
    SELECT
        t.customer_id,
        DATEDIFF((SELECT snapshot_date FROM snapshot), MAX(t.order_date)) AS recency_days,
        COUNT(DISTINCT t.invoice_id) AS frequency,
        ROUND(SUM(t.revenue), 2) AS monetary
    FROM transactions t
    GROUP BY t.customer_id
),
rfm_scored AS (
    SELECT
        customer_id,
        recency_days,
        frequency,
        monetary,
        NTILE(4) OVER (ORDER BY recency_days DESC) AS r_score,   -- 4 = most recent
        NTILE(4) OVER (ORDER BY frequency ASC)     AS f_score,  -- 4 = most frequent
        NTILE(4) OVER (ORDER BY monetary ASC)      AS m_score   -- 4 = highest spend
    FROM rfm_base
)
SELECT
    customer_id,
    recency_days,
    frequency,
    monetary,
    r_score, f_score, m_score,
    (r_score + f_score + m_score) AS rfm_total,
    CASE
        WHEN (r_score + f_score + m_score) >= 10 THEN 'Champion'
        WHEN (r_score + f_score + m_score) >= 7  THEN 'Loyal'
        WHEN (r_score + f_score + m_score) >= 5  THEN 'At Risk'
        ELSE 'Churn Risk'
    END AS customer_segment
FROM rfm_scored
ORDER BY rfm_total DESC;


-- ----------------------------------------------------------------------------
-- 6. Churn-risk customers: no purchase in the last 90 days but were
--    previously active (had 3+ orders historically)
-- ----------------------------------------------------------------------------
WITH snapshot AS (
    SELECT MAX(order_date) AS snapshot_date FROM transactions
),
customer_stats AS (
    SELECT
        customer_id,
        MAX(order_date)              AS last_order_date,
        COUNT(DISTINCT invoice_id)   AS total_orders,
        ROUND(SUM(revenue), 2)       AS lifetime_value
    FROM transactions
    GROUP BY customer_id
)
SELECT
    cs.customer_id,
    c.customer_name,
    cs.last_order_date,
    cs.total_orders,
    cs.lifetime_value,
    DATEDIFF((SELECT snapshot_date FROM snapshot), cs.last_order_date) AS days_since_last_order
FROM customer_stats cs
JOIN customers c ON cs.customer_id = c.customer_id
WHERE cs.total_orders >= 3
  AND DATEDIFF((SELECT snapshot_date FROM snapshot), cs.last_order_date) > 90
ORDER BY lifetime_value DESC
LIMIT 20;


-- ----------------------------------------------------------------------------
-- 7. Top 10 highest lifetime-value customers
-- ----------------------------------------------------------------------------
SELECT
    c.customer_id,
    c.customer_name,
    c.country,
    COUNT(DISTINCT t.invoice_id) AS total_orders,
    ROUND(SUM(t.revenue), 2)     AS lifetime_value
FROM transactions t
JOIN customers c ON t.customer_id = c.customer_id
GROUP BY c.customer_id, c.customer_name, c.country
ORDER BY lifetime_value DESC
LIMIT 10;