# Extraction returns each participant's stances

Decided at noesis's prompt on 2026-11-09, and built the same day (noesis
`planning/decision/2026-11-09-a-channel-s-voices-are-its-members.md`).
noesis extracts one argument from a conversation of several people, a chat
of a channel of The Floor or Claude's account of it, and needs to know which
of them accepts each proposition and which rejects it, so that Roxana's
toggles start where the conversation left them.

- **`POST /argument/extract` takes `participants`**, the names the text uses
  for its people. Without them, extraction is exactly as it was: the same
  prompt, schema and response.
- **With them, each step carries `accepted` and `rejected`**, Roxana's own
  field names. The response schema restricts the names to an enum of the
  participants, and `extract_argument` checks again afterwards: only names it
  was given, each once, and never in both lists, accepted winning. The
  published response is `ExtractedArguments` (`ExtractedStep` extends
  `Step`), so the other routes' `Step` and Roxana's generated types are
  unchanged.
- **One argument that every voice took part in.** A proposition one
  participant rejects stays in it, in the form the participant who asserted
  it gave it. Where participants disagree, the competing propositions are
  kept as separate steps rather than one side being chosen. A participant
  who takes no stance is in neither list, and no stance is inferred that the
  text does not show.
