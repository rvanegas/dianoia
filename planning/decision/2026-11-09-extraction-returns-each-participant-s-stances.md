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

## Inferences too

Added later on 2026-11-09, at noesis's prompt. A step with justifiers is also
an inference, and Roxana keeps stances on arguments as it does on
propositions. A participant may accept that a conclusion follows while
rejecting a premise, or reject the inference while accepting every
proposition in it. So each step also carries `inference_accepted` and
`inference_rejected`, with the same rules, and both are empty for a step with
no justifiers.

## Content, not attribution

Found on 2026-11-09 in Roxana discussion 5e48, exported from a channel's
chat: steps came out as "Rodrigo holds that a belief is irrational only if…"
and "Daniel Jensen holds that…". Both participants accept such reports, so the
stances fell on the attribution while the disagreement, which was about the
content, vanished. The prompt now says a proposition states content and never
who holds it, the stance lists saying that; the same goes for a text that is
itself a report naming who thinks what, as a channel's document is.

Not enough, found the same day in discussion d4r4, extracted again under that
rule: "holds that" was gone, but "Rodrigo's rationality standard would
permit…", "Rodrigo himself judged flat-earth belief stupid…" and "Rodrigo's own
evaluative practice applies…" carried the attribution instead. So a
proposition now never names a participant: a standard is written by what it
says, and an argument from a participant's own judgments or practice becomes
the general proposition they express, accepted by that participant, where the
inconsistency it points at shows in their stances. noesis's `argue` warns of
any proposition that still names one.
