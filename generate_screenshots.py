# -*- coding: utf-8 -*-
import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import QTimer, Qt, QRectF, QPointF
from PyQt5.QtGui import QPixmap, QPainter, QColor

# Add current directory to path
sys.path.append(os.getcwd())

from proeng.core.themes import THEMES, _ACTIVE, set_theme, T
from proeng.modules.ishikawa import IshikawaWidget
from proeng.modules.flowsheet import FlowsheetWidget, ProcessNode, Edge
from proeng.modules.eap import EAPWidget
from proeng.modules.bpmn import BPMNAutoWidget
from proeng.modules.canvas import PMCanvasWidget
from proeng.modules.w5h2 import W5H2Widget

def capture_widget(widget, filename):
    # Ensure layout is done
    widget.show()
    QApplication.processEvents()
    
    # Standard size for HD screenshots
    widget.resize(1920, 1080)
    QApplication.processEvents()
    
    # Force fitting for graphics-based widgets
    try:
        # Most widgets have self.view and self.scene
        if hasattr(widget, "view") and hasattr(widget, "scene"):
            rect = widget.scene.itemsBoundingRect()
            if not rect.isEmpty():
                widget.view.fitInView(rect.adjusted(-50, -50, 50, 50), Qt.KeepAspectRatio)
        # Flowsheet has self.canvas
        elif hasattr(widget, "canvas"):
            scene = widget.canvas.scene()
            if scene:
                rect = scene.itemsBoundingRect()
                if not rect.isEmpty():
                    widget.canvas.fitInView(rect.adjusted(-50, -50, 50, 50), Qt.KeepAspectRatio)
    except Exception as e:
        print(f"Aviso: Não foi possível ajustar zoom para {filename}: {e}")
    
    QApplication.processEvents()
    
    # Grab the whole widget
    pixmap = widget.grab()
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    pixmap.save(filename, "PNG")
    print(f"Salvou: {filename}")
    widget.hide()

def gen_ishikawa(theme_name):
    set_theme(theme_name)
    w = IshikawaWidget()
    # Populate with example: "PRODUÇÃO ABAIXO DA META"
    w.nodes[1]["text"] = "PRODUÇÃO ABAIXO DA META"
    
    # Adicionando causas detalhadas por categoria
    # Método (ID 2)
    c1 = w.next_id; w.next_id += 1
    w.nodes[c1] = {"text": "Falta de Padronização", "level": 2, "children": [], "parent": 2}
    w.nodes[2]["children"].append(c1)
    
    c2 = w.next_id; w.next_id += 1
    w.nodes[c2] = {"text": "Gargalo no Setor B", "level": 2, "children": [], "parent": 2}
    w.nodes[2]["children"].append(c2)

    # Máquina (ID 3)
    c3 = w.next_id; w.next_id += 1
    w.nodes[c3] = {"text": "Manutenção Atrasada", "level": 2, "children": [], "parent": 3}
    w.nodes[3]["children"].append(c3)

    # Mão de Obra (ID 5)
    c4 = w.next_id; w.next_id += 1
    w.nodes[c4] = {"text": "Alta Rotatividade", "level": 2, "children": [], "parent": 5}
    w.nodes[5]["children"].append(c4)
    
    c5 = w.next_id; w.next_id += 1
    w.nodes[c5] = {"text": "Falta de Treinamento", "level": 2, "children": [], "parent": 5}
    w.nodes[5]["children"].append(c5)

    # Meio Ambiente (ID 6)
    c6 = w.next_id; w.next_id += 1
    w.nodes[c6] = {"text": "Temperatura Elevada", "level": 2, "children": [], "parent": 6}
    w.nodes[6]["children"].append(c6)
    
    w._draw_diagram()
    capture_widget(w, f"proeng/resources/screenshots/ishikawa_{theme_name}.png")

def gen_eap(theme_name):
    set_theme(theme_name)
    w = EAPWidget()
    w.nodes[1]["text"] = "CONSTRUÇÃO DA NOVA FÁBRICA"
    
    # Gestão do Projeto
    n1 = w.next_id; w.next_id += 1
    w.nodes[n1] = {"text": "Gestão", "children": [], "parent": 1, "shape": "roundrect"}
    w.nodes[1]["children"].append(n1)
    
    n1_1 = w.next_id; w.next_id += 1
    w.nodes[n1_1] = {"text": "Planejamento", "children": [], "parent": n1, "shape": "roundrect"}
    w.nodes[n1]["children"].append(n1_1)

    # Engenharia e Civil
    n2 = w.next_id; w.next_id += 1
    w.nodes[n2] = {"text": "Civil e Infra", "children": [], "parent": 1, "shape": "roundrect"}
    w.nodes[1]["children"].append(n2)
    
    n2_1 = w.next_id; w.next_id += 1
    w.nodes[n2_1] = {"text": "Fundação", "children": [], "parent": n2, "shape": "roundrect"}
    w.nodes[n2]["children"].append(n2_1)
    
    n2_2 = w.next_id; w.next_id += 1
    w.nodes[n2_2] = {"text": "Alvenaria", "children": [], "parent": n2, "shape": "roundrect"}
    w.nodes[n2]["children"].append(n2_2)

    # Instalações
    n3 = w.next_id; w.next_id += 1
    w.nodes[n3] = {"text": "Instalações", "children": [], "parent": 1, "shape": "roundrect"}
    w.nodes[1]["children"].append(n3)
    
    n3_1 = w.next_id; w.next_id += 1
    w.nodes[n3_1] = {"text": "Elétrica", "children": [], "parent": n3, "shape": "roundrect"}
    w.nodes[n3]["children"].append(n3_1)
    
    w.draw_eap()
    capture_widget(w, f"proeng/resources/screenshots/eap_{theme_name}.png")

def gen_canvas(theme_name):
    set_theme(theme_name)
    w = PMCanvasWidget()
    w.sections["just"].append({"id": "j1", "text": "Melhorar eficiência de processos"})
    w.sections["obj"].append({"id": "o1", "text": "Redução de 30% no desperdício"})
    w.sections["prod"].append({"id": "p1", "text": "Plataforma ProEng v2.0"})
    w.sections["eqp"].append({"id": "e1", "text": "Equipe de Engenharia"})
    w.sections["stk"].append({"id": "s1", "text": "Diretoria, Fábrica, TI"})
    w.sections["risc"].append({"id": "r1", "text": "Atraso na entrega de hardware"})
    w.sections["cst"].append({"id": "c1", "text": "Total estimado: R$ 50k"})
    
    w._draw_board()
    capture_widget(w, f"proeng/resources/screenshots/canvas_{theme_name}.png")

def gen_w5h2(theme_name):
    set_theme(theme_name)
    w = W5H2Widget()
    w.nodes[1]["text"] = "IMPLANTAÇÃO DO PROENG CLOUD"
    
    # Ação 1
    a1 = w.next_id; w.next_id += 1
    w.nodes[a1] = {"text": "Configurar Servidores", "type": "WHAT", "parent": 1, "children": []}
    w.nodes[1]["children"].append(a1)
    
    for dt, tx in [("WHY", "Hospedar diagramas"), ("WHO", "Salomão"), ("WHEN", "Jun/2026"), ("HOW", "Docker containers")]:
        d = w.next_id; w.next_id += 1
        w.nodes[d] = {"text": tx, "type": dt, "parent": a1, "children": []}
        w.nodes[a1]["children"].append(d)

    # Ação 2
    a2 = w.next_id; w.next_id += 1
    w.nodes[a2] = {"text": "Treinamento da Equipe", "type": "WHAT", "parent": 1, "children": []}
    w.nodes[1]["children"].append(a2)
    
    for dt, tx in [("WHO", "RH / Qualidade"), ("WHERE", "Auditório"), ("COST", "R$ 2500")]:
        d = w.next_id; w.next_id += 1
        w.nodes[d] = {"text": tx, "type": dt, "parent": a2, "children": []}
        w.nodes[a2]["children"].append(d)
        
    w._draw_diagram()
    capture_widget(w, f"proeng/resources/screenshots/w5h2_{theme_name}.png")

def gen_flowsheet(theme_name):
    set_theme(theme_name)
    w = FlowsheetWidget()
    w.resize(1200, 800)
    # Add complex flowsheet items
    n1 = ProcessNode("Tanque de Alimentação")
    n1.setPos(50, 150)
    w.canvas.scene().addItem(n1)
    
    n2 = ProcessNode("Bomba de Recalque")
    n2.setPos(300, 150)
    w.canvas.scene().addItem(n2)
    
    n3 = ProcessNode("Trocador de Calor")
    n3.setPos(550, 150)
    w.canvas.scene().addItem(n3)

    n4 = ProcessNode("Tanque de Armazenamento")
    n4.setPos(850, 150)
    w.canvas.scene().addItem(n4)
    
    # Add edges
    w.canvas.scene().addItem(Edge(n1, n2, "right", "left"))
    w.canvas.scene().addItem(Edge(n2, n3, "right", "left"))
    w.canvas.scene().addItem(Edge(n3, n4, "right", "left"))
    
    capture_widget(w, f"proeng/resources/screenshots/flowsheet_{theme_name}.png")

def gen_bpmn(theme_name):
    set_theme(theme_name)
    w = BPMNAutoWidget()
    w.lanes = ["Vendas", "Qualidade", "Logística"]
    w.nodes = {}
    w.next_id = 1
    
    # Start (Lane 0)
    id_s = w.next_id; w.next_id += 1
    w.nodes[id_s] = {"text": "Nova Encomenda", "shape": "Evento Início", "level": 0, "lane": 0, "children": [], "parent": None}
    
    # Task 1 (Lane 0)
    id_t1 = w.next_id; w.next_id += 1
    w.nodes[id_t1] = {"text": "Processar Pedido", "shape": "Tarefa", "level": 1, "lane": 0, "children": [], "parent": id_s}
    w.nodes[id_s]["children"].append(id_t1)
    
    # Gateway (Lane 1)
    id_g = w.next_id; w.next_id += 1
    w.nodes[id_g] = {"text": "Aprovado?", "shape": "Gateway", "level": 2, "lane": 1, "children": [], "parent": id_t1}
    w.nodes[id_t1]["children"].append(id_g)
    
    # Task Success (Lane 2)
    id_ts = w.next_id; w.next_id += 1
    w.nodes[id_ts] = {"text": "Despachar", "shape": "Tarefa", "level": 3, "lane": 2, "children": [], "parent": id_g}
    w.nodes[id_g]["children"].append(id_ts)
    
    # End (Lane 2)
    id_e = w.next_id; w.next_id += 1
    w.nodes[id_e] = {"text": "Finalizado", "shape": "Evento Fim", "level": 4, "lane": 2, "children": [], "parent": id_ts}
    w.nodes[id_ts]["children"].append(id_e)
    
    w.draw_diagram()
    capture_widget(w, f"proeng/resources/screenshots/bpmn_{theme_name}.png")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    themes = ["dark", "light"]
    generators = [gen_ishikawa, gen_eap, gen_canvas, gen_w5h2, gen_flowsheet, gen_bpmn]
    
    for theme in themes:
        print(f"\nGerando para tema: {theme.upper()}")
        for gen in generators:
            try:
                gen(theme)
            except Exception as e:
                print(f"Erro ao gerar {gen.__name__}: {e}")
    
    print("\nConcluído!")
    sys.exit(0)
