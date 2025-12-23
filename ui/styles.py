"""
Theme and styling management
"""

from PyQt6.QtWidgets import QApplication, QCalendarWidget



def apply_theme(app: QApplication, dark: bool = True):

    if dark:
        app.setStyle('Fusion')

        # Dark theme stylesheet
        stylesheet = """
        QMainWindow, QDialog, QWidget {
            background-color: #141414;
            color: #e0e0e0;
        }
        
        QGroupBox {
            border: 1px solid #555;
            border-radius: 4px;
            margin-top: 8px;
            padding-top: 8px;
            font-weight: bold;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 3px;
        }
        
        QPushButton {
            background-color: #141414;
            border: 1px solid #555;
            border-radius: 3px;
            padding: 5px 15px;
            color: #e0e0e0;
        }
        
        QPushButton:hover {
            background-color: #4a4a4a;
            border: 1px solid #666;
        }
        
        QPushButton:pressed {
            background-color: #2a2a2a;
        }
        
        QPushButton:disabled {
            background-color: #2b2b2b;
            color: #666;
        }
        
        QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QDateEdit {
            background-color: #141414;
            border: 1px solid #555;
            border-radius: 3px;
            padding: 4px;
            color: #e0e0e0;
        }
        
        QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, 
        QComboBox:focus, QDateEdit:focus {
            border: 1px solid #888;
        }
        
        QTextEdit, QListWidget, QTableWidget {
            background-color: #141414;
            border: 1px solid #555;
            border-radius: 3px;
            color: #e0e0e0;
        }
        
        QTableWidget::item:selected {
            background-color: #4a4a4a;
        }
        
        QHeaderView::section {
            background-color: #3a3a3a;
            color: #e0e0e0;
            border: 1px solid #555;
            padding: 4px;
        }
        
        QLabel {
            color: #e0e0e0;
        }
        
        QCheckBox {
            color: #e0e0e0;
        }
        
        QProgressBar {
            border: 1px solid #555;
            border-radius: 3px;
            background-color: #3a3a3a;
            text-align: center;
        }
        
        QProgressBar::chunk {
            background-color: #4a90e2;
            border-radius: 2px;
        }
        
        QDockWidget {
            border: 1px solid #555;
            titlebar-close-icon: none;
            titlebar-normal-icon: none;
        }
        
        QDockWidget::title {
            background-color: #141414;
            padding: 4px;
        }
        
        QStatusBar {
            background-color: #3a3a3a;
            color: #e0e0e0;
        }
        """

        app.setStyleSheet(stylesheet)
    else:
        # Light theme (default Qt style)
        app.setStyle('Fusion')


def style_calendar(calendar: QCalendarWidget):
    """
    Apply minimal styling to calendar widget.
    """
    # Set properties for better appearance
    calendar.setGridVisible(True)
    calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
    calendar.setHorizontalHeaderFormat(QCalendarWidget.HorizontalHeaderFormat.SingleLetterDayNames)

