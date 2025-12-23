"""
Calculator Widget - UI component for stock calculations
"""

from datetime import date
from PyQt6.QtCore import QDate, Qt, QTimer
from PyQt6.QtWidgets import (
    QWidget, QGridLayout, QLabel, QListWidget, QListWidgetItem,
    QDoubleSpinBox, QDateEdit, QCalendarWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox
)

from core.calculator import StockCalculator, InputError, DataError
from core.data_store import DataStore
from ui.styles import style_calendar


class CalculatorWidget(QWidget):

    def __init__(self, data_store: DataStore, parent=None):
        super().__init__(parent)

        self.data_store = data_store
        self.calculator = StockCalculator(data_store)

        # Connect to data store updates for hot reload
        self.data_store.data_loaded.connect(self.on_data_loaded)
        self.data_store.data_updated.connect(self.on_data_updated)
        self.data_store.symbols_changed.connect(self.on_symbols_changed)

        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.timeout.connect(self.update_calculations)

        self.init_ui()

    def init_ui(self):
        """Initialize the UI components."""
        layout = QGridLayout(self)

        # Stock selection list
        self.stock_label = QLabel('Stocks:')
        self.stock_list = QListWidget()
        layout.addWidget(self.stock_label, 0, 0)
        layout.addWidget(self.stock_list, 0, 1)

        # Quantity input
        self.qty_label = QLabel('Quantity:')
        self.qty_spin = QDoubleSpinBox()
        self.qty_spin.setRange(0.0001, 10_000_000)
        self.qty_spin.setDecimals(2)
        self.qty_spin.setValue(1.0)
        layout.addWidget(self.qty_label, 1, 0)
        layout.addWidget(self.qty_spin, 1, 1)

        # Purchase date
        self.purchase_label = QLabel('Purchase Date:')
        self.purchase_date = QDateEdit()
        self.purchase_date.setDisplayFormat('yyyy-MM-dd')
        self.purchase_calendar = QCalendarWidget()
        style_calendar(self.purchase_calendar)
        layout.addWidget(self.purchase_label, 2, 0)
        layout.addWidget(self.purchase_date, 2, 1)
        layout.addWidget(self.purchase_calendar, 3, 0, 1, 2)

        # Sell date
        self.sell_label = QLabel('Sell Date:')
        self.sell_date = QDateEdit()
        self.sell_date.setDisplayFormat('yyyy-MM-dd')
        self.sell_calendar = QCalendarWidget()
        style_calendar(self.sell_calendar)
        layout.addWidget(self.sell_label, 4, 0)
        layout.addWidget(self.sell_date, 4, 1)
        layout.addWidget(self.sell_calendar, 5, 0, 1, 2)

        # Results table
        self.results_table = QTableWidget(3, 1)
        self.results_table.setVerticalHeaderLabels([
            'Purchase Total',
            'Sell Total',
            'Profit / Loss'
        ])
        self.results_table.setHorizontalHeaderLabels(['Results'])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.results_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.results_table, 6, 0, 1, 2)

        # Connect signals for calendar sync
        self.purchase_calendar.selectionChanged.connect(
            lambda: self.purchase_date.setDate(self.purchase_calendar.selectedDate())
        )
        self.purchase_date.dateChanged.connect(
            lambda date: self.purchase_calendar.setSelectedDate(date)
        )

        self.sell_calendar.selectionChanged.connect(
            lambda: self.sell_date.setDate(self.sell_calendar.selectedDate())
        )
        self.sell_date.dateChanged.connect(
            lambda date: self.sell_calendar.setSelectedDate(date)
        )

        # Connect input changes to debounced update
        def start_debounce():
            self._debounce.start(300)

        self.stock_list.itemChanged.connect(start_debounce)
        self.qty_spin.valueChanged.connect(start_debounce)
        self.purchase_date.dateChanged.connect(start_debounce)
        self.sell_date.dateChanged.connect(start_debounce)

    def on_data_loaded(self, df):
        """Handle initial data load."""
        print(f"[CalculatorWidget] Data loaded: {len(df)} rows")
        self.populate_stock_list()
        self.set_date_constraints()
        self.update_calculations()

    def on_data_updated(self, df):
        """Handle hot reload of data."""
        print(f"[CalculatorWidget] Data updated: {len(df)} rows - HOT RELOAD")

        # Save current selections
        selected_stocks = self.get_selected_stocks()

        # Refresh UI
        self.populate_stock_list()
        self.set_date_constraints()

        # Restore selections
        self.restore_selections(selected_stocks)

        # Recalculate
        self.update_calculations()

        # Show notification
        QMessageBox.information(
            self,
            'Data Updated',
            f'Stock data refreshed!\n{len(df)} rows, {len(df.columns)} symbols'
        )

    def on_symbols_changed(self, symbols):
        """Handle when available symbols change."""
        print(f"[CalculatorWidget] Symbols changed: {len(symbols)} symbols")
        self.populate_stock_list()

    def populate_stock_list(self):
        """Populate the stock list with available symbols."""
        self.stock_list.clear()

        for symbol in self.data_store.symbols:
            item = QListWidgetItem(symbol)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.stock_list.addItem(item)

    def set_date_constraints(self):
        """Set date range constraints based on dataset."""
        date_range = self.data_store.date_range

        if date_range[0] is None:
            return

        first_dt = date_range[0].date()
        last_dt = date_range[1].date()

        first_qdate = QDate(first_dt.year, first_dt.month, first_dt.day)
        last_qdate = QDate(last_dt.year, last_dt.month, last_dt.day)

        # Set constraints
        for de in (self.purchase_date, self.sell_date):
            de.setMinimumDate(first_qdate)
            de.setMaximumDate(last_qdate)

        for cal in (self.purchase_calendar, self.sell_calendar):
            cal.setMinimumDate(first_qdate)
            cal.setMaximumDate(last_qdate)

        # Set default dates
        default_purchase = QDate(max(first_dt.year, last_dt.year - 1), last_dt.month, last_dt.day)
        self.purchase_date.setDate(default_purchase)
        self.purchase_calendar.setSelectedDate(default_purchase)

        self.sell_date.setDate(last_qdate)
        self.sell_calendar.setSelectedDate(last_qdate)

    def get_selected_stocks(self) -> list:
        """Get list of selected stock symbols."""
        selected = []
        for i in range(self.stock_list.count()):
            item = self.stock_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected.append(item.text())
        return selected

    def restore_selections(self, selected_stocks: list):
        """Restore stock selections after refresh."""
        for i in range(self.stock_list.count()):
            item = self.stock_list.item(i)
            if item.text() in selected_stocks:
                item.setCheckState(Qt.CheckState.Checked)

    def update_calculations(self):
        """Update calculation results based on current inputs."""
        try:
            # Get inputs
            qty = self.qty_spin.value()

            p_qd = self.purchase_date.date()
            s_qd = self.sell_date.date()
            p_date = date(p_qd.year(), p_qd.month(), p_qd.day())
            s_date = date(s_qd.year(), s_qd.month(), s_qd.day())

            # Get selected stocks
            stocks = self.get_selected_stocks()

            if not stocks:
                # No selection - show empty
                self.results_table.setColumnCount(1)
                self.results_table.setHorizontalHeaderLabels(['Results'])
                for r in range(self.results_table.rowCount()):
                    self.results_table.setItem(r, 0, QTableWidgetItem(''))
                return

            # Resize table for selected stocks
            self.results_table.setColumnCount(len(stocks))
            self.results_table.setHorizontalHeaderLabels(stocks)

            # Calculate for each stock
            for col, stock in enumerate(stocks):
                try:
                    result = self.calculator.compute_trade(stock, qty, p_date, s_date)

                    # Row 0: Purchase Total
                    self.results_table.setItem(0, col, QTableWidgetItem(f"${result.purchase_total:,.2f}"))

                    # Row 1: Sell Total
                    self.results_table.setItem(1, col, QTableWidgetItem(f"${result.sell_total:,.2f}"))

                    # Row 2: Profit/Loss with color
                    profit_item = QTableWidgetItem(f"${result.profit:,.2f}")
                    if result.profit > 0:
                        profit_item.setForeground(Qt.GlobalColor.green)
                    elif result.profit < 0:
                        profit_item.setForeground(Qt.GlobalColor.red)
                    self.results_table.setItem(2, col, profit_item)

                except (InputError, DataError) as e:
                    # Show error in the column
                    err_item = QTableWidgetItem(str(e))
                    err_item.setForeground(Qt.GlobalColor.red)

                    for r in range(self.results_table.rowCount()):
                        self.results_table.setItem(r, col, QTableWidgetItem(''))

                    last_row = self.results_table.rowCount() - 1
                    self.results_table.setItem(last_row, col, err_item)

        except Exception as e:
            # Unexpected error
            self.results_table.setColumnCount(1)
            self.results_table.setHorizontalHeaderLabels(['Error'])

            for r in range(self.results_table.rowCount()):
                self.results_table.setItem(r, 0, QTableWidgetItem(''))

            last_row = self.results_table.rowCount() - 1
            err_item = QTableWidgetItem(f"Error: {str(e)}")
            err_item.setForeground(Qt.GlobalColor.red)
            self.results_table.setItem(last_row, 0, err_item)

