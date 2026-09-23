"""
DataFlow — Data Ingestion Module
=================================

Responsible for extracting raw data from various sources (CSV, JSON).
Handles reading malformed files gracefully by capturing parsing errors
and separating rejected records.

Outputs Pandas DataFrames for downstream processing.
"""

import csv
import json
import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

class DataIngestor:
    def __init__(self, raw_data_dir: Path, output_dir: Path):
        self.raw_data_dir = Path(raw_data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.rejected_records_file = self.output_dir / "ingestion_rejected_records.csv"
        
        # Initialize rejected records file
        with open(self.rejected_records_file, "w", encoding="utf-8") as f:
            f.write("file_source,error_reason,raw_data\n")

    def log_rejected_record(self, file_source: str, error_reason: str, raw_data: str):
        """Append a rejected record to the rejection log."""
        with open(self.rejected_records_file, "a", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([file_source, error_reason, raw_data.strip()])

    def ingest_customers(self) -> pd.DataFrame:
        """Ingest customers from CSV."""
        filepath = self.raw_data_dir / "customers.csv"
        logger.info(f"Ingesting customers from {filepath}")
        
        try:
            df = pd.read_csv(filepath)
            logger.info(f"Successfully loaded {len(df)} customer records.")
            return df
        except Exception as e:
            logger.error(f"Failed to read customers CSV: {e}")
            raise

    def ingest_transactions_csv(self) -> pd.DataFrame:
        """Ingest transactions from CSV."""
        filepath = self.raw_data_dir / "transactions.csv"
        logger.info(f"Ingesting transactions from {filepath}")
        
        try:
            df = pd.read_csv(filepath)
            logger.info(f"Successfully loaded {len(df)} transaction records from CSV.")
            return df
        except Exception as e:
            logger.error(f"Failed to read transactions CSV: {e}")
            raise

    def ingest_transactions_json(self) -> pd.DataFrame:
        """
        Ingest transactions from JSON array.
        Reads line by line to gracefully handle intentionally malformed JSON records.
        """
        filepath = self.raw_data_dir / "transactions_events.json"
        logger.info(f"Ingesting transactions from {filepath}")
        
        valid_records = []
        malformed_count = 0
        
        with open(filepath, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                stripped_line = line.strip()
                
                # Skip array brackets
                if stripped_line in ("[", "]"):
                    continue
                
                # Remove trailing comma for JSON parsing
                if stripped_line.endswith(","):
                    stripped_line = stripped_line[:-1]
                
                if not stripped_line:
                    continue
                    
                try:
                    record = json.loads(stripped_line)
                    valid_records.append(record)
                except json.JSONDecodeError as e:
                    malformed_count += 1
                    self.log_rejected_record(
                        file_source="transactions_events.json",
                        error_reason=f"JSON Parse Error at line {line_no}: {str(e)}",
                        raw_data=stripped_line
                    )

        logger.info(f"Successfully loaded {len(valid_records)} valid records from JSON.")
        if malformed_count > 0:
            logger.warning(f"Rejected {malformed_count} malformed JSON records.")
            
        return pd.DataFrame(valid_records)

    def ingest_all_transactions(self) -> pd.DataFrame:
        """Ingest and combine all transaction sources."""
        df_csv = self.ingest_transactions_csv()
        df_json = self.ingest_transactions_json()
        
        df_combined = pd.concat([df_csv, df_json], ignore_index=True)
        logger.info(f"Combined transactions dataframe shape: {df_combined.shape}")
        
        return df_combined

if __name__ == "__main__":
    # Configure logging for standalone test
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    project_root = Path(__file__).resolve().parent.parent
    raw_dir = project_root / "data" / "raw"
    output_dir = project_root / "data" / "output"
    
    ingestor = DataIngestor(raw_dir, output_dir)
    
    customers_df = ingestor.ingest_customers()
    transactions_df = ingestor.ingest_all_transactions()
    
    print("\n--- Ingestion Test Summary ---")
    print(f"Customers shape: {customers_df.shape}")
    print(f"Transactions shape: {transactions_df.shape}")
    print(f"Rejected records logged to: {ingestor.rejected_records_file}")
