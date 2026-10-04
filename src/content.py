"""Standalone Content Creator project and furniture foundation."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from uuid import uuid4


PROJECT_SCHEMA_VERSION = 1


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
        if any(Path(ref).is_absolute() or ".." in Path(ref).parts for ref in self.asset_references):
            issues.append("Asset references must remain inside the project.")
        allowed = {"verified", "partial", "unverified", "blocked", "not_applicable"}
        if any(value not in allowed for value in self.verification.values()):
            issues.append("Verification states must be recognized evidence states.")
        for record in self.evidence:
            if not isinstance(record, dict) or not str(record.get("title", "")).strip():
                issues.append("Each evidence record needs a title.")
                break
        return issues

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
