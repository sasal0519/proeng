# -*- coding: utf-8 -*-
"""
ProEng — Suíte de Ferramentas de Engenharia
Ponto de entrada principal.
"""
import sys
from PyQt5.QtWidgets import QApplication
from proeng.ui.main_app import MainApp

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("ProEng")
    app.setOrganizationName("ProEng Suite")
    window = MainApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
