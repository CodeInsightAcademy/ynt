"""
Personal Finance Dashboard - Fixed Version
Handles all file paths, missing data, and runtime errors
"""
import os
import csv
from datetime import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict
import matplotlib.pyplot as plt

# ================== Domain Models ==================
@dataclass
class Transaction:
    date: datetime
    amount: float
    category: str
    description: str

@dataclass
class Budget:
    category: str
    monthly_limit: float

@dataclass
class Account:
    name: str
    balance: float
    account_type: str

# ================== Data Layer ==================
class DataReader(ABC):
    @abstractmethod
    def load_transactions(self) -> List[Transaction]:
        pass
    
    @abstractmethod
    def load_budgets(self) -> List[Budget]:
        pass
    
    @abstractmethod
    def load_accounts(self) -> List[Account]:
        pass

class CsvDataReader(DataReader):
    def __init__(self, base_path: str):
        self.base_path = base_path
    
    def _read_csv(self, filename: str) -> List[Dict]:
        """Helper method to read CSV files with error handling"""
        path = os.path.join(self.base_path, filename)
        if not os.path.exists(path):
            print(f"Warning: {filename} not found at {path}")
            return []
            
        with open(path, 'r') as f:
            return list(csv.DictReader(f))
    
    def load_transactions(self) -> List[Transaction]:
        data = self._read_csv("transactions.csv")
        return [
            Transaction(
                date=datetime.strptime(row['date'], '%Y-%m-%d'),
                amount=float(row['amount']),
                category=row['category'],
                description=row['description']
            ) for row in data if 'date' in row
        ]
    
    def load_budgets(self) -> List[Budget]:
        data = self._read_csv("budgets.csv")
        return [
            Budget(
                category=row['category'],
                monthly_limit=float(row['monthly_limit'])
            ) for row in data if 'category' in row
        ]
    
    def load_accounts(self) -> List[Account]:
        data = self._read_csv("accounts.csv")
        return [
            Account(
                name=row['name'],
                balance=float(row['balance']),
                account_type=row['account_type']
            ) for row in data if 'name' in row
        ]

# ================== Service Layer ==================
class FinanceAnalyzer:
    def __init__(self, data_reader: DataReader):
        self.transactions = data_reader.load_transactions()
        self.budgets = data_reader.load_budgets()
        self.accounts = data_reader.load_accounts()
    
    def get_spending_by_category(self, start_date: datetime, end_date: datetime) -> Dict[str, float]:
        filtered = [t for t in self.transactions if start_date <= t.date <= end_date]
        spending = {}
        for t in filtered:
            spending[t.category] = spending.get(t.category, 0) + t.amount
        return spending
    
    def get_budget_status(self, month: int, year: int) -> Dict[str, Dict[str, float]]:
        start_date = datetime(year, month, 1)
        end_date = datetime(year, month + 1, 1) if month < 12 else datetime(year + 1, 1, 1)
        
        spending = self.get_spending_by_category(start_date, end_date)
        status = {}
        
        for budget in self.budgets:
            actual = spending.get(budget.category, 0)
            status[budget.category] = {
                'budget': budget.monthly_limit,
                'actual': actual,
                'remaining': budget.monthly_limit - actual
            }
        return status
    
    def get_net_worth(self) -> float:
        return sum(account.balance for account in self.accounts)

# ================== Report Generators ==================
class ReportGenerator(ABC):
    @abstractmethod
    def generate(self, data: Dict) -> None:
        pass

class ConsoleReportGenerator(ReportGenerator):
    def generate(self, data: Dict) -> None:
        print("\n=== BUDGET REPORT ===")
        for category, values in data.items():
            print(f"{category}:")
            print(f"  Budget: ${values['budget']:.2f}")
            print(f"  Spent: ${values['actual']:.2f}")
            status = "UNDER" if values['remaining'] >= 0 else "OVER"
            print(f"  Status: {status} by ${abs(values['remaining']):.2f}")
            print("-" * 30)

class VisualizationReportGenerator(ReportGenerator):
    def generate(self, data: Dict) -> None:
        if not data:
            print("No data available for visualization")
            return
            
        categories = list(data.keys())
        budgets = [v['budget'] for v in data.values()]
        actuals = [v['actual'] for v in data.values()]
        
        fig, ax = plt.subplots()
        x = range(len(categories))
        width = 0.35
        
        ax.bar(x, budgets, width, label='Budget')
        ax.bar([p + width for p in x], actuals, width, label='Actual')
        
        ax.set_ylabel('Amount ($)')
        ax.set_title('Budget vs Actual Spending')
        ax.set_xticks([p + width/2 for p in x])
        ax.set_xticklabels(categories, rotation=45, ha='right')
        ax.legend()
        
        plt.tight_layout()
        plt.savefig('budget_report.png')
        print("\nVisual report saved as 'budget_report.png'")

# ================== Alert System ==================
class AlertService:
    def __init__(self, analyzer: FinanceAnalyzer):
        self.analyzer = analyzer
    
    def check_budget_alerts(self, month: int, year: int) -> List[str]:
        status = self.analyzer.get_budget_status(month, year)
        alerts = []
        
        for category, values in status.items():
            if values['actual'] > values['budget']:
                overspend = values['actual'] - values['budget']
                alerts.append(
                    f"ALERT: Overspent ${overspend:.2f} in {category} "
                    f"(Budget: ${values['budget']:.2f}, "
                    f"Actual: ${values['actual']:.2f})"
                )
        return alerts

# ================== Main Application ==================
def main():
    try:
        # Initialize with proper path handling
        script_dir = os.path.dirname(os.path.abspath(__file__))
        data_reader = CsvDataReader(os.path.join(script_dir, 'data'))
        
        analyzer = FinanceAnalyzer(data_reader)
        alert_service = AlertService(analyzer)
        
        print("\nPersonal Finance Dashboard")
        print("=" * 40)
        
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        # Generate reports
        budget_status = analyzer.get_budget_status(current_month, current_year)
        
        console_report = ConsoleReportGenerator()
        console_report.generate(budget_status)
        
        visual_report = VisualizationReportGenerator()
        visual_report.generate(budget_status)
        
        # Check alerts
        alerts = alert_service.check_budget_alerts(current_month, current_year)
        if alerts:
            print("\n=== BUDGET ALERTS ===")
            for alert in alerts:
                print(alert)
        
        # Show net worth
        print(f"\nCurrent Net Worth: ${analyzer.get_net_worth():,.2f}")
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        print("Please check:")
        print("- Data files exist in 'data' folder")
        print("- CSV files have correct headers")
        print("- No commas in text fields without quotes")

if __name__ == "__main__":
    # Ensure matplotlib is installed
    try:
        import matplotlib
        main()
    except ImportError:
        print("Error: matplotlib not installed. Run:")
        print("pip install matplotlib")