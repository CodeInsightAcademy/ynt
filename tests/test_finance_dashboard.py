import pytest
import os
from datetime import datetime
from unittest.mock import patch, MagicMock
from finance_dashboard import (
    Transaction, Budget, Account,
    CsvDataReader, FinanceAnalyzer,
    ConsoleReportGenerator, VisualizationReportGenerator, AlertService, main
)

# --- Fixtures for common test data ---

@pytest.fixture
def temp_data_dir(tmp_path):
    """Creates a temporary directory for data files."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir

@pytest.fixture
def sample_transactions_csv(temp_data_dir):
    """Creates a sample transactions.csv file."""
    filepath = temp_data_dir / "transactions.csv"
    content = (
        "date,amount,category,description\n"
        "2023-01-01,50.00,Food,Groceries\n"
        "2023-01-05,20.00,Transport,Bus fare\n"
        "2023-01-10,100.00,Utilities,Electricity bill\n"
        "2023-02-01,30.00,Food,Restaurant\n"
        "2023-02-15,75.00,Entertainment,Movie tickets\n"
    )
    filepath.write_text(content)
    return filepath

@pytest.fixture
def sample_budgets_csv(temp_data_dir):
    """Creates a sample budgets.csv file."""
    filepath = temp_data_dir / "budgets.csv"
    content = (
        "category,monthly_limit\n"
        "Food,100.00\n"
        "Transport,50.00\n"
        "Utilities,120.00\n"
        "Entertainment,60.00\n"
    )
    filepath.write_text(content)
    return filepath

@pytest.fixture
def sample_accounts_csv(temp_data_dir):
    """Creates a sample accounts.csv file."""
    filepath = temp_data_dir / "accounts.csv"
    content = (
        "name,balance,account_type\n"
        "Checking,1500.50,Bank\n"
        "Savings,5000.00,Bank\n"
        "Credit Card,-200.00,Credit\n"
    )
    filepath.write_text(content)
    return filepath

@pytest.fixture
def data_reader_with_data(sample_transactions_csv, sample_budgets_csv, sample_accounts_csv, temp_data_dir):
    """Provides a CsvDataReader initialized with sample data."""
    return CsvDataReader(str(temp_data_dir))

@pytest.fixture
def finance_analyzer_with_data(data_reader_with_data):
    """Provides a FinanceAnalyzer initialized with sample data."""
    return FinanceAnalyzer(data_reader_with_data)

# --- Tests for Domain Models (basic instantiation) ---

def test_transaction_creation():
    date = datetime(2023, 7, 8)
    transaction = Transaction(date, 50.75, "Food", "Lunch")
    assert transaction.date == date
    assert transaction.amount == 50.75
    assert transaction.category == "Food"
    assert transaction.description == "Lunch"

def test_budget_creation():
    budget = Budget("Rent", 1200.00)
    assert budget.category == "Rent"
    assert budget.monthly_limit == 1200.00

def test_account_creation():
    account = Account("Savings", 10000.00, "Bank")
    assert account.name == "Savings"
    assert account.balance == 10000.00
    assert account.account_type == "Bank"

# --- Tests for Data Layer (CsvDataReader) ---

def test_csv_data_reader_load_transactions(data_reader_with_data):
    transactions = data_reader_with_data.load_transactions()
    assert len(transactions) == 5
    assert transactions[0] == Transaction(datetime(2023, 1, 1), 50.00, "Food", "Groceries")
    assert transactions[4] == Transaction(datetime(2023, 2, 15), 75.00, "Entertainment", "Movie tickets")

def test_csv_data_reader_load_budgets(data_reader_with_data):
    budgets = data_reader_with_data.load_budgets()
    assert len(budgets) == 4
    assert budgets[0] == Budget("Food", 100.00)
    assert budgets[3] == Budget("Entertainment", 60.00)

def test_csv_data_reader_load_accounts(data_reader_with_data):
    accounts = data_reader_with_data.load_accounts()
    assert len(accounts) == 3
    assert accounts[0] == Account("Checking", 1500.50, "Bank")
    assert accounts[2] == Account("Credit Card", -200.00, "Credit")

def test_csv_data_reader_missing_files(temp_data_dir, capsys):
    """Tests that missing files are handled gracefully with warnings."""
    reader = CsvDataReader(str(temp_data_dir))
    
    transactions = reader.load_transactions()
    assert len(transactions) == 0
    captured = capsys.readouterr()
    assert "Warning: transactions.csv not found" in captured.out

    budgets = reader.load_budgets()
    assert len(budgets) == 0
    captured = capsys.readouterr() # read again after second call
    assert "Warning: budgets.csv not found" in captured.out

    accounts = reader.load_accounts()
    assert len(accounts) == 0
    captured = capsys.readouterr() # read again after third call
    assert "Warning: accounts.csv not found" in captured.out

def test_csv_data_reader_empty_files(temp_data_dir):
    """Tests loading from empty CSV files."""
    (temp_data_dir / "transactions.csv").write_text("date,amount,category,description\n")
    (temp_data_dir / "budgets.csv").write_text("category,monthly_limit\n")
    (temp_data_dir / "accounts.csv").write_text("name,balance,account_type\n")

    reader = CsvDataReader(str(temp_data_dir))
    assert reader.load_transactions() == []
    assert reader.load_budgets() == []
    assert reader.load_accounts() == []

# --- Tests for Service Layer (FinanceAnalyzer) ---

def test_finance_analyzer_get_spending_by_category(finance_analyzer_with_data):
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 1, 31)
    spending = finance_analyzer_with_data.get_spending_by_category(start_date, end_date)
    assert spending == {
        "Food": 50.00,
        "Transport": 20.00,
        "Utilities": 100.00
    }

def test_finance_analyzer_get_spending_by_category_no_transactions_in_period(finance_analyzer_with_data):
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 1, 31)
    spending = finance_analyzer_with_data.get_spending_by_category(start_date, end_date)
    assert spending == {}

def test_finance_analyzer_get_net_worth(finance_analyzer_with_data):
    net_worth = finance_analyzer_with_data.get_net_worth()
    # 1500.50 (Checking) + 5000.00 (Savings) - 200.00 (Credit Card)
    assert net_worth == 6300.50

def test_finance_analyzer_empty_data(temp_data_dir):
    """Tests analyzer behavior with no data files."""
    reader = CsvDataReader(str(temp_data_dir))
    analyzer = FinanceAnalyzer(reader)

    assert analyzer.transactions == []
    assert analyzer.budgets == []
    assert analyzer.accounts == []

    assert analyzer.get_spending_by_category(datetime(2023, 1, 1), datetime(2023, 1, 31)) == {}
    assert analyzer.get_budget_status(1, 2023) == {}
    assert analyzer.get_net_worth() == 0.0

# --- Tests for Report Generators ---

def test_console_report_generator_generate(capsys):
    data = {
        "Food": {"budget": 100.00, "actual": 75.00, "remaining": 25.00},
        "Utilities": {"budget": 50.00, "actual": 60.00, "remaining": -10.00}
    }
    generator = ConsoleReportGenerator()
    generator.generate(data)
    captured = capsys.readouterr()
    
    assert "=== BUDGET REPORT ===" in captured.out
    assert "Food:" in captured.out
    assert "Budget: $100.00" in captured.out
    assert "Spent: $75.00" in captured.out
    assert "Status: UNDER by $25.00" in captured.out
    assert "Utilities:" in captured.out
    assert "Budget: $50.00" in captured.out
    assert "Spent: $60.00" in captured.out
    assert "Status: OVER by $10.00" in captured.out

def test_console_report_generator_empty_data(capsys):
    generator = ConsoleReportGenerator()
    generator.generate({})
    captured = capsys.readouterr()
    assert "=== BUDGET REPORT ===" in captured.out
    assert "Food:" not in captured.out # Ensure no data is printed

@patch('matplotlib.pyplot.savefig')
@patch('matplotlib.pyplot.show') # Patch show to prevent window from popping up
@patch('matplotlib.pyplot.subplots')
def test_visualization_report_generator_generate(mock_subplots, mock_show, mock_savefig, capsys):
    mock_fig = MagicMock()
    mock_ax = MagicMock()
    mock_subplots.return_value = (mock_fig, mock_ax)

    data = {
        "Food": {"budget": 100.00, "actual": 75.00, "remaining": 25.00},
        "Utilities": {"budget": 50.00, "actual": 60.00, "remaining": -10.00}
    }
    generator = VisualizationReportGenerator()
    generator.generate(data)
    
    mock_subplots.assert_called_once()
    mock_ax.bar.call_count == 2
    mock_ax.set_ylabel.assert_called_with('Amount ($)')
    mock_ax.set_title.assert_called_with('Budget vs Actual Spending')
    mock_ax.set_xticks.assert_called_once()
    mock_ax.set_xticklabels.assert_called_once_with(['Food', 'Utilities'], rotation=45, ha='right')
    mock_ax.legend.assert_called_once()
    mock_savefig.assert_called_with('budget_report.png')
    captured = capsys.readouterr()
    assert "Visual report saved as 'budget_report.png'" in captured.out

@patch('matplotlib.pyplot.savefig')
@patch('matplotlib.pyplot.show')
@patch('matplotlib.pyplot.subplots')
def test_visualization_report_generator_empty_data(mock_subplots, mock_show, mock_savefig, capsys):
    generator = VisualizationReportGenerator()
    generator.generate({})
    captured = capsys.readouterr()
    assert "No data available for visualization" in captured.out
    mock_subplots.assert_not_called()
    mock_savefig.assert_not_called()

# --- Tests for Alert System ---

def test_alert_service_check_budget_alerts_no_overspend(finance_analyzer_with_data):
    # Data for January 2023 (no overspending in sample)
    alerts = AlertService(finance_analyzer_with_data).check_budget_alerts(1, 2023)
    assert alerts == []

def test_alert_service_check_budget_alerts_with_overspend(finance_analyzer_with_data):
    # Entertainment overspent in February 2023
    alerts = AlertService(finance_analyzer_with_data).check_budget_alerts(2, 2023)
    assert len(alerts) == 1
    assert "ALERT: Overspent $15.00 in Entertainment" in alerts[0]

def test_alert_service_no_budgets_no_alerts(temp_data_dir):
    """Tests alert service when no budgets are loaded."""
    (temp_data_dir / "transactions.csv").write_text("date,amount,category,description\n2023-01-01,100.00,Food,Dinner\n")
    reader = CsvDataReader(str(temp_data_dir))
    analyzer = FinanceAnalyzer(reader)
    alerts = AlertService(analyzer).check_budget_alerts(1, 2023)
    assert alerts == []
