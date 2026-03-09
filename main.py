# main.py
import sys
from PyQt5.QtWidgets import QApplication
from ui.launcher import LauncherWindow

if __name__ == "__main__":
    # Create ppplication
    app = QApplication(sys.argv)
    
    # App Style
    app.setStyle('Fusion') 

    # Start launcher
    launcher = LauncherWindow()
    launcher.show()

    sys.exit(app.exec_())
