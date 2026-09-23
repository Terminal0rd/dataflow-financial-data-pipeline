-- DataFlow — Database Schema
-- --------------------------------------------------------
-- Defines the normalized relational structure for the cleaned data.
-- Includes primary keys, foreign keys, check constraints, and indexes
-- optimized for downstream analytics.

DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS customers;

-- --------------------------------------------------------
-- 1. Customers Table
-- --------------------------------------------------------
CREATE TABLE customers (
    customer_id VARCHAR(50) PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    age INT CHECK (age >= 18 AND age <= 120),
    city VARCHAR(100) NOT NULL,
    account_type VARCHAR(50) NOT NULL,
    account_open_date DATE NOT NULL
);

-- Index for demographic analysis by city and account type
CREATE INDEX idx_customers_city ON customers(city);
CREATE INDEX idx_customers_account_type ON customers(account_type);

-- --------------------------------------------------------
-- 2. Transactions Table
-- --------------------------------------------------------
CREATE TABLE transactions (
    transaction_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    transaction_date TIMESTAMP NOT NULL,
    transaction_type VARCHAR(20) NOT NULL,
    category VARCHAR(50) NOT NULL,
    amount DECIMAL(15, 2) NOT NULL CHECK (amount > 0),
    currency VARCHAR(10) NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    merchant VARCHAR(150),
    transaction_status VARCHAR(20) NOT NULL,
    
    -- Enforce referential integrity: Every transaction must belong to a valid customer
    CONSTRAINT fk_customer
        FOREIGN KEY (customer_id) 
        REFERENCES customers(customer_id)
        ON DELETE CASCADE
);

-- Indexes for common analytical query patterns
CREATE INDEX idx_transactions_customer_id ON transactions(customer_id);
CREATE INDEX idx_transactions_date ON transactions(transaction_date);
CREATE INDEX idx_transactions_category ON transactions(category);
CREATE INDEX idx_transactions_status ON transactions(transaction_status);

-- Note: In a true enterprise data warehouse (like Snowflake/Redshift), 
-- you might not use traditional B-tree indexes like this, but in standard
-- Postgres/MySQL OLTP/Reporting systems, these speed up aggregations significantly.
