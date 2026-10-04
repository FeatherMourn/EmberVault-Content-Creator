"""Standalone Content Creator project and furniture foundation."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


PROJECT_SCHEMA_VERSION = 1
SUPPORTED_FURNITURE_CATEGORIES = {"bed", "chair", "table", "storage", "decor"}

OFFLINE_DONOR_LIBRARY = [
    {"name": "Vanilla bed donor", "category": "bed", "item_id": 2940001508, "recipe_id": 3531872774, "source": "tested bed workflow"},
    {"name": "Rough wood chair donor", "category": "chair", "item_id": None, "recipe_id": None, "source": "medieval armchair offline fixture"},
]


def search_donor_library(query: str = "") -> list[dict]:
    query = query.strip().lower()
    return [record for record in OFFLINE_DONOR_LIBRARY if not query or query in " ".join(str(value).lower() for value in record.values())]


def import_package_metadata(package_root: Path) -> dict:
    """Read safe JSON metadata from an existing package without executing it."""
    root = Path(package_root)
    if not root.is_dir():
        raise ValueError("Package metadata source must be a directory.")
    imported = {}
    for name in ("mod.json", "validation.json"):
        source = root / name
        if not source.is_file():
            continue
        if source.stat().st_size > 2_000_000:
            raise ValueError(f"Metadata file is too large: {name}.")
        try:
            value = json.loads(source.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"Unable to read safe metadata file {name}: {exc}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"Metadata file must contain an object: {name}.")
        imported[name] = value
    if not imported:
        raise ValueError("No supported JSON metadata files were found.")
    return {"source": str(root), "files": imported, "executed": False, "installed": False}


class BlueprintLibrary:
    """Local, design-only library of reusable Content Creator projects."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, project: "FurnitureProject", tags: list[str] | None = None) -> Path:
        issues = project.validate()
        if issues:
            raise ValueError("Cannot add invalid blueprint: " + " ".join(issues))
        record = project.to_project_dict()
        destination = self.root / f"{project.project_id}.json"
        previous = {}
        if destination.exists():
            try:
                previous = json.loads(destination.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                previous = {}
        versions = list(previous.get("blueprint", {}).get("versions", []))
        version = int(previous.get("blueprint", {}).get("version", 0)) + 1
        if previous:
            versions.append({"version": version - 1, "preview_hash": previous.get("blueprint", {}).get("preview_hash", "")})
        record["blueprint"] = {
            "title": project.name,
            "tags": sorted({tag.strip() for tag in (tags or []) if tag.strip()}),
            "workflow_mode": project.workflow_mode,
            "evidence_state": "review-required" if project.review_issues() else "reviewed",
            "preview_hash": project.preview()["preview_hash"],
            "version": version,
            "versions": versions,
        }
        destination.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        self._log("blueprint_saved", project.project_id, {"version": version, "tags": record["blueprint"]["tags"]})
        return destination

    def search(self, query: str = "", evidence_state: str | None = None, game_build: str | None = None) -> list[dict]:
        query = query.strip().lower()
        results = []
        for source in sorted(self.root.glob("*.json")):
            try:
                record = json.loads(source.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            blueprint = record.get("blueprint", {})
            haystack = " ".join(str(value).lower() for value in [blueprint, record.get("project", {})])
            compatibility = record.get("project", {}).get("blender_handoff", {})
            if (not query or query in haystack) and (not evidence_state or blueprint.get("evidence_state") == evidence_state) and (not game_build or compatibility.get("game_build") == game_build):
                results.append({"path": source, "record": record})
        return results

    def _log(self, event: str, project_id: str, details: dict | None = None) -> None:
        entry = {"event": event, "project_id": project_id, "details": details or {}}
        with (self.root / "activity.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(entry, sort_keys=True) + "\n")

    def duplicate(self, source: Path) -> "FurnitureProject":
        project = FurnitureProject.load(Path(source))
        project.project_id = f"cc-{uuid4().hex}"
        project.name = f"Copy of {project.name}"
        project.history = []
        self._log("blueprint_duplicated", project.project_id, {"source": str(source)})
        return project

    def public_record(self, project: "FurnitureProject") -> dict:
        """Build a sanitized Web Catalog record without private workspace data."""
        issues = project.review_issues()
        preview = project.preview()
        return {
            "record_type": "content-blueprint",
            "record_version": 1,
            "title": project.name,
            "category": project.category,
            "workflow_mode": project.workflow_mode,
            "description": project.description,
            "tags": [project.category, project.workflow_mode],
            "preview_hash": preview["preview_hash"],
            "evidence_state": "review-required" if issues else "reviewed",
            "review_issues": issues,
            "compatibility": {
                "game_build": project.blender_handoff.get("game_build", "unknown"),
                "blender_version": project.blender_handoff.get("blender_version", "unknown"),
            },
            "application_state": "design-only",
            "live_game_files_touched": False,
        }

    @staticmethod
    def validate_public_record(record: dict) -> list[str]:
        required = {"record_type", "record_version", "title", "category", "workflow_mode", "preview_hash", "evidence_state", "compatibility", "application_state", "live_game_files_touched"}
        issues = [f"missing:{key}" for key in sorted(required - record.keys())]
        if record.get("record_type") != "content-blueprint": issues.append("record_type")
        if record.get("record_version") != 1: issues.append("record_version")
        if record.get("application_state") != "design-only": issues.append("application_state")
        if record.get("live_game_files_touched") is not False: issues.append("live_game_files_touched")
        if not isinstance(record.get("compatibility"), dict): issues.append("compatibility")
        return issues

    def publish_record(self, project: "FurnitureProject", destination: Path) -> Path:
        record = self.public_record(project)
        issues = self.validate_public_record(record)
        if issues:
            raise ValueError("Public record invalid: " + " ".join(issues))
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        self._log("catalog_record_prepared", project.project_id, {"destination": "sanitized-public-record"})
        return destination

    def catalog_snapshot(self, projects: list["FurnitureProject"]) -> dict:
        """Create a sanitized public-catalog envelope for Web Catalog handoff."""
        records = [self.public_record(project) for project in projects]
        return {
            "schema_version": 1,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "contract_versions": {
                "module_manifest": 1, "package_manifest": 1, "research_record": 1,
                "content_project": 1, "tuning_adapter": 1,
            },
            "packages": [], "modules": [], "tuning_adapters": [], "knowledge": [],
            "research": [], "content_projects": records,
        }


def validate_export_contract(payload: dict) -> list[str]:
    issues = []
    required = {"schema_version", "schema_id", "application_state", "content_type", "project", "runtime_plan", "evidence_summary", "evidence", "live_game_files_touched"}
    issues.extend(f"missing:{key}" for key in sorted(required - payload.keys()))
    if payload.get("schema_version") != 1:
        issues.append("schema_version")
    if payload.get("schema_id") != "https://embervault.dev/contracts/content-project-export.schema.json":
        issues.append("schema_id")
    if payload.get("application_state") != "design-only":
        issues.append("application_state")
    if payload.get("live_game_files_touched") is not False:
        issues.append("live_game_files_touched")
    evidence_summary = payload.get("evidence_summary", {})
    for key in ("verification", "evidence_count", "open_questions"):
        if key not in evidence_summary:
            issues.append(f"evidence_summary.{key}")
    return issues


@dataclass
class FurnitureProject:
    project_id: str = field(default_factory=lambda: f"cc-{uuid4().hex}")
    name: str = ""
    description: str = ""
    category: str = "bed"
    width: float = 2.0
    height: float = 1.0
    depth: float = 3.0
    materials: list[str] = field(default_factory=list)
    asset_references: list[str] = field(default_factory=list)
    source_template: str = ""
    donor_item_id: int | None = None
    donor_recipe_id: int | None = None
    clone_item_id: int | None = None
    clone_recipe_id: int | None = None
    workflow_mode: str = "donor-preserving-clone"
    target_model_guid: str = ""
    base_template_guid: str = ""
    base_item_guid: str = ""
    evidence: list[dict] = field(default_factory=list)
    blender_handoff: dict = field(default_factory=dict)
    history: list[dict] = field(default_factory=list)
    verification: dict[str, str] = field(default_factory=lambda: {
        "registration": "unverified",
        "visuals": "unverified",
        "ui_linkage": "unverified",
        "placement": "unverified",
        "persistence": "unverified",
        "multiplayer": "unverified",
    })

    def to_project_dict(self) -> dict:
        return {
            "project_schema_version": PROJECT_SCHEMA_VERSION,
            "project_id": self.project_id,
            "content_type": "furniture",
            "project": asdict(self),
        }

    def save(self, destination: Path) -> Path:
        """Persist an editable project without touching game files."""
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_name(f".{destination.name}.tmp")
        temporary.write_text(json.dumps(self.to_project_dict(), indent=2) + "\n", encoding="utf-8")
        temporary.replace(destination)
        return destination

    def snapshot(self, label: str = "checkpoint") -> dict:
        """Record a portable recovery snapshot without touching game files."""
        snapshot = {
            "label": label.strip() or "checkpoint",
            "project": self.to_project_dict(),
        }
        self.history.append(snapshot)
        return snapshot

    def restore_snapshot(self, snapshot: dict) -> None:
        payload = snapshot.get("project", {})
        restored = payload.get("project", {})
        if payload.get("project_schema_version") != PROJECT_SCHEMA_VERSION or restored.get("project_id") != self.project_id:
            raise ValueError("Snapshot does not belong to this project or uses an unsupported version.")
        allowed = {field.name for field in self.__dataclass_fields__.values() if field.name != "history"}
        for key, value in restored.items():
            if key in allowed:
                setattr(self, key, value)

    def undo(self) -> None:
        if len(self.history) < 2:
            raise ValueError("No earlier project snapshot is available.")
        current = self.history.pop()
        self.restore_snapshot(self.history[-1])
        self.history.append(current)

    def compatibility_warnings(self, blender_version: str = "", game_build: str = "") -> list[str]:
        warnings = []
        handoff = self.blender_handoff
        if handoff and blender_version and handoff.get("blender_version") != blender_version:
            warnings.append("Blender version differs from the recorded handoff.")
        if handoff and game_build and handoff.get("game_build") != game_build:
            warnings.append("Game build differs from the recorded handoff.")
        if not handoff:
            warnings.append("No external-tool handoff has been recorded.")
        return warnings

    @classmethod
    def load(cls, source: Path) -> "FurnitureProject":
        source = Path(source)
        try:
            payload = json.loads(source.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"Unable to load project: {exc}") from exc
        if payload.get("project_schema_version") != PROJECT_SCHEMA_VERSION:
            raise ValueError("Unsupported Content Creator project version.")
        project = payload.get("project")
        if not isinstance(project, dict) or project.get("project_id") != payload.get("project_id"):
            raise ValueError("Project identity is missing or inconsistent.")
        allowed = {field.name for field in cls.__dataclass_fields__.values()}
        values = {key: value for key, value in project.items() if key in allowed}
        loaded = cls(**values)
        issues = loaded.validate()
        if issues:
            raise ValueError("Invalid project: " + " ".join(issues))
        return loaded

    def validate(self) -> list[str]:
        issues = []
        if not self.name.strip():
            issues.append("A furniture name is required.")
        if any(value <= 0 for value in (self.width, self.height, self.depth)):
            issues.append("Furniture dimensions must be greater than zero.")
        if self.workflow_mode not in {"replacement", "new-model", "donor-preserving-clone"}:
            issues.append("Workflow mode must be replacement, new-model, or donor-preserving-clone.")
        elif self.workflow_mode == "replacement" and (self.donor_item_id is None or self.donor_recipe_id is None):
            issues.append("Replacement workflow requires a vanilla donor item and recipe.")
        elif self.workflow_mode == "new-model" and not all((self.target_model_guid, self.base_template_guid, self.base_item_guid)):
            issues.append("New-model workflow requires target, base template, and base item GUIDs.")
        if self.category not in SUPPORTED_FURNITURE_CATEGORIES:
            issues.append(f"Unsupported furniture category: {self.category}.")
        if any(Path(ref).is_absolute() or ".." in Path(ref).parts for ref in self.asset_references):
            issues.append("Asset references must remain inside the project.")
        allowed = {"verified", "partial", "unverified", "blocked", "not_applicable"}
        if any(value not in allowed for value in self.verification.values()):
            issues.append("Verification states must be recognized evidence states.")
        for record in self.evidence:
            if not isinstance(record, dict) or not str(record.get("title", "")).strip():
                issues.append("Each evidence record needs a title.")
                break
        if self.blender_handoff:
            for key in ("repository", "tool_version", "blender_version", "game_build", "source_guids", "package_files"):
                if not self.blender_handoff.get(key):
                    issues.append(f"Blender handoff is missing {key}.")
        return issues

    def set_dimensions(self, width: float, height: float, depth: float) -> None:
        self.width, self.height, self.depth = width, height, depth
        issues = self.validate()
        if any("dimensions" in issue for issue in issues):
            raise ValueError("Furniture dimensions must be greater than zero.")

    def add_asset_reference(self, reference: str) -> None:
        reference = str(reference).strip()
        if not reference or Path(reference).is_absolute() or ".." in Path(reference).parts:
            raise ValueError("Asset references must remain inside the project.")
        if reference not in self.asset_references:
            self.asset_references.append(reference)

    def set_donor(self, item_id: int, recipe_id: int) -> None:
        if not isinstance(item_id, int) or isinstance(item_id, bool) or item_id <= 0:
            raise ValueError("A positive donor item id is required.")
        if not isinstance(recipe_id, int) or isinstance(recipe_id, bool) or recipe_id <= 0:
            raise ValueError("A positive donor recipe id is required.")
        self.donor_item_id = item_id
        self.donor_recipe_id = recipe_id

    def apply_reference_fixture(self, fixture: dict, workflow_mode: str = "new-model") -> None:
        if workflow_mode not in {"replacement", "new-model"}:
            raise ValueError("Workflow mode must be replacement or new-model.")
        target = fixture.get("target", {})
        required = ("target_guid", "base_template_guid", "base_item_guid")
        if any(not str(target.get(key, "")).strip() for key in required):
            raise ValueError("Reference fixture is missing target or donor GUID metadata.")
        self.workflow_mode = workflow_mode
        self.target_model_guid = str(target["target_guid"])
        self.base_template_guid = str(target["base_template_guid"])
        self.base_item_guid = str(target["base_item_guid"])
        self.source_template = str(target.get("model_name", self.source_template))
        self.add_evidence("Reference fixture applied", str(fixture.get("source_label", "offline fixture")), state="observed")

    def set_blender_handoff(self, repository: str, tool_version: str, blender_version: str,
                            game_build: str, source_guids: list[str], package_files: list[str]) -> None:
        values = [repository.strip(), tool_version.strip(), blender_version.strip(), game_build.strip()]
        if not all(values) or not source_guids or not package_files:
            raise ValueError("Blender handoff requires tool provenance, source GUIDs, and package files.")
        if any(Path(item).is_absolute() or ".." in Path(item).parts for item in package_files):
            raise ValueError("Blender package files must remain relative to the export package.")
        self.blender_handoff = {
            "repository": repository.strip(), "tool_version": tool_version.strip(),
            "blender_version": blender_version.strip(), "game_build": game_build.strip(),
            "source_guids": list(source_guids), "package_files": list(package_files),
            "validation_state": "unverified",
        }

    def validate_blender_package(self, available_files: list[str]) -> list[str]:
        expected = {"mod.json", "validation.json", "render_data.bin", "src/mod.lua"}
        available = {str(Path(item).as_posix()) for item in available_files}
        issues = [f"Missing generated package file: {item}" for item in sorted(expected - available)]
        if self.blender_handoff:
            self.blender_handoff["validation_state"] = "validated" if not issues else "incomplete"
        return issues

    def hash_blender_package(self, package_root: Path) -> dict:
        """Hash the recorded package files without executing or installing them."""
        root = Path(package_root)
        if not root.is_dir():
            raise ValueError("Blender package root must be a directory.")
        files = self.blender_handoff.get("package_files", [])
        inventory = {}
        for relative in files:
            candidate = root / relative
            if Path(relative).is_absolute() or ".." in Path(relative).parts:
                raise ValueError("Blender package files must remain relative to the package root.")
            if not candidate.is_file():
                inventory[str(Path(relative).as_posix())] = {"state": "missing"}
                continue
            digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
            inventory[str(Path(relative).as_posix())] = {"state": "present", "size": candidate.stat().st_size, "sha256": digest}
        self.blender_handoff["file_inventory"] = inventory
        self.blender_handoff["inventory_state"] = "complete" if all(item["state"] == "present" for item in inventory.values()) else "incomplete"
        return inventory

    def blender_review_report(self) -> dict:
        handoff = self.blender_handoff
        return {
            "ready_for_round_trip": bool(handoff) and handoff.get("validation_state") == "validated" and handoff.get("inventory_state") == "complete",
            "validation_state": handoff.get("validation_state", "unverified"),
            "inventory_state": handoff.get("inventory_state", "unverified"),
            "tool_version": handoff.get("tool_version", "unknown"),
            "blender_version": handoff.get("blender_version", "unknown"),
            "game_build": handoff.get("game_build", "unknown"),
            "runtime_testing": "not_started",
        }

    def add_resource_metadata(self, resource_type: str, resource_id: str, source: str) -> None:
        record = {"resource_type": resource_type.strip(), "resource_id": resource_id.strip(), "source": source.strip()}
        if not all(record.values()):
            raise ValueError("Resource metadata requires a type, id, and source.")
        self.evidence.append({"title": f"Resource metadata: {record['resource_type']}", **record, "state": "observed"})

    def set_verification(self, area: str, state: str) -> None:
        if area not in self.verification:
            raise ValueError(f"Unknown verification area: {area}.")
        if state not in {"verified", "partial", "unverified", "blocked", "not_applicable"}:
            raise ValueError(f"Unknown verification state: {state}.")
        self.verification[area] = state

    def add_evidence(self, title: str, source: str, state: str = "observed", **provenance: str) -> None:
        title, source = title.strip(), source.strip()
        if not title or not source:
            raise ValueError("Evidence requires a title and source.")
        record = {"title": title, "source": source, "state": state}
        record.update({key: value.strip() for key, value in provenance.items() if isinstance(value, str) and value.strip()})
        self.evidence.append(record)

    def remove_evidence(self, title: str) -> bool:
        before = len(self.evidence)
        self.evidence = [record for record in self.evidence if record.get("title") != title]
        return len(self.evidence) != before

    def review_issues(self) -> list[str]:
        issues = self.validate()
        if not self.evidence:
            issues.append("At least one evidence record is required for review.")
        if any(value in {"unverified", "partial"} for value in self.verification.values()):
            issues.append("Unverified or partial verification areas remain open.")
        states = {record.get("state") for record in self.evidence}
        if "contradicted" in states:
            issues.append("Contradictory evidence requires review.")
        return issues

    def preview(self) -> dict:
        """Return a deterministic, UI-safe summary without reading game files."""
        summary = {
            "project_id": self.project_id,
            "name": self.name,
            "category": self.category,
            "dimensions": {"width": self.width, "height": self.height, "depth": self.depth},
            "materials": sorted(self.materials),
            "asset_references": sorted(self.asset_references),
            "donor_item_id": self.donor_item_id,
            "donor_recipe_id": self.donor_recipe_id,
            "verification": dict(sorted(self.verification.items())),
            "evidence_count": len(self.evidence),
            "application_state": "design-only",
        }
        encoded = json.dumps(summary, sort_keys=True, separators=(",", ":")).encode("utf-8")
        summary["preview_hash"] = hashlib.sha256(encoded).hexdigest()
        return summary

    def export_review(self) -> dict:
        issues = self.review_issues()
        return {"ready": not issues, "issues": issues, "preview_hash": self.preview()["preview_hash"]}

    def export_checklist(self) -> list[dict]:
        review = self.export_review()
        return [
            {"check": "Project fields", "state": "pass" if not self.validate() else "blocked", "details": "Required project data is valid." if not self.validate() else "Project data needs correction."},
            {"check": "Evidence review", "state": "pass" if self.evidence and not any(record.get("state") == "contradicted" for record in self.evidence) else "blocked", "details": f"{len(self.evidence)} evidence record(s) attached."},
            {"check": "Compatibility", "state": "warning" if self.compatibility_warnings() else "pass", "details": "; ".join(self.compatibility_warnings()) or "No recorded compatibility warnings."},
            {"check": "Design-only boundary", "state": "pass", "details": "Live game files remain untouched."},
            {"check": "Review readiness", "state": "pass" if review["ready"] else "blocked", "details": "Ready for export." if review["ready"] else "Open: " + " ".join(review["issues"])},
        ]

    def manifest(self) -> dict:
        payload = {
            "manifest_version": 1,
            "schema_version": 1,
            "schema_id": "https://embervault.dev/contracts/content-project-export.schema.json",
            "application": "EmberVault Content Creator",
            "application_state": "design-only",
            "content_type": "furniture",
            "project": asdict(self),
            "runtime_plan": {
                "strategy": "vanilla-replacement" if self.workflow_mode == "replacement" else "donor-preserving-clone",
                "donor_item_id": self.donor_item_id,
                "donor_recipe_id": self.donor_recipe_id,
                "clone_item_id": self.clone_item_id,
                "clone_recipe_id": self.clone_recipe_id,
                "requires_build_validation": True,
            },
            "evidence_summary": {
                "verification": dict(self.verification),
                "evidence_count": len(self.evidence),
                "open_questions": [key for key, value in self.verification.items()
                                   if value in {"unverified", "partial"}],
            },
            "evidence": list(self.evidence),
            "live_game_files_touched": False,
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        payload["export_metadata"] = {
            "project_hash": hashlib.sha256(encoded).hexdigest(),
            "preview_hash": self.preview()["preview_hash"],
            "file_inventory": sorted(self.blender_handoff.get("package_files", [])),
            "checklist": self.export_checklist(),
        }
        return payload

    def export(self, destination: Path) -> Path:
        issues = self.validate()
        if issues:
            raise ValueError(" ".join(issues))
        issues = validate_export_contract(self.manifest())
        if issues:
            raise ValueError("Export contract invalid: " + " ".join(issues))
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(self.manifest(), indent=2), encoding="utf-8")
        return destination


def bed_template() -> FurnitureProject:
    project = FurnitureProject(
        name="New Bed Design",
        description="Furniture based on the proven in-game bed workflow.",
        category="bed",
        width=2.0,
        height=1.0,
        depth=3.0,
        materials=["wood", "fabric"],
        source_template="tested-bed-workflow",
        donor_item_id=2940001508,
        donor_recipe_id=3531872774,
        evidence=[{
            "title": "Controlled bed registration probe",
            "source": "EmberVault furniture-clone-registration research",
            "scope": "independent ItemInfo and recipe registration route",
            "state": "partial",
        }],
        verification={
            "registration": "verified",
            "visuals": "unverified",
            "ui_linkage": "unverified",
            "placement": "unverified",
            "persistence": "unverified",
            "multiplayer": "unverified",
        },
    )
    project.workflow_mode = "replacement"
    return project


def prepare_bed_vertical_slice(destination: Path, package_files: list[str] | None = None) -> dict:
    """Run the complete offline bed workflow and write reviewable artifacts."""
    project = bed_template()
    project.set_blender_handoff(
        "https://github.com/Baik90/EnshroudedBlenderTools", "0.25.0", "5.2 LTS",
        "1076226", ["bed-render-model"], package_files or ["mod.json", "validation.json", "render_data.bin", "src/mod.lua"],
    )
    project.add_evidence(
        "Bed donor and Blender handoff", "EmberVault bed workflow and EnshroudedBlenderTools",
        state="partial", game_build="1076226", evidence_scope="offline package preparation",
    )
    package_issues = project.validate_blender_package(project.blender_handoff["package_files"])
    root = Path(destination)
    root.mkdir(parents=True, exist_ok=True)
    project_path = project.save(root / "bed-project.json")
    manifest_path = project.export(root / "bed-export.json")
    return {
        "project": project,
        "project_path": project_path,
        "manifest_path": manifest_path,
        "preview": project.preview(),
        "review": project.export_review(),
        "package_issues": package_issues,
    }


def create_furniture_project(name: str, category: str = "bed") -> FurnitureProject:
    """Create a guided furniture project without accessing game resources."""
    name = name.strip()
    if not name:
        raise ValueError("A furniture name is required.")
    if category not in SUPPORTED_FURNITURE_CATEGORIES:
        raise ValueError(f"Unsupported furniture category: {category}.")
    return FurnitureProject(name=name, category=category)
