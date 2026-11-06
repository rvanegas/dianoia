# Planning

Everything about Dianoia that is not code and not the agent instructions
(`AGENTS.md`), laid out as technosophia's `PLANNING.md` says. Each directory
holds items, one file each; its `README.md` is its convention.

- **`task/`**: the roadmap. Features, audits, open questions.
- **`backlog/`**: what is known and not done.
- **`decision/`**: what was built and why, one dated file per decision;
  `decision/archive/` holds the old `notes/`.

The standing documents at this level:

- **`DOCKER_ARCH.md`**: how Dianoia runs on the `commons` box, its config and
  health, and deploying. Read before changing any of them.

`LOGIC-ASCII.md` and `LOGIC-JSON.md` stay at the repository root: they are
not planning but inputs, copied into the image and read into the agents'
prompts (`src/services/agent_prompts.py`).
