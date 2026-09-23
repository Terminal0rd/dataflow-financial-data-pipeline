"""
DataFlow — Data Validation Module (Data Quality Framework)
==========================================================

Validates incoming data against business rules and data quality constraints.
Separates valid data from invalid data and generates a detailed DQ report.

Checks implemented:
- Completeness (missing required fields)
- Uniqueness (duplicate IDs)
- Validity (amounts > 0, valid categories, valid dates)
- Referential Integrity (transaction customer_ids exist in customer dataset)
"""

import json
import logging
from pathlib import Path
from typing import Tuple

import pandas as pd

logger = logging.getLogger(__name__)

# Reference data
VALID_CATEGORIES = {
    "groceries", "utilities", "entertainment", "healthcare",
    "education", "travel", "dining", "shopping", "fuel",
    "insurance", "rent", "salary", "investment", "transfer",
    "subscription",
}

class DataValidator:
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.dq_report_path = self.output_dir / "data_quality_report.json"
        self.rejected_records_path = self.output_dir / "validation_rejected_records.csv"
        
        # Initialize report structure
        self.report = {
            "customers": {
                "records_processed": 0,
                "valid_records": 0,
                "rejected_records": 0,
                "issues": {
                    "missing_customer_id": 0,
                    "duplicate_customer_id": 0
                }
            },
            "transactions": {
                "records_processed": 0,
                "valid_records": 0,
                "rejected_records": 0,
                "issues": {
                    "missing_fields": 0,
                    "duplicate_transaction_id": 0,
                    "invalid_amount": 0,
                    "invalid_category": 0,
                    "orphan_transaction": 0,
                    "invalid_date": 0
                }
            }
        }
        
        # Reset rejected records file
        with open(self.rejected_records_path, "w", encoding="utf-8") as f:
            f.write("entity,error_reason,raw_data\n")

    def _log_rejected(self, entity: str, error_reason: str, df_rejected: pd.DataFrame):
        """Append rejected records to the rejected log file."""
        if df_rejected.empty:
            return
            
        with open(self.rejected_records_path, "a", encoding="utf-8") as f:
            for _, row in df_rejected.iterrows():
                # Convert row to dict, handling NaNs
                row_dict = {k: ("" if pd.isna(v) else v) for k, v in row.items()}
                # Dump as a JSON string to keep it contained in one CSV column
                raw_data = json.dumps(row_dict)
                f.write(f'{entity},"{error_reason}","{raw_data.replace('"', '""')}"\n')

    def validate_customers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate customer records."""
        logger.info("Validating customer records...")
        self.report["customers"]["records_processed"] = len(df)
        
        valid_df = df.copy()
        
        # 1. Completeness: Missing customer_id
        missing_id_mask = valid_df["customer_id"].isna()
        if missing_id_mask.any():
            missing_count = missing_id_mask.sum()
            self.report["customers"]["issues"]["missing_customer_id"] = int(missing_count)
            self._log_rejected("customer", "Missing customer_id", valid_df[missing_id_mask])
            valid_df = valid_df[~missing_id_mask]

        # 2. Uniqueness: Duplicate customer_id
        duplicate_mask = valid_df.duplicated(subset=["customer_id"], keep="first")
        if duplicate_mask.any():
            dup_count = duplicate_mask.sum()
            self.report["customers"]["issues"]["duplicate_customer_id"] = int(dup_count)
            self._log_rejected("customer", "Duplicate customer_id", valid_df[duplicate_mask])
            valid_df = valid_df[~duplicate_mask]

        self.report["customers"]["valid_records"] = len(valid_df)
        self.report["customers"]["rejected_records"] = len(df) - len(valid_df)
        
        logger.info(f"Customer validation complete. Valid: {len(valid_df)}, Rejected: {len(df) - len(valid_df)}")
        return valid_df

    def validate_transactions(self, df: pd.DataFrame, valid_customer_ids: set) -> pd.DataFrame:
        """Validate transaction records."""
        logger.info("Validating transaction records...")
        self.report["transactions"]["records_processed"] = len(df)
        
        valid_df = df.copy()
        
        # 1. Completeness (Missing ID or Amount)
        missing_mask = valid_df["customer_id"].isna() | valid_df["amount"].isna()
        if missing_mask.any():
            missing_count = missing_mask.sum()
            self.report["transactions"]["issues"]["missing_fields"] = int(missing_count)
            self._log_rejected("transaction", "Missing customer_id or amount", valid_df[missing_mask])
            valid_df = valid_df[~missing_mask]

        # 2. Uniqueness
        duplicate_mask = valid_df.duplicated(subset=["transaction_id"], keep="first")
        if duplicate_mask.any():
            dup_count = duplicate_mask.sum()
            self.report["transactions"]["issues"]["duplicate_transaction_id"] = int(dup_count)
            self._log_rejected("transaction", "Duplicate transaction_id", valid_df[duplicate_mask])
            valid_df = valid_df[~duplicate_mask]

        # 3. Validity: Amounts must be > 0
        # Coerce amounts to numeric, setting errors to NaN just in case
        amounts = pd.to_numeric(valid_df["amount"], errors="coerce")
        invalid_amount_mask = amounts <= 0
        if invalid_amount_mask.any():
            invalid_count = invalid_amount_mask.sum()
            self.report["transactions"]["issues"]["invalid_amount"] = int(invalid_count)
            self._log_rejected("transaction", "Amount <= 0", valid_df[invalid_amount_mask])
            valid_df = valid_df[~invalid_amount_mask]

        # 4. Validity: Categories
        invalid_category_mask = ~valid_df["category"].isin(VALID_CATEGORIES)
        if invalid_category_mask.any():
            invalid_cat_count = invalid_category_mask.sum()
            self.report["transactions"]["issues"]["invalid_category"] = int(invalid_cat_count)
            self._log_rejected("transaction", "Invalid category", valid_df[invalid_category_mask])
            valid_df = valid_df[~invalid_category_mask]
            
        # 5. Validity: Dates
        # Valid range roughly between 2000 and 2050
        dates = pd.to_datetime(valid_df["transaction_date"], errors="coerce")
        invalid_date_mask = dates.isna() | (dates.dt.year < 2000) | (dates.dt.year > 2050)
        if invalid_date_mask.any():
            invalid_date_count = invalid_date_mask.sum()
            self.report["transactions"]["issues"]["invalid_date"] = int(invalid_date_count)
            self._log_rejected("transaction", "Invalid date", valid_df[invalid_date_mask])
            valid_df = valid_df[~invalid_date_mask]

        # 6. Referential Integrity: Orphan transactions
        orphan_mask = ~valid_df["customer_id"].isin(valid_customer_ids)
        if orphan_mask.any():
            orphan_count = orphan_mask.sum()
            self.report["transactions"]["issues"]["orphan_transaction"] = int(orphan_count)
            self._log_rejected("transaction", "Orphan transaction (customer_id not found)", valid_df[orphan_mask])
            valid_df = valid_df[~orphan_mask]

        self.report["transactions"]["valid_records"] = len(valid_df)
        self.report["transactions"]["rejected_records"] = len(df) - len(valid_df)
        
        logger.info(f"Transaction validation complete. Valid: {len(valid_df)}, Rejected: {len(df) - len(valid_df)}")
        return valid_df

    def save_report(self):
        """Save the Data Quality Report to a JSON file."""
        with open(self.dq_report_path, "w", encoding="utf-8") as f:
            json.dump(self.report, f, indent=4)
        logger.info(f"Data Quality Report saved to {self.dq_report_path}")

    def run_validation(self, df_customers: pd.DataFrame, df_transactions: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Run all validations and return cleaned dataframes."""
        valid_customers = self.validate_customers(df_customers)
        
        # Get set of valid customer IDs for referential integrity check
        valid_customer_ids = set(valid_customers["customer_id"].dropna().unique())
        
        valid_transactions = self.validate_transactions(df_transactions, valid_customer_ids)
        
        self.save_report()
        return valid_customers, valid_transactions

if __name__ == "__main__":
    from ingest import DataIngestor
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    project_root = Path(__file__).resolve().parent.parent
    raw_dir = project_root / "data" / "raw"
    output_dir = project_root / "data" / "output"
    
    # 1. Ingest
    ingestor = DataIngestor(raw_dir, output_dir)
    raw_customers = ingestor.ingest_customers()
    raw_transactions = ingestor.ingest_all_transactions()
    
    # 2. Validate
    validator = DataValidator(output_dir)
    valid_customers, valid_transactions = validator.run_validation(raw_customers, raw_transactions)
    
    print("\n--- Validation Test Summary ---")
    print(f"Customers Input: {len(raw_customers)} -> Valid: {len(valid_customers)}")
    print(f"Transactions Input: {len(raw_transactions)} -> Valid: {len(valid_transactions)}")
    print(f"Data Quality Report: {validator.dq_report_path}")
    print(f"Rejected Records File: {validator.rejected_records_path}")
