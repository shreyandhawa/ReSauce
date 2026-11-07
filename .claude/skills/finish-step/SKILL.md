---
name: finish-step
description: Close out a completed ReSauce milestone step - run tests, update docs/handoff.md, commit only the step's files without AI attribution, push, and show raw git output. Only when the user types /finish-step.
disable-model-invocation: true
argument-hint: "[commit message]"
---

Close out the current ReSauce step. Follow CLAUDE.md. Explain each action in plain language; the user is a beginner.

1. Run `.venv/bin/python -m pytest -p no:cacheprovider -v`. Show the raw summary line. If any test fails, stop and report the failure. Do not commit.
2. Run `git status --short`. List every changed or untracked file and say which belong to this step. If you are unsure about any file, ask the user before continuing. Never commit `.env` files, `.claude/settings.local.json`, `.venv/` or caches.
3. If docs/handoff.md has no entry for this step yet, add one at the top with: Status, Done, Decisions & why, Next steps, Open questions, How to verify.
4. Stage only this step's files, by explicit path. Never use `git add -A` or `git add .`.
5. Commit with this message: $ARGUMENTS
   If no message was given, propose one and wait for the user's approval.
   Do not add "Co-Authored-By" or any other AI attribution lines.
6. Run `git push`.
7. After pushing, show the raw output of `git push`, then `git status`, then `git log --oneline -3`.
8. Tell the user what was committed, and that they can now tell the reviewing assistant "pushed".
