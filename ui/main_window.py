"""
Main Window for Stockvenant Application.
Coordinates DataStore, Calculator, and DataLoader.
"""

from pathlib import Path
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMainWindow, QDockWidget, QMessageBox

from core.data_store import DataStore
from ui.calculator_widget import CalculatorWidget
from dataloader.data_manager import DataManager
from dataloader.loader_widget import DataLoaderWidget


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        # Initialize core data store
        self.data_store = DataStore()

        # Initialize dataloader manager
        self.data_manager = DataManager()
        self.data_manager.auto_merge_enabled = True

        # Connect dataloader to data store for hot reload
        self.data_manager.merge_completed.connect(self.on_dataloader_merge)
        self.data_store.error_occurred.connect(self.on_error)

        # Create calculator widget (central)
        self.calculator_widget = CalculatorWidget(self.data_store)
        self.setCentralWidget(self.calculator_widget)

        # Create data loader widget (dock)
        self.data_loader_widget = DataLoaderWidget(self.data_manager)
        data_loader_dock = QDockWidget("Data Loader", self)
        data_loader_dock.setWidget(self.data_loader_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, data_loader_dock)

        # Load initial dataset
        self.load_initial_data()

        # Setup window
        self.setWindowTitle('Stockvenant - Stock Calculator Framework')
        self.resize(1200, 800)

    def load_initial_data(self):
        """Load initial dataset from CSV."""
        dataset_path = Path(__file__).parent.parent / 'data' / 'samples.csv'

        if dataset_path.exists():
            success = self.data_store.load_from_csv(str(dataset_path))
            if success:
                print(f"[MainWindow] Loaded initial data from {dataset_path}")
            else:
                QMessageBox.warning(
                    self,
                    'Data Load Warning',
                    f'Failed to load initial data from {dataset_path}'
                )
        else:
            QMessageBox.information(
                self,
                'No Initial Data',
                'No dataset found. Please use Data Loader to fetch stock data.'
            )

    def on_dataloader_merge(self, merged_df):
        """
        Handle data merge from dataloader - HOT RELOAD.
        Updates DataStore without restarting the app.
        """
        if merged_df.empty:
            print("[MainWindow] Merged data is empty")
            return

        print(f"[MainWindow] Hot reload triggered: {len(merged_df)} rows")

        # Save merged data for persistence
        temp_file = Path(__file__).parent.parent / 'data' / 'temp_merged.csv'
        temp_file.parent.mkdir(exist_ok=True)
        merged_df.to_csv(temp_file, index=False)

        # HOT RELOAD: Update data store (triggers reactive updates)
        success = self.data_store.update_data(merged_df)

        if success:
            print("[MainWindow] Hot reload complete - UI updated automatically")
        else:
            QMessageBox.warning(
                self,
                'Update Failed',
                'Failed to update data store with new data'
            )

    def on_error(self, error_msg):
        """Handle errors from data store."""
        QMessageBox.critical(self, 'Data Error', error_msg)

