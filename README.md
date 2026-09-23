# DataFlow — Customer Transaction Data Quality & Analytics Pipeline

## Project Overview
DataFlow is an end-to-end Python and SQL ETL (Extract, Transform, Load) pipeline designed to ingest, validate, clean, and analyze synthetic financial transaction data. 

**Note on Data:** This project uses *completely synthetic, randomly generated data* using the Python `Faker` library. No real customer information was used. The project serves as a portfolio piece to demonstrate data engineering and data quality principles.

## Business Problem
Reliable data is the foundation of any financial institution. Poor data quality (duplicates, missing records, orphaned transactions) leads to inaccurate analytics, flawed reporting, and regulatory risk. This project demonstrates how to build a robust pipeline that intercepts "dirty" source data, validates it against business rules, isolates bad records for auditing, and prepares a clean, normalized dataset for downstream analytics.

## Architecture & Pipeline
![Architecture](https://via.placeholder.com/800x200.png?text=Raw+Data+%E2%86%92+Validation+%E2%86%92+Transformation+%E2%86%92+Database+%E2%86%92+Analytics)

The pipeline follows a standard batch ETL architecture:

1. **Extract (`src/ingest.py`)**: Ingests multi-format source data (CSV, JSON). Includes a custom parser to gracefully bypass structurally malformed JSON records without crashing the pipeline.
2. **Validate (`src/validate.py`)**: Runs strict data quality checks.
3. **Transform (`src/transform.py`)**: Cleans, standardizes, and type-casts the data.
4. **Load (`src/load.py` & `sql/schema.sql`)**: Uses SQLAlchemy to bulk-load the clean Parquet data into a normalized PostgreSQL schema enforcing referential integrity.
5. **Analyze (`src/analysis.py` & `sql/analysis.sql`)**: Generates business reports and visual dashboards using Pandas, Matplotlib, and advanced SQL (CTEs, Window Functions).

## Technologies Used
- **Python**: `pandas` (Data processing), `pytest` (Testing), `Faker` (Synthetic data generation)
- **Database**: PostgreSQL, `sqlalchemy`
- **File Formats**: CSV, JSON, Parquet
- **Infrastructure**: Docker & Docker Compose

## Data Quality Framework
The validation module intentionally traps a controlled percentage of bad records. Rules enforced:
* **Completeness**: Drops rows with NULL `customer_id` or `amount`.
* **Uniqueness**: Removes duplicate `transaction_id` and `customer_id` records.
* **Validity**: Rejects negative amounts, out-of-range dates, and unknown transaction categories.
* **Referential Integrity**: Drops "orphan" transactions where the `customer_id` does not exist in the primary customer dataset.

Rejected records are logged to `data/output/validation_rejected_records.csv` alongside a summary JSON report for auditing.

## Example Output Metrics (Synthetic)
* **Customers Processed**: 10,050 (10,000 valid, 50 duplicates rejected)
* **Transactions Processed**: 75,690 (73,379 valid, ~2,300 invalid rejected)

## How to Run

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Generate the Synthetic Data:**
   ```bash
   python src/generate_data.py
   ```

3. **Run the ETL Pipeline:**
   ```bash
   python src/ingest.py
   python src/validate.py
   python src/transform.py
   ```

4. **Run Analytics & Testing:**
   ```bash
   python src/analysis.py
   pytest tests/ -v
   ```

*(Optional) To load data into PostgreSQL, copy `.env.example` to `.env`, run `docker-compose up -d`, and execute `python src/load.py`.*

## Limitations & Disclaimer
This is a portfolio simulation project. It operates on synthetic batch data generated locally and is not intended to represent the scale, real-time streaming architectures, or strict regulatory governance models of production banking infrastructure like that of JPMorgan Chase. It strictly demonstrates fundamental coding, database, and data quality concepts.
