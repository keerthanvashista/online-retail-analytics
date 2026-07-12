

import os
from pathlib import Path
from urllib.parse import quote_plus

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sqlalchemy import create_engine

MYSQL_USER = os.environ.get("MYSQL_USER", "root")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD")
MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.environ.get("MYSQL_PORT", 3306))
MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "retail_analytics")

if not MYSQL_PASSWORD:
    raise SystemExit(
        "MYSQL_PASSWORD environment variable is not set.\n"
        "Set it first, e.g. in PowerShell:\n"
        '    $env:MYSQL_PASSWORD = "your_actual_password"\n'
        "then re-run this script."
    )

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VIZ_DIR = PROJECT_ROOT / "visualizations"
VIZ_DIR.mkdir(exist_ok=True)

sns.set_theme(style="whitegrid")

_encoded_password = quote_plus(MYSQL_PASSWORD)
_connection_string = (
    f"mysql+mysqlconnector://{MYSQL_USER}:{_encoded_password}"
    f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
)
conn = create_engine(_connection_string)


def query(sql: str) -> pd.DataFrame:
    return pd.read_sql_query(sql, conn)


# ---------------------------------------------------------------------------
# 1. Top 10 products by revenue
# ---------------------------------------------------------------------------
top_products = query("""
    SELECT p.product_name, SUM(t.revenue) AS total_revenue
    FROM transactions t
    JOIN products p ON t.product_id = p.product_id
    GROUP BY p.product_id, p.product_name
    ORDER BY total_revenue DESC
    LIMIT 10
""")

plt.figure(figsize=(10, 6))
sns.barplot(data=top_products, y="product_name", x="total_revenue", palette="viridis")
plt.title("Top 10 Products by Revenue")
plt.xlabel("Total Revenue ($)")
plt.ylabel("Product")
plt.tight_layout()
plt.savefig(VIZ_DIR / "top_10_products.png", dpi=150)
plt.close()

# ---------------------------------------------------------------------------
# 2. Monthly revenue trend
# ---------------------------------------------------------------------------
monthly_revenue = query("""
    SELECT CONCAT(YEAR(order_date), '-', LPAD(MONTH(order_date), 2, '0')) AS order_month, SUM(revenue) AS monthly_revenue
    FROM transactions
    GROUP BY order_month
    ORDER BY order_month
""")

plt.figure(figsize=(12, 5))
sns.lineplot(data=monthly_revenue, x="order_month", y="monthly_revenue", marker="o")
plt.title("Monthly Revenue Trend")
plt.xlabel("Month")
plt.ylabel("Revenue ($)")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(VIZ_DIR / "monthly_revenue_trend.png", dpi=150)
plt.close()

# ---------------------------------------------------------------------------
# 3. Revenue by category
# ---------------------------------------------------------------------------
category_revenue = query("""
    SELECT p.category, SUM(t.revenue) AS total_revenue
    FROM transactions t
    JOIN products p ON t.product_id = p.product_id
    GROUP BY p.category
    ORDER BY total_revenue DESC
""")

plt.figure(figsize=(9, 6))
sns.barplot(data=category_revenue, y="category", x="total_revenue", palette="mako")
plt.title("Revenue by Product Category")
plt.xlabel("Total Revenue ($)")
plt.ylabel("Category")
plt.tight_layout()
plt.savefig(VIZ_DIR / "revenue_by_category.png", dpi=150)
plt.close()

# ---------------------------------------------------------------------------
# 4. RFM customer segmentation distribution
# ---------------------------------------------------------------------------
rfm = query("""
    WITH snapshot AS (
        SELECT DATE_ADD(MAX(order_date), INTERVAL 1 DAY) AS snapshot_date FROM transactions
    ),
    rfm_base AS (
        SELECT
            t.customer_id,
            DATEDIFF((SELECT snapshot_date FROM snapshot), MAX(t.order_date)) AS recency_days,
            COUNT(DISTINCT t.invoice_id) AS frequency,
            SUM(t.revenue) AS monetary
        FROM transactions t
        GROUP BY t.customer_id
    ),
    rfm_scored AS (
        SELECT
            customer_id,
            NTILE(4) OVER (ORDER BY recency_days DESC) AS r_score,
            NTILE(4) OVER (ORDER BY frequency ASC)     AS f_score,
            NTILE(4) OVER (ORDER BY monetary ASC)      AS m_score
        FROM rfm_base
    )
    SELECT
        customer_id,
        (r_score + f_score + m_score) AS rfm_total,
        CASE
            WHEN (r_score + f_score + m_score) >= 10 THEN 'Champion'
            WHEN (r_score + f_score + m_score) >= 7  THEN 'Loyal'
            WHEN (r_score + f_score + m_score) >= 5  THEN 'At Risk'
            ELSE 'Churn Risk'
        END AS customer_segment
    FROM rfm_scored
""")

segment_counts = rfm["customer_segment"].value_counts().reset_index()
segment_counts.columns = ["customer_segment", "count"]

plt.figure(figsize=(7, 6))
colors = {"Champion": "#2a9d8f", "Loyal": "#457b9d", "At Risk": "#f4a261", "Churn Risk": "#e76f51"}
order = ["Champion", "Loyal", "At Risk", "Churn Risk"]
segment_counts["customer_segment"] = pd.Categorical(segment_counts["customer_segment"], categories=order, ordered=True)
segment_counts = segment_counts.sort_values("customer_segment")
plt.pie(
    segment_counts["count"],
    labels=segment_counts["customer_segment"],
    autopct="%1.1f%%",
    colors=[colors[s] for s in segment_counts["customer_segment"]],
    startangle=90,
)
plt.title("Customer Segmentation (RFM Analysis)")
plt.tight_layout()
plt.savefig(VIZ_DIR / "rfm_customer_segments.png", dpi=150)
plt.close()

# ---------------------------------------------------------------------------
# 5. Revenue by country
# ---------------------------------------------------------------------------
country_revenue = query("""
    SELECT c.country, SUM(t.revenue) AS total_revenue
    FROM transactions t
    JOIN customers c ON t.customer_id = c.customer_id
    GROUP BY c.country
    ORDER BY total_revenue DESC
""")

plt.figure(figsize=(9, 6))
sns.barplot(data=country_revenue, y="country", x="total_revenue", palette="crest")
plt.title("Revenue by Country")
plt.xlabel("Total Revenue ($)")
plt.ylabel("Country")
plt.tight_layout()
plt.savefig(VIZ_DIR / "revenue_by_country.png", dpi=150)
plt.close()

conn.dispose()

print("Analysis complete. Visualizations saved to:", VIZ_DIR)
for f in sorted(VIZ_DIR.glob("*.png")):
    print(" -", f.name)
