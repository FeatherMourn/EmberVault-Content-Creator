# EmberVault Content Creator Roadmap

## Purpose

Create evidence-aware, design-only content projects for furniture, buildings,
recipes, assets, and future content types.

## Scope

Included: project authoring, donors, asset references, evidence, previews,
validation, and export packages.

Excluded: direct live game mutation, unverified runtime claims, and automatic
promotion of research into working game content.

## Dependencies

- EmberVault-Contracts: project and export schemas.
- EmberVault-Module-SDK: module boundary.
- Control Center: profiles, operations, evidence, and recovery context.
- Mod Research: donor and verification evidence.

## Milestones

### Foundation — completed

1. [x] Consume the shared Module SDK.
2. [x] Add the canonical Content Project Export contract to EmberVault Contracts.
3. [x] Identify exports with the canonical schema and package the contract in
   Control Center.
4. [x] Establish the design-only boundary and bed donor workflow foundation.

### Content Creator 2.0 — active build sequence

5. [ ] Create and open projects with deterministic project identifiers.
6. [ ] Build structured authoring for furniture, buildings, recipes, and assets.
7. [ ] Add donor, recipe, resource, and asset-reference selection with path
   safety validation.
8. [ ] Add evidence records, verification-state editing, and open-question
   tracking.
9. [ ] Add deterministic previews and a clear separation between design data,
   runtime plans, and unsupported claims.
10. [ ] Validate project exports against the shared Content Project Export
    contract and sanitize public-facing fields.
11. [ ] Add save/load persistence with corruption and incompatible-version
    handling.
12. [ ] Connect the standalone project model to the Control Center module
    lifecycle without allowing live-game mutation.
13. [ ] Build the first complete bed workflow from authoring through export,
    including registration evidence and unresolved visual/runtime questions.
14. [ ] Add end-to-end tests, clean-install packaging checks, documentation,
    and GitHub backup.

### Later promotion work

15. [ ] Publish only sanitized, review-approved exports to EmberVault Web.
16. [ ] Add runtime adapters only when current-build evidence proves behavior,
    persistence, multiplayer impact, and rollback.

## Definition of done

- [x] Design-only boundary is enforced.
- [x] Registration, visuals, UI linkage, placement, persistence, and
      multiplayer states are distinct.
- [x] Incomplete or contradictory evidence is surfaced.
- [x] Export packages identify and target the shared schema.
- [ ] Export packages are schema-validated and sanitized in the application.
- [ ] Projects persist safely across saves, loads, and version changes.
- [ ] Control Center lifecycle integration is verified.
- [ ] Tests, documentation, and package verification pass.
- [ ] Changes are committed and pushed.
