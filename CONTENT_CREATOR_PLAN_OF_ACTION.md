# Content Creator 2.0 — Plan of Action

## Objective

Build a design-only content workspace that turns donor research, Blender Tools
work, and verification evidence into reviewable, sanitized content packages.

## Phase 1 — Establish the project foundation

1. Define stable project identifiers and project file layout.
2. Add create, save, open, and version checks.
3. Preserve unknown fields during upgrades where safe.
4. Reject corrupted, incompatible, or unsafe project files.

**Gate:** A project can be created, reopened, validated, and exported without
touching the live game.

## Phase 2 — Build structured authoring

1. Support furniture first, using the proven bed workflow as the fixture.
2. Add dimensions, materials, asset references, donor item, and donor recipe.
3. Keep buildings, recipes, and other content types extensible but explicit.
4. Reject path escapes, invalid dimensions, and incomplete identity fields.

**Gate:** A valid furniture project produces a deterministic internal manifest.

## Phase 3 — Envelop external Blender Tools research

1. Record tool repository, version, Blender version, and game build.
2. Record source RenderModel GUIDs, donor resources, and generated package files.
3. Validate generated package paths and expected files without installing them.
4. Preserve Blender/static evidence separately from runtime evidence.

**Gate:** A Blender handoff is reproducible and clearly labeled as static,
experimental, or runtime-verified.

## Phase 4 — Evidence and review

1. Attach evidence records to each project decision.
2. Track registration, visuals, UI linkage, placement, persistence, and
   multiplayer independently.
3. Surface contradictions, missing evidence, and open questions.
4. Require review before an export is marked ready.

**Gate:** No unsupported runtime claim can be promoted by export.

## Phase 5 — Export and Control Center integration

1. Validate against the shared Content Project Export contract.
2. Sanitize public-facing fields and preserve provenance.
3. Return versioned Module SDK results with evidence and recovery references.
4. Integrate project operations into Control Center without live mutation.

**Gate:** Control Center can discover, validate, review, and recover a project
operation while keeping the live game untouched.

## Phase 6 — First complete fixture

1. Complete the bed workflow from project creation through export.
2. Compare output with the documented Blender Tools package shape.
3. Run offline package, schema, and provenance validation.
4. Conduct controlled runtime testing only after the offline gate passes.

**Gate:** The bed fixture has an auditable package and explicit verified versus
unknown results.

## Operating rule

Every research action must record its source, game build, tool version, result,
limitations, and next question. Static or simulated success must never be
reported as proof of live-game behavior.
