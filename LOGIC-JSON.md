# JSON Logic Format

This document describes the JSON representation of logical formulas used in Dianoia.
Every formula in ASCII (see `LOGIC-ASCII.md`) has an exact JSON equivalent.
`src/core/logic.py` converts between the two forms.

---

## Node Types

Every JSON formula is an object with a `"type"` field. The possible types are:

`predicate` `identity` `connective` `quantifier` `modal`

Every JSON argument position (inside `args`, `vars`, `left`, `right`) is a
**symbol node** with a `"type"` field:

`variable` `constant` `pred_variable`

---

## Symbol Nodes

```json
{"type": "variable",      "name": "x"}   -- individual variable (x y z u v w)
{"type": "constant",      "name": "a"}   -- individual constant (a b c ... a1 ...)
{"type": "pred_variable", "name": "X"}   -- predicate variable  (X Y Z U V W)
```

---

## Formula Nodes

### predicate

The head is either a named predicate constant (`"name"`) or a bound predicate
variable (`"pred_var"`). `"args"` is an array of symbol nodes (may be empty).

```json
{"type": "predicate", "name": "P", "args": []}
```
ASCII: `P`

```json
{"type": "predicate", "name": "P", "args": [{"type": "variable", "name": "x"}]}
```
ASCII: `Px`

```json
{
  "type": "predicate",
  "name": "R",
  "args": [
    {"type": "variable", "name": "x"},
    {"type": "constant", "name": "a"}
  ]
}
```
ASCII: `Rxa`

```json
{
  "type": "predicate",
  "pred_var": "X",
  "args": [{"type": "variable", "name": "x"}]
}
```
ASCII: `Xx`

### identity

`"left"` and `"right"` are symbol nodes (any kind).

```json
{
  "type": "identity",
  "left":  {"type": "variable", "name": "x"},
  "right": {"type": "constant", "name": "a"}
}
```
ASCII: `x = a`

```json
{
  "type": "identity",
  "left":  {"type": "variable",      "name": "x"},
  "right": {"type": "pred_variable", "name": "Y"}
}
```
ASCII: `x = Y`

### connective

`"op"` is one of `"not"` `"and"` `"or"` `"implies"` `"equiv"`.
`"args"` is an array of formula nodes: one element for `"not"`, two for the rest.

```json
{"type": "connective", "op": "not", "args": [<formula>]}
```
ASCII: `not <formula>`

```json
{
  "type": "connective",
  "op": "and",
  "args": [<formula1>, <formula2>]
}
```
ASCII: `<formula1> and <formula2>` (parentheses added by precedence rules)

### quantifier

`"quant"` is `"forall"` or `"exists"`. `"vars"` is a non-empty array of symbol
nodes, each of type `"variable"` or `"pred_variable"`. `"body"` is a formula node.

```json
{
  "type": "quantifier",
  "quant": "forall",
  "vars": [{"type": "variable", "name": "x"}],
  "body": <formula>
}
```
ASCII: `forall x. <formula>`

```json
{
  "type": "quantifier",
  "quant": "forall",
  "vars": [
    {"type": "variable",      "name": "x"},
    {"type": "pred_variable", "name": "X"}
  ],
  "body": <formula>
}
```
ASCII: `forall x,X. <formula>`

### modal

`"mod"` is `"nec"` or `"pos"`. `"body"` is a formula node.

```json
{"type": "modal", "mod": "nec", "body": <formula>}
```
ASCII: `nec <formula>`

---

## Complete Example

ASCII: `forall x,X. pos Xx and x = a`

```json
{
  "type": "quantifier",
  "quant": "forall",
  "vars": [
    {"type": "variable",      "name": "x"},
    {"type": "pred_variable", "name": "X"}
  ],
  "body": {
    "type": "modal",
    "mod": "pos",
    "body": {
      "type": "connective",
      "op": "and",
      "args": [
        {
          "type": "predicate",
          "pred_var": "X",
          "args": [{"type": "variable", "name": "x"}]
        },
        {
          "type": "identity",
          "left":  {"type": "variable", "name": "x"},
          "right": {"type": "constant", "name": "a"}
        }
      ]
    }
  }
}
```

---

## Field Reference

| `"type"`          | Required fields                                              | Notes                                           |
|-------------------|--------------------------------------------------------------|-------------------------------------------------|
| `"predicate"`     | `"name": string` OR `"pred_var": string`; `"args": []`      | exactly one of `name`/`pred_var`                |
| `"identity"`      | `"left": symbol`, `"right": symbol`                         |                                                 |
| `"connective"`    | `"op": string`, `"args": [formula, ...]`                    | `not` takes 1 arg; others take 2                |
| `"quantifier"`    | `"quant": string`, `"vars": [symbol, ...]`, `"body": formula` | `vars` entries are `variable` or `pred_variable` |
| `"modal"`         | `"mod": string`, `"body": formula`                          |                                                 |
| `"variable"`      | `"name": string`                                            | canonical: `x y z u v w`                       |
| `"constant"`      | `"name": string`                                            | canonical: `a b c d e f` (then `a1` ...)        |
| `"pred_variable"` | `"name": string`                                            | canonical: `X Y Z U V W`                       |
