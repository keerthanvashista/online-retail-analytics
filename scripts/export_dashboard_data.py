
import json
import os
from pathlib import Path
from urllib.parse import quote_plus

import pandas as pd
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
DASHBOARD_DIR = PROJECT_ROOT / "dashboard"
DASHBOARD_DIR.mkdir(exist_ok=True)

encoded_password = quote_plus(MYSQL_PASSWORD)
connection_string = (
    f"mysql+mysqlconnector://{MYSQL_USER}:{encoded_password}"
    f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
)
engine = create_engine(connection_string)


def query(sql: str) -> pd.DataFrame:
    return pd.read_sql_query(sql, engine)


def main():
    output = {}

    # 1. KPI summary cards
    kpis = query("""
        SELECT
            ROUND(SUM(revenue), 2) AS total_revenue,
            COUNT(DISTINCT customer_id) AS total_customers,
            COUNT(DISTINCT invoice_id) AS total_orders,
            ROUND(AVG(revenue), 2) AS avg_order_value
        FROM transactions
    """)
    output["kpis"] = kpis.iloc[0].to_dict()

    # 2. Top 10 products overall
    top_products = query("""
        SELECT p.product_name AS label, ROUND(SUM(t.revenue), 2) AS value
        FROM transactions t
        JOIN products p ON t.product_id = p.product_id
        GROUP BY p.product_id, p.product_name
        ORDER BY value DESC
        LIMIT 10
    """)
    output["top_products"] = {"all": top_products.to_dict(orient="records")}

    # 2b. Top products broken down by category, for the dashboard's
    #     category filter dropdown
    categories = query("SELECT DISTINCT category FROM products ORDER BY category")
    for cat in categories["category"]:
        rows = query(f"""
            SELECT p.product_name AS label, ROUND(SUM(t.revenue), 2) AS value
            FROM transactions t
            JOIN products p ON t.product_id = p.product_id
            WHERE p.category = '{cat}'
            GROUP BY p.product_id, p.product_name
            ORDER BY value DESC
            LIMIT 10
        """)
        output["top_products"][cat] = rows.to_dict(orient="records")

    # 3. Monthly revenue trend
    monthly = query("""
        SELECT CONCAT(YEAR(order_date), '-', LPAD(MONTH(order_date), 2, '0')) AS label,
               ROUND(SUM(revenue), 2) AS value
        FROM transactions
        GROUP BY label
        ORDER BY label
    """)
    output["monthly_trend"] = monthly.to_dict(orient="records")

    # 4. Revenue by category
    by_category = query("""
        SELECT p.category AS label, ROUND(SUM(t.revenue), 2) AS value
        FROM transactions t
        JOIN products p ON t.product_id = p.product_id
        GROUP BY p.category
        ORDER BY value DESC
    """)
    output["by_category"] = by_category.to_dict(orient="records")

    # 5. Revenue by country
    by_country = query("""
        SELECT c.country AS label, ROUND(SUM(t.revenue), 2) AS value
        FROM transactions t
        JOIN customers c ON t.customer_id = c.customer_id
        GROUP BY c.country
        ORDER BY value DESC
    """)
    output["by_country"] = by_country.to_dict(orient="records")

    # 6. RFM customer segmentation
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
                NTILE(4) OVER (ORDER BY frequency ASC) AS f_score,
                NTILE(4) OVER (ORDER BY monetary ASC) AS m_score
            FROM rfm_base
        )
        SELECT
            CASE
                WHEN (r_score + f_score + m_score) >= 10 THEN 'Champion'
                WHEN (r_score + f_score + m_score) >= 7  THEN 'Loyal'
                WHEN (r_score + f_score + m_score) >= 5  THEN 'At Risk'
                ELSE 'Churn Risk'
            END AS segment,
            COUNT(*) AS count
        FROM rfm_scored
        GROUP BY segment
    """)
    total_customers = int(rfm["count"].sum())
    rfm["pct"] = (rfm["count"] / total_customers * 100).round(1)
    output["rfm_segments"] = rfm.to_dict(orient="records")

    # Write JSON
    out_path = DASHBOARD_DIR / "data.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2, default=str)

    print(f"Dashboard data exported to {out_path}")
    print(f"  Categories found: {list(categories['category'])}")
    print(f"  Total customers: {total_customers}")


if __name__ == "__main__":
    main()
