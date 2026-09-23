"""
DataFlow — Data Analysis and Visualization
==========================================

Performs analytical queries using Pandas and generates summary reports and 
professional visualizations using Matplotlib.
"""

import logging
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)

class DataAnalyzer:
    def __init__(self, processed_dir: Path, reports_dir: Path):
        self.processed_dir = Path(processed_dir)
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Load cleaned datasets
        logger.info("Loading cleaned datasets for analysis...")
        self.customers = pd.read_parquet(self.processed_dir / "customers_clean.parquet")
        self.transactions = pd.read_parquet(self.processed_dir / "transactions_clean.parquet")
        
        # Merge for combined analysis
        self.merged_df = pd.merge(
            self.transactions, 
            self.customers, 
            on="customer_id", 
            how="inner"
        )
        
        # Set chart style
        plt.style.use('bmh')

    def generate_summary_reports(self):
        """Generate tabular summary CSV reports."""
        logger.info("Generating summary reports...")
        
        # 1. Monthly Transactions
        # Convert date to Year-Month period for grouping
        self.merged_df['month'] = self.merged_df['transaction_date'].dt.to_period('M')
        monthly_summary = self.merged_df.groupby('month').agg(
            total_transactions=('transaction_id', 'count'),
            total_value=('amount', 'sum'),
            avg_value=('amount', 'mean')
        ).reset_index()
        monthly_summary['month'] = monthly_summary['month'].astype(str)
        monthly_summary.to_csv(self.reports_dir / "monthly_transactions.csv", index=False)
        
        # 2. Category Analysis
        category_summary = self.merged_df.groupby('category').agg(
            transaction_count=('transaction_id', 'count'),
            total_value=('amount', 'sum')
        ).sort_values('total_value', ascending=False).reset_index()
        category_summary.to_csv(self.reports_dir / "category_analysis.csv", index=False)
        
        # 3. Customer Summary (Top 100)
        customer_summary = self.merged_df.groupby(['customer_id', 'first_name', 'last_name', 'city']).agg(
            total_transactions=('transaction_id', 'count'),
            total_spent=('amount', 'sum')
        ).sort_values('total_spent', ascending=False).head(100).reset_index()
        customer_summary.to_csv(self.reports_dir / "customer_summary.csv", index=False)

    def generate_visualizations(self):
        """Generate Matplotlib charts."""
        logger.info("Generating visualizations...")
        
        # Create a single figure with multiple subplots
        fig = plt.figure(figsize=(15, 12))
        fig.suptitle('DataFlow Transaction Analytics', fontsize=18, fontweight='bold', y=0.98)
        
        # Plot 1: Monthly Transaction Volume & Value
        ax1 = plt.subplot(2, 2, 1)
        monthly_data = self.merged_df.groupby('month')['amount'].sum()
        monthly_data.index = monthly_data.index.astype(str)
        monthly_data.plot(kind='line', marker='o', color='#1f77b4', ax=ax1)
        ax1.set_title('Monthly Transaction Value', fontsize=12)
        ax1.set_ylabel('Total Amount')
        ax1.set_xlabel('Month')
        ax1.tick_params(axis='x', rotation=45)
        
        # Plot 2: Transaction Category Distribution
        ax2 = plt.subplot(2, 2, 2)
        cat_data = self.merged_df.groupby('category')['transaction_id'].count().sort_values(ascending=True)
        cat_data.plot(kind='barh', color='#2ca02c', ax=ax2)
        ax2.set_title('Transaction Volume by Category', fontsize=12)
        ax2.set_xlabel('Count')
        
        # Plot 3: Failed vs Successful Transactions
        ax3 = plt.subplot(2, 2, 3)
        status_data = self.merged_df['transaction_status'].value_counts()
        status_data.plot(kind='pie', autopct='%1.1f%%', colors=['#2ca02c', '#d62728', '#ff7f0e'], ax=ax3)
        ax3.set_title('Transaction Status', fontsize=12)
        ax3.set_ylabel('') # Remove y-label for pie chart
        
        # Plot 4: Transaction Value by Top 10 Cities
        ax4 = plt.subplot(2, 2, 4)
        city_data = self.merged_df.groupby('city')['amount'].sum().sort_values(ascending=False).head(10)
        city_data.plot(kind='bar', color='#9467bd', ax=ax4)
        ax4.set_title('Total Value by Top 10 Cities', fontsize=12)
        ax4.set_ylabel('Total Amount')
        ax4.tick_params(axis='x', rotation=45)
        
        plt.tight_layout(pad=3.0)
        
        # Save figure
        chart_path = self.reports_dir / "analytics_dashboard.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        logger.info(f"Visualizations saved to {chart_path}")

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    project_root = Path(__file__).resolve().parent.parent
    processed_dir = project_root / "data" / "processed"
    reports_dir = project_root / "reports"
    
    analyzer = DataAnalyzer(processed_dir, reports_dir)
    analyzer.generate_summary_reports()
    analyzer.generate_visualizations()
    
    print("\n--- Analytics Generation Complete ---")
    print("Reports generated in /reports folder.")
