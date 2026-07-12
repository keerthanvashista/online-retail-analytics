"""
generate_data.py
----------------
Generates a realistic synthetic online retail transactions dataset.

Why synthetic data: keeps the project fully reproducible without depending on
external dataset downloads, while mirroring the structure of real-world
e-commerce transaction logs (customers, products, invoices, countries, dates).

Output: data/customers.csv, data/products.csv, data/transactions.csv
"""

import random
from datetime import datetime, timedelta

import pandas as pd
from faker import Faker

fake = Faker()
Faker.seed(42)
random.seed(42)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
NUM_CUSTOMERS = 800
NUM_PRODUCTS = 120
NUM_TRANSACTIONS = 15000
START_DATE = datetime(2024, 1, 1)
END_DATE = datetime(2025, 12, 31)

CATEGORIES = [
    "Home & Kitchen", "Electronics", "Stationery", "Apparel",
    "Toys", "Beauty", "Sports & Outdoors", "Books",
]

COUNTRIES = [
    "United States", "United Kingdom", "Germany", "France",
    "India", "Australia", "Canada", "Netherlands",
]

# ---------------------------------------------------------------------------
# Generate customers
# ---------------------------------------------------------------------------
customers = []
for cid in range(1, NUM_CUSTOMERS + 1):
    customers.append({
        "customer_id": cid,
        "customer_name": fake.name(),
        "country": random.choice(COUNTRIES),
        "signup_date": fake.date_between(start_date=START_DATE, end_date=START_DATE + timedelta(days=180)),
    })
customers_df = pd.DataFrame(customers)

# ---------------------------------------------------------------------------
# Generate products (with a realistic price per category)
# ---------------------------------------------------------------------------
category_price_range = {
    "Home & Kitchen": (8, 90),
    "Electronics": (15, 400),
    "Stationery": (2, 25),
    "Apparel": (10, 120),
    "Toys": (5, 60),
    "Beauty": (5, 70),
    "Sports & Outdoors": (10, 150),
    "Books": (5, 35),
}

products = []
for pid in range(1, NUM_PRODUCTS + 1):
    category = random.choice(CATEGORIES)
    low, high = category_price_range[category]
    products.append({
        "product_id": pid,
        "product_name": f"{fake.word().capitalize()} {category.split()[0]} {pid}",
        "category": category,
        "unit_price": round(random.uniform(low, high), 2),
    })
products_df = pd.DataFrame(products)

# ---------------------------------------------------------------------------
# Generate transactions
# Some customers are "power buyers" (Pareto-ish distribution) to make
# RFM segmentation and churn analysis meaningful.
# ---------------------------------------------------------------------------
customer_weights = [random.paretovariate(1.5) for _ in range(NUM_CUSTOMERS)]
total_weight = sum(customer_weights)
customer_weights = [w / total_weight for w in customer_weights]

transactions = []
for i in range(1, NUM_TRANSACTIONS + 1):
    customer_id = random.choices(customers_df["customer_id"].tolist(), weights=customer_weights, k=1)[0]
    product_row = products_df.sample(1).iloc[0]
    quantity = random.randint(1, 6)

    days_range = (END_DATE - START_DATE).days
    order_date = START_DATE + timedelta(days=random.randint(0, days_range))

    transactions.append({
        "invoice_id": 10000 + i,
        "customer_id": customer_id,
        "product_id": int(product_row["product_id"]),
        "quantity": quantity,
        "unit_price": product_row["unit_price"],
        "order_date": order_date.date(),
    })

transactions_df = pd.DataFrame(transactions)
transactions_df["revenue"] = (transactions_df["quantity"] * transactions_df["unit_price"]).round(2)

# ---------------------------------------------------------------------------
# Save outputs
# ---------------------------------------------------------------------------
customers_df.to_csv("data/customers.csv", index=False)
products_df.to_csv("data/products.csv", index=False)
transactions_df.to_csv("data/transactions.csv", index=False)

print("Generated:")
print(f"  data/customers.csv     ({len(customers_df)} rows)")
print(f"  data/products.csv      ({len(products_df)} rows)")
print(f"  data/transactions.csv  ({len(transactions_df)} rows)")
