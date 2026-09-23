"""
Tests for Data Validation Module (Data Quality Framework)
"""

import pytest
import pandas as pd
from pathlib import Path

# Adjust path so we can import src modules
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from validate import DataValidator

@pytest.fixture
def validator(tmp_path):
    """Fixture providing a DataValidator instance with a temporary output directory."""
    return DataValidator(output_dir=tmp_path)

@pytest.fixture
def sample_customers():
    """Fixture providing valid customer records."""
    return pd.DataFrame({
        "customer_id": ["CUST001", "CUST002", "CUST003", "CUST001"], # Intentionally added duplicate
        "first_name": ["Alice", "Bob", "Charlie", "Alice"],
        "last_name": ["Smith", "Jones", "Brown", "Smith"],
        "age": [25, 30, 35, 25],
        "city": ["Mumbai", "Delhi", "Pune", "Mumbai"],
        "account_type": ["savings", "current", "salary", "savings"],
        "account_open_date": ["2023-01-01", "2023-02-01", "2023-03-01", "2023-01-01"]
    })

@pytest.fixture
def sample_transactions():
    """Fixture providing transaction records with various data quality issues."""
    return pd.DataFrame({
        "transaction_id": ["TXN001", "TXN002", "TXN003", "TXN004", "TXN005", "TXN006", "TXN007"],
        "customer_id": ["CUST001", "CUST002", "CUST999", None, "CUST001", "CUST002", "CUST001"],
        "transaction_date": [
            "2023-10-01 10:00:00", 
            "2023-10-01 11:00:00", 
            "2023-10-01 12:00:00", # Orphan (CUST999 doesn't exist)
            "2023-10-01 13:00:00", # Missing customer_id
            "1899-01-01 00:00:00", # Invalid date
            "2023-10-01 15:00:00",
            "2023-10-01 16:00:00"
        ],
        "transaction_type": ["credit", "debit", "credit", "debit", "credit", "debit", "credit"],
        "category": ["salary", "groceries", "salary", "dining", "salary", "INVALID_CAT", "salary"],
        "amount": [5000.0, -100.0, 2000.0, 50.0, 1000.0, 200.0, None], # Includes negative and missing amounts
        "currency": ["INR", "INR", "INR", "INR", "INR", "INR", "INR"],
        "payment_method": ["upi", "card", "upi", "upi", "upi", "card", "upi"],
        "merchant": ["Employer", "Store", "Employer", "Cafe", "Employer", "Store", "Employer"],
        "transaction_status": ["success", "success", "success", "success", "success", "success", "success"]
    })

def test_customer_deduplication(validator, sample_customers):
    """Test that duplicate customer records are removed."""
    valid_customers = validator.validate_customers(sample_customers)
    
    # Should drop the 4th row (duplicate of CUST001)
    assert len(valid_customers) == 3
    assert validator.report["customers"]["issues"]["duplicate_customer_id"] == 1

def test_transaction_validation_rules(validator, sample_transactions):
    """Test various transaction validation rules (amounts, categories, orphans)."""
    # Mock valid customer IDs
    valid_customer_ids = {"CUST001", "CUST002", "CUST003"}
    
    valid_txns = validator.validate_transactions(sample_transactions, valid_customer_ids)
    
    # Let's see what should be valid:
    # TXN001: Valid
    # TXN002: Invalid (Negative amount -100)
    # TXN003: Invalid (Orphan, CUST999)
    # TXN004: Invalid (Missing customer_id)
    # TXN005: Invalid (Invalid date 1899)
    # TXN006: Invalid (Invalid category INVALID_CAT)
    # TXN007: Invalid (Missing amount)
    
    assert len(valid_txns) == 1
    assert valid_txns.iloc[0]["transaction_id"] == "TXN001"
    
    # Check if report captured issues correctly
    issues = validator.report["transactions"]["issues"]
    assert issues["invalid_amount"] == 1
    assert issues["orphan_transaction"] == 1
    assert issues["missing_fields"] == 2 # TXN004 (missing cust id) and TXN007 (missing amount)
    assert issues["invalid_date"] == 1
    assert issues["invalid_category"] == 1
