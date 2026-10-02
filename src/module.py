from __future__ import annotations

from embervault_sdk import ModuleContext, ModuleResult

MODULE_ID = "embervault.content-creator"


def describe() -> dict:
    return {"id": MODULE_ID, "execution": "embedded", "application_state": "design-only", "touches_live_game": False}


def validate_design(context: ModuleContext, design_type: str, asset_references: list[str]) -> ModuleResult:
    if context.module_id != MODULE_ID or not context.profile_id:
        return ModuleResult("blocked", "Content Creator requires a profile-scoped context.")
    if not design_type.strip():
        return ModuleResult("blocked", "A design type is required.")
    references = list(asset_references)
    if any(reference.startswith(("/", "\\")) or ".." in reference.replace("\\", "/").split("/") for reference in references):
        return ModuleResult("blocked", "Asset references must remain relative to the design project.")
    return ModuleResult("ready", "Design manifest validated.", {
        "design_type": design_type.strip(), "asset_references": references,
        "application_state": "design-only", "touches_live_game": False,
    })
