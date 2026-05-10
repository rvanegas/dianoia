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


# --- Terms ---

@dataclass(frozen=True)
class Term:
    pass


@dataclass(frozen=True)
class Variable(Term):
    name: str


@dataclass(frozen=True)
class Constant(Term):
    name: str


# --- Formula base and subclasses ---

@dataclass(frozen=True)
class Formula:
    def to_dict(self) -> Dict[str, Any]:
        raise NotImplementedError

    def to_ascii(self) -> str:
        raise NotImplementedError


@dataclass(frozen=True)
class Predicate(Formula):
    name: str
    args: List[Term]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "predicate",
            "name": self.name,
            "args": [term_to_dict(t) for t in self.args]
        }

    def to_ascii(self) -> str:
        if not self.args:
            return self.name
        args = ", ".join(arg_to_ascii(a) for a in self.args)
        return f"{self.name}({args})"


@dataclass(frozen=True)
class Identity(Formula):
    left: Term
    right: Term

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "identity",
            "left": term_to_dict(self.left),
            "right": term_to_dict(self.right)
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
            "args": [a.to_dict() for a in self.args]
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
    var: Variable
    body: Formula

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "quantifier",
            "quant": self.quant.value,
            "var": term_to_dict(self.var),
            "body": self.body.to_dict()
        }

    def to_ascii(self) -> str:
        return f"{self.quant.value} {self.var.name}. {self.body.to_ascii()}"


@dataclass(frozen=True)
class Modal(Formula):
    mod: ModalType
    body: Formula

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "modal",
            "mod": self.mod.value,
            "body": self.body.to_dict()
        }

    def to_ascii(self) -> str:
        return f"{self.mod.value} {self.body.to_ascii()}"


# --- Helpers for terms and args ---

def term_to_dict(t: Term) -> Dict[str, Any]:
    if isinstance(t, Variable):
        return {"type": "variable", "name": t.name}
    if isinstance(t, Constant):
        return {"type": "constant", "name": t.name}
    raise TypeError(f"Unknown term {t!r}")


def arg_to_ascii(a: Union[Term, Formula]) -> str:
    if isinstance(a, Term):
        return a.name
    return a.to_ascii()


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
        # same precedence: parens needed when associativity would give a different tree
        if right_assoc and not is_right:   # left child of right-assoc op
            return f"({s})"
        if not right_assoc and is_right:   # right child of left-assoc op
            return f"({s})"
    return s


_CANONICAL_VARIABLES = {'x', 'y', 'z', 'u', 'v', 'w'}
_CANONICAL_CONST_RE = _re.compile(r'^[a-f]\d*$')


def _is_canonical_const(name: str) -> bool:
    return bool(_CANONICAL_CONST_RE.match(name))


def validate_canonical(formula: 'Formula') -> None:
    """Raise ValueError if formula contains non-canonical Variable or Constant names."""
    if isinstance(formula, Predicate):
        for arg in formula.args:
            if isinstance(arg, Variable):
                if arg.name not in _CANONICAL_VARIABLES:
                    raise ValueError(f"Variable {arg.name!r} not in canonical set {_CANONICAL_VARIABLES}")
            elif isinstance(arg, Constant):
                if not _is_canonical_const(arg.name):
                    raise ValueError(f"Constant {arg.name!r} not in a–f[N]")
    elif isinstance(formula, Identity):
        for t in (formula.left, formula.right):
            if isinstance(t, Variable) and t.name not in _CANONICAL_VARIABLES:
                raise ValueError(f"Variable {t.name!r} not in canonical set")
            if isinstance(t, Constant) and not _is_canonical_const(t.name):
                raise ValueError(f"Constant {t.name!r} not in a–f[N]")
    elif isinstance(formula, Connective):
        for arg in formula.args:
            validate_canonical(arg)
    elif isinstance(formula, Quantifier):
        if formula.var.name not in _CANONICAL_VARIABLES:
            raise ValueError(f"Quantifier variable {formula.var.name!r} not in canonical set")
        validate_canonical(formula.body)
    elif isinstance(formula, Modal):
        validate_canonical(formula.body)


# --- JSON → Formula deserializer ---

def from_json(d: Dict[str, Any]) -> Formula:
    t = d.get("type")
    if t == "predicate":
        args = [term_from_dict(a) for a in d["args"]]
        return Predicate(d["name"], args)
    if t == "identity":
        left = term_from_dict(d["left"])
        right = term_from_dict(d["right"])
        return Identity(left, right)
    if t == "connective":
        op = ConnectiveType(d["op"])
        args = [from_json(a) for a in d["args"]]
        return Connective(op, args)
    if t == "quantifier":
        quant = QuantifierType(d["quant"])
        var = Variable(d["var"]["name"])
        body = from_json(d["body"])
        return Quantifier(quant, var, body)
    if t == "modal":
        mod = ModalType(d["mod"])
        body = from_json(d["body"])
        return Modal(mod, body)
    raise ValueError(f"Unknown formula type {t!r}")


def term_from_dict(d: Dict[str, Any]) -> Term:
    tt = d.get("type")
    if tt == "variable":
        return Variable(d["name"])
    if tt == "constant":
        return Constant(d["name"])
    raise ValueError(f"Unknown term type {tt!r}")


# --- Example usage ---

if __name__ == "__main__":
    x = Variable("x")
    a = Constant("a")
    phi = Quantifier(
        quant=QuantifierType.FORALL,
        var=x,
        body=Modal(
            mod=ModalType.DIAMOND,
            body=Connective(
                op=ConnectiveType.AND,
                args=[Predicate("P", [x]), Identity(x, a)]
            )
        )
    )
    js = phi.to_dict()
    print(json.dumps(js, indent=2))
    print("ASCII:", phi.to_ascii())
    phi2 = from_json(js)
    assert phi2 == phi
