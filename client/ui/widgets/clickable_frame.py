"""ClickableFrame widget - a QFrame that emits clicked signal."""
from PyQt5.QtWidgets import QFrame
from PyQt5.QtCore import pyqtSignal, Qt


class ClickableFrame(QFrame):
    """A QFrame that emits a clicked signal when clicked."""
    
    clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
    
    def mousePressEvent(self, event):
        """Handle mouse press event."""
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

