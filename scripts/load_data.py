"""
load_data.py
------------
Loads the generated CSV files into a MySQL database (retail_analytics)
using the schema defined in sql/schema.sql.

Run this after data/generate_data.py, and after running sql/schema.sql
in MySQL Workbench to create the tables.

SETUP: This script reads your MySQL password from an environment variable
(MYSQL_PASSWORD) rather than hardcoding it in the file — this keeps the
project safe to push to a public GitHub repo.

To set it before running (PowerShell):
    $env:MYSQL_PASSWORD = "your_actual_password"
    python scripts/load_data.py
"""

import os
from pathlib import Path
from urllib.parse import quote_plus

import pandas as pd
from sqlalchemy import create_engine

# ---------------------------------------------------------------------------
# MySQL connection settings
# ---------------------------------------------------------------------------
MYSQL_USER = os.environ.get("MYSQL_USER", "root")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD")  # required, no default
MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.environ.get("MYSQL_PORT", 3306))
MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "retail_analytics")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"


def main():
    if not MYSQL_PASSWORD:
        raise SystemExit(
            "MYSQL_PASSWORD environment variable is not set.\n"
            "Set it first, e.g. in PowerShell:\n"
            '    $env:MYSQL_PASSWORD = "your_actual_password"\n'
            "then re-run this script."
        )

    # URL-encode the password: special characters like '@', ':', '/' inside
    # a password break the connection string unless escaped this way.
    encoded_password = quote_plus(MYSQL_PASSWORD)

    connection_string = (
        f"mysql+mysqlconnector://{MYSQL_USER}:{encoded_password}"
        f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
    )
    engine = create_engine(connection_string)

    # 1. Load CSVs
    customers_df = pd.read_csv(DATA_DIR / "customers.csv")
    products_df = pd.read_csv(DATA_DIR / "products.csv")
    transactions_df = pd.read_csv(DATA_DIR / "transactions.csv")

    # 2. Push into MySQL tables (tables already created via schema_mysql.sql,
    #    so we use if_exists="append" — NOT "replace", which would drop
    #    the schema/types we carefully defined)
    customers_df.to_sql("customers", engine, if_exists="append", index=False)
    print(f"  customers: {len(customers_df)} rows loaded")

    products_df.to_sql("products", engine, if_exists="append", index=False)
    print(f"  products: {len(products_df)} rows loaded")

    transactions_df.to_sql("transactions", engine, if_exists="append", index=False)
    print(f"  transactions: {len(transactions_df)} rows loaded")

    print("\nAll data loaded into MySQL database:", MYSQL_DATABASE)


if __name__ == "__main__":
    main()
