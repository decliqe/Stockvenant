"""
Data Loader Widget
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
    QLabel, QDateEdit, QComboBox, QTextEdit, QGroupBox, QSpinBox,
    QProgressBar, QFileDialog, QMessageBox
)
from PyQt6.QtCore import QDate, QTimer
from dataloader.yfinance_loader import YFinanceDataLoader
from dataloader.data_manager import DataManager
from datetime import datetime


class DataLoaderWidget(QWidget):


    def __init__(self, data_manager: DataManager):
        super().__init__()
        self.data_manager = data_manager
        self.loader = YFinanceDataLoader()
        self.data_manager.register_loader('yfinance', self.loader)

        # Connect signals
        self.loader.data_received.connect(self.on_data_received)
        self.loader.error_occurred.connect(self.on_error)
        self.loader.progress_update.connect(self.on_progress_update)
        self.data_manager.merge_completed.connect(self.on_merge_completed)
        self.data_manager.error_occurred.connect(self.on_error)

        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        main_layout = QVBoxLayout()

        # === Symbol Input Section ===
        symbol_group = QGroupBox("Symbols")
        symbol_layout = QVBoxLayout()

        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("Symbols:"))
        self.symbol_input = QLineEdit()
        self.symbol_input.setPlaceholderText("Single: AAPL  |  Multiple: AAPL,MSFT,GOOGL,TSLA")
        input_layout.addWidget(self.symbol_input)
        symbol_layout.addLayout(input_layout)

        symbol_group.setLayout(symbol_layout)
        main_layout.addWidget(symbol_group)

        # === Date Range Section ===
        date_group = QGroupBox("Date Range")
        date_layout = QHBoxLayout()

        date_layout.addWidget(QLabel("From:"))
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addMonths(-3))
        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat('yyyy-MM-dd')
        date_layout.addWidget(self.start_date)

        date_layout.addWidget(QLabel("To:"))
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        self.end_date.setDisplayFormat('yyyy-MM-dd')
        date_layout.addWidget(self.end_date)

        date_layout.addWidget(QLabel("Interval:"))
        self.interval_combo = QComboBox()
        self.interval_combo.addItems(['1d', '1h', '30m', '15m', '5m', '1m'])
        date_layout.addWidget(self.interval_combo)

        date_group.setLayout(date_layout)
        main_layout.addWidget(date_group)

        # === Actions Section ===
        actions_group = QGroupBox(" Actions")
        actions_layout = QVBoxLayout()

        # Fetch row
        fetch_row = QHBoxLayout()
        self.fetch_btn = QPushButton(" Fetch Data")
        self.fetch_btn.clicked.connect(self.fetch_data)
        fetch_row.addWidget(self.fetch_btn)

        actions_layout.addLayout(fetch_row)



        actions_group.setLayout(actions_layout)
        main_layout.addWidget(actions_group)

        # === Data Management Section ===
        mgmt_group = QGroupBox(" Data Management")
        mgmt_layout = QVBoxLayout()

        # First row
        mgmt_row1 = QHBoxLayout()
        self.merge_btn = QPushButton(" Merge Cached Data")
        self.merge_btn.clicked.connect(self.merge_data)
        mgmt_row1.addWidget(self.merge_btn)

        self.save_btn = QPushButton(" Save to CSV")
        self.save_btn.clicked.connect(self.save_to_csv)
        mgmt_row1.addWidget(self.save_btn)
        mgmt_layout.addLayout(mgmt_row1)

        # Second row
        mgmt_row2 = QHBoxLayout()
        self.load_btn = QPushButton(" Load from CSV")
        self.load_btn.clicked.connect(self.load_from_csv)
        mgmt_row2.addWidget(self.load_btn)

        self.stats_btn = QPushButton(" Show Statistics")
        self.stats_btn.clicked.connect(self.show_statistics)
        mgmt_row2.addWidget(self.stats_btn)
        mgmt_layout.addLayout(mgmt_row2)

        # Third row
        mgmt_row3 = QHBoxLayout()
        self.clear_btn = QPushButton("️ Clear Cache")
        self.clear_btn.clicked.connect(self.clear_cache)
        mgmt_row3.addWidget(self.clear_btn)

        self.refresh_btn = QPushButton(" Refresh View")
        self.refresh_btn.clicked.connect(self.refresh_view)
        mgmt_row3.addWidget(self.refresh_btn)
        mgmt_layout.addLayout(mgmt_row3)

        mgmt_group.setLayout(mgmt_layout)
        main_layout.addWidget(mgmt_group)

        # === Progress Section ===
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        # === Status Log Section ===
        status_group = QGroupBox(" Status Log")
        status_layout = QVBoxLayout()

        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMaximumHeight(350)
        status_layout.addWidget(self.status_text)

        status_group.setLayout(status_layout)
        main_layout.addWidget(status_group)

        self.setLayout(main_layout)
        self.log_status(" Data Loader initialized")

    def parse_symbols(self) -> list:
        """Parse symbol input (handles both single and comma-separated)."""
        symbols_str = self.symbol_input.text().strip().upper()
        if not symbols_str:
            return []
        return [s.strip() for s in symbols_str.split(',') if s.strip()]

    def fetch_data(self):
        """Fetch historical data for one or more symbols."""
        symbols = self.parse_symbols()
        if not symbols:
            self.log_status(" Please enter at least one symbol")
            return

        start = self.start_date.date().toString('yyyy-MM-dd')
        end = self.end_date.date().toString('yyyy-MM-dd')
        interval = self.interval_combo.currentText()

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        if len(symbols) == 1:
            self.log_status(f" Fetching {symbols[0]} ({start} to {end}, {interval})...")
            self.loader.fetch_historical_data(symbols[0], start, end, interval)
        else:
            self.log_status(f" Fetching {len(symbols)} symbols...")
            self.loader.fetch_multiple_symbols(symbols, start, end, interval)


    def merge_data(self):
        """Manually trigger data merge."""
        symbols = self.data_manager.get_cached_symbols()
        if not symbols:
            self.log_status(" No cached data to merge")
            return

        self.log_status(f" Merging {len(symbols)} symbols...")
        self.data_manager.merge_symbol_data()

    def save_to_csv(self):
        """Save merged data to CSV file."""
        if self.data_manager.master_df is None or self.data_manager.master_df.empty:
            self.log_status("No data to save. Fetch or merge data first.")
            return

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Data",
            f"stock_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV Files (*.csv)"
        )

        if filename:
            if self.data_manager.save_master_to_csv(filename):
                self.log_status(f"✓ Saved to {filename}")

    def load_from_csv(self):
        """Load data from CSV file."""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Load Data",
            "",
            "CSV Files (*.csv)"
        )

        if filename:
            self.log_status(f" Loading from {filename}...")
            df = self.data_manager.load_master_from_csv(filename)
            if not df.empty:
                self.log_status(f" Loaded {len(df)} rows, {len(df.columns)-1} symbols")

    def show_statistics(self):
        """Display data statistics."""
        stats = self.data_manager.get_statistics()

        msg = f""" **Data Statistics**

**Cache:**
• Symbols: {stats['cached_symbols']}
• Symbols List: {', '.join(stats['symbol_list']) if stats['symbol_list'] else 'None'}

**Master DataFrame:**
• Rows: {stats['master_rows']}
• Columns: {stats['master_columns']}
• Date Range: {stats['earliest_date']} to {stats['latest_date']}
• Days Span: {stats['date_span_days']}

**Settings:**
• Auto-merge: {'Enabled' if stats['auto_merge'] else 'Disabled'}
"""

        QMessageBox.information(self, "Statistics", msg)
        self.log_status("Statistics displayed")

    def clear_cache(self):
        """Clear all cached data."""
        reply = QMessageBox.question(
            self,
            "Clear Cache",
            "Are you sure you want to clear all cached data?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.data_manager.clear_cache()
            self.log_status(" Cache cleared")

    def refresh_view(self):
        """Refresh the view with current cached data."""
        symbols = self.data_manager.get_cached_symbols()
        self.log_status(f"Refreshed: {len(symbols)} symbols cached")

    def on_data_received(self, data, symbol):
        """Handle data received signal."""
        if not data.empty:
            self.data_manager.update_data(symbol, data)
            self.log_status(f" Received {len(data)} rows for {symbol}")

    def on_merge_completed(self, merged_df):
        """Handle merge completion."""
        if not merged_df.empty:
            cols = len(merged_df.columns) - 1
            rows = len(merged_df)
            self.log_status(f" Merged: {cols} symbols, {rows} rows")

    def on_progress_update(self, message, percentage):
        """Handle progress updates."""
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(percentage)
        self.log_status(message)

        if percentage >= 100:
            QTimer.singleShot(2000, lambda: self.progress_bar.setVisible(False))

    def on_error(self, error_msg):
        """Handle error messages."""
        self.log_status(f" ERROR: {error_msg}")
        self.progress_bar.setVisible(False)

    def log_status(self, message):
        """Log status message with timestamp."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.status_text.append(f"[{timestamp}] {message}")
