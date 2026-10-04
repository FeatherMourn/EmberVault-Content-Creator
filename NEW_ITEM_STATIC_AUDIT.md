# New-Item Armchair Static Audit

## Result

The generated package is structurally a new-model package, not a vanilla
RenderModel replacement. It was audited offline only; no game execution or
runtime behavior is claimed.

## Confirmed from generated metadata

- `new_model` is true.
- The package contains a new item name and description.
- Base item and base template references are present.
- The target RenderModel GUID is present.
- The export uses full topology with one material range.
- The package contains `mod.json`, `render_data.bin`, `validation.json`, and
  `src/mod.lua`.
- The replacement comparison package has `new_model` false and no base-item or
  base-template references.

## Confirmed from generated Lua

- A new RenderModel resource is created from the selected source resource.
- A new TemplateResource is cloned and added to its template registry.
- A new ItemInfo resource is cloned from the base item.
- The new item receives a generated identity, name, caption, and description.
- The new item points to the cloned template and generated RenderModel.
- The item registry is extended with the new item.
- A recipe registry is cloned, a recipe is appended, and its output is rebound
  to the new item.
- The recipe receives a new recipe identity and explicit knowledge settings.
- The script includes failure checks for missing resources and registry links.

## Gaps and warnings

- The validation metadata reports no custom icon. The Lua attempts to clone the
  base icon only when the source icon exists; actual icon visibility is not
  proven offline.
- The generated package selects the first recipe that outputs the base item.
  The chosen recipe and ingredients need runtime confirmation.
- The package has no collider or effect-anchor patches.
- Registry rebinding, item visibility, recipe visibility, crafting, placement,
  persistence, rollback, and multiplayer behavior remain unverified.
- The package is staged in an isolated workspace only. It has not been run in
  the game.

## Conclusion

The package is ready for a later isolated runtime test. Static evidence supports
the claim that it attempts new item, template, RenderModel, and recipe
registration. Static evidence does not prove that the game accepts or exposes
those resources at runtime.
