"""The standalone EmberVault Content Creator application."""
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QComboBox, QFormLayout, QGroupBox, QLabel, QLineEdit,
    QListWidget, QMainWindow, QMessageBox, QPushButton, QDoubleSpinBox,
    QVBoxLayout, QWidget,
)

from .content import FurnitureProject, bed_template


class ContentCreatorWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.project = FurnitureProject()
        self.setWindowTitle("EmberVault Content Creator")
        self.resize(920, 680)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QWidget()
        layout = QVBoxLayout(root)
        title = QLabel("EMBERVAULT CONTENT CREATOR")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #ef8b4d;")
        layout.addWidget(title)
        layout.addWidget(QLabel("Design furniture and other content in a project workspace. Export is design-only until explicitly tested."))

        furniture = QGroupBox("Furniture workspace")
        form = QFormLayout(furniture)
        self.name = QLineEdit()
        self.description = QLineEdit()
        self.category = QComboBox(); self.category.addItems(["bed", "chair", "table", "storage", "other"])
        self.width = self._dimension(2.0)
        self.height = self._dimension(1.0)
        self.depth = self._dimension(3.0)
        self.materials = QLineEdit("wood, fabric")
        self.assets = QLineEdit()
        form.addRow("Name", self.name)
        form.addRow("Description", self.description)
        form.addRow("Furniture type", self.category)
        form.addRow("Width", self.width); form.addRow("Height", self.height); form.addRow("Depth", self.depth)
        form.addRow("Materials", self.materials); form.addRow("Asset references", self.assets)
        layout.addWidget(furniture)

        actions = QVBoxLayout()
        template = QPushButton("Start from tested bed template")
        template.clicked.connect(self.load_bed_template)
        preview = QPushButton("Preview furniture design")
        preview.clicked.connect(self.preview)
        export = QPushButton("Export design manifest")
        export.clicked.connect(self.export_manifest)
        actions.addWidget(template); actions.addWidget(preview); actions.addWidget(export)
        layout.addLayout(actions)
        self.status = QLabel("No furniture project loaded.")
        layout.addWidget(self.status)
        self.preview_list = QListWidget()
        layout.addWidget(self.preview_list)
        self.setCentralWidget(root)

    @staticmethod
    def _dimension(value: float) -> QDoubleSpinBox:
        field = QDoubleSpinBox(); field.setRange(0.01, 1000.0); field.setValue(value); field.setSingleStep(0.1)
        return field

    def load_bed_template(self) -> None:
        self.project = bed_template()
        self.name.setText(self.project.name); self.description.setText(self.project.description)
        self.category.setCurrentText(self.project.category); self.width.setValue(self.project.width)
        self.height.setValue(self.project.height); self.depth.setValue(self.project.depth)
        self.materials.setText(", ".join(self.project.materials))
        self.status.setText("Loaded tested bed workflow as a new furniture project.")

    def _read_project(self) -> FurnitureProject:
        return FurnitureProject(
            name=self.name.text(), description=self.description.text(), category=self.category.currentText(),
            width=self.width.value(), height=self.height.value(), depth=self.depth.value(),
            materials=[item.strip() for item in self.materials.text().split(",") if item.strip()],
            asset_references=[item.strip() for item in self.assets.text().split(",") if item.strip()],
            source_template=self.project.source_template,
        )

    def preview(self) -> None:
        self.project = self._read_project(); issues = self.project.validate(); self.preview_list.clear()
        if issues:
            self.status.setText("Needs review: " + " ".join(issues)); return
        for key, value in self.project.manifest()["project"].items():
            self.preview_list.addItem(f"{key}: {value}")
        self.status.setText("Furniture design preview ready. Live game files are untouched.")

    def export_manifest(self) -> None:
        self.project = self._read_project()
        try:
            destination = self.project.export(Path.cwd() / "content-projects" / "furniture" / "design-manifest.json")
        except ValueError as exc:
            QMessageBox.warning(self, "Design needs review", str(exc)); return
        self.status.setText(f"Exported design-only manifest to {destination}")


def main() -> int:
    app = QApplication(sys.argv)
    window = ContentCreatorWindow(); window.show()
    if "--smoke-test" in sys.argv:
        from PySide6.QtCore import QTimer
        QTimer.singleShot(250, app.quit)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
