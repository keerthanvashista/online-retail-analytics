# Online Retail SQL Analytics Dashboard

An end-to-end data analytics project that answers real business questions —
top products, revenue trends, customer segmentation, and churn risk — using
MySQL for data storage/querying and Python for analysis and visualization.

## Overview

This project simulates the analytics workflow of an e-commerce business:
data is stored relationally (customers, products, transactions) in MySQL,
queried with SQL to answer specific business questions, and visualized with
Python to support decision-making.

**Business questions answered:**
- Which products and categories drive the most revenue?
- How is revenue trending month over month?
- Which countries/markets contribute most to the business?
- Which customers are most valuable (RFM segmentation)?
- Which previously active customers are at risk of churning?

## Tech Stack

| Layer | Tool |
|---|---|
| Database | MySQL 8+ |
| Querying | SQL (joins, window functions, CTEs) |
| Data generation | Python, Faker |
| Analysis & visualization | Python, pandas, matplotlib, seaborn, SQLAlchemy |

## Project Structure

```
online-retail-sql-analytics/
├── data/
│   ├── generate_data.py      # Generates synthetic customers/products/transactions
│   ├── customers.csv
│   ├── products.csv
│   └── transactions.csv
├── sql/
│   ├── schema.sql            # Table definitions (MySQL)
│   └── queries.sql           # All business analytics queries
├── scripts/
│   ├── load_data.py          # Loads CSVs into MySQL using schema.sql
│   └── analysis.py           # Runs queries, generates visualizations
├── visualizations/
│   ├── top_10_products.png
│   ├── monthly_revenue_trend.png
│   ├── revenue_by_category.png
│   ├── revenue_by_country.png
│   └── rfm_customer_segments.png
├── .env.example               # Template for MySQL credentials (safe to commit)
├── requirements.txt
└── README.md
```

## How to Run

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Generate the synthetic dataset

```bash
python data/generate_data.py
```

### 3. Create the database and tables

In MySQL Workbench (or the `mysql` CLI):

```sql
CREATE DATABASE retail_analytics;
```

Then run `sql/schema.sql` against that database to create the `customers`,
`products`, and `transactions` tables.

### 4. Set your MySQL credentials

This project reads credentials from environment variables — never hardcoded
in the scripts — so it's safe to keep this repo public. Copy `.env.example`
for reference, then set the password in your terminal session:

```powershell
# PowerShell
$env:MYSQL_PASSWORD = "your_actual_password"
```
```bash
# macOS/Linux
export MYSQL_PASSWORD="your_actual_password"
```

`MYSQL_USER`, `MYSQL_HOST`, `MYSQL_PORT`, and `MYSQL_DATABASE` can also be
overridden via environment variables if your setup differs from the
defaults (`root` / `localhost` / `3306` / `retail_analytics`).

### 5. Load data into MySQL

```bash
python scripts/load_data.py
```

### 6. Run analysis and generate visualizations

```bash
python scripts/analysis.py
```

## Key Analysis: RFM Customer Segmentation

Customers are segmented into four tiers using **Recency, Frequency, and
Monetary (RFM)** scoring — a widely used business analytics technique for
prioritizing marketing and retention efforts:

| Segment | Meaning |
|---|---|
| **Champion** | Recent, frequent, high-spending customers |
| **Loyal** | Consistent repeat customers |
| **At Risk** | Previously active, declining engagement |
| **Churn Risk** | Long since last purchase — needs re-engagement |

See `sql/queries.sql` (query 5) for the full SQL implementation using
window functions (`NTILE`), and `visualizations/rfm_customer_segments.png`
for the resulting distribution.

## Sample Visualizations

- **Top 10 Products by Revenue** — identifies best-selling items
- **Monthly Revenue Trend** — tracks business growth over time
- **Revenue by Category** — highlights which product lines matter most
- **Revenue by Country** — geographic performance breakdown
- **Customer Segmentation** — RFM-based customer value tiers

## Notes on the Dataset

The dataset is synthetically generated (`data/generate_data.py`) rather than
downloaded, to keep the project fully reproducible and self-contained. It
mirrors the structure of real-world e-commerce transaction logs (customers,
products, orders across time) and includes an intentional Pareto-style skew
in purchase behavior, so segmentation and churn analysis produce realistic,
non-uniform patterns rather than a flat distribution. The same pipeline and
queries apply directly to real transactional datasets (e.g., the UCI/Kaggle
Online Retail dataset), which include additional real-world messiness such
as missing customer IDs and returns.

## Security Note

Database credentials are never hardcoded in this repo. Scripts read them
from environment variables (see `.env.example` for the required variables).
A local `.env` file, if you create one, is excluded via `.gitignore` and
will never be committed.

## Author

Keerthan Vashista Uppunooti
