

from dataclasses import dataclass as _dataclass_min, field as _field_min

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QPalette, QColor
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import QApplication, QWidget, QCalendarWidget,QStyleFactory



# Minimal Theme

@_dataclass_min(frozen=True)
class MinimalPalette:
    bg: QColor = _field_min(default_factory=lambda: QColor("#FFFFFF"))
    panel: QColor = _field_min(default_factory=lambda: QColor("#FFFFFF"))
    border: QColor = _field_min(default_factory=lambda: QColor("#DADDE3"))
    text: QColor = _field_min(default_factory=lambda: QColor("#222222"))
    text_dim: QColor = _field_min(default_factory=lambda: QColor("#6B7685"))
    accent: QColor = _field_min(default_factory=lambda: QColor("#2A7ADE"))


def apply_minimal_theme(app_or_widget: QApplication | QWidget, *, dark: bool = False, accent: str | None = None) -> None:

    # Ensure cross-platform Fusion style
    try:
        if "Fusion" in QStyleFactory.keys():
            if isinstance(app_or_widget, QApplication):
                app_or_widget.setStyle("Fusion")
            else:
                QApplication.instance().setStyle("Fusion")
    except Exception:
        pass

    pal = _build_minimal_palette(dark=dark, accent_hex=accent)
    _apply_palette_minimal(app_or_widget, pal)
    app_or_widget.setStyleSheet(_minimal_stylesheet(pal, dark))


def style_calendar_minimal(cal: QCalendarWidget) -> None:
    #Keep calendar simple and readable
    cal.setGridVisible(True)
    cal.setHorizontalHeaderFormat(QCalendarWidget.HorizontalHeaderFormat.ShortDayNames)
    cal.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.ISOWeekNumbers)
    cal.setFirstDayOfWeek(Qt.DayOfWeek.Monday)


def _build_minimal_palette(*, dark: bool, accent_hex: str | None) -> MinimalPalette:
    if dark:
        bg = QColor("#141414"); panel = QColor("#1B1B1B"); border = QColor("#2A2A2A")
        text = QColor("#EAEAEA"); text_dim = QColor("#A7A7A7"); accent = QColor("#4A90E2")
        if accent_hex:
            a = QColor(accent_hex)
            if a.isValid():
                accent = a
        return MinimalPalette(bg=bg, panel=panel, border=border, text=text, text_dim=text_dim, accent=accent)

    pal = MinimalPalette()
    if accent_hex:
        a = QColor(accent_hex)
        if a.isValid():
            pal = MinimalPalette(bg=pal.bg, panel=pal.panel, border=pal.border, text=pal.text, text_dim=pal.text_dim, accent=a)
    return pal


def _apply_palette_minimal(app_or_widget: QApplication | QWidget, p: MinimalPalette) -> None:
    qp = QPalette()
    qp.setColor(QPalette.ColorRole.Window, p.bg)
    qp.setColor(QPalette.ColorRole.WindowText, p.text)
    qp.setColor(QPalette.ColorRole.Base, p.panel)
    qp.setColor(QPalette.ColorRole.AlternateBase, p.panel)
    qp.setColor(QPalette.ColorRole.ToolTipBase, p.panel)
    qp.setColor(QPalette.ColorRole.ToolTipText, p.text)
    qp.setColor(QPalette.ColorRole.Text, p.text)
    qp.setColor(QPalette.ColorRole.Button, p.panel)
    qp.setColor(QPalette.ColorRole.ButtonText, p.text)
    qp.setColor(QPalette.ColorRole.BrightText, QColor("#FFFFFF"))
    qp.setColor(QPalette.ColorRole.Highlight, p.accent)
    qp.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))

    if isinstance(app_or_widget, QApplication):
        app_or_widget.setPalette(qp)
    else:
        QApplication.instance().setPalette(qp)


def _minimal_stylesheet(p: MinimalPalette, dark: bool) -> str:
    radius = 6
    bg0 = p.bg.name(); bgp = p.panel.name(); bd = p.border.name(); tx = p.text.name(); acc = p.accent.name()
    return f"""
/* Base */
QWidget {{
  background: {bg0};
  color: {tx};
}}

/* Inputs */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QDateEdit {{
  background: {bgp};
  border: 1px solid {bd};
  border-radius: {radius}px;
  padding: 4px 8px;
}}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus, QDateEdit:focus {{
  border: 1px solid {acc};
}}



/* Tables */
QHeaderView::section {{
  background: {('#F6F7F9' if not dark else '#202020')};
  border: 1px solid {bd};
  padding: 6px 8px;
}}
QTableWidget {{
  gridline-color: {bd};
  selection-background-color: {acc};
  selection-color: #FFFFFF;
}}

/* Scrollbars */
QScrollBar:vertical {{ background: {bgp}; width: 12px; }}
QScrollBar::handle:vertical {{ background: {bd}; min-height: 24px; border-radius: 6px; }}
QScrollBar:horizontal {{ background: {bgp}; height: 12px; }}
QScrollBar::handle:horizontal {{ background: {bd}; min-width: 24px; border-radius: 6px; }}

/* Calendar */
QCalendarWidget {{
  border: 1px solid {bd};
  border-radius: {radius}px;
  background: {bgp};
}}
QCalendarWidget QAbstractItemView::item:selected {{
  background: {acc};
  color: #FFFFFF;
}}
"""


# -----------------------------
# Icon (hash) SVG and factory
# -----------------------------

def make_hash_icon(size: int = 128) -> QIcon:

    renderer = QSvgRenderer(bytearray(_HASH_SVG, "utf-8"))
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pm)
    renderer.render(painter)
    painter.end()
    return QIcon(pm)


# Inline SVG data for the hash icon (crisp on all DPIs)
_HASH_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256">
  <rect width="256" height="256" fill="none"/>
  <g fill="none" stroke="#6B7685" stroke-width="28" stroke-linecap="round" stroke-linejoin="round">
    <path d="M86 32 L58 224"/>
    <path d="M172 32 L144 224"/>
    <path d="M32 100 H224"/>
    <path d="M24 164 H216"/>
  </g>
</svg>
"""
