# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

setup(
    name="proeng",
    version="1.2.0",
    description="Suíte de ferramentas de engenharia: PFD, EAP, BPMN, PM Canvas, Ishikawa, 5W2H",
    author="PRO ENG Contributors",
    python_requires=">=3.9",
    packages=find_packages(),
    install_requires=["PyQt5>=5.15"],
    entry_points={
        "console_scripts": [
            "proeng=main:main",
        ],
    },
)
