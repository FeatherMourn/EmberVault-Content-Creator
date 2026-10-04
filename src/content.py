"""Standalone Content Creator project and furniture foundation."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
import hashlib
from pathlib import Path
from uuid import uuid4


PROJECT_SCHEMA_VERSION = 1
SUPPORTED_FURNITURE_CATEGORIES = {"bed", "chair", "table", "storage", "decor"}


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
    evidence: list[dict] = field(default_factory=list)
    blender_handoff: dict = field(default_factory=dict)
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

    def manifest(self) -> dict:
        return {
            "schema_version": 1,
            "schema_id": "https://embervault.dev/contracts/content-project-export.schema.json",
            "application": "EmberVault Content Creator",
            "application_state": "design-only",
            "content_type": "furniture",
            "project": asdict(self),
            "runtime_plan": {
                "strategy": "donor-preserving-clone",
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
    return FurnitureProject(
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
