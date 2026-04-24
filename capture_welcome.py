# -*- coding: utf-8 -*-
import os
import sys
import time

from PyQt5.QtCore import QDate, Qt
from PyQt5.QtWidgets import QApplication

# Add current directory to path
sys.path.append(os.getcwd())

from proeng.core.themes import set_theme
from proeng.modules.bpmn import BPMNAutoWidget
from proeng.modules.canvas import PMCanvasWidget
from proeng.modules.eap import EAPWidget
from proeng.modules.flowsheet import Edge, FlowsheetWidget, ProcessNode
from proeng.modules.gantt import GanttWidget
from proeng.modules.ishikawa import IshikawaWidget
from proeng.modules.kanban import WidgetKanban
from proeng.modules.pdca import WidgetPDCAView
from proeng.modules.script_module import _ScriptModule
from proeng.modules.scrum import ScrumWidget
from proeng.modules.w5h2 import W5H2Widget
from proeng.ui.welcome import WelcomeScreen


CAPTURE_SIZE = (1920, 1080)
CAPTURE_DELAY_SECONDS = 0.8
DOCS_SCREENSHOTS_DIR = os.path.join("docs", "screenshots")


def _process_and_wait(delay_seconds=CAPTURE_DELAY_SECONDS):
    QApplication.processEvents()
    time.sleep(delay_seconds)
    QApplication.processEvents()


def _fit_widget_view(widget):
    try:
        if hasattr(widget, "view") and hasattr(widget, "scene"):
            rect = widget.scene.itemsBoundingRect()
            if not rect.isEmpty():
                widget.view.fitInView(rect.adjusted(-60, -60, 60, 60), Qt.KeepAspectRatio)
        elif hasattr(widget, "canvas") and hasattr(widget.canvas, "scene"):
            scene = widget.canvas.scene()
            if scene:
                rect = scene.itemsBoundingRect()
                if not rect.isEmpty():
                    widget.canvas.fitInView(rect.adjusted(-60, -60, 60, 60), Qt.KeepAspectRatio)
    except Exception as exc:
        print(f"Aviso: fitInView falhou para {type(widget).__name__}: {exc}")


def _prepare_widget(widget):
    widget.resize(*CAPTURE_SIZE)
    widget.show()
    widget.raise_()
    _process_and_wait()
    _fit_widget_view(widget)
    _process_and_wait(0.3)
    return widget


def _save_widget(widget, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    pixmap = widget.grab()
    pixmap.save(output_path, "PNG")
    print(f"Salvou: {output_path}")


def capture_widget(factory, slug, theme_name):
    set_theme(theme_name)
    widget = _prepare_widget(factory())
    output_path = os.path.join(DOCS_SCREENSHOTS_DIR, f"{slug}_{theme_name}.png")
    _save_widget(widget, output_path)
    widget.close()


def build_welcome():
    return WelcomeScreen()


def build_flowsheet():
    widget = FlowsheetWidget()
    widget.resize(1600, 900)

    tank = ProcessNode("Tanque de Alimentacao")
    tank.setPos(40, 160)
    pump = ProcessNode("Bomba de Recalque")
    pump.setPos(320, 160)
    hx = ProcessNode("Trocador de Calor")
    hx.setPos(620, 160)
    reactor = ProcessNode("Reator")
    reactor.setPos(920, 160)
    storage = ProcessNode("Tanque Final")
    storage.setPos(1220, 160)

    for item in (tank, pump, hx, reactor, storage):
        widget.canvas.scene().addItem(item)

    widget.canvas.scene().addItem(Edge(tank, pump, "right", "left"))
    widget.canvas.scene().addItem(Edge(pump, hx, "right", "left"))
    widget.canvas.scene().addItem(Edge(hx, reactor, "right", "left"))
    widget.canvas.scene().addItem(Edge(reactor, storage, "right", "left"))
    return widget


def build_bpmn():
    widget = BPMNAutoWidget()
    widget.lanes = ["Vendas", "Qualidade", "Logistica"]
    widget.nodes = {}
    widget.next_id = 1

    start = widget.next_id
    widget.next_id += 1
    widget.nodes[start] = {
        "text": "Novo Pedido",
        "shape": "Evento Inicio",
        "level": 0,
        "lane": 0,
        "children": [],
        "parent": None,
    }

    task_1 = widget.next_id
    widget.next_id += 1
    widget.nodes[task_1] = {
        "text": "Validar Pedido",
        "shape": "Tarefa",
        "level": 1,
        "lane": 0,
        "children": [],
        "parent": start,
    }
    widget.nodes[start]["children"].append(task_1)

    gateway = widget.next_id
    widget.next_id += 1
    widget.nodes[gateway] = {
        "text": "Aprovado?",
        "shape": "Gateway",
        "level": 2,
        "lane": 1,
        "children": [],
        "parent": task_1,
    }
    widget.nodes[task_1]["children"].append(gateway)

    task_2 = widget.next_id
    widget.next_id += 1
    widget.nodes[task_2] = {
        "text": "Despachar",
        "shape": "Tarefa",
        "level": 3,
        "lane": 2,
        "children": [],
        "parent": gateway,
    }
    widget.nodes[gateway]["children"].append(task_2)

    end = widget.next_id
    widget.next_id += 1
    widget.nodes[end] = {
        "text": "Concluido",
        "shape": "Evento Fim",
        "level": 4,
        "lane": 2,
        "children": [],
        "parent": task_2,
    }
    widget.nodes[task_2]["children"].append(end)
    widget.draw_diagram()
    return widget


def build_eap():
    widget = EAPWidget()
    widget.nodes[1]["text"] = "IMPLANTACAO DO PRO ENG CLOUD"

    gestao = widget.next_id
    widget.next_id += 1
    widget.nodes[gestao] = {"text": "Gestao", "children": [], "parent": 1, "shape": "roundrect"}
    widget.nodes[1]["children"].append(gestao)

    planejamento = widget.next_id
    widget.next_id += 1
    widget.nodes[planejamento] = {
        "text": "Planejamento",
        "children": [],
        "parent": gestao,
        "shape": "roundrect",
    }
    widget.nodes[gestao]["children"].append(planejamento)

    tecnologia = widget.next_id
    widget.next_id += 1
    widget.nodes[tecnologia] = {"text": "Tecnologia", "children": [], "parent": 1, "shape": "roundrect"}
    widget.nodes[1]["children"].append(tecnologia)

    backend = widget.next_id
    widget.next_id += 1
    widget.nodes[backend] = {"text": "Backend", "children": [], "parent": tecnologia, "shape": "roundrect"}
    widget.nodes[tecnologia]["children"].append(backend)

    frontend = widget.next_id
    widget.next_id += 1
    widget.nodes[frontend] = {"text": "Frontend", "children": [], "parent": tecnologia, "shape": "roundrect"}
    widget.nodes[tecnologia]["children"].append(frontend)

    rollout = widget.next_id
    widget.next_id += 1
    widget.nodes[rollout] = {"text": "Rollout", "children": [], "parent": 1, "shape": "roundrect"}
    widget.nodes[1]["children"].append(rollout)

    treinamento = widget.next_id
    widget.next_id += 1
    widget.nodes[treinamento] = {"text": "Treinamento", "children": [], "parent": rollout, "shape": "roundrect"}
    widget.nodes[rollout]["children"].append(treinamento)

    widget.draw_eap()
    return widget


def build_canvas():
    widget = PMCanvasWidget()
    widget.sections["just"].append({"id": "j1", "text": "Aumentar eficiencia operacional"})
    widget.sections["obj"].append({"id": "o1", "text": "Reducao de 30% no retrabalho"})
    widget.sections["prod"].append({"id": "p1", "text": "Plataforma ProEng Web"})
    widget.sections["stk"].append({"id": "s1", "text": "Fabrica, Diretoria e TI"})
    widget.sections["eqp"].append({"id": "e1", "text": "Engenharia + Produto"})
    widget.sections["risc"].append({"id": "r1", "text": "Dependencia de infraestrutura"})
    widget.sections["cst"].append({"id": "c1", "text": "Budget estimado de R$ 80 mil"})
    widget._draw_board()
    return widget


def build_ishikawa():
    widget = IshikawaWidget()
    widget.nodes[1]["text"] = "ATRASOS NAS ENTREGAS"

    causa_1 = widget.next_id
    widget.next_id += 1
    widget.nodes[causa_1] = {"text": "Falta de Padronizacao", "level": 2, "children": [], "parent": 2}
    widget.nodes[2]["children"].append(causa_1)

    causa_2 = widget.next_id
    widget.next_id += 1
    widget.nodes[causa_2] = {"text": "Setup Demorado", "level": 2, "children": [], "parent": 3}
    widget.nodes[3]["children"].append(causa_2)

    causa_3 = widget.next_id
    widget.next_id += 1
    widget.nodes[causa_3] = {"text": "Material em Falta", "level": 2, "children": [], "parent": 4}
    widget.nodes[4]["children"].append(causa_3)

    causa_4 = widget.next_id
    widget.next_id += 1
    widget.nodes[causa_4] = {"text": "Treinamento Insuficiente", "level": 2, "children": [], "parent": 5}
    widget.nodes[5]["children"].append(causa_4)

    causa_5 = widget.next_id
    widget.next_id += 1
    widget.nodes[causa_5] = {"text": "Temperatura Alta", "level": 2, "children": [], "parent": 6}
    widget.nodes[6]["children"].append(causa_5)

    widget._draw_diagram()
    return widget


def build_w5h2():
    widget = W5H2Widget()
    widget.nodes[1]["text"] = "IMPLANTAR PORTAL DO CLIENTE"

    action = widget.next_id
    widget.next_id += 1
    widget.nodes[action] = {"text": "Configurar Infraestrutura", "type": "WHAT", "parent": 1, "children": []}
    widget.nodes[1]["children"].append(action)

    details = [
        ("WHY", "Escalar atendimento"),
        ("WHO", "Equipe DevOps"),
        ("WHERE", "Cloud publica"),
        ("WHEN", "Q3 2026"),
        ("HOW", "Containers + CI/CD"),
        ("COST", "R$ 12 mil"),
    ]
    for node_type, text in details:
        detail_id = widget.next_id
        widget.next_id += 1
        widget.nodes[detail_id] = {"text": text, "type": node_type, "parent": action, "children": []}
        widget.nodes[action]["children"].append(detail_id)

    widget._draw_diagram()
    return widget


def build_gantt():
    widget = GanttWidget()
    widget.tasks = {}
    widget.next_task_id = 1

    today = QDate.currentDate()
    widget.add_task("Kickoff", today, today, is_milestone=True)
    widget.add_task("Planejamento", today.addDays(1), today.addDays(8), progress=100)
    widget.add_task("Design", today.addDays(9), today.addDays(20), progress=65)
    widget.add_task("Desenvolvimento", today.addDays(21), today.addDays(38), progress=30)
    widget.add_task("Testes", today.addDays(39), today.addDays(48), progress=0)
    widget.add_task("Go Live", today.addDays(49), today.addDays(49), is_milestone=True)
    widget.signals.calculate_cpm.emit()
    return widget


def build_kanban():
    return WidgetKanban()


def build_scrum():
    return ScrumWidget()


def build_pdca():
    return WidgetPDCAView()


def build_script():
    return _ScriptModule()


CAPTURE_FACTORIES = [
    ("welcome", build_welcome),
    ("flowsheet", build_flowsheet),
    ("bpmn", build_bpmn),
    ("eap", build_eap),
    ("canvas", build_canvas),
    ("ishikawa", build_ishikawa),
    ("w5h2", build_w5h2),
    ("gantt", build_gantt),
    ("kanban", build_kanban),
    ("scrum", build_scrum),
    ("pdca", build_pdca),
    ("script", build_script),
]


def capture_all(theme_name):
    for slug, factory in CAPTURE_FACTORIES:
        capture_widget(factory, slug, theme_name)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    theme_name = sys.argv[1] if len(sys.argv) > 1 else "solar"
    capture_all(theme_name)

    sys.exit(0)
