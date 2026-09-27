# Intake — Paseo GUI runtime for Pi on Unraid

Workstream ID: `feature-paseo-gui-runtime`
Kind: `feature`
Branch: `feat/paseo-gui-runtime`
Integration target: `main`
Base: `ca196378bc38d87f5267b870de2c5545905279d4`
State: `complete`

## Operator intent

Establish Paseo as the normal GUI/control surface for Pi on Unraid and design the production runtime around that usage model. The user does not intend to use terminal Pi as the normal interface. Exploration includes deployment shape, native paths/state, Relay access, browser tooling, capabilities/extensions, update/rollback, sessions/workers, recovery and the eventual retirement of the unused standalone Pi bootstrap container.

## Discovery / identity

- No existing Paseo-named workstream or branch was found in `elmakus/pi-unraid`.
- The completed Phase 1 bootstrap workstream is terminal and integrated; this feature does not require parent-only unmerged state.
- This feature is therefore independent and branches from the current `main` integration target.
- Existing `pi-unraid` issue #3 is relevant to repository mutation safety but is not this feature's identity.

## Downstream classification

Path: `brainstorming`
Next route: `brainstorming:paseo-gui-runtime@R1`

Canonical exploratory record:
`brainstorming/PASEO_GUI_RUNTIME.md`

The selected workstream manifest now points `routing.exploratory_scope` to that exact record.

Definition promotion remains user-owned and is not authorized by the original `#feature` directive.
