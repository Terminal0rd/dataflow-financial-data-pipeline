"""
Tests for Data Transformation Module
"""

import pytest
import pandas as pd
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from transform import DataTransformer

@pytest.fixture
def transformer(tmp_path):
    """Fixture providing a DataTransformer instance with a temporary output directory."""
    return DataTransformer(processed_dir=tmp_path)

def test_customer_transformation(transformer):
    """Test text normalization and date parsing for customers."""
    input_data = pd.DataFrame({
        "customer_id": ["1", "2"],
        "first_name": ["Alice", "Bob"],
        "last_name": ["Smith", "Jones"],
        "age": ["25", "30"], # String instead of int
        "city": ["mumbai", "NEW YORK"], # Messy casing
        "account_type": ["savings", "current"],
        "account_open_date": ["2023-01-01 10:00:00", "2023-02-01"] # Mixed date formats
    })
    
    transformed = transformer.transform_customers(input_data)
    
    # Check Type casting
    assert transformed["age"].dtype in ["int32", "int64"]
    assert pd.api.types.is_string_dtype(transformed["customer_id"])
    
    # Check Text Normalization (Title Case)
    assert transformed["city"].iloc[0] == "Mumbai"
    assert transformed["city"].iloc[1] == "New York"
    
    # Check Date parsing (Should be stripped to date only)
    assert str(transformed["account_open_date"].iloc[0]) == "2023-01-01"
    assert str(transformed["account_open_date"].iloc[1]) == "2023-02-01"

def test_transaction_transformation(transformer):
    """Test category normalization and float rounding for transactions."""
    input_data = pd.DataFrame({
        "transaction_id": ["1"],
        "customer_id": ["C1"],
        "transaction_date": ["2023-10-01 10:15:30"],
        "transaction_type": ["credit"],
        "category": ["  GROCERIES  "], # Messy whitespace and casing
        "amount": ["123.45678"], # String format float with many decimals
        "currency": ["inr"], # Lowercase
        "payment_method": ["upi"],
        "merchant": ["Store"],
        "transaction_status": ["success"]
    })
    
    transformed = transformer.transform_transactions(input_data)
    
    # Check Currency normalization
    assert transformed["currency"].iloc[0] == "INR"
    
    # Check Category normalization
    assert transformed["category"].iloc[0] == "groceries"
    
    # Check Amount rounding
    assert transformed["amount"].iloc[0] == 123.46 # Rounded to 2 decimal places
    assert transformed["amount"].dtype == "float64"
    
    # Check Date Parsing
    assert pd.api.types.is_datetime64_any_dtype(transformed["transaction_date"])
