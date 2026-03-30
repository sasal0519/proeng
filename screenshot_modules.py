# -*- coding: utf-8 -*-
import sys
import os
import time
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

# Importando os módulos do ProEng
from proeng.ui.main_app import MainApp
from proeng.modules.flowsheet import _FlowsheetModule
from proeng.modules.eap import _EAPModule
from proeng.modules.bpmn import _BPMNModule
from proeng.modules.canvas import _CanvasModule
from proeng.modules.ishikawa import _IshikawaModule
from proeng.modules.w5h2 import _W5H2Module

def take_screenshots():
    app = QApplication(sys.argv)
    
    modules = {
        "01_Flowsheet": _FlowsheetModule,
        "02_EAP": _EAPModule,
        "03_BPMN": _BPMNModule,
        "04_Canvas": _CanvasModule,
        "05_Ishikawa": _IshikawaModule,
        "06_W5H2": _W5H2Module
    }

    output_dir = os.path.abspath("docs/screenshots")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"Iniciando captura de screenshots em: {output_dir}")

    for name, module_class in modules.items():
        print(f"Capturando {name}...")
        
        # Instancia o módulo
        widget = module_class()
        widget.setWindowTitle(f"ProEng Screenshot - {name}")
        widget.resize(1280, 720) # Tamanho padrão para os prints
        widget.show()
        
        # Processa eventos para garantir que a UI renderizou
        QApplication.processEvents()
        time.sleep(1) # Pequena pausa para animações/renderização
        
        # Tira o screenshot
        screen = QApplication.primaryScreen()
        screenshot = screen.grabWindow(widget.winId())
        
        # Salva o arquivo
        file_path = os.path.join(output_dir, f"{name}.png")
        screenshot.save(file_path, "png")
        print(f"Salvo: {file_path}")
        
        widget.close()

    print("\nProcesso concluído com sucesso!")
    sys.exit(0)

if __name__ == "__main__":
    take_screenshots()
