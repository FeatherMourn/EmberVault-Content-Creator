# EmberVault Content Creator Roadmap

## Purpose

Create evidence-aware, design-only content projects for furniture, buildings,
recipes, assets, and future content types.

## Scope

Included: project authoring, donors, asset references, evidence, previews,
validation, and export packages.

Excluded: direct live game mutation, unverified runtime claims, and automatic
promotion of research into working game content.

## Current state — 2026-10-04

The read-only Mod Research client now validates the expanded 19-record,
design-only handoff. It preserves evidence counts, confidence, limitations,
open questions, contradiction warnings, and an explicit false runtime-approval
flag. The standalone PySide authoring shell is now verified with dashboard,
guided workflow, donor and blueprint search, metadata import, preview,
validation, recovery snapshots, save/load, and design-only export paths.

## Dependencies

- EmberVault-Contracts: project and export schemas.
- EmberVault-Module-SDK: module boundary.
- Control Center: profiles, operations, evidence, and recovery context.
- Mod Research: donor and verification evidence.
- EnshroudedBlenderTools research and generated-package evidence. Content
  Creator will orchestrate and validate this external pipeline rather than
  reimplement Blender or the game resource encoder.

## Milestones

### Foundation — completed

1. [x] Consume the shared Module SDK.
2. [x] Add the canonical Content Project Export contract to EmberVault Contracts.
3. [x] Identify exports with the canonical schema and package the contract in
   Control Center.
4. [x] Establish the design-only boundary and bed donor workflow foundation.

### Content Creator 2.0 — active build sequence

5. [x] Create and open projects with deterministic project identifiers.
6. [x] Build a real project workspace with save, load, autosave, versioning,
   recovery, and corruption handling.
7. [x] Build guided authoring workflows for furniture, buildings, recipes, and
   assets, while keeping unsupported content types explicit.
8. [x] Add donor, recipe, resource, and asset-reference selection with path
   safety validation.
9. [x] Add the initial read-only donor search and resource metadata client from
   Mod Research; UI integration remains active.
10. [x] Add an external-tool handoff panel for EnshroudedBlenderTools, recording the
   repository/version, Blender version, game build, source GUIDs, generated
   package paths, and tool validation results.
11. [ ] Add visible verification states for verified, partial, unknown, and
    blocked results.
12. [ ] Add evidence attachment, provenance display, contradiction warnings,
    and open-question tracking.
13. [x] Add deterministic previews and a clear separation between design data,
    runtime plans, and unsupported claims.
14. [ ] Validate generated EML/package structures without installing them.
15. [x] Validate project exports against the shared Content Project Export
    contract and sanitize public-facing fields.
16. [ ] Add import/export compatibility checks and clear, actionable error
    messages.
17. [ ] Connect the standalone project model to the Control Center module
    lifecycle without allowing live-game mutation.
18. [ ] Add Control Center operations for review, validation, recovery, and
    package handoff.
19. [ ] Build the first complete bed workflow from project creation through
    donor selection, evidence attachment, Blender handoff, validation, and
    export.
20. [ ] Add end-to-end tests, clean-install packaging checks, documentation,
    including registration evidence and unresolved visual/runtime questions.
21. [ ] Add GitHub backup and a reviewable release artifact for the completed
    bed vertical slice.
22. [ ] Define an adapter boundary for external tools and keep Blender Tools
    integration replaceable.
23. [ ] Add reference fixtures for bed creation, furniture replacement, and
    new-model workflows.
24. [ ] Define a capability matrix for each content type and workflow.
25. [ ] Add deterministic package hashes and export manifests.
26. [x] Add project migration tooling for contract and schema changes.
27. [ ] Add undo, redo, and operation history for authoring decisions.
28. [ ] Add preview thumbnails and before/after comparison snapshots.
29. [ ] Add an explicit offline mode when game resources or external tools are
    unavailable.
30. [ ] Add structured logs for validation, handoff, export, and recovery.
31. [x] Add a review checklist before a package can be marked ready.
32. [x] Add compatibility warnings for Blender, game-build, and tool-version
    mismatches.
33. [ ] Build a corpus of valid, invalid, incomplete, and contradictory project
    fixtures.

### Usability, traceability, and release hardening — planned

34. [ ] Add a project dashboard with recent projects, fixture templates,
     workflow status, and recovery state.
35. [ ] Add a guided workflow wizard from project setup through donor selection,
     evidence review, handoff, validation, and export.
36. [ ] Add inline field validation with actionable guidance before preview or
     export.
37. [ ] Expand evidence records with notes, timestamps, source types, and
     confidence levels.
38. [x] Add automatic project snapshots, recovery history, undo, and redo;
     autosave safeguards are included.
39. [x] Add a compatibility panel for game builds, Blender versions, and
     external-tool versions.
40. [x] Add complete export manifests with hashes, file inventories, and
     replacement-versus-new-item comparisons.
41. [x] Add fixture templates for chairs and tables; storage and decorative
     fixtures remain future coverage.
42. [x] Add a searchable donor and recipe library backed by Mod Research.
43. [x] Add a pre-export review checklist showing verified, unknown, and blocked
     requirements.
44. [ ] Add safe import of metadata from previously generated EML-related
     packages without modifying original files.
45. [ ] Add structured, user-visible activity logs for project changes,
     validation, handoff, export, and recovery.
46. [ ] Add a capability matrix that separates offline-supported,
     external-tool-dependent, and runtime-unverified features.

### Controlled new-item verification — future gated phase

47. [ ] Automate new-model project setup, base GUID validation, item and recipe
    metadata validation, package generation, hashes, and replacement checks.
48. [ ] Create isolated test-package and profile preparation with verified
    backups, rollback instructions, and test-state tracking.
49. [ ] Run a controlled new-item test with the armchair as the first candidate,
    keeping it separate from vanilla replacement workflows.
50. [ ] Record direct runtime observations for independent registration, recipe
    visibility, crafting or acquisition, icon and name display, model visuals,
    placement, interaction, persistence, and rollback.
51. [ ] Test multiplayer behavior as a separate evidence gate.
52. [ ] Require user-confirmed or reproducible runtime evidence before marking
    any new-item capability verified.

### Advanced offline validation and publication hardening — planned

53. [x] Add GUID collision checks against current KFC3 resources and known
     vanilla identities.
54. [x] Add automatic replacement-versus-new-item package comparison, including
     target identity, base references, registries, recipes, and file inventory.
55. [x] Import generated package metadata back into the project and preserve
     provenance, hashes, and source-tool versions.
56. [x] Validate `crafting.json`, `validation.json`, icon metadata, and package
     manifests against shared schemas.
57. [x] Add icon and package previews to the project review UI; recipe-preview
     detail remains part of schema validation work.
58. [ ] Record exact Blender, external-extension, game-build, and package
     versions in reproducibility reports.
59. [x] Add package security checks for unsafe paths, unexpected files, size
     limits, and executable-content boundaries.
60. [x] Add a second new-item fixture so new-item authoring is not armchair
     specific.
61. [x] Add a dry-run registration simulator for static Lua resource and
     registry references without executing the package in-game.
62. [x] Clarify offline-verified, runtime-unverified, blocked, and unsupported
     states throughout the project and export UI.
63. [x] Add Web Catalog publication metadata for provenance, authorship,
     licensing, compatibility, and review state.

### Later promotion work

64. [ ] Publish only sanitized, review-approved exports to EmberVault Web.
65. [ ] Add runtime adapters only when current-build evidence proves behavior,
    persistence, multiplayer impact, and rollback.

## Definition of done

- [x] Design-only boundary is enforced.
- [x] Registration, visuals, UI linkage, placement, persistence, and
      multiplayer states are distinct.
- [x] Incomplete or contradictory evidence is surfaced.
- [x] Export packages identify and target the shared schema.
- [x] Export packages are schema-validated and sanitized in the application.
- [ ] External Blender Tools handoffs retain provenance and are independently
      validated before being included in an export package.
- [ ] Projects persist safely across saves, loads, and version changes.
- [ ] Control Center lifecycle integration is verified.
- [ ] Runtime claims remain separate from static Blender/package evidence.
- [ ] External-tool adapters, fixtures, capability matrix, hashes, migrations,
      history, previews, offline mode, logs, review checks, compatibility
      warnings, test corpus, dashboard, guided wizard, evidence enrichment,
      snapshots, comparison views, fixture library, searchable donor library,
      safe metadata import, and capability matrix are implemented.
- [ ] Tests, documentation, and package verification pass.
- [ ] New-item verification separates automated package evidence from
      user-confirmed runtime observations and multiplayer evidence.
- [ ] Offline collision checks, package diffs, metadata re-import, schema
      validation, previews, reproducibility, security checks, multiple
      new-item fixtures, dry-run simulation, and publication metadata pass.
- [ ] Changes are committed and pushed.
