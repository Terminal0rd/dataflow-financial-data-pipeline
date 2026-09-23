"""
DataFlow — Database Load Module
===============================

Loads the cleaned, validated Parquet datasets into the PostgreSQL database.
Uses SQLAlchemy for connection management and Pandas `to_sql` for efficient bulk insertion.
Also handles initializing the schema.
"""

import os
import logging
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

class DataLoader:
    def __init__(self, processed_dir: Path, sql_dir: Path):
        self.processed_dir = Path(processed_dir)
        self.sql_dir = Path(sql_dir)
        
        # Load environment variables
        load_dotenv()
        
        self.db_host = os.getenv("DB_HOST", "localhost")
        self.db_port = os.getenv("DB_PORT", "5432")
        self.db_name = os.getenv("DB_NAME", "dataflow")
        self.db_user = os.getenv("DB_USER", "dataflow_user")
        self.db_password = os.getenv("DB_PASSWORD", "dataflow_pass")
        
        self.connection_string = (
            f"postgresql://{self.db_user}:{self.db_password}@"
            f"{self.db_host}:{self.db_port}/{self.db_name}"
        )

    def get_engine(self) -> Engine:
        """Create and return a SQLAlchemy engine."""
        return create_engine(self.connection_string)

    def initialize_schema(self, engine: Engine):
        """Execute the SQL schema file to create tables and indexes."""
        schema_path = self.sql_dir / "schema.sql"
        logger.info(f"Initializing database schema from {schema_path}")
        
        with open(schema_path, "r", encoding="utf-8") as f:
            sql_statements = f.read()
            
        with engine.connect() as conn:
            # We wrap the text execution to allow multiple statements
            # Typically separated by semicolons in the .sql file
            # SQLAlchemy handles this cleanly.
            conn.execute(text(sql_statements))
            conn.commit()
            
        logger.info("Database schema initialized successfully.")

    def load_customers(self, engine: Engine):
        """Load the cleaned customers dataset into the database."""
        filepath = self.processed_dir / "customers_clean.parquet"
        logger.info(f"Loading customers from {filepath}")
        
        df = pd.read_parquet(filepath)
        
        with engine.begin() as conn:
            # chunksize limits memory consumption on huge datasets
            df.to_sql(
                name="customers",
                con=conn,
                if_exists="append",
                index=False,
                chunksize=10000,
                method="multi"
            )
            
        logger.info(f"Successfully loaded {len(df)} customer records into DB.")

    def load_transactions(self, engine: Engine):
        """Load the cleaned transactions dataset into the database."""
        filepath = self.processed_dir / "transactions_clean.parquet"
        logger.info(f"Loading transactions from {filepath}")
        
        df = pd.read_parquet(filepath)
        
        with engine.begin() as conn:
            df.to_sql(
                name="transactions",
                con=conn,
                if_exists="append",
                index=False,
                chunksize=10000,
                method="multi"
            )
            
        logger.info(f"Successfully loaded {len(df)} transaction records into DB.")

    def run_load(self):
        """Execute the full database loading process."""
        try:
            engine = self.get_engine()
            
            # 1. Setup tables
            self.initialize_schema(engine)
            
            # 2. Insert data (Must load customers first due to Foreign Key)
            self.load_customers(engine)
            self.load_transactions(engine)
            
            logger.info("Data loading complete!")
            
        except Exception as e:
            logger.error(f"Failed to load data into database: {e}")
            raise

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    project_root = Path(__file__).resolve().parent.parent
    processed_dir = project_root / "data" / "processed"
    sql_dir = project_root / "sql"
    
    loader = DataLoader(processed_dir, sql_dir)
    loader.run_load()
