---
description: Agentic Documentation of Git Changes
---

# Workflow: doc-history

**Role:** You are the Lead Documentation Architect.

**Task:** 1. Use the terminal to run `git log --reverse` to extract the full commit history of this repository. 2. Divide the total commits into chronological chunks (e.g., 50 commits per chunk). 3. **Orchestrate:** Switch to the Agent Manager surface and spawn a separate sub-agent for each chunk. 4. **Sub-Agent Instructions:** Instruct each sub-agent to read the diffs for their assigned commit hashes, analyze the architectural changes, and generate an Artifact (a markdown file named `chunk_X_history.md`). 5. **Compile:** Once all sub-agents have reported back with their completed Artifacts, synthesize their markdown files into a single, comprehensive `PROJECT_ARCHITECTURE.md` document. Clean up by deleting the temporary chunk files.
