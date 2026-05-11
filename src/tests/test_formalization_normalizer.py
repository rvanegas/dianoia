"""Tests for services/formalization_normalizer.py"""

import json
import pytest

from core.logic import (
    Predicate, Constant, Variable, Quantifier, QuantifierType,
    Connective, ConnectiveType, from_json, validate_canonical,
)
from services.formalization_normalizer import (
    normalize_formalizations,
    FormalizationNormalizationError,
)


def _js(formula) -> str:
    return json.dumps(formula.to_dict())


def _item(symbol, formula):
    return {"symbol": symbol, "ascii": formula.to_ascii(), "json_structure": _js(formula)}


# ---------------------------------------------------------------------------
# Basic predicate mapping
# ---------------------------------------------------------------------------

def test_single_predicate_and_constant():
    # is_man(socrates) → P(a)
    formula = Predicate("is_man", [Constant("socrates")])
    result = normalize_formalizations([_item("A", formula)], confidence=0.9, reasoning="")
    fmls = result["formalizations"]
    assert len(fmls) == 1
    assert fmls[0]["symbol"] == "A"
    assert fmls[0]["ascii"] == "Pa"
    defs = result["definitions"]
    assert {"symbol": "P", "value": "is_man", "arity": 1} in defs["predicates"]
    assert {"symbol": "a", "value": "socrates"} in defs["constants"]


def test_two_predicates_ordered():
    # is_man(socrates), is_mortal(socrates) → P(a), Q(a)
    f1 = Predicate("is_man", [Constant("socrates")])
    f2 = Predicate("is_mortal", [Constant("socrates")])
    result = normalize_formalizations(
        [_item("A", f1), _item("B", f2)], confidence=1.0, reasoning=""
    )
    fmls = {f["symbol"]: f["ascii"] for f in result["formalizations"]}
    assert fmls["A"] == "Pa"
    assert fmls["B"] == "Qa"


# ---------------------------------------------------------------------------
# Cross-step consistency
# ---------------------------------------------------------------------------

def test_shared_predicate_gets_same_symbol():
    # is_mortal appears in both steps → both get Q (second unique predicate)
    f1 = Predicate("is_man", [Constant("socrates")])
    f2 = Predicate("is_mortal", [Constant("socrates")])
    f3 = Connective(
        op=ConnectiveType.AND,
        args=[Predicate("is_man", [Constant("socrates")]), Predicate("is_mortal", [Constant("socrates")])],
    )
    result = normalize_formalizations(
        [_item("A", f1), _item("B", f2), _item("C", f3)],
        confidence=1.0, reasoning=""
    )
    fmls = {f["symbol"]: f["ascii"] for f in result["formalizations"]}
    assert fmls["A"] == "Pa"
    assert fmls["B"] == "Qa"
    assert fmls["C"] == "Pa and Qa"


# ---------------------------------------------------------------------------
# Zero-argument predicates (replaces PropVar)
# ---------------------------------------------------------------------------

def test_zero_arg_predicate():
    formula = Predicate("is_raining", [])
    result = normalize_formalizations([_item("A", formula)], confidence=0.8, reasoning="")
    assert result["formalizations"][0]["ascii"] == "P"
    assert {"symbol": "P", "value": "is_raining", "arity": 0} in result["definitions"]["predicates"]
    assert result["definitions"]["constants"] == []


# ---------------------------------------------------------------------------
# Alpha-normalization of bound variables
# ---------------------------------------------------------------------------

def test_bound_variable_normalized_to_x():
    # forall individual. is_man(individual) → forall x. Px
    formula = Quantifier(
        quant=QuantifierType.FORALL,
        vars=[Variable("individual")],
        body=Predicate("is_man", [Variable("individual")]),
    )
    result = normalize_formalizations([_item("A", formula)], confidence=1.0, reasoning="")
    assert result["formalizations"][0]["ascii"] == "forall x. Px"


def test_nested_quantifiers_get_x_then_y():
    # forall entity. exists thing. Rxy
    inner = Quantifier(
        quant=QuantifierType.EXISTS,
        vars=[Variable("thing")],
        body=Predicate("rel", [Variable("entity"), Variable("thing")]),
    )
    outer = Quantifier(
        quant=QuantifierType.FORALL,
        vars=[Variable("entity")],
        body=inner,
    )
    result = normalize_formalizations([_item("A", outer)], confidence=1.0, reasoning="")
    ascii_out = result["formalizations"][0]["ascii"]
    assert "forall x." in ascii_out
    assert "exists y." in ascii_out


def test_independent_formulas_both_start_at_x():
    f1 = Quantifier(
        quant=QuantifierType.FORALL,
        vars=[Variable("individual")],
        body=Predicate("is_man", [Variable("individual")]),
    )
    f2 = Quantifier(
        quant=QuantifierType.FORALL,
        vars=[Variable("entity")],
        body=Predicate("is_mortal", [Variable("entity")]),
    )
    result = normalize_formalizations([_item("A", f1), _item("B", f2)], confidence=1.0, reasoning="")
    fmls = {f["symbol"]: f["ascii"] for f in result["formalizations"]}
    assert fmls["A"] == "forall x. Px"
    assert fmls["B"] == "forall x. Qx"


# ---------------------------------------------------------------------------
# Definitions accuracy
# ---------------------------------------------------------------------------

def test_definitions_completeness():
    f1 = Predicate("is_man", [Constant("socrates")])
    f2 = Predicate("is_mortal", [Constant("plato")])
    result = normalize_formalizations([_item("A", f1), _item("B", f2)], confidence=1.0, reasoning="")
    pred_syms = {d["value"]: d["symbol"] for d in result["definitions"]["predicates"]}
    const_syms = {d["value"]: d["symbol"] for d in result["definitions"]["constants"]}
    assert pred_syms == {"is_man": "P", "is_mortal": "Q"}
    assert const_syms == {"socrates": "a", "plato": "b"}


# ---------------------------------------------------------------------------
# ascii is Python-generated
# ---------------------------------------------------------------------------

def test_ascii_matches_to_ascii():
    formula = Connective(
        op=ConnectiveType.IMPLIES,
        args=[Predicate("is_man", [Constant("socrates")]), Predicate("is_mortal", [Constant("socrates")])],
    )
    result = normalize_formalizations([_item("A", formula)], confidence=1.0, reasoning="")
    out = result["formalizations"][0]
    parsed_back = from_json(json.loads(out["json_structure"]))
    assert out["ascii"] == parsed_back.to_ascii()


# ---------------------------------------------------------------------------
# Round-trip: output json_structure is parseable and validates canonically
# ---------------------------------------------------------------------------

def test_round_trip_validate_canonical():
    formula = Quantifier(
        quant=QuantifierType.FORALL,
        vars=[Variable("individual")],
        body=Connective(
            op=ConnectiveType.IMPLIES,
            args=[Predicate("is_man", [Variable("individual")]), Predicate("is_mortal", [Variable("individual")])],
        ),
    )
    result = normalize_formalizations([_item("A", formula)], confidence=1.0, reasoning="")
    out_js = result["formalizations"][0]["json_structure"]
    parsed = from_json(json.loads(out_js))
    validate_canonical(parsed)  # must not raise


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------

def test_malformed_json_structure_raises():
    bad_item = {"symbol": "A", "ascii": "", "json_structure": '{"type": "unknown_type"}'}
    with pytest.raises(FormalizationNormalizationError):
        normalize_formalizations([bad_item], confidence=0.0, reasoning="")


def test_many_predicates_uses_numbered_symbols():
    # 27 unique predicate names — should succeed with P1, Q1… instead of raising
    items = [
        _item(chr(ord("A") + i % 26), Predicate(f"pred_{i}", []))
        for i in range(27)
    ]
    result = normalize_formalizations(items, confidence=0.0, reasoning="")
    syms = {d["symbol"] for d in result["definitions"]["predicates"]}
    assert "P1" in syms  # 12th predicate (index 11) → P1


def test_too_many_variables_raises():
    # 7 nested quantifiers
    body: Formula = Predicate("p", [])
    for i in range(7):
        body = Quantifier(quant=QuantifierType.FORALL, vars=[Variable(f"v{i}")], body=body)
    with pytest.raises(ValueError, match="more than"):
        normalize_formalizations([_item("A", body)], confidence=0.0, reasoning="")
