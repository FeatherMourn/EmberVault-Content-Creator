"""The standalone EmberVault Content Creator application."""
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QComboBox, QFormLayout, QGroupBox, QLabel, QLineEdit,
    QListWidget, QMainWindow, QMessageBox, QPushButton, QDoubleSpinBox, QFileDialog,
    QVBoxLayout, QHBoxLayout, QWidget,
)

from .content import BlueprintLibrary, FurnitureProject, bed_template, search_donor_library


class ContentCreatorWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.project = FurnitureProject()
        self.blueprints = BlueprintLibrary(Path.cwd() / "content-projects" / "blueprints")
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

        dashboard = QGroupBox("Project dashboard")
        dashboard_layout = QVBoxLayout(dashboard)
        self.project_summary = QLabel("No project loaded. Start from a fixture or begin a new design.")
        self.workflow_step = QComboBox()
        self.workflow_step.addItems(["1. Project setup", "2. Authoring", "3. Evidence review", "4. Tool handoff", "5. Export review"])
        self.workflow_step.currentIndexChanged.connect(self._update_workflow_step)
        dashboard_layout.addWidget(self.project_summary)
        dashboard_layout.addWidget(QLabel("Guided workflow step"))
        dashboard_layout.addWidget(self.workflow_step)
        layout.addWidget(dashboard)

        library = QGroupBox("Offline donor and recipe library")
        library_layout = QVBoxLayout(library)
        self.donor_search = QLineEdit()
        self.donor_search.setPlaceholderText("Search donors, recipes, categories, or sources")
        self.donor_search.textChanged.connect(self._search_donors)
        self.donor_results = QListWidget()
        self.donor_results.itemClicked.connect(self._select_donor)
        library_layout.addWidget(self.donor_search)
        library_layout.addWidget(self.donor_results)
        layout.addWidget(library)

        blueprints = QGroupBox("Blueprint library")
        blueprint_layout = QVBoxLayout(blueprints)
        self.blueprint_search = QLineEdit()
        self.blueprint_search.setPlaceholderText("Search saved blueprints")
        self.blueprint_search.textChanged.connect(self._search_blueprints)
        self.blueprint_results = QListWidget()
        self.blueprint_results.itemClicked.connect(self._select_blueprint)
        save_blueprint = QPushButton("Save current project as blueprint")
        save_blueprint.clicked.connect(self.save_blueprint)
        blueprint_layout.addWidget(self.blueprint_search)
        blueprint_layout.addWidget(self.blueprint_results)
        blueprint_layout.addWidget(save_blueprint)
        layout.addWidget(blueprints)

        furniture = QGroupBox("Furniture workspace")
        form = QFormLayout(furniture)
        self.name = QLineEdit()
        self.description = QLineEdit()
        self.category = QComboBox(); self.category.addItems(["bed", "chair", "table", "storage", "decor"])
        self.workflow = QComboBox(); self.workflow.addItems(["replacement", "new-model"])
        self.width = self._dimension(2.0)
        self.height = self._dimension(1.0)
        self.depth = self._dimension(3.0)
        self.materials = QLineEdit("wood, fabric")
        self.assets = QLineEdit()
        self.donor_item = QLineEdit()
        self.donor_recipe = QLineEdit()
        self.target_guid = QLineEdit()
        self.base_template_guid = QLineEdit()
        self.base_item_guid = QLineEdit()
        self.evidence_title = QLineEdit()
        self.evidence_source = QLineEdit()
        form.addRow("Name", self.name)
        form.addRow("Description", self.description)
        form.addRow("Furniture type", self.category)
        form.addRow("Workflow", self.workflow)
        form.addRow("Width", self.width); form.addRow("Height", self.height); form.addRow("Depth", self.depth)
        form.addRow("Materials", self.materials); form.addRow("Asset references", self.assets)
        form.addRow("Donor item ID", self.donor_item); form.addRow("Donor recipe ID", self.donor_recipe)
        form.addRow("Target RenderModel GUID", self.target_guid)
        form.addRow("Base template GUID", self.base_template_guid); form.addRow("Base item GUID", self.base_item_guid)
        form.addRow("Evidence title", self.evidence_title); form.addRow("Evidence source", self.evidence_source)
        layout.addWidget(furniture)

        actions = QVBoxLayout()
        template = QPushButton("Start from tested bed template")
        template.clicked.connect(self.load_bed_template)
        preview = QPushButton("Preview furniture design")
        preview.clicked.connect(self.preview)
        export = QPushButton("Export design manifest")
        export.clicked.connect(self.export_manifest)
        save = QPushButton("Save project"); save.clicked.connect(self.save_project)
        open_project = QPushButton("Open project"); open_project.clicked.connect(self.open_project)
        snapshot = QPushButton("Create recovery snapshot"); snapshot.clicked.connect(self.create_snapshot)
        undo = QPushButton("Undo last snapshot"); undo.clicked.connect(self.undo_snapshot)
        compatibility = QPushButton("Check compatibility")
        compatibility.clicked.connect(self.check_compatibility)
        actions.addWidget(template); actions.addWidget(preview); actions.addWidget(save)
        actions.addWidget(open_project); actions.addWidget(snapshot); actions.addWidget(undo)
        actions.addWidget(compatibility); actions.addWidget(export)
        layout.addLayout(actions)
        self.status = QLabel("No furniture project loaded.")
        layout.addWidget(self.status)
        self.preview_list = QListWidget()
        layout.addWidget(self.preview_list)
        self.checklist = QListWidget()
        self.checklist.setMaximumHeight(130)
        layout.addWidget(QLabel("Pre-export review checklist"))
        layout.addWidget(self.checklist)
        self.capabilities = QLabel("Capabilities: choose a workflow to inspect support.")
        layout.addWidget(self.capabilities)
        self.verification = QLabel("Verification: no project loaded.")
        layout.addWidget(self.verification)
        self.inline_validation = QLabel("Validation: enter a project name to begin.")
        layout.addWidget(self.inline_validation)
        self.workflow.currentTextChanged.connect(self._update_capabilities)
        self.name.textChanged.connect(self._update_inline_validation)
        self.category.currentTextChanged.connect(self._update_inline_validation)
        self.donor_item.textChanged.connect(self._update_inline_validation)
        self.donor_recipe.textChanged.connect(self._update_inline_validation)
        self._update_capabilities(self.workflow.currentText())
        self._update_inline_validation()
        self._search_donors("")
        self._search_blueprints("")
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
        self.workflow.setCurrentText(self.project.workflow_mode)
        self.donor_item.setText(str(self.project.donor_item_id or ""))
        self.donor_recipe.setText(str(self.project.donor_recipe_id or ""))
        self.target_guid.clear(); self.base_template_guid.clear(); self.base_item_guid.clear()
        self.evidence_title.clear(); self.evidence_source.clear()
        self.verification.setText("Verification: " + ", ".join(f"{key}={value}" for key, value in self.project.verification.items()))
        self._update_project_summary()
        self.status.setText("Loaded tested bed workflow as a new furniture project.")

    def _read_project(self) -> FurnitureProject:
        project = FurnitureProject(
            project_id=self.project.project_id,
            name=self.name.text(), description=self.description.text(), category=self.category.currentText(),
            width=self.width.value(), height=self.height.value(), depth=self.depth.value(),
            materials=[item.strip() for item in self.materials.text().split(",") if item.strip()],
            asset_references=[item.strip() for item in self.assets.text().split(",") if item.strip()],
            source_template=self.project.source_template,
        )
        project.donor_item_id = self.project.donor_item_id
        project.donor_recipe_id = self.project.donor_recipe_id
        project.evidence = list(self.project.evidence)
        project.verification = dict(self.project.verification)
        project.blender_handoff = dict(self.project.blender_handoff)
        project.workflow_mode = self.workflow.currentText()
        for field, label in ((self.donor_item, "donor item"), (self.donor_recipe, "donor recipe")):
            if field.text().strip():
                try:
                    value = int(field.text().strip())
                except ValueError as exc:
                    raise ValueError(f"{label} ID must be an integer.") from exc
                if label == "donor item": project.donor_item_id = value
                else: project.donor_recipe_id = value
        project.target_model_guid = self.target_guid.text().strip()
        project.base_template_guid = self.base_template_guid.text().strip()
        project.base_item_guid = self.base_item_guid.text().strip()
        if self.evidence_title.text().strip() or self.evidence_source.text().strip():
            project.add_evidence(self.evidence_title.text(), self.evidence_source.text())
        return project

    def _update_capabilities(self, workflow: str) -> None:
        if workflow == "replacement":
            supported = "mesh replacement, donor item, donor recipe"
            unknown = "visuals, placement, persistence, multiplayer"
        else:
            supported = "new model metadata, base template, base item, recipe plan"
            unknown = "independent registration, crafting UI, icon display, persistence, multiplayer"
        self.capabilities.setText(f"Supported offline: {supported}. Unverified: {unknown}.")

    def _update_workflow_step(self, index: int) -> None:
        self.status.setText(f"Guided workflow: {self.workflow_step.itemText(index)}")

    def _search_donors(self, query: str) -> None:
        self.donor_results.clear()
        for record in search_donor_library(query):
            item_id = record["item_id"] if record["item_id"] is not None else "not registered"
            recipe_id = record["recipe_id"] if record["recipe_id"] is not None else "not registered"
            self.donor_results.addItem(f"{record['name']} · {record['category']} · item {item_id} · recipe {recipe_id} · offline evidence")

    def _select_donor(self, item) -> None:
        selected = item.text()
        for record in search_donor_library(""):
            if record["name"] not in selected:
                continue
            if record["item_id"] is not None:
                self.donor_item.setText(str(record["item_id"]))
            if record["recipe_id"] is not None:
                self.donor_recipe.setText(str(record["recipe_id"]))
            self.status.setText(f"Selected offline donor: {record['name']}. Runtime behavior remains unverified.")
            return

    def _search_blueprints(self, query: str) -> None:
        self.blueprint_results.clear()
        for result in self.blueprints.search(query):
            blueprint = result["record"].get("blueprint", {})
            self.blueprint_results.addItem(
                f"{blueprint.get('title', 'Untitled')} · {blueprint.get('workflow_mode', 'unknown')} · "
                f"{blueprint.get('evidence_state', 'unknown')}"
            )

    def _select_blueprint(self, item) -> None:
        title = item.text().split(" · ", 1)[0]
        for result in self.blueprints.search(title):
            if result["record"].get("blueprint", {}).get("title") == title:
                self.project = self.blueprints.duplicate(result["path"])
                self._populate_fields()
                self.status.setText(f"Created a new project from blueprint: {title}")
                return

    def save_blueprint(self) -> None:
        try:
            self.project = self._read_project()
            destination = self.blueprints.save(self.project, [self.project.category, self.project.workflow_mode])
            self._search_blueprints(self.blueprint_search.text())
            self.status.setText(f"Blueprint saved: {destination.name}")
        except ValueError as exc:
            self.status.setText("Blueprint blocked: " + str(exc))

    def _update_project_summary(self) -> None:
        if not self.project.name:
            self.project_summary.setText("No project loaded. Start from a fixture or begin a new design.")
            return
        self.project_summary.setText(
            f"{self.project.name} · {self.project.category} · {self.project.workflow_mode} · "
            f"evidence: {len(self.project.evidence)} · project ID: {self.project.project_id}"
        )

    def _update_inline_validation(self) -> None:
        try:
            project = self._read_project()
            issues = project.validate()
        except ValueError as exc:
            issues = [str(exc)]
        if issues:
            self.inline_validation.setText("Validation: " + " ".join(issues))
            self.inline_validation.setStyleSheet("color: #d66;")
        else:
            self.inline_validation.setText("Validation: current project fields are valid.")
            self.inline_validation.setStyleSheet("color: #6c6;")

    def preview(self) -> None:
        self.project = self._read_project(); issues = self.project.validate(); self.preview_list.clear()
        self._update_project_summary()
        self.checklist.clear()
        for item in self.project.export_checklist():
            self.checklist.addItem(f"{item['state'].upper()}: {item['check']} — {item['details']}")
        if issues:
            self.status.setText("Needs review: " + " ".join(issues)); return
        for key, value in self.project.manifest()["project"].items():
            self.preview_list.addItem(f"{key}: {value}")
        review = self.project.export_review()
        self.verification.setText("Verification: " + ", ".join(f"{key}={value}" for key, value in self.project.verification.items()))
        self.status.setText(("Review required: " + " ".join(review["issues"])) if not review["ready"]
                            else "Furniture design preview ready for export. Live game files are untouched.")

    def create_snapshot(self) -> None:
        try:
            self.project = self._read_project()
            self.project.snapshot("UI checkpoint")
            self._update_project_summary()
            self.status.setText(f"Recovery snapshot created ({len(self.project.history)} saved).")
        except ValueError as exc:
            self.status.setText("Snapshot blocked: " + str(exc))

    def undo_snapshot(self) -> None:
        try:
            self.project.undo()
            self._populate_fields()
            self.status.setText("Restored the previous recovery snapshot.")
        except ValueError as exc:
            self.status.setText("Undo unavailable: " + str(exc))

    def check_compatibility(self) -> None:
        warnings = self.project.compatibility_warnings()
        self.status.setText("Compatibility: " + (" ".join(warnings) if warnings else "no recorded mismatches."))

    def _populate_fields(self) -> None:
        self.name.setText(self.project.name); self.description.setText(self.project.description)
        self.category.setCurrentText(self.project.category); self.width.setValue(self.project.width)
        self.height.setValue(self.project.height); self.depth.setValue(self.project.depth)
        self.materials.setText(", ".join(self.project.materials)); self.assets.setText(", ".join(self.project.asset_references))
        self.workflow.setCurrentText(self.project.workflow_mode)
        self.donor_item.setText(str(self.project.donor_item_id or "")); self.donor_recipe.setText(str(self.project.donor_recipe_id or ""))
        self.target_guid.setText(self.project.target_model_guid or ""); self.base_template_guid.setText(self.project.base_template_guid or "")
        self.base_item_guid.setText(self.project.base_item_guid or "")
        self.verification.setText("Verification: " + ", ".join(f"{key}={value}" for key, value in self.project.verification.items()))
        self._update_project_summary(); self._update_inline_validation()

    def save_project(self) -> None:
        self.project = self._read_project()
        destination, _ = QFileDialog.getSaveFileName(self, "Save Content Creator Project", "", "Content Creator Project (*.json)")
        if not destination:
            return
        try:
            self.project.save(Path(destination))
            self.status.setText(f"Project saved: {destination}")
        except ValueError as exc:
            QMessageBox.warning(self, "Project could not be saved", str(exc))

    def open_project(self) -> None:
        source, _ = QFileDialog.getOpenFileName(self, "Open Content Creator Project", "", "Content Creator Project (*.json)")
        if not source:
            return
        try:
            self.project = FurnitureProject.load(Path(source))
            self._populate_fields()
            self.evidence_title.clear(); self.evidence_source.clear()
            self.status.setText(f"Project opened: {source}")
        except ValueError as exc:
            QMessageBox.warning(self, "Project could not be opened", str(exc))

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
