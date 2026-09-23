"""
DataFlow — Synthetic Financial Data Generator
==============================================

Generates realistic but completely fictional customer and transaction data
for portfolio demonstration purposes. This is NOT real customer data.

Data Quality Issues (Intentionally Introduced)
-----------------------------------------------
The generator deliberately introduces controlled data quality problems
to simulate imperfect source data commonly found in real-world systems.

Issue                           | Approx. %  | Description
------------------------------- | ---------- | ----------------------------------
Duplicate transactions          | 1.0%       | Exact duplicate transaction rows
Missing customer_id             | 0.5%       | NULL customer_id on transactions
Missing amount                  | 0.5%       | NULL transaction amounts
Invalid amounts (negative/zero) | 0.3%       | Amounts <= 0
Inconsistent city casing        | 2.0%       | e.g. "mumbai", "MUMBAI"
Invalid transaction categories  | 0.3%       | Categories not in valid list
Invalid dates                   | 0.2%       | Dates outside reasonable range
Duplicate customers             | 0.5%       | Same customer appearing twice
Orphan transactions             | 0.3%       | customer_id not in customers table
Malformed JSON records          | 0.2%       | Broken JSON structure

Usage:
    python src/generate_data.py
"""

import os
import csv
import json
import random
import logging
from datetime import datetime, timedelta
from pathlib import Path

from faker import Faker

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SEED = 42
NUM_CUSTOMERS = 10_000
NUM_TRANSACTIONS = 75_000

# Data quality issue rates (as fractions)
DUPLICATE_TRANSACTION_RATE = 0.010   # 1.0%
MISSING_CUSTOMER_ID_RATE = 0.005     # 0.5%
MISSING_AMOUNT_RATE = 0.005          # 0.5%
INVALID_AMOUNT_RATE = 0.003          # 0.3%
INCONSISTENT_CITY_RATE = 0.020       # 2.0%
INVALID_CATEGORY_RATE = 0.003        # 0.3%
INVALID_DATE_RATE = 0.002            # 0.2%
DUPLICATE_CUSTOMER_RATE = 0.005      # 0.5%
ORPHAN_TRANSACTION_RATE = 0.003      # 0.3%
MALFORMED_JSON_RATE = 0.002          # 0.2%

# Valid domain values
CITIES = [
    "Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai",
    "Kolkata", "Pune", "Ahmedabad", "Jaipur", "Lucknow",
    "New York", "London", "Singapore", "Dubai", "Tokyo",
]

ACCOUNT_TYPES = ["savings", "current", "salary", "fixed_deposit"]

TRANSACTION_TYPES = ["credit", "debit"]

VALID_CATEGORIES = [
    "groceries", "utilities", "entertainment", "healthcare",
    "education", "travel", "dining", "shopping", "fuel",
    "insurance", "rent", "salary", "investment", "transfer",
    "subscription",
]

INVALID_CATEGORIES = ["xyz_invalid", "unknown_cat", "!!error", "N/A"]

CURRENCIES = ["INR", "USD", "GBP", "SGD", "AED"]

PAYMENT_METHODS = ["upi", "credit_card", "debit_card", "net_banking", "cash"]

TRANSACTION_STATUSES = ["success", "failed", "pending"]

MERCHANTS = [
    "Amazon", "Flipkart", "BigBasket", "Swiggy", "Zomato",
    "Uber", "Ola", "Netflix", "Spotify", "Airtel",
    "Jio", "HDFC Insurance", "SBI Mutual Fund", "BookMyShow",
    "Apollo Pharmacy", "Reliance Fresh", "DMart", "Croma",
    "Myntra", "PhonePe Merchant",
]

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

fake = Faker()
Faker.seed(SEED)
random.seed(SEED)


def random_date(start: datetime, end: datetime) -> datetime:
    """Return a random datetime between *start* and *end*."""
    delta = end - start
    random_seconds = random.randint(0, int(delta.total_seconds()))
    return start + timedelta(seconds=random_seconds)


# ---------------------------------------------------------------------------
# Customer Generation
# ---------------------------------------------------------------------------

def generate_customers() -> list[dict]:
    """Generate a list of synthetic customer records."""
    logger.info("Generating %s customers ...", NUM_CUSTOMERS)

    customers = []
    start_date = datetime(2020, 1, 1)
    end_date = datetime(2025, 6, 30)

    for i in range(1, NUM_CUSTOMERS + 1):
        city = random.choice(CITIES)
        customer = {
            "customer_id": f"CUST{i:06d}",
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "age": random.randint(18, 75),
            "city": city,
            "account_type": random.choice(ACCOUNT_TYPES),
            "account_open_date": random_date(start_date, end_date).strftime(
                "%Y-%m-%d"
            ),
        }
        customers.append(customer)

    return customers


def introduce_customer_issues(customers: list[dict]) -> list[dict]:
    """Introduce data-quality issues into customer records."""
    issues_summary: dict[str, int] = {}

    # --- Duplicate customers ---
    num_duplicates = int(len(customers) * DUPLICATE_CUSTOMER_RATE)
    duplicates = random.sample(customers, num_duplicates)
    customers.extend(duplicates)
    issues_summary["duplicate_customers"] = num_duplicates

    # --- Inconsistent city casing ---
    num_city_issues = int(len(customers) * INCONSISTENT_CITY_RATE)
    city_indices = random.sample(range(len(customers)), num_city_issues)
    for idx in city_indices:
        original = customers[idx]["city"]
        # Randomly apply upper/lower casing
        customers[idx]["city"] = random.choice(
            [original.upper(), original.lower(), original.swapcase()]
        )
    issues_summary["inconsistent_city_casing"] = num_city_issues

    random.shuffle(customers)
    logger.info("Customer issues introduced: %s", issues_summary)
    return customers


# ---------------------------------------------------------------------------
# Transaction Generation
# ---------------------------------------------------------------------------

def generate_transactions(customer_ids: list[str]) -> list[dict]:
    """Generate synthetic transaction records linked to customer IDs."""
    logger.info("Generating %s transactions ...", NUM_TRANSACTIONS)

    start_date = datetime(2024, 7, 1)
    end_date = datetime(2025, 6, 30)

    transactions = []
    for i in range(1, NUM_TRANSACTIONS + 1):
        txn_date = random_date(start_date, end_date)
        txn_type = random.choice(TRANSACTION_TYPES)

        # Amount: mostly reasonable, skewed toward smaller values
        amount = round(random.lognormvariate(6.5, 1.5), 2)
        amount = min(amount, 500_000)  # cap extreme outliers

        transaction = {
            "transaction_id": f"TXN{i:07d}",
            "customer_id": random.choice(customer_ids),
            "transaction_date": txn_date.strftime("%Y-%m-%d %H:%M:%S"),
            "transaction_type": txn_type,
            "category": random.choice(VALID_CATEGORIES),
            "amount": amount,
            "currency": random.choice(CURRENCIES),
            "payment_method": random.choice(PAYMENT_METHODS),
            "merchant": random.choice(MERCHANTS),
            "transaction_status": random.choices(
                TRANSACTION_STATUSES,
                weights=[0.85, 0.10, 0.05],  # 85% success, 10% failed, 5% pending
                k=1,
            )[0],
        }
        transactions.append(transaction)

    return transactions


def introduce_transaction_issues(
    transactions: list[dict], valid_customer_ids: set[str]
) -> list[dict]:
    """Introduce controlled data-quality issues into transaction records."""
    issues_summary: dict[str, int] = {}
    n = len(transactions)

    # We'll track which indices have already been mutated to avoid
    # stacking multiple issues onto the same record.
    mutated_indices: set[int] = set()

    def _pick_indices(rate: float) -> list[int]:
        count = int(n * rate)
        available = list(set(range(n)) - mutated_indices)
        chosen = random.sample(available, min(count, len(available)))
        mutated_indices.update(chosen)
        return chosen

    # --- Duplicate transactions ---
    num_dups = int(n * DUPLICATE_TRANSACTION_RATE)
    dup_sources = random.sample(range(n), num_dups)
    duplicates = [transactions[i].copy() for i in dup_sources]
    transactions.extend(duplicates)
    issues_summary["duplicate_transactions"] = num_dups

    # --- Missing customer_id ---
    for idx in _pick_indices(MISSING_CUSTOMER_ID_RATE):
        transactions[idx]["customer_id"] = None
    issues_summary["missing_customer_id"] = int(n * MISSING_CUSTOMER_ID_RATE)

    # --- Missing amount ---
    for idx in _pick_indices(MISSING_AMOUNT_RATE):
        transactions[idx]["amount"] = None
    issues_summary["missing_amount"] = int(n * MISSING_AMOUNT_RATE)

    # --- Invalid amounts (negative / zero) ---
    for idx in _pick_indices(INVALID_AMOUNT_RATE):
        transactions[idx]["amount"] = round(random.uniform(-1000, 0), 2)
    issues_summary["invalid_amount"] = int(n * INVALID_AMOUNT_RATE)

    # --- Invalid categories ---
    for idx in _pick_indices(INVALID_CATEGORY_RATE):
        transactions[idx]["category"] = random.choice(INVALID_CATEGORIES)
    issues_summary["invalid_category"] = int(n * INVALID_CATEGORY_RATE)

    # --- Invalid dates ---
    for idx in _pick_indices(INVALID_DATE_RATE):
        # Set a date far in the future or past
        bad_date = random.choice(
            [
                datetime(1900, 1, 1),
                datetime(2099, 12, 31),
            ]
        )
        transactions[idx]["transaction_date"] = bad_date.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    issues_summary["invalid_date"] = int(n * INVALID_DATE_RATE)

    # --- Orphan transactions (customer_id not in customers) ---
    for idx in _pick_indices(ORPHAN_TRANSACTION_RATE):
        # Generate a customer_id that definitely does not exist
        orphan_id = f"CUST{900_000 + idx:06d}"
        while orphan_id in valid_customer_ids:
            orphan_id = f"CUST{random.randint(900_000, 999_999):06d}"
        transactions[idx]["customer_id"] = orphan_id
    issues_summary["orphan_transactions"] = int(n * ORPHAN_TRANSACTION_RATE)

    random.shuffle(transactions)
    logger.info("Transaction issues introduced: %s", issues_summary)
    return transactions


# ---------------------------------------------------------------------------
# Writers
# ---------------------------------------------------------------------------

def write_customers_csv(customers: list[dict], filepath: Path) -> None:
    """Write customer records to a CSV file."""
    fieldnames = [
        "customer_id", "first_name", "last_name", "age",
        "city", "account_type", "account_open_date",
    ]
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(customers)

    logger.info("Wrote %s customer records to %s", len(customers), filepath)


def write_transactions_csv(transactions: list[dict], filepath: Path) -> None:
    """Write transaction records to a CSV file."""
    fieldnames = [
        "transaction_id", "customer_id", "transaction_date",
        "transaction_type", "category", "amount", "currency",
        "payment_method", "merchant", "transaction_status",
    ]
    # Split: ~60 % of transactions go into CSV
    csv_txns = transactions[: int(len(transactions) * 0.6)]

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_txns)

    logger.info("Wrote %s transaction records to %s", len(csv_txns), filepath)
    return len(csv_txns)


def write_transactions_json(
    transactions: list[dict], filepath: Path, num_csv: int
) -> None:
    """
    Write remaining transaction records to a JSON file.

    Intentionally introduces a small number of malformed records to simulate
    real-world data-ingestion issues from API/event sources.
    """
    json_txns = transactions[num_csv:]
    records_to_write: list = []

    num_malformed = int(len(json_txns) * MALFORMED_JSON_RATE)
    malformed_indices = set(random.sample(range(len(json_txns)), num_malformed))

    for i, txn in enumerate(json_txns):
        if i in malformed_indices:
            # Create a malformed record: missing closing brace, extra comma, etc.
            # We store it as a raw string marker so we can write broken JSON later.
            records_to_write.append({"__malformed__": True, "partial": str(txn)[:80]})
        else:
            records_to_write.append(txn)

    # Write as a JSON array, but then manually corrupt the malformed entries
    # Strategy: write valid JSON, then post-process the file to break some lines
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("[\n")
        for i, record in enumerate(records_to_write):
            comma = "," if i < len(records_to_write) - 1 else ""
            if record.get("__malformed__"):
                # Write deliberately broken JSON — missing closing brace
                f.write(
                    f'  {{"transaction_id": "MALFORMED", "data": '
                    f'"{record["partial"]}"{comma}\n'
                )
            else:
                f.write(f"  {json.dumps(record)}{comma}\n")
        f.write("]\n")

    logger.info(
        "Wrote %s transaction records to %s (%s malformed)",
        len(json_txns),
        filepath,
        num_malformed,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """Generate all synthetic datasets."""
    logger.info("=" * 60)
    logger.info("DataFlow — Synthetic Data Generator")
    logger.info("=" * 60)

    # Ensure output directory exists
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # ---- Customers ----
    customers = generate_customers()
    customers = introduce_customer_issues(customers)
    write_customers_csv(customers, RAW_DATA_DIR / "customers.csv")

    # Collect valid customer IDs (before duplicates, for orphan detection)
    valid_customer_ids = {c["customer_id"] for c in customers}

    # ---- Transactions ----
    # Use original (non-duplicate) customer IDs for generation
    original_ids = [f"CUST{i:06d}" for i in range(1, NUM_CUSTOMERS + 1)]
    transactions = generate_transactions(original_ids)
    transactions = introduce_transaction_issues(transactions, valid_customer_ids)

    num_csv = write_transactions_csv(
        transactions, RAW_DATA_DIR / "transactions.csv"
    )
    write_transactions_json(
        transactions, RAW_DATA_DIR / "transactions_events.json", num_csv
    )

    # ---- Summary ----
    logger.info("=" * 60)
    logger.info("Generation complete!")
    logger.info("  Customers:    %s records (with issues)", len(customers))
    logger.info("  Transactions: %s records (with issues)", len(transactions))
    logger.info("  CSV file:     %s", RAW_DATA_DIR / "transactions.csv")
    logger.info("  JSON file:    %s", RAW_DATA_DIR / "transactions_events.json")
    logger.info("  Customer CSV: %s", RAW_DATA_DIR / "customers.csv")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
