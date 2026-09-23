"""
DataFlow — Data Transformation Module
=====================================

Performs data cleaning, normalization, and type casting on validated data.
Outputs the final clean dataset as Parquet files, demonstrating an understanding
of efficient columnar storage formats for analytics.
"""

import logging
from pathlib import Path
from typing import Tuple

import pandas as pd

logger = logging.getLogger(__name__)

class DataTransformer:
    def __init__(self, processed_dir: Path):
        self.processed_dir = Path(processed_dir)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def transform_customers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and normalize customer records."""
        logger.info("Transforming customer records...")
        
        # We use .copy() to avoid SettingWithCopyWarning
        df_clean = df.copy()

        # 1. Type Casting
        df_clean["customer_id"] = df_clean["customer_id"].astype(str)
        df_clean["first_name"] = df_clean["first_name"].astype(str)
        df_clean["last_name"] = df_clean["last_name"].astype(str)
        df_clean["age"] = df_clean["age"].astype(int)
        df_clean["account_type"] = df_clean["account_type"].astype(str)
        
        # Parse dates to proper datetime objects
        df_clean["account_open_date"] = pd.to_datetime(df_clean["account_open_date"], format="mixed").dt.date

        # 2. Text Normalization: Fix inconsistent city casing (e.g., "MUMBAI", "mumbai" -> "Mumbai")
        # .str.title() capitalizes the first letter of each word
        df_clean["city"] = df_clean["city"].astype(str).str.strip().str.title()

        logger.info(f"Customer transformation complete. Shape: {df_clean.shape}")
        return df_clean

    def transform_transactions(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and normalize transaction records."""
        logger.info("Transforming transaction records...")
        
        df_clean = df.copy()

        # 1. Type Casting
        df_clean["transaction_id"] = df_clean["transaction_id"].astype(str)
        df_clean["customer_id"] = df_clean["customer_id"].astype(str)
        df_clean["transaction_type"] = df_clean["transaction_type"].astype(str)
        df_clean["category"] = df_clean["category"].astype(str)
        df_clean["currency"] = df_clean["currency"].astype(str).str.upper()
        df_clean["payment_method"] = df_clean["payment_method"].astype(str)
        df_clean["merchant"] = df_clean["merchant"].astype(str)
        df_clean["transaction_status"] = df_clean["transaction_status"].astype(str)

        # Cast amounts to float and round to 2 decimal places
        df_clean["amount"] = df_clean["amount"].astype(float).round(2)
        
        # Parse timestamps
        df_clean["transaction_date"] = pd.to_datetime(df_clean["transaction_date"])

        # 2. Text Normalization
        # Standardize categories to lowercase just in case
        df_clean["category"] = df_clean["category"].str.lower().str.strip()
        
        logger.info(f"Transaction transformation complete. Shape: {df_clean.shape}")
        return df_clean

    def save_to_parquet(self, df_customers: pd.DataFrame, df_transactions: pd.DataFrame):
        """Save the cleaned DataFrames to Parquet format for downstream analytics/loading."""
        customers_path = self.processed_dir / "customers_clean.parquet"
        transactions_path = self.processed_dir / "transactions_clean.parquet"
        
        logger.info(f"Saving cleaned customers to {customers_path}")
        df_customers.to_parquet(customers_path, index=False)
        
        logger.info(f"Saving cleaned transactions to {transactions_path}")
        df_transactions.to_parquet(transactions_path, index=False)

    def run_transformation(self, df_customers: pd.DataFrame, df_transactions: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Run all transformations and export to Parquet."""
        clean_customers = self.transform_customers(df_customers)
        clean_transactions = self.transform_transactions(df_transactions)
        
        self.save_to_parquet(clean_customers, clean_transactions)
        return clean_customers, clean_transactions

if __name__ == "__main__":
    from ingest import DataIngestor
    from validate import DataValidator
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    project_root = Path(__file__).resolve().parent.parent
    raw_dir = project_root / "data" / "raw"
    output_dir = project_root / "data" / "output"
    processed_dir = project_root / "data" / "processed"
    
    # 1. Ingest
    ingestor = DataIngestor(raw_dir, output_dir)
    raw_customers = ingestor.ingest_customers()
    raw_transactions = ingestor.ingest_all_transactions()
    
    # 2. Validate
    validator = DataValidator(output_dir)
    valid_customers, valid_transactions = validator.run_validation(raw_customers, raw_transactions)
    
    # 3. Transform
    transformer = DataTransformer(processed_dir)
    clean_customers, clean_transactions = transformer.run_transformation(valid_customers, valid_transactions)
    
    print("\n--- Transformation Test Summary ---")
    print(f"Clean Customers: {clean_customers.shape}")
    print(f"Clean Transactions: {clean_transactions.shape}")
    print("Files saved to data/processed/ as Parquet.")
