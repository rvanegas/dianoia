"""Canonicalize formalization symbol names produced by the LLM.

The model uses descriptive semantic names (e.g. ``is_mortal``, ``socrates``)
and the ``core/logic.py`` JSON format.  This module assigns the final
single-letter canonical symbols deterministically:

- Predicates → P, Q, R … (in order of first appearance across all steps)
- Constants  → a, b, c … a–o (in order of first appearance)
- Bound individual variables → x, y, z, u, v, w (per-formula, DFS order)
- Bound predicate variables  → X, Y, Z, U, V, W (per-formula, DFS order)

``ascii`` strings are regenerated from the normalized formula tree rather
than taken from the model.
"""

from __future__ import annotations

import json
import string
from typing import Any

from core.logic import (
    Formula, Predicate, Identity, Connective, ConnectiveType, Quantifier, Modal,
    Variable, Constant, PredicateVariable, Arg,
    from_json, validate_canonical,
)
from schemas.agent_results import FormalizerResult
from core.utils import logger

_PRED_BASE     = ['P','Q','R','S','T','G','H','I','J','K','L','M','N','O']  # 14
_CONST_BASE    = list(string.ascii_lowercase[:6])                            # a–f
_VAR_SEQ       = ['x', 'y', 'z', 'u', 'v', 'w']
_PRED_VAR_SEQ  = ['X', 'Y', 'Z', 'U', 'V', 'W']


def _pred_symbol(i: int) -> str:
    return _PRED_BASE[i % 14] + (str(i // 14) if i >= 14 else "")


def _const_symbol(i: int) -> str:
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
    """Normalize a batch of raw formalization dicts from the LLM."""
    parsed: list[tuple[str, Formula]] = []
    skipped: list[str] = []
    for item in raw_items:
        sym = item["symbol"]
        try:
            tree, _ = json.JSONDecoder().raw_decode(item["json_structure"].strip())
            formula = from_json(tree)
            parsed.append((sym, formula))
        except Exception as exc:
            logger.warning(f"Skipping step {sym!r} — failed to parse json_structure: {exc}")
            skipped.append(sym)

    if skipped and not parsed:
        raise FormalizationNormalizationError(
            f"Failed to parse json_structure for all steps: {skipped}"
        )

    pred_names: list[str] = []
    const_names: list[str] = []
    pred_arities: dict[str, int] = {}
    for _, formula in parsed:
        _collect_pred_names(formula, pred_names)
        _collect_const_names(formula, const_names)
        _collect_pred_arities(formula, pred_arities)

    pred_map  = {name: _pred_symbol(i) for i, name in enumerate(pred_names)}
    const_map = {name: _const_symbol(i) for i, name in enumerate(const_names)}

    result_items = []
    for sym, formula in parsed:
        var_map: dict[str, Arg] = {}
        formula = _alpha_normalize(formula, var_map, [0, 0])
        formula = _substitute(formula, pred_map, const_map)

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
        if isinstance(formula.head, str) and formula.head not in seen:
            seen.append(formula.head)
    elif isinstance(formula, Connective):
        for arg in formula.args:
            _collect_pred_names(arg, seen)
    elif isinstance(formula, (Quantifier, Modal)):
        _collect_pred_names(formula.body, seen)


def _collect_pred_arities(formula: Formula, arities: dict[str, int]) -> None:
    if isinstance(formula, Predicate):
        if isinstance(formula.head, str):
            arities[formula.head] = len(formula.args)
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
    var_map: dict[str, Arg],
    counter: list[int],  # [individual_idx, pred_var_idx]
) -> Formula:
    """Rename bound variables to canonical sequences in DFS quantifier order."""
    if isinstance(formula, Quantifier):
        new_vars = []
        new_var_map = dict(var_map)
        for v in formula.vars:
            if isinstance(v, Variable):
                if counter[0] >= len(_VAR_SEQ):
                    raise ValueError(
                        f"Formula has more than {len(_VAR_SEQ)} bound individual variables"
                    )
                new_name = _VAR_SEQ[counter[0]]
                counter[0] += 1
                new_var_map[v.name] = Variable(new_name)
                new_vars.append(Variable(new_name))
            elif isinstance(v, PredicateVariable):
                if counter[1] >= len(_PRED_VAR_SEQ):
                    raise ValueError(
                        f"Formula has more than {len(_PRED_VAR_SEQ)} bound predicate variables"
                    )
                new_name = _PRED_VAR_SEQ[counter[1]]
                counter[1] += 1
                new_var_map[v.name] = PredicateVariable(new_name)
                new_vars.append(PredicateVariable(new_name))
        var_map = new_var_map
        new_body = _alpha_normalize(formula.body, var_map, counter)
        return Quantifier(quant=formula.quant, vars=new_vars, body=new_body)
    elif isinstance(formula, Predicate):
        new_head = formula.head
        if isinstance(formula.head, PredicateVariable) and formula.head.name in var_map:
            renamed = var_map[formula.head.name]
            if isinstance(renamed, PredicateVariable):
                new_head = renamed
        new_args = [_rename_arg(a, var_map) for a in formula.args]
        return Predicate(head=new_head, args=new_args)
    elif isinstance(formula, Identity):
        return Identity(
            left=_rename_arg(formula.left, var_map),
            right=_rename_arg(formula.right, var_map),
        )
    elif isinstance(formula, Connective):
        return Connective(
            op=formula.op,
            args=[_alpha_normalize(a, var_map, counter) for a in formula.args],
        )
    elif isinstance(formula, Modal):
        return Modal(mod=formula.mod, body=_alpha_normalize(formula.body, var_map, counter))
    return formula


def _rename_arg(arg: Arg, var_map: dict[str, Arg]) -> Arg:
    if isinstance(arg, (Variable, PredicateVariable)) and arg.name in var_map:
        return var_map[arg.name]
    return arg


# ---------------------------------------------------------------------------
# Predicate / constant substitution
# ---------------------------------------------------------------------------

def _substitute(
    formula: Formula,
    pred_map: dict[str, str],
    const_map: dict[str, str],
) -> Formula:
    if isinstance(formula, Predicate):
        if isinstance(formula.head, str):
            new_head = pred_map.get(formula.head, formula.head)
        else:
            new_head = formula.head
        new_args = [_substitute_arg(a, const_map) for a in formula.args]
        return Predicate(head=new_head, args=new_args)
    elif isinstance(formula, Identity):
        return Identity(
            left=_substitute_arg(formula.left, const_map),
            right=_substitute_arg(formula.right, const_map),
        )
    elif isinstance(formula, Connective):
        return Connective(
            op=formula.op,
            args=[_substitute(a, pred_map, const_map) for a in formula.args],
        )
    elif isinstance(formula, Quantifier):
        return Quantifier(
            quant=formula.quant,
            vars=formula.vars,
            body=_substitute(formula.body, pred_map, const_map),
        )
    elif isinstance(formula, Modal):
        return Modal(mod=formula.mod, body=_substitute(formula.body, pred_map, const_map))
    return formula


def _substitute_arg(arg: Arg, const_map: dict[str, str]) -> Arg:
    if isinstance(arg, Constant):
        return Constant(const_map.get(arg.name, arg.name))
    return arg
