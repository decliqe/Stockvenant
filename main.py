"""
Stockvenant - Stock Calculator Framework

"""

import sys
from PyQt6.QtWidgets import QApplication

from ui.main_window import MainWindow
from ui.styles import apply_theme


def main():
    """Main entry point."""
    app = QApplication(sys.argv)

    # Apply theme
    apply_theme(app, dark=True)

    # Create and show main window
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()

