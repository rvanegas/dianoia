from dataclasses import dataclass, field
from enum import Enum
from typing import List, Union, Dict, Any
import json
import re


# --- Enums for constrained values ---

class QuantifierType(str, Enum):
    FORALL = "forall"
    EXISTS = "exists"


class BinaryOpType(str, Enum):
    AND = "and"
    OR = "or"
    IMPLIES = "implies"


class ModalType(str, Enum):
    BOX = "box"
    DIAMOND = "diamond"


# --- Terms ---

@dataclass(frozen=True)
class Term:
    pass


@dataclass(frozen=True)
class Variable(Term):
    name: str

    def __post_init__(self):
        if not re.fullmatch(r"[p-z]", self.name):
            raise ValueError(f"Variable name {self.name!r} not in p–z")


@dataclass(frozen=True)
class Constant(Term):
    name: str

    def __post_init__(self):
        if not re.fullmatch(r"[a-o]", self.name):
            raise ValueError(f"Constant name {self.name!r} not in a–o")


# --- Formula base and subclasses ---

@dataclass(frozen=True)
class Formula:
    def to_dict(self) -> Dict[str, Any]:
        raise NotImplementedError

    def to_unicode(self) -> str:
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

    def to_unicode(self) -> str:
        args = ", ".join(arg_to_unicode(a) for a in self.args)
        return f"{self.name}({args})"

    def to_ascii(self) -> str:
        args = ", ".join(arg_to_ascii(a) for a in self.args)
        return f"{self.name}({args})"


@dataclass(frozen=True)
class PropVar(Formula):
    name: str

    def __post_init__(self):
        if not re.fullmatch(r"[P-Z]", self.name):
            raise ValueError(f"Proposition variable {self.name!r} must be P–Z")

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "propvar", "name": self.name}

    def to_unicode(self) -> str:
        return self.name

    def to_ascii(self) -> str:
        return self.name.lower()


@dataclass(frozen=True)
class Equality(Formula):
    left: Term
    right: Term

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "equality",
            "left": term_to_dict(self.left),
            "right": term_to_dict(self.right)
        }

    def to_unicode(self) -> str:
        return f"{arg_to_unicode(self.left)} = {arg_to_unicode(self.right)}"

    def to_ascii(self) -> str:
        return f"{arg_to_ascii(self.left)} = {arg_to_ascii(self.right)}"


@dataclass(frozen=True)
class Not(Formula):
    formula: Formula

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "not", "formula": self.formula.to_dict()}

    def to_unicode(self) -> str:
        return f"¬{self.formula.to_unicode()}"

    def to_ascii(self) -> str:
        return f"~{self.formula.to_ascii()}"


@dataclass(frozen=True)
class BinaryOp(Formula):
    op: BinaryOpType
    left: Formula
    right: Formula

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "binary",
            "op": self.op.value,
            "left": self.left.to_dict(),
            "right": self.right.to_dict()
        }

    def to_unicode(self) -> str:
        sym = {"and": "∧", "or": "∨", "implies": "→"}[self.op.value]
        return f"({self.left.to_unicode()} {sym} {self.right.to_unicode()})"

    def to_ascii(self) -> str:
        sym = {"and": "/\\", "or": "\\/", "implies": "->"}[self.op.value]
        return f"({self.left.to_ascii()} {sym} {self.right.to_ascii()})"


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

    def to_unicode(self) -> str:
        sym = {"forall": "∀", "exists": "∃"}[self.quant.value]
        return f"{sym}{self.var.name}. {self.body.to_unicode()}"

    def to_ascii(self) -> str:
        return f"{self.quant.value} {self.var.name}. ({self.body.to_ascii()})"


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

    def to_unicode(self) -> str:
        sym = {"box": "□", "diamond": "◊"}[self.mod.value]
        return f"{sym}{self.body.to_unicode()}"

    def to_ascii(self) -> str:
        sym = {"box": "[]", "diamond": "<>"}[self.mod.value]
        return f"{sym}{self.body.to_ascii()}"


# --- Helpers for terms and args ---

def term_to_dict(t: Term) -> Dict[str, Any]:
    if isinstance(t, Variable):
        return {"type": "variable", "name": t.name}
    if isinstance(t, Constant):
        return {"type": "constant", "name": t.name}
    raise TypeError(f"Unknown term {t!r}")


def arg_to_unicode(a: Union[Term, Formula]) -> str:
    if isinstance(a, Term):
        return a.name
    return a.to_unicode()


def arg_to_ascii(a: Union[Term, Formula]) -> str:
    if isinstance(a, Term):
        return a.name
    return a.to_ascii()


# --- JSON → Formula deserializer ---

def from_json(d: Dict[str, Any]) -> Formula:
    t = d.get("type")
    if t == "predicate":
        args = [term_from_dict(a) for a in d["args"]]
        return Predicate(d["name"], args)
    if t == "propvar":
        return PropVar(d["name"])
    if t == "equality":
        left = term_from_dict(d["left"])
        right = term_from_dict(d["right"])
        return Equality(left, right)
    if t == "not":
        return Not(from_json(d["formula"]))
    if t == "binary":
        op = BinaryOpType(d["op"])
        left = from_json(d["left"])
        right = from_json(d["right"])
        return BinaryOp(op, left, right)
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
    # ∀x ◊(P(x) ∧ x = a)
    x = Variable("x")       # must be p–z
    a = Constant("a")       # must be a–o
    phi = Quantifier(
        quant=QuantifierType.FORALL,
        var=x,
        body=Modal(
            mod=ModalType.DIAMOND,
            body=BinaryOp(
                op=BinaryOpType.AND,
                left=Predicate("P", [x]),
                right=Equality(x, a)
            )
        )
    )
    js = phi.to_dict()
    print(json.dumps(js, indent=2))
    print("Unicode:", phi.to_unicode())
    print("ASCII:", phi.to_ascii())
    # round‐trip
    phi2 = from_json(js)
    assert phi2 == phi
