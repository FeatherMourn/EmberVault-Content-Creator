# EmberVault Content Creator

The standalone EmberVault Content Creator application is the design workspace for furniture and future content types. It has its own identity and project model; Control Center will launch and bridge to it later.

## Current foundation

- Standalone Qt application entry point in `src/app.py`.
- Furniture project model with validation and design-only manifest export.
- Tested bed workflow as the first furniture template.
- No live game files are modified.

Run the application with `python -m src.app` after installing PySide6. Use `--smoke-test` for a headless startup check.
