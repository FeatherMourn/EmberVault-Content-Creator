# Content Creator Handoff

Content Creator is a design-only authoring module. It creates project records,
reviews offline donor, recipe, Blender, and package evidence, and prepares
sanitized exports. It does not install packages, modify live game files, or
claim runtime behavior.

## Evidence boundary

- `observed`, `partial`, `contradicted`, and `unknown` evidence states remain
  visible in review surfaces.
- Partial or contradictory evidence keeps export readiness blocked.
- Donor and recipe records identify their offline source and remain runtime
  unverified.
- Public records contain review state and compatibility summaries, not private
  evidence paths or research notes.

## Consumers

- Mod Research is the evidence authority.
- Control Center may launch and review Content Creator through its approved
  module boundary.
- Web Catalog receives sanitized, design-only publication records.

## Verification

Run the unit suite and the offscreen UI smoke check before handoff. Build a
wheel and install it into an isolated target for packaging verification. Never
use a live game directory or real runtime test as a substitute for recorded
evidence.
