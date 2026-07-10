"""Audit an argument's graph structure against the structural conditions.

Purely deterministic: connectivity, conclusion structure, and integrity are
graph properties computed exactly, with no LLM involvement — cheap enough to
run synchronously on every edit. Per-proposition language quality (transition
openers, anaphora, ambiguous connectives) is the phrasing evaluator's job and
runs in the background evaluation pipeline instead.

The output is guidance on how to revise the argument, never a revised
argument.
"""

from schemas.audit import AuditFinding, AuditResult
from schemas.step import Step


def _find_cycle_members(steps: list[Step], symbol_set: set[str]) -> list[str]:
    """Return symbols of steps that lie on a justifier cycle, in step order."""
    edges = {s.symbol: [j for j in s.justifiers if j in symbol_set] for s in steps}
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {sym: WHITE for sym in edges}
    on_cycle: set[str] = set()

    def visit(sym: str, stack: list[str]) -> None:
        color[sym] = GRAY
        stack.append(sym)
        for j in edges[sym]:
            if color[j] == GRAY:
                on_cycle.update(stack[stack.index(j):])
            elif color[j] == WHITE:
                visit(j, stack)
        stack.pop()
        color[sym] = BLACK

    for sym in edges:
        if color[sym] == WHITE:
            visit(sym, [])
    return [s.symbol for s in steps if s.symbol in on_cycle]


def audit_argument(steps: list[Step]) -> AuditResult:
    """Deterministic graph checks: connectivity, conclusion structure, integrity."""
    findings: list[AuditFinding] = []
    if not steps:
        return AuditResult(satisfied=True, findings=[])

    symbol_set = {s.symbol for s in steps}
    cited = {j for s in steps for j in s.justifiers}
    final = steps[-1]

    # Integrity: dangling justifier symbols
    dangling = [s.symbol for s in steps
                if any(j not in symbol_set for j in s.justifiers)]
    if dangling:
        findings.append(AuditFinding(
            condition="integrity",
            step_symbols=dangling,
            issue="Some justifiers reference symbols that do not exist in the argument.",
            pointer="Remove or correct the nonexistent justifier symbols.",
        ))

    # Integrity: self-justification
    self_just = [s.symbol for s in steps if s.symbol in s.justifiers]
    if self_just:
        findings.append(AuditFinding(
            condition="integrity",
            step_symbols=self_just,
            issue="Steps cite themselves as justifiers.",
            pointer="Remove the self-reference from each step's justifiers.",
        ))

    # Integrity: cycles
    cycle_members = _find_cycle_members(steps, symbol_set)
    cycle_members = [sym for sym in cycle_members if sym not in self_just]
    if cycle_members:
        findings.append(AuditFinding(
            condition="integrity",
            step_symbols=cycle_members,
            issue="Justifier references form a cycle; no step in it is independently supported.",
            pointer="Break the cycle by removing or redirecting at least one justifier link.",
        ))

    # Connectivity: orphan steps (no justifiers, cited by nothing)
    orphans = [s.symbol for s in steps
               if not s.justifiers and s.symbol not in cited and s is not final]
    if orphans:
        findings.append(AuditFinding(
            condition="connectivity",
            step_symbols=orphans,
            issue="Steps neither justify any other step nor are justified themselves.",
            pointer="Cite each step in the justifiers of the steps it supports, or remove it.",
        ))

    # Conclusion structure: non-final steps that nothing cites (extra sinks)
    extra_sinks = [s.symbol for s in steps
                   if s is not final and s.symbol not in cited and s.justifiers]
    if extra_sinks:
        findings.append(AuditFinding(
            condition="conclusion",
            step_symbols=extra_sinks,
            issue="Non-final steps are cited by nothing, so the argument has more than one terminal conclusion.",
            pointer="Cite each step in the justifiers of a later step so all chains converge on the final step, or reorder so the true conclusion comes last.",
        ))

    # Conclusion structure: steps with no transitive path to the final step
    supports_final = {final.symbol}
    frontier = [final.symbol]
    by_symbol = {s.symbol: s for s in steps}
    while frontier:
        current = by_symbol[frontier.pop()]
        for j in current.justifiers:
            if j in symbol_set and j not in supports_final:
                supports_final.add(j)
                frontier.append(j)
    already_flagged = set(orphans) | set(extra_sinks)
    unreachable = [s.symbol for s in steps
                   if s.symbol not in supports_final and s.symbol not in already_flagged]
    if unreachable:
        findings.append(AuditFinding(
            condition="conclusion",
            step_symbols=unreachable,
            issue="Steps do not support the final step through any chain of justifiers.",
            pointer="Connect each step, directly or through intermediate steps, to the final step's justifier chain, or remove it.",
        ))

    return AuditResult(satisfied=not findings, findings=findings)
