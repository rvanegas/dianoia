# Extraction returns each participant's stances

Decided 2026-11-09, at noesis's prompt (noesis
`planning/decision/2026-11-09-a-channel-s-voices-are-its-members.md`). noesis extracts one
argument from a conversation of several people, a chat of a channel of The
Floor or Claude's account of it, and needs to know which of them accepts
each proposition and which rejects it, so that Roxana's toggles start where
the conversation left them.

**The contract for `POST /argument/extract`:**

- The request takes `participants`, a list of the names the text uses for
  its people. If it is missing or empty, extraction works as it does now.
- With participants, each returned `Step` carries `accepted` and `rejected`,
  lists of those names (Roxana's own field names). Where the text gives no
  stance, a name is in neither list. Every voice in the conversation takes
  part in the one argument: a proposition one participant rejects is still
  part of it, in the form the person who asserted it gave it.
- The extraction prompt (`services/extraction.py`) asks for stances only
  when participants are given.

noesis sends `participants` and reads the two lists, ignoring them when they
are absent.
