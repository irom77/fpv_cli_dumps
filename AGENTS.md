# Agent Instructions

Proceed directly with repository tasks without invoking any `superpowers:*` skills. Use a Superpowers skill only when the user explicitly requests that specific skill.

Before creating new scripts, tooling, or workflows, inspect `.claude/skills/` (`/home/irom/fpv_cli_dumps/.claude/skills`) for existing solutions. Read the relevant `SKILL.md` files and actively reuse applicable skills and their supporting tools.

Improve these skills iteratively as part of the work: when a task reveals a gap, bug, or edge case, update or extend the relevant existing skill and tooling before creating a separate solution. Validate changes against the case that exposed the issue and record reusable guidance in the skill.

Keep skill definitions, documentation, examples, and any packaged copies aligned with current tooling and actual usage. When behavior or invocation changes, update the corresponding instructions in the same change.
