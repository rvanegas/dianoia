from services.conversation import Gpt

# Agent-specific system prompt for justification
agent_justify_system_prompt = """
You are an AI agent working on logical argumentation. Your task is to help improve arguments
by generating justifications for propositions. You work with natural language propositions and 
can optionally use formal logical representations as guidance.

Always maintain the logical integrity of arguments and respect the context provided.

### Task: Generate Justifications

You will receive a proposition that needs justification, along with optional formalization context.
Your goal is to generate supporting propositions that justify the given proposition.

### Input Format
- proposition: The proposition to justify (inferred from target_loc and target_index)
- target_loc: Location in argument structure ('argument')
- target_index: Position in the argument (the proposition is extracted from argument[target_index])
- argument: Full list of propositions in the main argument
- assumptions: List of background assumptions (for context only, not justified)
- formalization_context: Optional formal logical representation to guide your justification

Note: The proposition field is inferred from the argument structure at the specified location and index to ensure consistency. Only propositions in 'argument' can be justified - assumptions are foundational premises that are not justified.

### Guidelines
1. Generate 1-2 supporting propositions that justify the given proposition
2. Consider the full argument context when generating justifications
3. If formalization context is provided, use it to guide your justification
4. If no formalization is provided, work with natural language logic
5. Ensure justifications are logically sound and relevant to the overall argument
6. Avoid duplicating existing propositions in the argument
7. Return propositions as separate strings, without numbering or prefixes

### Examples

Input:
proposition: "Socrates is mortal"
target_loc: "argument"
target_index: 2
argument: ["Socrates is a man", "All men are mortal", "Socrates is mortal"]
assumptions: []

Output:
["All men are mortal.", "Socrates is a man."]

Input:
proposition: "The economy will improve"
target_loc: "argument"
target_index: 1
argument: ["Government stimulus measures are effective", "The economy will improve"]
assumptions: ["Current economic policies are sound"]

Output:
["Consumer confidence is increasing.", "Employment rates are rising."]
"""

# Create GPT instance for agent justification
agent_gpt_justify = Gpt(
    instructions=agent_justify_system_prompt,
    response_format_base={
        "type": "object",
        "properties": {
            "propositions": {
                "type": "array",
                "items": {"type": "string"}
            }
        },
        "required": ["propositions"],
        "additionalProperties": False
    }
)

# Agent-specific system prompt for content evaluation
agent_evaluate_content_system_prompt = """
You are an AI agent working on logical argumentation. Your task is to evaluate the truth, validity, coherence, and identify weak inferences in natural language content.

For the purposes of this task, we define "valid" to accord with its sense in mathematical logic, not its more general and equivocal sense in debate or rhetoric. Validity is strict formal validity, _not_ soundness. The validity of an argument is not affected by the truth of its premises or conclusion.

### Input Format
The input will be a JSON object with the following structure:
- agent_data.argument: List of Step objects in the main argument
- agent_data.assumptions: List of Step objects for background assumptions
- agent_data.target_type: Type of content being evaluated (e.g., "argument", "proposition")
- agent_data.target_content: Specific content being targeted (if applicable)

Each Step object contains:
- symbol: String identifier (e.g., "A", "B", "C")
- proposition: The natural language proposition
- justifiers: List of symbols that justify this step
- valid_content: Content validity from previous evaluation (optional)
- valid_formal: Formal validity from previous evaluation (optional)
- formalization: Formal logic representation (optional)

### Task

You will receive argument data with Step objects containing symbols, propositions, and justifiers. You will evaluate and return comprehensive assessments including:

1. **Truth Evaluation**: Individual proposition assessments by symbol (truth values from 0.0 to 1.0)
2. **Validity Assessment**: Validity of each step in relation to its justifiers (validity values from 0.0 to 1.0)
3. **Coherence Analysis**: How well the propositions work together as a unified argument
4. **Weak Inference Identification**: Steps with the lowest validity scores

### Considerations

**Truth Evaluation**:
- For each Step, assess the truth value of its proposition given the assumptions
- 1.0 = certainly true, 0.0 = certainly false, intermediate values for degrees of 
  likelihood, in increments of 0.1
- Consider empirical evidence, logical consistency, and background knowledge
- Return truth values indexed by Step symbol

**Validity Assessment**:
- For each Step with justifiers, evaluate the validity of the inference from its justifiers to its proposition
- 1.0 = deductively valid, 0.0 = contradictory, intermediate values for inductive/abductive strength
- Consider the logical relationship between the Step's proposition and its justifiers
- Steps without justifiers (premises/assumptions) should not receive validity values
- Return validity values indexed by Step symbol (only for steps with justifiers)

**Coherence Analysis**:
- Evaluate how well the propositions form a unified argument
- Check for internal consistency and logical flow
- Identify gaps, contradictions, or redundancies
- Identify sets of steps that are mutually incoherent
- Assign incoherence values: 1.0 = logical contradiction, lower values for lesser incoherence

**Weak Inference Identification**:
- Weak inferences are implicitly identified by low validity scores in validity_evaluations
- No need to explicitly list them - they can be found by examining the validity values
- Provide specific recommendations for strengthening weak inferences

### Examples

# Valid but not sound argument

Input:
{
  "agent_data": {
    "argument": [
      {
        "symbol": "A",
        "proposition": "Socrates is a god",
        "justifiers": []
      },
      {
        "symbol": "B", 
        "proposition": "All gods are immortal",
        "justifiers": []
      },
      {
        "symbol": "C",
        "proposition": "Socrates is immortal", 
        "justifiers": ["A", "B"]
      }
    ],
    "assumptions": [],
    "target_type": "argument",
    "target_content": null
  }
}

Output:
{
  "truth_evaluations": [
    {"symbol": "A", "truth_value": 0.0, "reasoning": "Contradicts historical and theological knowledge"},
    {"symbol": "B", "truth_value": 0.8, "reasoning": "Common theological assumption, though debatable"},
    {"symbol": "C", "truth_value": 0.0, "reasoning": "False conclusion from false premise"}
  ],
  "validity_evaluations": [
    {"symbol": "C", "validity_value": 1.0, "reasoning": "Valid deduction from A and B, though premises are false"}
  ],

  "incoherent_sets": [],
  "logical_issues": ["Argument is valid but unsound due to false premise"],
  "recommendations": [
    "Replace false premise A with true statement about Socrates",
    "Provide evidence for theological assumptions in B if used"
  ]
}

# Coherent and sound argument

Input:
{
  "agent_data": {
    "argument": [
      {
        "symbol": "A",
        "proposition": "Socrates is a man",
        "justifiers": []
      },
      {
        "symbol": "B",
        "proposition": "All men are mortal", 
        "justifiers": []
      },
      {
        "symbol": "C",
        "proposition": "Socrates is mortal",
        "justifiers": ["A", "B"]
      }
    ],
    "assumptions": [],
    "target_type": "argument",
    "target_content": null
  }
}

Output:
{
  "truth_evaluations": [
    {"symbol": "A", "truth_value": 0.95, "reasoning": "Historical fact, well-documented"},
    {"symbol": "B", "truth_value": 0.98, "reasoning": "Universal biological truth, no known exceptions"},
    {"symbol": "C", "truth_value": 0.95, "reasoning": "Valid conclusion from true premises"}
  ],
  "validity_evaluations": [
    {"symbol": "C", "validity_value": 1.0, "reasoning": "Valid deduction from A and B"}
  ],

  "incoherent_sets": [],
  "logical_issues": [],
  "recommendations": ["Argument is logically sound and well-structured"]
}

# Argument with logical contradiction

Input:
{
  "agent_data": {
    "argument": [
      {
        "symbol": "A",
        "proposition": "All humans are mortal",
        "justifiers": []
      },
      {
        "symbol": "B",
        "proposition": "Socrates is human",
        "justifiers": []
      },
      {
        "symbol": "C",
        "proposition": "Socrates is immortal",
        "justifiers": ["A", "B"]
      }
    ],
    "assumptions": [],
    "target_type": "argument",
    "target_content": null
  }
}

Output:
{
  "truth_evaluations": [
    {"symbol": "A", "truth_value": 0.98, "reasoning": "Universal biological truth"},
    {"symbol": "B", "truth_value": 0.95, "reasoning": "Historical fact"},
    {"symbol": "C", "truth_value": 0.0, "reasoning": "Contradicts premises A and B"}
  ],
  "validity_evaluations": [
    {"symbol": "C", "validity_value": 0.0, "reasoning": "Logical contradiction with premises"}
  ],
  "incoherent_sets": [
    {
      "symbols": ["A", "B", "C"],
      "incoherence_value": 1.0
    }
  ],
  "logical_issues": ["Contains logical contradiction"],
  "recommendations": [
    "Fix contradiction in C - Socrates cannot be both mortal (from A+B) and immortal"
  ]
}

# Argument with weak inferences
{
  "agent_data": {
    "argument": [
      {
        "symbol": "A",
        "proposition": "The policy worked in another country",
        "justifiers": []
      },
      {
        "symbol": "B",
        "proposition": "Our country is similar",
        "justifiers": []
      },
      {
        "symbol": "C",
        "proposition": "The policy will work here",
        "justifiers": ["A", "B"]
      }
    ],
    "assumptions": [],
    "target_type": "argument",
    "target_content": null
  }
}

Output:
{
  "truth_evaluations": [
    {"symbol": "A", "truth_value": 0.7, "reasoning": "Limited evidence, context-dependent"},
    {"symbol": "B", "truth_value": 0.6, "reasoning": "Vague similarity claim, needs specification"},
    {"symbol": "C", "truth_value": 0.5, "reasoning": "Weak conclusion from weak premises"}
  ],
  "validity_evaluations": [
    {"symbol": "C", "validity_value": 0.6, "reasoning": "Weak analogical inference from A and B"}
  ],

  "incoherent_sets": [
    {
      "symbols": ["A", "B", "C"],
      "incoherence_value": 0.7
    }
  ],
  "logical_issues": ["Relies on weak analogical reasoning"],
  "recommendations": [
    "Provide specific evidence of policy success in other country (A)",
    "Specify relevant similarities and differences between countries (B)",
    "Strengthen analogical reasoning in C"
  ]
}
"""

# Create GPT instance for content evaluation
agent_gpt_evaluate_content = Gpt(
    instructions=agent_evaluate_content_system_prompt,
    response_format_base={
        "type": "object",
        "properties": {
            "truth_evaluations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string"},
                        "truth_value": {"type": "number"},
                        "reasoning": {"type": "string"}
                    },
                    "required": ["symbol", "truth_value", "reasoning"],
                    "additionalProperties": False
                }
            },
            "validity_evaluations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string"},
                        "validity_value": {"type": "number"},
                        "reasoning": {"type": "string"}
                    },
                    "required": ["symbol", "validity_value", "reasoning"],
                    "additionalProperties": False
                }
            },


            "incoherent_sets": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "symbols": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "incoherence_value": {"type": "number"}
                    },
                    "required": ["symbols", "incoherence_value"],
                    "additionalProperties": False
                }
            },
            "logical_issues": {
                "type": "array",
                "items": {"type": "string"}
            },
            "recommendations": {
                "type": "array",
                "items": {"type": "string"}
            }
        },
        "required": ["truth_evaluations", "validity_evaluations", "incoherent_sets", "logical_issues", "recommendations"],
        "additionalProperties": False
    }
)

# Agent-specific system prompt for form evaluation
agent_evaluate_form_system_prompt = """
You are an AI agent working on logical argumentation. Your task is to evaluate ONLY the logical validity of formalized arguments, ignoring the truth of individual propositions.

For the purposes of this task, we define "valid" to accord with its sense in mathematical logic, not its more general and equivocal sense in debate or rhetoric. Validity is strict formal validity, _not_ soundness. The validity of an argument is not affected by the truth of its premises or conclusion.

### Input Format
- formalizations: List of formal logical representations of the propositions

### Task

You will receive formalizations of logical propositions. You will evaluate ONLY the logical validity of the formal logical structure, completely ignoring any semantic content.

For each formalization, set truth_value to 0.5 (neither true nor false by form alone) and focus entirely on whether the logical structure is valid.

The argument_validity should reflect the formal logical validity of the argument structure, not the truth of the premises or conclusion.

### Considerations

- Set all proposition truth_values to 0.5 (neither true nor false by form alone)
- Focus entirely on the logical structure and validity of the argument
- Evaluate whether the conclusion follows logically from the premises
- Ignore the semantic content and truth of individual propositions
- Consider only the formal logical relationships between propositions
- Use the formalizations to assess logical validity
- **IMPORTANT**: Pay attention to variable renaming and the transitivity of implication
- When premises use different variable names (e.g., ∀y (Q(y) → R(y)) and ∀x (P(x) → Q(x))), the argument can still be valid if the logical structure supports the conclusion
- The transitivity of implication means: if ∀x (P(x) → Q(x)) and ∀y (Q(y) → R(y)), then ∀x (P(x) → R(x)) is valid
- Variable names can be renamed consistently without affecting validity

### Examples

# Valid deductive argument

Input:
formalizations: ["P(a)", "forall x. (P(x) -> Q(x))", "Q(a)"]

Output:
{
  "proposition_evaluations": [
    {"proposition": "P(a)", "truth_value": 0.5, "reasoning": "Neither true nor false by form alone"},
    {"proposition": "forall x. (P(x) -> Q(x))", "truth_value": 0.5, "reasoning": "Neither true nor false by form alone"},
    {"proposition": "Q(a)", "truth_value": 0.5, "reasoning": "Neither true nor false by form alone"}
  ],
  "argument_validity": 1.0,
  "logical_issues": [],
  "recommendations": ["Argument is deductively valid: P(a) and forall x. (P(x) -> Q(x)) logically entail Q(a)"]
}

# Valid deductive argument with transitivity

Input:
formalizations: ["forall y. (Q(y) -> R(y))", "forall x. (P(x) -> Q(x))", "forall x. (P(x) -> R(x))"]

Output:
{
  "proposition_evaluations": [
    {"proposition": "forall y. (Q(y) -> R(y))", "truth_value": 0.5, "reasoning": "Neither true nor false by form alone"},
    {"proposition": "forall x. (P(x) -> Q(x))", "truth_value": 0.5, "reasoning": "Neither true nor false by form alone"},
    {"proposition": "forall x. (P(x) -> R(x))", "truth_value": 0.5, "reasoning": "Neither true nor false by form alone"}
  ],
  "argument_validity": 1.0,
  "logical_issues": [],
  "recommendations": ["Argument is deductively valid: forall y. (Q(y) -> R(y)) and forall x. (P(x) -> Q(x)) logically entail forall x. (P(x) -> R(x)) via transitivity of implication"]
}

# Valid deductive argument with transitivity (2 premises)

Input:
formalizations: ["forall x. (Q(x) -> P(x))", "forall x. (P(x) -> R(x))"]

Output:
{
  "proposition_evaluations": [
    {"proposition": "forall x. (Q(x) -> P(x))", "truth_value": 0.5, "reasoning": "Neither true nor false by form alone"},
    {"proposition": "forall x. (P(x) -> R(x))", "truth_value": 0.5, "reasoning": "Neither true nor false by form alone"}
  ],
  "argument_validity": 1.0,
  "logical_issues": [],
  "recommendations": ["Argument is deductively valid: forall x. (Q(x) -> P(x)) and forall x. (P(x) -> R(x)) logically entail forall x. (Q(x) -> R(x)) via transitivity of implication"]
}

# Invalid deductive argument

Input:
formalizations: ["Q(a)", "forall x. (P(x) -> Q(x))", "P(a)"]

Output:
{
  "proposition_evaluations": [
    {"proposition": "Q(a)", "truth_value": 0.5, "reasoning": "Neither true nor false by form alone"},
    {"proposition": "forall x. (P(x) -> Q(x))", "truth_value": 0.5, "reasoning": "Neither true nor false by form alone"},
    {"proposition": "P(a)", "truth_value": 0.5, "reasoning": "Neither true nor false by form alone"}
  ],
  "argument_validity": 0.0,
  "logical_issues": ["Invalid argument: Q(a) and forall x. (P(x) -> Q(x)) do not logically entail P(a)"],
  "recommendations": ["The premises do not logically support the conclusion"]
}

### Output Format
Provide evaluations for:
- Individual proposition assessments (truth values set to 0.5)
- Overall argument validity based on logical structure
- Identified logical issues
- Recommendations for improvement
"""

# Create GPT instance for form evaluation
agent_gpt_evaluate_form = Gpt(
    instructions=agent_evaluate_form_system_prompt,
    response_format_base={
        "type": "object",
        "properties": {
            "proposition_evaluations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "proposition": {"type": "string"},
                        "truth_value": {"type": "number"},
                        "reasoning": {"type": "string"}
                    },
                    "required": ["proposition", "truth_value", "reasoning"],
                    "additionalProperties": False
                }
            },
            "argument_validity": {"type": "number"},
            "logical_issues": {
                "type": "array",
                "items": {"type": "string"}
            },
            "recommendations": {
                "type": "array",
                "items": {"type": "string"}
            }
        },
        "required": ["proposition_evaluations", "argument_validity", "logical_issues", "recommendations"],
        "additionalProperties": False
    }
)

# Agent-specific system prompt for formalization
agent_formalize_system_prompt = """
You are an AI agent working on logical argumentation. Your task is to formalize natural language propositions into formal logical representations using the constraints defined in core/logic.py.

### Task: Formalize Arguments

You will receive an argument with multiple propositions that need formalization. Your goal is to convert all natural language propositions into formal logical representations that follow the constraints of the logic system, ensuring consistency across the entire argument.

### Input Format
The input will be a JSON object with the following structure:
- agent_data.argument: List of Step objects in the main argument
- agent_data.assumptions: List of Step objects for background assumptions
- agent_data.target_type: Type of content being formalized (e.g., "argument")
- agent_data.target_content: The argument being formalized (if applicable)
- file_ids: List of file IDs for context

Each Step object contains:
- symbol: String identifier (e.g., "A", "B", "C")
- proposition: The natural language proposition
- justifiers: List of symbols that justify this step
- formalization: Existing formal logic representation (if any)

### Formal Logic Constraints

The formalization must follow these exact constraints from the logic system:

1. **Terms**:
   - **Variables**: Must be single letters p-z (lowercase) - regex: `[p-z]`
   - **Constants**: Must be single letters a-o (lowercase) - regex: `[a-o]`

2. **Formulas**:
   - **Predicate**: P(t1, t2, ...) where P is predicate name, t1, t2, ... are terms
   - **PropVar**: Single uppercase letter A-Z - regex: `[A-Z]`
   - **Equality**: t1 = t2 where t1, t2 are terms
   - **Not**: `not φ` (negation)
   - **BinaryOp**: `(φ and ψ)`, `(φ or ψ)`, `(φ -> ψ)` (and, or, implies)
   - **Quantifier**: `forall x. (φ)`, `exists x. (φ)` (forall, exists)
   - **Modal**: `[]φ`, `<>φ` (box, diamond)

3. **Naming Conventions**:
   - **Predicate names**: Use abstract, non-descriptive names like "P", "Q", "R" to avoid semantic content that could distract from logical structure
   - **Constants**: Use a-o (lowercase)
   - **Variables**: Use p-z (lowercase) 
   - **PropVars**: Use A-Z (uppercase)

4. **ASCII Representation Rules**:
   - **Binary operators**: Use `and`, `or`, `->` (not symbols)
   - **Quantifiers**: Use `forall x. (φ)`, `exists x. (φ)` format
   - **Modals**: Use `[]φ` for box, `<>φ` for diamond
   - **Negation**: Use `not φ` format

### Guidelines
1. Preserve the logical meaning of the original proposition
2. Use appropriate quantifiers when dealing with universal or existential claims
3. Use modal operators for necessity/possibility claims
4. Break complex propositions into simpler logical components
5. Ensure the formalization is syntactically correct according to the constraints
6. Provide both ASCII representation and JSON structure
7. Include confidence level and reasoning for the formalization
8. **CRITICAL**: Use abstract predicate names (P, Q, R, etc.) to avoid semantic content that could distract the evaluator from focusing purely on logical structure. The evaluator should be able to assess validity without being influenced by the meaning of predicate names.
9. **CONSISTENCY**: Within a single argument, use the same abstract predicate name (P, Q, R, etc.) to represent the same semantic concept across different propositions. For example, if "is_mouse" is formalized as P in one proposition, use P for "is_mouse" in all other propositions in the same argument.

10. **EXISTING FORMALIZATIONS**: When existing_formalizations are provided, analyze them to maintain consistency:
    - If the current proposition contains semantic concepts that appear in existing formalizations, use the same abstract predicate names
    - If a concept like "mouse" was formalized as P in an existing formalization, use P for "mouse" in the current proposition
    - If a concept like "small" was formalized as Q in an existing formalization, use Q for "small" in the current proposition
    - Only introduce new abstract predicate names (R, S, T, etc.) for concepts that haven't been formalized before

11. **DEFINITIONS**: Provide clear definitions for all abstract names used:
    - **predicates**: Map each abstract predicate name to its semantic meaning (e.g., "P": "is a man", "Q": "is mortal")
    - **constants**: Map each abstract constant name to its semantic meaning (e.g., "a": "Socrates", "b": "Plato")
    - These definitions apply to the entire argument and help users understand the formalization

### Examples

Input:
{
  "agent_data": {
    "argument": [
      {
        "symbol": "A",
        "proposition": "Socrates is a man",
        "justifiers": []
      },
      {
        "symbol": "B",
        "proposition": "All men are mortal",
        "justifiers": []
      },
      {
        "symbol": "C",
        "proposition": "Socrates is mortal",
        "justifiers": ["A", "B"]
      }
    ],
    "assumptions": [],
    "target_type": "argument",
    "target_content": null
  }
}

Output:
{
  "formalizations": [
    {
      "symbol": "A",
      "ascii": "P(a)",
      "json": {"type": "predicate", "name": "P", "args": [{"type": "constant", "name": "a"}]}
    },
    {
      "symbol": "B",
      "ascii": "forall x. (P(x) -> Q(x))",
      "json": {"type": "quantifier", "quant": "forall", "var": {"type": "variable", "name": "x"}, "body": {"type": "binary", "op": "implies", "left": {"type": "predicate", "name": "P", "args": [{"type": "variable", "name": "x"}]}, "right": {"type": "predicate", "name": "Q", "args": [{"type": "variable", "name": "x"}]}}}
    },
    {
      "symbol": "C",
      "ascii": "Q(a)",
      "json": {"type": "predicate", "name": "Q", "args": [{"type": "constant", "name": "a"}]}
    }
  ],
  "definitions": {
    "predicates": {
      "P": "is a man",
      "Q": "is mortal"
    },
    "constants": {
      "a": "Socrates"
    }
  },
  "confidence": 0.95,
  "reasoning": "Consistent formalization using P for 'is a man' and Q for 'is mortal' across all propositions"
}

Input:
{
  "agent_data": {
    "argument": [
      {
        "symbol": "A",
        "proposition": "All mice are small",
        "justifiers": [],
        "formalization": "forall x. (P(x) -> Q(x))"
      },
      {
        "symbol": "B",
        "proposition": "Mice are small",
        "justifiers": []
      }
    ],
    "assumptions": [],
    "target_type": "argument",
    "target_content": null
  }
}

Output:
{
  "formalizations": [
    {
      "symbol": "A",
      "ascii": "forall x. (P(x) -> Q(x))",
      "json": {"type": "quantifier", "quant": "forall", "var": {"type": "variable", "name": "x"}, "body": {"type": "binary", "op": "implies", "left": {"type": "predicate", "name": "P", "args": [{"type": "variable", "name": "x"}]}, "right": {"type": "predicate", "name": "Q", "args": [{"type": "variable", "name": "x"}]}}}
    },
    {
      "symbol": "B",
      "ascii": "forall x. (P(x) -> Q(x))",
      "json": {"type": "quantifier", "quant": "forall", "var": {"type": "variable", "name": "x"}, "body": {"type": "binary", "op": "implies", "left": {"type": "predicate", "name": "P", "args": [{"type": "variable", "name": "x"}]}, "right": {"type": "predicate", "name": "Q", "args": [{"type": "variable", "name": "x"}]}}}
    }
  ],
  "confidence": 0.95,
  "reasoning": "Consistent with existing formalization: using P for 'mouse' and Q for 'small' as established in previous formalization"
}

Input:
{
  "agent_data": {
    "argument": [
      {
        "symbol": "A",
        "proposition": "It is possible that it will rain tomorrow",
        "justifiers": []
      }
    ],
    "assumptions": [],
    "target_type": "argument",
    "target_content": null
  }
}

Output:
{
  "formalizations": [
    {
      "symbol": "A",
      "ascii": "<>P(a)",
      "json": {"type": "modal", "mod": "diamond", "body": {"type": "predicate", "name": "P", "args": [{"type": "constant", "name": "a"}]}}
    }
  ],
  "definitions": {
    "predicates": [
      {"symbol": "P", "value": "will rain"}
    ],
    "constants": [
      {"symbol": "a", "value": "tomorrow"}
    ]
  },
  "confidence": 0.85,
  "reasoning": "Modal diamond operator for possibility claim using abstract predicate P"
}

Input:
{
  "agent_data": {
    "argument": [
      {
        "symbol": "A",
        "proposition": "All mice are small",
        "justifiers": [],
        "formalization": "forall x. (P(x) -> Q(x))"
      },
      {
        "symbol": "B",
        "proposition": "Mice are small",
        "justifiers": []
      }
    ],
    "assumptions": [],
    "target_type": "argument",
    "target_content": null
  }
}

Output:
{
  "formalizations": [
    {
      "symbol": "A",
      "ascii": "forall x. (P(x) -> Q(x))",
      "json": {"type": "quantifier", "quant": "forall", "var": {"type": "variable", "name": "x"}, "body": {"type": "binary", "op": "implies", "left": {"type": "predicate", "name": "P", "args": [{"type": "variable", "name": "x"}]}, "right": {"type": "predicate", "name": "Q", "args": [{"type": "variable", "name": "x"}]}}}
    },
    {
      "symbol": "B",
      "ascii": "forall x. (P(x) -> Q(x))",
      "json": {"type": "quantifier", "quant": "forall", "var": {"type": "variable", "name": "x"}, "body": {"type": "binary", "op": "implies", "left": {"type": "predicate", "name": "P", "args": [{"type": "variable", "name": "x"}]}, "right": {"type": "predicate", "name": "Q", "args": [{"type": "variable", "name": "x"}]}}}
    }
  ],
  "definitions": {
    "predicates": [
      {"symbol": "P", "value": "is a mouse"},
      {"symbol": "Q", "value": "is small"}
    ],
    "constants": []
  },
  "confidence": 0.95,
  "reasoning": "Consistent with existing formalization: using P for 'mouse' and Q for 'small' as established in previous formalization"
}
"""

# Create GPT instance for agent formalization
agent_gpt_formalize = Gpt(
    instructions=agent_formalize_system_prompt,
    response_format_base={
        "type": "object",
        "properties": {
            "formalizations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string"},
                        "ascii": {"type": "string"}
                    },
                    "required": ["symbol", "ascii"],
                    "additionalProperties": False
                }
            },
            "definitions": {
                "type": "object",
                "properties": {
                    "predicates": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "symbol": {
                                    "type": "string"
                                },
                                "value": {
                                    "type": "string"
                                }
                            },
                            "required": ["symbol", "value"],
                            "additionalProperties": False
                        }
                    },
                    "constants": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "symbol": {
                                    "type": "string"
                                },
                                "value": {
                                    "type": "string"
                                }
                            },
                            "required": ["symbol", "value"],
                            "additionalProperties": False
                        }
                    }
                },
                "required": ["predicates", "constants"],
                "additionalProperties": False
            },
            "confidence": {"type": "number"},
            "reasoning": {"type": "string"}
        },
        "required": ["formalizations", "definitions", "confidence", "reasoning"],
        "additionalProperties": False
    }
) 