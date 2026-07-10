"""Structural conditions every extracted argument must satisfy.

Shared by the extraction prompt (generation time), the deterministic argument
auditor (edit time), and the phrasing evaluator so they never drift.
"""

CONNECTIVITY = """\
1. **Connectivity.** Every proposition must take part in an inference: it must
   appear in some later step's `justifiers`, or itself have justifiers (or
   both). Background, framing, or attribution statements that support nothing
   downstream do not belong in the argument — either they are omitted, or, if
   the claim genuinely underwrites later steps, it is cited in their
   `justifiers`."""

ORDER_INDEPENDENCE = """\
2. **Order-independence.** Each proposition must be fully legible on its own,
   read in any order. A proposition must never begin with an inferential
   transition ("Therefore", "Thus", "Hence", "So", "Because of this") and must
   never use anaphora that points at another step ("this", "these", "such a
   view", "the above"). Any needed referent is restated explicitly within the
   proposition. Logical dependency is expressed exclusively through
   `justifiers`, never through wording."""

CONCLUSION_LEGIBILITY = """\
3. **Conclusion legibility.** The final step must state the argument's
   substantive conclusion — the claim itself, not a summary or a remark about
   the source text — and must be readable, standing alone, as the conclusion
   of the entire set. Every other step must support it, directly or
   transitively."""

STRUCTURAL_CONDITIONS = "\n\n".join(
    [CONNECTIVITY, ORDER_INDEPENDENCE, CONCLUSION_LEGIBILITY]
)
