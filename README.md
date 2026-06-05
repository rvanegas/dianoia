# Dianoia — An Argument Clinic

**Multi-agent argument analysis backend**
Python · FastAPI · Anthropic API

---

## What it is

Dianoia is a backend service for extracting, formalizing, and evaluating arguments from free-form text. Given a piece of argumentative prose, it returns a structured sequence of propositions with assessments of each step's content validity, formal validity, and logical strength — along with suggestions for improvement.

It is the analytical engine underlying [mdc](https://github.com/rvanegas/mdc) and [Noesis](https://github.com/rvanegas/noesis).

---

## Why it exists

Most argument analysis tools either stay at the level of informal critique or require users to manually formalize arguments before evaluation. Dianoia automates the formalization step while preserving the distinction between content validity ("would this follow if the premises were true?") and formal validity ("does the logical form itself support the inference?") — a distinction that turns out to matter considerably when working with language models.

---

## Architecture

Four specialized agents run as daemon threads, each receiving only the fields relevant to its task:

- **Content Evaluator** — assesses whether each proposition is plausible and whether each inferential step is content-valid
- **Formalizer** — extracts logical form from natural language propositions, producing a structured AST
- **Formal Evaluator** — evaluates validity at the level of logical form, independent of content
- **Improvement Generator** — suggests revisions to weak or invalid steps

Results are snapshot-bound: each agent operates on the argument state that triggered it, preventing stale or interleaved evaluations.

A two-pass formalization normalizer assigns canonical single-letter symbols across all argument steps, ensuring consistent variable naming throughout a multi-step argument.

---

## The logic layer

The formal representation uses a full modal first-order logic AST implemented as immutable Python dataclasses. The type hierarchy covers:

- Atomic propositions, predicates, quantifiers (universal, existential)
- Modal operators (necessity, possibility)
- Connectives (conjunction, disjunction, negation, implication, biconditional)

This is not a wrapper around an existing logic library — it is a ground-up implementation motivated by the specific requirements of natural language argument formalization.

---

## A research finding

Building and running Dianoia produced an empirical result worth noting:

Language models can extract logical form correctly. They can evaluate formal validity correctly when presented with pure logical form. But when asked to perform both operations together — evaluating validity of a formalized argument while the original natural language content is still present — performance degrades significantly, even with explicit instructions to focus on form.

The fix: a two-context architecture that extracts form in one agent call and evaluates in a separate call with the content removed. This works reliably.

The implication: semantic and formal processing in current language models are architecturally entangled rather than modular. The model cannot cleanly suppress content-driven associations when performing formal operations, even when instructed to. Architectural separation compensates where instructional separation fails.

---

## Name

In Platonic epistemology, *dianoia* is discursive reasoning — the analytical, step-by-step working through of an argument. That is what the server does. *Noesis* is direct intellectual intuition — the immediate grasp of the whole. That is closer to what a user interface affords: seeing the argument as a unified thing.

---

## Related projects

- [mdc](https://github.com/rvanegas/mdc) — terminal LLM research platform that uses Dianoia for argument analysis
- [Noesis](https://github.com/rvanegas/noesis) — React frontend for interactive argument evaluation via Dianoia
