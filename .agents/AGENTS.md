# Project Rules & Customizations

This file outlines project-specific rules, style guidelines, and mandatory workflows for developers and AI agents working on this project.

## Mandatory Developer & Agent Workflow

Whenever starting a new task or resuming work on this codebase, you must follow these steps:

1. **Look at [docs/index.html](file:///home/vaibhavshah/Code/price_tracker_agent/docs/index.html)** first for reference and high-level project status.
2. **Get more, precise context** by inspecting the actual implementation files.
3. **Plan the changes** carefully before editing code (if in planning mode).
4. **Implement the changes required** in a new branch (prefer prefix `feature/`).
5. **Update [docs/index.html](file:///home/vaibhavshah/Code/price_tracker_agent/docs/index.html)** to keep the documentation fully synchronized with the changes, including:
   - Version history and changelog.
   - Known issues and bugs resolved.
   - Data model and codebase structure updates.
6. **Create a Pull Request (PR)** from the new branch into the `main` branch.

## Code Style & Architectural Decisions

- **Single Responsibility & Open/Closed Principles**:
  - Encapsulate distinct capabilities in their own service classes inheriting from `BaseService`.
  - Intent classification and routing reside solely inside the `Orchestrator` singleton.
- **ACID-Compliant Transactions**:
  - Always wrap database writes in try/except blocks and handle transactions cleanly in the service layer using repository functions.
- **No Mid-File Imports**:
  - Keep imports at the top of python files unless absolutely necessary to prevent circular dependencies.
- **Port Isolation**:
  - The OpenClaw gateway operates on internal Docker networks only (port `18789`). External communication must route through the web service or standard channels.
