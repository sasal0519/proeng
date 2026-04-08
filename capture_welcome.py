# -*- coding: utf-8 -*-
import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer, Qt

# Add current directory to path
sys.path.append(os.getcwd())

from proeng.ui.main_app import WelcomeScreen
from proeng.core.themes import set_theme

def capture_welcome(theme_name):
    set_theme(theme_name)
    app = QApplication.instance() or QApplication(sys.argv)
    
    w = WelcomeScreen()
    w.show()
    w.resize(1920, 1080)
    
    # Process events to render
    QApplication.processEvents()
    
    # Wait a bit for carousel to settle/render
    loop = QTimer()
    loop.setSingleShot(True)
    loop.timeout.connect(lambda: None)
    
    # Simple way to wait in PyQt without blocking too much for a screenshot
    import time
    time.sleep(1) # Wait for animations/rendering
    QApplication.processEvents()
    
    pixmap = w.grab()
    
    filename = f"proeng/resources/screenshots/welcome_{theme_name}.png"
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    pixmap.save(filename, "PNG")
    print(f"Salvou: {filename}")
    w.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    capture_welcome("dark")
    capture_welcome("light")
    sys.exit(0)
