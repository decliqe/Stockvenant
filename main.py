import sys
from pathlib import Path
from datetime import date

from PyQt6.QtCore import QDate, Qt,QTimer
from PyQt6.QtWidgets import (
    QLabel, QDialog, QApplication,
    QGridLayout, QDoubleSpinBox, QMessageBox, QDateEdit, QCalendarWidget,  QListWidget, QTableWidget, QTableWidgetItem, QHeaderView,QListWidgetItem
)

from utils.logics import load_dataset, get_stocks, compute_trade, InputError, DataError
from utils.theme import apply_minimal_theme, style_calendar_minimal, make_hash_icon





class StockTradeProfitCalculator(QDialog):

    def __init__(self):
        super().__init__()

        # Load dataset once
        dataset_path = Path(__file__).parent / 'data' / 'Stock_Market_Dataset.csv'
        try:
            self.df = load_dataset(str(dataset_path))
            # Get list of stock names
            stock_names = get_stocks(self.df)
            stock_count = len(stock_names)
            
            # Display success message with stock information
            message = f"Data loaded successfully!\n\n"
            message += f"Total stocks available: {stock_count}\n\n"
            # message += "Stocks:\n" + ", ".join(stock_names)
            
            #QMessageBox.information(self, 'Dataset Loaded', message)
            
        except DataError as e:
            QMessageBox.critical(self, 'Dataset Error', str(e))
            raise
        except Exception as e:
            QMessageBox.critical(self, 'Error', f"Error reading data: {e}")
            raise

        # --- Widgets ---
        # Populate list with checkable items (tick boxes) so users can click to select many
        self.stock_label = QLabel('Stocks:')
        self.stock_list = QListWidget()
        for name in get_stocks(self.df):
            item = QListWidgetItem(name)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.stock_list.addItem(item)


        self.qty_label = QLabel('Quantity:')
        self.qty_spin = QDoubleSpinBox()
        self.qty_spin.setRange(0.0001, 10_000_000)
        self.qty_spin.setDecimals(2)
        self.qty_spin.setValue(1.0)

        # Date inputs:
        self.purchase_label = QLabel('Purchase Date:')
        self.purchase_date = QDateEdit()
        self.purchase_date.setDisplayFormat('yyyy-MM-dd')
        self.purchase_calendar = QCalendarWidget()
        
        self.sell_label = QLabel('Sell Date:')
        self.sell_date = QDateEdit()
        self.sell_date.setDisplayFormat('yyyy-MM-dd')
        self.sell_calendar = QCalendarWidget()

        # Apply minimal calendar styling
        style_calendar_minimal(self.purchase_calendar)
        style_calendar_minimal(self.sell_calendar)

       #Results Widgets
        self.results_table = QTableWidget(3, 1)
        self.results_table.setVerticalHeaderLabels([
            'Purchase Total',
            'Sell Total',
            'Profit / Loss',
        ])
        self.results_table.setHorizontalHeaderLabels(['—'])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.results_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        # --- Layout ---
        grid = QGridLayout(self)
        grid.addWidget(self.stock_label, 0, 0)
        grid.addWidget(self.stock_list, 0, 1)
        grid.addWidget(self.qty_label,     1, 0)
        grid.addWidget(self.qty_spin,      1, 1)
        
        # Purchase date section with calendar
        grid.addWidget(self.purchase_label, 2, 0)
        grid.addWidget(self.purchase_date,  2, 1)
        grid.addWidget(self.purchase_calendar, 3, 0, 1, 2)  # Span 2 columns
        
        # Sell date section with calendar
        grid.addWidget(self.sell_label,    4, 0)
        grid.addWidget(self.sell_date,     4, 1)
        grid.addWidget(self.sell_calendar, 5, 0, 1, 2)  # Span 2 columns

       # Results section
        grid.addWidget(self.results_table, 6, 0, 1, 2)

        # --- Defaults from dataset ---
        first_dt = self.df.index.min().date()
        last_dt  = self.df.index.max().date()

        # Constrain date edits and calendars to dataset range
        first_qdate = QDate(first_dt.year, first_dt.month, first_dt.day)
        last_qdate = QDate(last_dt.year, last_dt.month, last_dt.day)
        
        for de in (self.purchase_date, self.sell_date):
            de.setMinimumDate(first_qdate)
            de.setMaximumDate(last_qdate)
        
        for cal in (self.purchase_calendar, self.sell_calendar):
            cal.setMinimumDate(first_qdate)
            cal.setMaximumDate(last_qdate)

        # Default purchase ≈ one year before last (clamped), sell = last
        default_purchase = QDate(max(first_dt.year, last_dt.year - 1), last_dt.month, last_dt.day)
        self.purchase_date.setDate(default_purchase)
        self.purchase_calendar.setSelectedDate(default_purchase)
        
        self.sell_date.setDate(last_qdate)
        self.sell_calendar.setSelectedDate(last_qdate)

        # Debounce for update ui
        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.timeout.connect(self.updateUi)
        # for ui overlaps
        self._updating = False

        # --- Signals ---
        # Sync calendars widgets with date edits (bidirectional)
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

        def _start_debounce():
            self._debounce.start(300)  # 300 millisecs

        self.stock_list.itemChanged.connect(_start_debounce)
        self.stock_list.itemSelectionChanged.connect(_start_debounce)
        self.qty_spin.valueChanged.connect(_start_debounce)
        self.purchase_date.dateChanged.connect(_start_debounce)
        self.sell_date.dateChanged.connect(_start_debounce)
        self.purchase_date.editingFinished.connect(_start_debounce)
        self.sell_date.editingFinished.connect(_start_debounce)

        

        self.setWindowTitle('Stockvenant - Stock Calculator Framework')
        self.updateUi()

    def updateUi(self):
        
        try:
            # Common inputs
            qty = self.qty_spin.value()

            p_qd = self.purchase_date.date()
            s_qd = self.sell_date.date()
            p_date = date(p_qd.year(), p_qd.month(), p_qd.day())
            s_date = date(s_qd.year(), s_qd.month(), s_qd.day())

            # Selected stocks
            selected_items = self.stock_list.selectedItems()
            stocks = [it.text() for it in selected_items]

            stocks = []
            for i in range(self.stock_list.count()):
                it = self.stock_list.item(i)
                if it.checkState() == Qt.CheckState.Checked:
                    stocks.append(it.text())

            if not stocks:
                # No selection: show empty single column
                self.results_table.setColumnCount(1)
                self.results_table.setHorizontalHeaderLabels(['Results'])
                for r in range(self.results_table.rowCount()):
                    self.results_table.setItem(r, 0, QTableWidgetItem(''))
                return

            # Resize columns to number of selected stocks
            self.results_table.setColumnCount(len(stocks))
            self.results_table.setHorizontalHeaderLabels(stocks)

            # Fill table per stock
            for col, stock in enumerate(stocks):
                try:
                    result = compute_trade(self.df, stock, qty, p_date, s_date)

                    # Row 0: Purchase Total
                    self.results_table.setItem(0, col, QTableWidgetItem(f"${result.purchase_total:,.2f}"))
                    # Row 1: Sell Total
                    self.results_table.setItem(1, col, QTableWidgetItem(f"${result.sell_total:,.2f}"))
                    # Row 2: Profit / Loss
                    profit_item = QTableWidgetItem(f"${result.profit:,.2f}")
                    # Color profit cell
                    if result.profit > 0:
                        profit_item.setForeground(Qt.GlobalColor.green)
                    elif result.profit < 0:
                        profit_item.setForeground(Qt.GlobalColor.red)
                    self.results_table.setItem(2, col, profit_item)


                except InputError as ie:

                    # Show input errors inline per stock column

                    err_item = QTableWidgetItem(str(ie))

                    err_item.setForeground(Qt.GlobalColor.red)

                    # Blank out all rows for this column

                    for r in range(self.results_table.rowCount()):
                        self.results_table.setItem(r, col, QTableWidgetItem(''))

                    # Put the error message in the last row (Profit / Loss row)

                    last_row = self.results_table.rowCount() - 1

                    self.results_table.setItem(last_row, col, err_item)


        except Exception as e:

            # On unexpected error, collapse to a single column with the message

            self.results_table.setColumnCount(1)

            self.results_table.setHorizontalHeaderLabels(['Error'])

            # Clear all cells

            for r in range(self.results_table.rowCount()):
                self.results_table.setItem(r, 0, QTableWidgetItem(''))

            # Put the error in the last row

            last_row = self.results_table.rowCount() - 1

            err_item = QTableWidgetItem(f"Unexpected error: {e}")

            err_item.setForeground(Qt.GlobalColor.red)

            self.results_table.setItem(last_row, 0, err_item)
   


if __name__ == '__main__':
    app = QApplication(sys.argv)
    apply_minimal_theme(app, dark=True)
    app.setWindowIcon(make_hash_icon(128))
    stock_calculator = StockTradeProfitCalculator()
    stock_calculator.show()

    sys.exit(app.exec())