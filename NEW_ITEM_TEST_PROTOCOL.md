# Controlled New-Item Verification Protocol

## Current fixture

- Content: Ember Vault Medieval Armchair
- Workflow: `NEW_MODEL`
- Target RenderModel: `global_props_roughwood_chair_01_a`
- Base item and template: recorded in `validation.json`
- Package state: generated and validated offline
- Live installation: not performed

## Automated preflight

- [x] Preserve the original Blender source.
- [x] Preserve the original game installation and save directory.
- [x] Load the current KFC3 resources through the installed Blender extension.
- [x] Generate a new-model package in a temporary output directory.
- [x] Confirm `new_model` is true and the base GUIDs are present.
- [x] Hash `mod.json`, `render_data.bin`, `validation.json`, and `src/mod.lua`.
- [x] Copy the current saves into a separate rollback backup.
- [x] Keep replacement and new-model packages separate.

## Runtime evidence gates

These remain unverified until a user-authorized isolated installation and direct
observation are completed.

- [ ] Independent item registration
- [ ] Recipe visibility
- [ ] Crafting or acquisition
- [ ] Item name and icon
- [ ] Model visuals
- [ ] Placement and interaction
- [ ] Save and reload persistence
- [ ] Removal and rollback
- [ ] Multiplayer behavior

## Safety rules

- Install only into the isolated test environment.
- Do not overwrite the original Blender source or live saves.
- Record the exact package hash before installation.
- Stop if the package targets the vanilla item instead of creating a new item.
- Restore the copied save set after testing and document the result.
- Do not promote any behavior to verified without reproducible evidence.
