# Online Retail SQL Analytics Dashboard

I built this project to get hands-on with the kind of SQL and data analysis
work that shows up in real business settings — not just running SELECT
statements, but actually answering questions a business would care about:
which products are worth pushing, which customers are worth keeping, and
which ones are quietly slipping away.

## What it does

It's a small e-commerce analytics pipeline. Data lives in MySQL across
three related tables (customers, products, transactions), I query it with
SQL to pull out real business insights, and then visualize the results —
both as static charts and as a live interactive dashboard.

Questions it answers:
- Which products and categories are actually driving revenue?
- How's revenue trending month to month?
- Which countries/markets matter most?
- Who are the most valuable customers, and who's at risk of churning?

## Tech stack

| Layer | Tool |
|---|---|
| Database | MySQL 8+ |
| Querying | SQL — joins, CTEs, window functions |
| Data generation | Python, Faker |
| Analysis & visualization | Python, pandas, matplotlib, seaborn, SQLAlchemy |
| Dashboard | HTML, JS, Chart.js |

## Project structure

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
│   ├── load_data.py               # Loads CSVs into MySQL
│   ├── analysis.py                # Runs queries, generates static charts
│   └── export_dashboard_data.py   # Exports query results for the dashboard
├── dashboard/
│   ├── index.html            # Interactive dashboard (Chart.js)
│   └── data.json             # Exported data the dashboard reads
├── visualizations/            # Static PNG charts
├── .env.example               # Template for MySQL credentials — safe to commit
├── requirements.txt
└── README.md
```

## How to run it

**1. Install dependencies**
```bash
pip install -r requirements.txt
```

**2. Generate the dataset**
```bash
python data/generate_data.py
```
(More on why this is synthetic rather than downloaded, below.)

**3. Set up the database**

In MySQL Workbench or the CLI:
```sql
CREATE DATABASE retail_analytics;
```
Then run `sql/schema.sql` against it to create the tables.

**4. Set your MySQL credentials**

I didn't want to hardcode a password anywhere in this repo, so the scripts
read credentials from environment variables instead. Copy `.env.example`
for reference, then set your password for the session:

```powershell
# PowerShell
$env:MYSQL_PASSWORD = "your_actual_password"
```
```bash
# macOS/Linux
export MYSQL_PASSWORD="your_actual_password"
```

(`MYSQL_USER`, `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_DATABASE` can be overridden
the same way if your setup differs from the defaults.)

**5. Load the data**
```bash
python scripts/load_data.py
```

**6. Generate the charts**
```bash
python scripts/analysis.py
```

**7. (Optional) Build the interactive dashboard**
```bash
python scripts/export_dashboard_data.py
cd dashboard
python -m http.server 8000
```
Then open `http://localhost:8000` in your browser. Note: you can't just
double-click `index.html` — browsers block local file reads for security,
so it needs to be served, even just locally like this.

## The RFM segmentation (the part I'm most proud of)

Customers get split into four tiers using **Recency, Frequency, and
Monetary (RFM)** scoring — a real technique used in marketing/retention
work, not something I made up for this project:

| Segment | What it means |
|---|---|
| **Champion** | Recent, frequent, high-spending |
| **Loyal** | Steady repeat customers |
| **At Risk** | Used to be active, engagement is dropping |
| **Churn Risk** | Hasn't bought in a while — needs winning back |

This is implemented with `NTILE()` window functions and a CTE in
`sql/queries.sql` (query 5) — the part of this project where I learned the
most, honestly.

## Why the dataset is synthetic, not downloaded

I generate the data (`data/generate_data.py`) instead of pulling a Kaggle
dataset, mainly to keep the project fully reproducible for anyone who
clones it. It's built to mirror real e-commerce transaction structure —
customers, products, orders over time — with a deliberate Pareto-style
skew in buying behavior, so the segmentation and churn analysis produce
realistic, uneven patterns instead of a flat distribution. The same schema
and queries work directly against real transactional data too (e.g. the
UCI/Kaggle Online Retail dataset), which comes with its own real-world mess
— missing customer IDs, returns, that sort of thing.

## A note on security

No credentials are hardcoded anywhere in this repo. Everything sensitive
comes from environment variables, and the actual `.env` file (if you make
one locally) is git-ignored — only the placeholder `.env.example` is
tracked.

## Author

Keerthan Vashista Uppunooti
