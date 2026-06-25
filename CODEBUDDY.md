# CODEBUDDY.md

This file provides guidance to CodeBuddy Code when working with code in this repository.

## Project Overview

智能基金监控系统 (FundWave) - A professional-grade desktop application for monitoring and analyzing mutual fund investments in China. Built with PySide6 (Qt6) and SQLite, featuring real-time fund data fetching, portfolio analysis, profit/loss calculations, and multi-channel notifications.

**Key Features:**
- Real-time fund estimation monitoring via TianTian Fund API
- Portfolio analysis dashboard with profit/loss calculations
- Dividend tracking and recording
- Investment calculator (fixed investment vs lump sum comparison)
- System tray integration and background monitoring
- Multi-channel notifications (popup + DingTalk webhook)
- Privacy protection with visibility toggles for sensitive financial data

## Architecture

**MVC Pattern Implementation:**
- **Model Layer** (`models/`): DatabaseManager handles SQLite persistence with thread-safe connections
- **View Layer** (`ui/`): PySide6 widgets, dialogs, and theme system
- **Controller Layer** (`ui/main_window.py`): FundMonitor orchestrates business logic and UI updates
- **Service Layer** (`services/`): Data fetching, calculations, notifications

**Key Design Patterns:**
- Singleton pattern for ThemeManager
- Decorator pattern for retry logic (`@retry_on_failure`)
- Observer pattern via Qt Signal/Slot
- Context manager for database transactions

## Development Commands

### Running the Application
```bash
# Standard launch
python main.py

# Using startup script (handles Qt platform plugin issues)
bash start.sh
```

### Testing
```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_database.py -v

# Run specific test class
pytest tests/test_database.py::TestDatabaseManager -v

# Run with coverage
pytest tests/ --cov=models --cov=services --cov-report=html

# Parallel execution (requires pytest-xdist)
pytest tests/ -n auto
```

### Code Quality
```bash
# Style checking
flake8 models/ services/ ui/ utils/

# Import sorting check
isort --check-only .

# Auto-format imports
isort .

# Auto-format code
autopep8 --in-place --aggressive --aggressive <file>
```

### Dependencies
```bash
# Install core dependencies
pip install PySide6 matplotlib requests pytest pytest-cov pytest-qt

# Install all dependencies
pip install -r requirements.txt
```

## Database Schema

The SQLite database (`fund_monitor.db`) contains these tables:

1. **monitored_funds**: User's selected fund list
   - `fund_code` (TEXT, unique): 6-digit fund code
   - `fund_name` (TEXT): Fund name
   - `created_at`, `updated_at`

2. **fund_holdings**: Portfolio holdings data
   - `fund_code` (TEXT, unique)
   - `cost_price` (REAL): User's cost price per share
   - `shares` (REAL): Number of shares held
   - `amount` (REAL): Total holding value

3. **settings**: System settings
   - `refresh_interval` (INTEGER): Auto-refresh interval in seconds (default 60, range 5-3600)
   - `auto_refresh_enabled` (BOOLEAN)
   - `key`, `value`: Generic key-value settings

4. **notification_settings**: Notification configuration
   - `popup_enabled`, `dingtalk_enabled`
   - `dingtalk_webhook`, `dingtalk_secret`
   - `rise_threshold`, `fall_threshold` (percentages)
   - `profit_threshold`, `loss_threshold` (amounts)

5. **ui_settings**: UI preference persistence
   - `profit_visible`, `daily_profit_visible`
   - `position_cost_visible`, `current_value_visible`

6. **dividend_records**: Dividend tracking
   - `fund_code`, `dividend_amount`, `dividend_date`

**Database Best Practices:**
- Always use `with db_manager.get_cursor() as cursor:` for transactions (auto-commits on success, rollback on error)
- Thread-safe: each thread gets its own connection via `threading.local()`
- DatabaseManager automatically migrates old schemas on initialization

## Data Sources and APIs

**Primary Data API:**
- Fund estimation: `http://fundgz.1234567.com.cn/js/{code}.js`
  - Returns JSONP format: `jsonpgz({...})`
  - Fields: `name`, `gsz` (estimated value), `gszzl` (estimated change %)

**Fund List API:**
- All funds: `https://fund.eastmoney.com/js/fundcode_search.js`
  - Returns: `[[code, type, name, type2, pinyin], ...]`

**Data Fetching Patterns:**
- Use `FundDataFetcher.get_fund(code)` for single fund
- Use `FundDataFetcher.get_all_funds()` for search functionality
- Always validate codes with `FundDataFetcher.validate_fund_code(code)` before API calls
- Built-in retry mechanism (3 retries, 1 second delay) via `@retry_on_failure` decorator

## UI Components and Theme System

**Theme Architecture:**
- `ui/theme/theme_manager.py`: Singleton ThemeManager with responsive design
- Two themes: ProfessionalTheme (light) and DarkTheme
- Theme can be toggled and persisted in database
- Responsive breakpoints: xs/sm/md/lg/xl/xxl based on screen width

**Key Widgets:**
- `ui/widgets/table_widget.py`: Custom table with numeric sorting (NumericItem, PercentageItem)
- `ui/widgets/search_widget.py`: Fund search with autocomplete
- `ui/widgets/portfolio_dashboard.py`: Portfolio analysis visualization
- `ui/widgets/investment_calculator_dialog.py`: Investment calculator UI

**UI Thread Safety:**
- Data updates run in `DataUpdateThread` (QThread) to avoid blocking UI
- Never modify UI directly from background threads - use Qt signals

## Profit/Loss Calculation Logic

**Key Formulas:**
```
Position Cost = cost_price × shares
Current Value = estimated_value × shares
Daily Profit = current_value × (estimated_change % / 100)
Total Profit = current_value - position_cost + dividend_amount
Profit % = (total_profit / position_cost) × 100
```

**Implementation Location:**
- `services/investment_calculator.py`: Fixed investment calculator
- Calculations integrated in `ui/main_window.py` via `update_total_profit()` and `get_fund_holdings_detail()`

## Important Files

**Entry Point:**
- `main.py`: Minimal entry that calls `ui.main_window.main()`

**Configuration:**
- `config.py`: FundConfig dataclass with API URLs, timeouts, retry settings

**Logging:**
- `utils/logger.py`: Rotating file handler (10MB max, 5 backups) + console output
- Log file: `fund_monitor.log`

**Utilities:**
- `utils/decorators.py`: `@retry_on_failure`, `@measure_time`

## Coding Conventions

### Imports Structure
```python
# Standard library
import json
import logging
import os

# Third-party
import requests
from PySide6.QtCore import Qt, QThread

# Local imports
from config import config
from models.database import DatabaseManager
from services.data_fetcher import FundDataFetcher
from utils.logger import logger
```

### Type Annotations
All public functions must have type annotations:
```python
def get_fund(self, code: str) -> Optional[Dict[str, Any]]:
    """Get fund data by code."""
```

### Docstring Format
Use Google-style docstrings:
```python
def method(self, param1: str, param2: int) -> bool:
    """Brief description.

    Args:
        param1: Description
        param2: Description

    Returns:
        Description of return value

    Raises:
        ValueError: When invalid input
    """
```

### Database Queries
Always use parameterized queries (never string interpolation):
```python
cursor.execute('SELECT * FROM monitored_funds WHERE fund_code = ?', (fund_code,))
```

### Qt Signal/Slot
Use new-style signals:
```python
class DataUpdateThread(QThread):
    data_updated = Signal(object)  # Define signal
    error_occurred = Signal(str)

    # In caller:
    thread.data_updated.connect(self.on_data_updated)
```

## Common Tasks

### Adding a New Fund to Monitoring
1. Validate code: `FundDataFetcher.validate_fund_code(code)`
2. Fetch data: `FundDataFetcher.get_fund(code)`
3. Insert to database: `cursor.execute('INSERT INTO monitored_funds...')`
4. Trigger async update via signal

### Updating Holdings Data
1. Use `update_fund_holdings_detail(code, cost_price, shares, amount)`
2. Handles both INSERT and UPDATE automatically
3. Commits via context manager

### Creating New Dialog/Widget
1. Inherit from `QDialog` or `QWidget`
2. Call `ProfessionalTheme.apply_to_widget(self)` for styling
3. Use layout managers (QVBoxLayout, QHBoxLayout, QGridLayout)
4. Connect signals for inter-widget communication

### Adding Notification Channel
1. Extend `NotificationManager` class in `services/notification.py`
2. Add settings fields to `notification_settings` table
3. Create UI settings dialog integration
4. Implement cooldown logic to prevent spam

## Testing Guidelines

**Test File Organization:**
- `tests/test_database.py`: DatabaseManager tests
- `tests/test_calculator.py`: Investment calculator tests
- `tests/test_config.py`: Configuration tests
- `tests/test_new_features.py`: Feature-specific tests

**Fixture Pattern:**
```python
@pytest.fixture(scope='module')
def db_manager():
    """Create temporary test database."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    manager = DatabaseManager(db_path=db_path)
    yield manager
    manager.close()
    os.unlink(db_path)
```

**UI Testing:**
- Use `pytest-qt` for Qt widget tests
- `qtbot.addWidget()` to manage widget lifecycle
- Test signals with `qtbot.waitSignal()`

## Performance Considerations

1. **Network Requests:** 10-second timeout per request, max 3 retries
2. **Thread Safety:** Database uses per-thread connections
3. **UI Rendering:** Data updates in QThread, never block main thread
4. **Caching:** Consider adding cache layer for fund list (9000+ funds)

## Debugging Tips

**Qt Platform Issues:**
- Use `start.sh` which sets `QT_QPA_PLATFORM="xcb"`
- Check `QT_PLUGIN_PATH` environment variable

**Database Issues:**
- Enable SQL logging: add `logging.getLogger('sqlite3').setLevel(logging.DEBUG)`
- Check transaction commits: look for "数据库操作失败" in logs

**Network Issues:**
- Check `fund_monitor.log` for timeout/retry messages
- Verify API URLs are accessible from your network
- User-Agent header required for some endpoints

**UI Layout Issues:**
- Use `widget.dumpObjectTree()` to print widget hierarchy
- Check stylesheet conflicts with `widget.styleSheet()`

## Version Information

- Python: 3.8+
- PySide6: ≥ 6.0
- SQLite: Built-in with Python
- pytest: ≥ 7.0
- matplotlib: ≥ 3.5

## Documentation References

For detailed architecture and development guides, see:
- `docs/developer_guide.md`: Full development documentation
- `docs/upgrade_roadmap.md`: Feature roadmap and architecture analysis
- `docs/api_reference.md`: API endpoint documentation
- `docs/user_guide.md`: End-user manual