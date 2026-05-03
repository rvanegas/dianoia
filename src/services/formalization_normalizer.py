"""Canonicalize formalization symbol names produced by the LLM.

The model uses descriptive semantic names (e.g. ``is_mortal``, ``socrates``)
and the ``core/logic.py`` JSON format.  This module assigns the final
single-letter canonical symbols deterministically:

- Predicates → P, Q, R … (in order of first appearance across all steps)
- Constants  → a, b, c … a–o (in order of first appearance)
- Bound variables → x, y, z, u, v, w (per-formula, in DFS quantifier order)

``ascii`` strings are regenerated from the normalized formula tree rather
than taken from the model.
"""

from __future__ import annotations

import json
import string
from typing import Any

from core.logic import (
    Formula, Predicate, Identity, Connective, ConnectiveType, Quantifier, Modal,
    Term, Variable, Constant,
    from_json, validate_canonical,
)
from schemas.agent_results import FormalizerResult

_PRED_BASE = ['P','Q','R','S','T','G','H','I','J','K','L','M','N','O']  # G–T, starting at P (14)
_CONST_BASE = list(string.ascii_lowercase[:6])                          # a–f (6)
_VAR_SEQ = ['x', 'y', 'z', 'u', 'v', 'w']                             # u–z, starting at x (6)


def _pred_symbol(i: int) -> str:
    """P…T,G…O for i<14; P1… etc."""
    return _PRED_BASE[i % 14] + (str(i // 14) if i >= 14 else "")


def _const_symbol(i: int) -> str:
    """a…f for i<6; a1…f1 for i<12; a2… etc."""
    return _CONST_BASE[i % 6] + (str(i // 6) if i >= 6 else "")


class FormalizationNormalizationError(Exception):
    pass


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def normalize_formalizations(
    raw_items: list[dict],
    confidence: float,
    reasoning: str,
) -> FormalizerResult:
    """Normalize a batch of raw formalization dicts from the LLM.

    Each item in *raw_items* is ``{symbol, ascii, json_structure}`` where
    ``json_structure`` is a JSON string in ``core/logic.py`` format with
    semantic (multi-character) predicate/constant names.

    Returns a complete ``FormalizerResult`` with canonical symbols and
    Python-generated ``ascii`` strings.
    """
    # --- parse ---
    parsed: list[tuple[str, Formula]] = []
    for item in raw_items:
        sym = item["symbol"]
        try:
            tree, _ = json.JSONDecoder().raw_decode(item["json_structure"].strip())
            formula = from_json(tree)
        except Exception as exc:
            raise FormalizationNormalizationError(
                f"Failed to parse json_structure for step {sym!r}: {exc}"
            ) from exc
        parsed.append((sym, formula))

    # --- collect names and arities (cross-step) ---
    pred_names: list[str] = []
    const_names: list[str] = []
    pred_arities: dict[str, int] = {}
    for _, formula in parsed:
        _collect_pred_names(formula, pred_names)
        _collect_const_names(formula, const_names)
        _collect_pred_arities(formula, pred_arities)

    # --- build canonical maps ---
    pred_map = {name: _pred_symbol(i) for i, name in enumerate(pred_names)}
    const_map = {name: _const_symbol(i) for i, name in enumerate(const_names)}

    # --- normalize each formula ---
    result_items = []
    for sym, formula in parsed:
        # alpha-normalize bound variables first (per-formula)
        var_map: dict[str, str] = {}
        formula = _alpha_normalize(formula, var_map, [0])

        # substitute canonical predicate and constant names
        formula = _substitute(formula, pred_map, const_map)

        # validate
        try:
            validate_canonical(formula)
        except ValueError as exc:
            raise FormalizationNormalizationError(
                f"Canonical validation failed for step {sym!r}: {exc}"
            ) from exc

        result_items.append({
            "symbol": sym,
            "ascii": formula.to_ascii(),
            "json_structure": json.dumps(formula.to_dict()),
        })

    definitions: dict = {
        "predicates": [{"symbol": v, "value": k, "arity": pred_arities.get(k, 0)} for k, v in pred_map.items() if k != v],
        "constants":  [{"symbol": v, "value": k} for k, v in const_map.items() if k != v],
    }

    return {
        "formalizations": result_items,
        "definitions": definitions,
        "confidence": confidence,
        "reasoning": reasoning,
    }


# ---------------------------------------------------------------------------
# Name collection (DFS, first-appearance order)
# ---------------------------------------------------------------------------

def _collect_pred_names(formula: Formula, seen: list[str]) -> None:
    if isinstance(formula, Predicate):
        if formula.name not in seen:
            seen.append(formula.name)
    elif isinstance(formula, Connective):
        for arg in formula.args:
            _collect_pred_names(arg, seen)
    elif isinstance(formula, (Quantifier, Modal)):
        _collect_pred_names(formula.body, seen)
    # Identity: no predicates


def _collect_pred_arities(formula: Formula, arities: dict[str, int]) -> None:
    if isinstance(formula, Predicate):
        arities[formula.name] = len(formula.args)
    elif isinstance(formula, Connective):
        for arg in formula.args:
            _collect_pred_arities(arg, arities)
    elif isinstance(formula, (Quantifier, Modal)):
        _collect_pred_arities(formula.body, arities)


def _collect_const_names(formula: Formula, seen: list[str]) -> None:
    if isinstance(formula, Predicate):
        for arg in formula.args:
            if isinstance(arg, Constant) and arg.name not in seen:
                seen.append(arg.name)
    elif isinstance(formula, Identity):
        for t in (formula.left, formula.right):
            if isinstance(t, Constant) and t.name not in seen:
                seen.append(t.name)
    elif isinstance(formula, Connective):
        for arg in formula.args:
            _collect_const_names(arg, seen)
    elif isinstance(formula, (Quantifier, Modal)):
        _collect_const_names(formula.body, seen)


# ---------------------------------------------------------------------------
# Alpha-normalization (per-formula bound variable renaming)
# ---------------------------------------------------------------------------

def _alpha_normalize(
    formula: Formula,
    var_map: dict[str, str],
    counter: list[int],  # mutable single-element list used as a counter
) -> Formula:
    """Rename bound variables to x, y, z, u, v, w in DFS quantifier order."""
    if isinstance(formula, Quantifier):
        if counter[0] >= len(_VAR_SEQ):
            raise ValueError(
                f"Formula has more than {len(_VAR_SEQ)} nested quantifiers"
            )
        new_var_name = _VAR_SEQ[counter[0]]
        counter[0] += 1
        old_name = formula.var.name
        var_map = {**var_map, old_name: new_var_name}
        new_body = _alpha_normalize(formula.body, var_map, counter)
        return Quantifier(quant=formula.quant, var=Variable(new_var_name), body=new_body)
    elif isinstance(formula, Predicate):
        new_args = [_rename_term(a, var_map) for a in formula.args]
        return Predicate(name=formula.name, args=new_args)
    elif isinstance(formula, Identity):
        return Identity(
            left=_rename_term(formula.left, var_map),
            right=_rename_term(formula.right, var_map),
        )
    elif isinstance(formula, Connective):
        return Connective(
            op=formula.op,
            args=[_alpha_normalize(a, var_map, counter) for a in formula.args],
        )
    elif isinstance(formula, Modal):
        return Modal(mod=formula.mod, body=_alpha_normalize(formula.body, var_map, counter))
    return formula


def _rename_term(term: Term, var_map: dict[str, str]) -> Term:
    if isinstance(term, Variable) and term.name in var_map:
        return Variable(var_map[term.name])
    return term


# ---------------------------------------------------------------------------
# Predicate / constant substitution
# ---------------------------------------------------------------------------

def _substitute(
    formula: Formula,
    pred_map: dict[str, str],
    const_map: dict[str, str],
) -> Formula:
    if isinstance(formula, Predicate):
        new_name = pred_map.get(formula.name, formula.name)
        new_args = [_substitute_term(a, const_map) for a in formula.args]
        return Predicate(name=new_name, args=new_args)
    elif isinstance(formula, Identity):
        return Identity(
            left=_substitute_term(formula.left, const_map),
            right=_substitute_term(formula.right, const_map),
        )
    elif isinstance(formula, Connective):
        return Connective(
            op=formula.op,
            args=[_substitute(a, pred_map, const_map) for a in formula.args],
        )
    elif isinstance(formula, Quantifier):
        return Quantifier(
            quant=formula.quant,
            var=formula.var,
            body=_substitute(formula.body, pred_map, const_map),
        )
    elif isinstance(formula, Modal):
        return Modal(mod=formula.mod, body=_substitute(formula.body, pred_map, const_map))
    return formula


def _substitute_term(term: Term, const_map: dict[str, str]) -> Term:
    if isinstance(term, Constant):
        return Constant(const_map.get(term.name, term.name))
    return term
