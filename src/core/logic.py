from dataclasses import dataclass
from enum import Enum
from typing import List, Union, Dict, Any
import json
import re as _re


# --- Enums for constrained values ---

class ConnectiveType(str, Enum):
    NOT     = "not"
    AND     = "and"
    OR      = "or"
    IMPLIES = "implies"
    EQUIV   = "equiv"


class QuantifierType(str, Enum):
    FORALL = "forall"
    EXISTS = "exists"


class ModalType(str, Enum):
    BOX     = "nec"
    DIAMOND = "pos"


# Precedence (higher = tighter binding). Unary operators are right-to-left;
# implies is right-associative; and/or are left-associative.
_PREC: Dict[str, int] = {
    "not": 5,
    "and": 4,
    "or":  3,
    "implies": 2,
    "equiv": 1,
    "nec": 0, "pos": 0, "forall": 0, "exists": 0,
}
_RIGHT_ASSOC = frozenset({"implies"})


# --- Terms and predicate variables ---

@dataclass(frozen=True)
class Term:
    pass


@dataclass(frozen=True)
class Variable(Term):
    name: str


@dataclass(frozen=True)
class Constant(Term):
    name: str


@dataclass(frozen=True)
class PredicateVariable:
    """A variable ranging over universals/predicates (X, Y, Z, U, V, W)."""
    name: str


# Anything that can appear in an argument or identity position.
Arg = Union[Variable, Constant, PredicateVariable]

# Anything that can appear as the head of a predicate application.
PredHead = Union[str, PredicateVariable]


# --- Formula base and subclasses ---

@dataclass(frozen=True)
class Formula:
    def to_dict(self) -> Dict[str, Any]:
        raise NotImplementedError

    def to_ascii(self) -> str:
        raise NotImplementedError


@dataclass(frozen=True)
class Predicate(Formula):
    head: PredHead          # str = predicate constant name; PredicateVariable = bound variable
    args: List[Arg]

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "type": "predicate",
            "args": [arg_to_dict(a) for a in self.args],
        }
        if isinstance(self.head, PredicateVariable):
            d["pred_var"] = self.head.name
        else:
            d["name"] = self.head
        return d

    def to_ascii(self) -> str:
        h = self.head.name if isinstance(self.head, PredicateVariable) else self.head
        if not self.args:
            return h
        return h + "".join(arg_to_ascii(a) for a in self.args)


@dataclass(frozen=True)
class Identity(Formula):
    left: Arg
    right: Arg

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "identity",
            "left": arg_to_dict(self.left),
            "right": arg_to_dict(self.right),
        }

    def to_ascii(self) -> str:
        return f"{arg_to_ascii(self.left)} = {arg_to_ascii(self.right)}"


@dataclass(frozen=True)
class Connective(Formula):
    op: ConnectiveType
    args: List[Formula]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "connective",
            "op": self.op.value,
            "args": [a.to_dict() for a in self.args],
        }

    def to_ascii(self) -> str:
        p = _PREC[self.op.value]
        if self.op == ConnectiveType.NOT:
            body = self.args[0]
            s = body.to_ascii()
            return f"not {_wrap(s, body, p)}"
        left, right = self.args[0], self.args[1]
        right_assoc = self.op.value in _RIGHT_ASSOC
        ls = _wrap(left.to_ascii(),  left,  p, is_right=False, right_assoc=right_assoc)
        rs = _wrap(right.to_ascii(), right, p, is_right=True,  right_assoc=right_assoc)
        return f"{ls} {self.op.value} {rs}"


@dataclass(frozen=True)
class Quantifier(Formula):
    quant: QuantifierType
    vars: List[Union[Variable, PredicateVariable]]
    body: Formula

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "quantifier",
            "quant": self.quant.value,
            "vars": [arg_to_dict(v) for v in self.vars],
            "body": self.body.to_dict(),
        }

    def to_ascii(self) -> str:
        var_str = ",".join(v.name for v in self.vars)
        return f"{self.quant.value} {var_str}. {self.body.to_ascii()}"


@dataclass(frozen=True)
class Modal(Formula):
    mod: ModalType
    body: Formula

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "modal",
            "mod": self.mod.value,
            "body": self.body.to_dict(),
        }

    def to_ascii(self) -> str:
        return f"{self.mod.value} {self.body.to_ascii()}"


# --- Helpers ---

def arg_to_dict(a: Arg) -> Dict[str, Any]:
    if isinstance(a, Variable):
        return {"type": "variable", "name": a.name}
    if isinstance(a, Constant):
        return {"type": "constant", "name": a.name}
    if isinstance(a, PredicateVariable):
        return {"type": "pred_variable", "name": a.name}
    raise TypeError(f"Unknown arg {a!r}")


def arg_to_ascii(a: Union[Arg, Formula]) -> str:
    if isinstance(a, (Variable, Constant, PredicateVariable)):
        return a.name
    return a.to_ascii()


def arg_from_dict(d: Dict[str, Any]) -> Arg:
    tt = d.get("type")
    if tt == "variable":
        return Variable(d["name"])
    if tt == "constant":
        return Constant(d["name"])
    if tt == "pred_variable":
        return PredicateVariable(d["name"])
    raise ValueError(f"Unknown arg type {tt!r}")


def _formula_prec(f: Formula) -> int:
    if isinstance(f, Connective):
        return _PREC[f.op.value]
    if isinstance(f, Modal):
        return _PREC[f.mod.value]
    if isinstance(f, Quantifier):
        return _PREC[f.quant.value]
    return 99  # Predicate, Identity: atomic


def _wrap(s: str, child: Formula, parent_prec: int,
          is_right: bool = True, right_assoc: bool = False) -> str:
    cp = _formula_prec(child)
    if cp < parent_prec:
        return f"({s})"
    if cp == parent_prec:
        if right_assoc and not is_right:
            return f"({s})"
        if not right_assoc and is_right:
            return f"({s})"
    return s


_CANONICAL_VARIABLES      = {'x', 'y', 'z', 'u', 'v', 'w'}
_CANONICAL_PRED_VARIABLES = {'X', 'Y', 'Z', 'U', 'V', 'W'}
_CANONICAL_CONST_RE       = _re.compile(r'^[a-f]\d*$')


def _is_canonical_const(name: str) -> bool:
    return bool(_CANONICAL_CONST_RE.match(name))


def validate_canonical(formula: 'Formula') -> None:
    """Raise ValueError if formula contains non-canonical symbol names."""
    def _check_arg(a: Arg) -> None:
        if isinstance(a, Variable) and a.name not in _CANONICAL_VARIABLES:
            raise ValueError(f"Variable {a.name!r} not in canonical set")
        elif isinstance(a, Constant) and not _is_canonical_const(a.name):
            raise ValueError(f"Constant {a.name!r} not in a–f[N]")
        elif isinstance(a, PredicateVariable) and a.name not in _CANONICAL_PRED_VARIABLES:
            raise ValueError(f"Predicate variable {a.name!r} not in canonical set")

    if isinstance(formula, Predicate):
        if isinstance(formula.head, PredicateVariable):
            _check_arg(formula.head)
        for arg in formula.args:
            _check_arg(arg)
    elif isinstance(formula, Identity):
        _check_arg(formula.left)
        _check_arg(formula.right)
    elif isinstance(formula, Connective):
        for arg in formula.args:
            validate_canonical(arg)
    elif isinstance(formula, Quantifier):
        for v in formula.vars:
            _check_arg(v)
        validate_canonical(formula.body)
    elif isinstance(formula, Modal):
        validate_canonical(formula.body)


# --- JSON → Formula deserializer ---

def from_json(d: Dict[str, Any]) -> Formula:
    t = d.get("type")
    if t == "predicate":
        head: PredHead = PredicateVariable(d["pred_var"]) if "pred_var" in d else d["name"]
        args = [arg_from_dict(a) for a in d["args"]]
        return Predicate(head, args)
    if t == "identity":
        return Identity(arg_from_dict(d["left"]), arg_from_dict(d["right"]))
    if t == "connective":
        op = ConnectiveType(d["op"])
        args = [from_json(a) for a in d["args"]]
        return Connective(op, args)
    if t == "quantifier":
        quant = QuantifierType(d["quant"])
        vars_ = [arg_from_dict(v) for v in d["vars"]]
        body = from_json(d["body"])
        return Quantifier(quant, vars_, body)
    if t == "modal":
        mod = ModalType(d["mod"])
        body = from_json(d["body"])
        return Modal(mod, body)
    raise ValueError(f"Unknown formula type {t!r}")


# --- Example usage ---

if __name__ == "__main__":
    x = Variable("x")
    X = PredicateVariable("X")
    a = Constant("a")

    # forall x,X. pos Xx and x = a
    phi = Quantifier(
        quant=QuantifierType.FORALL,
        vars=[x, X],
        body=Modal(
            mod=ModalType.DIAMOND,
            body=Connective(
                op=ConnectiveType.AND,
                args=[Predicate(X, [x]), Identity(x, a)]
            )
        )
    )
    js = phi.to_dict()
    print(json.dumps(js, indent=2))
    print("ASCII:", phi.to_ascii())
    phi2 = from_json(js)
    assert phi2 == phi
