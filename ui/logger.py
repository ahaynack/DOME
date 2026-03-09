# ui/logger.py
import sys
from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtGui import QTextCursor

class Stream(QObject):
    """Redirects console output to a PyQt signal."""
    new_text = pyqtSignal(str)

    def write(self, text):
        self.new_text.emit(str(text))

    def flush(self):
        pass

class LogWidget(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setStyleSheet("background-color: #f0f0f0; font-family: Consolas, 'Courier New', monospace; font-size: 10pt;")
        
        sys.stdout = Stream(new_text=self.on_update_text)

    def on_update_text(self, text):
        """
        Robust handler for text with carriage returns (\r).
        """
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        # Split text by \r to handle cases where multiple overwrites come in one chunk
        parts = text.split('\r')
        
        for i, part in enumerate(parts):
            # If i > 0, encountered \r, so overwrite the current line
            if i > 0:
                # Move anchor to start of the current block (line)
                cursor.movePosition(QTextCursor.StartOfBlock, QTextCursor.MoveAnchor)
                # Select to the end of the block
                cursor.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
                # Remove the existing text on this line
                cursor.removeSelectedText()
            
            # Insert new text part
            if part:
                cursor.insertText(part)
        
        # Scroll to bottom
        self.setTextCursor(cursor)
        self.ensureCursorVisible()