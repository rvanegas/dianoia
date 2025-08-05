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
- target_loc: Location in argument structure ('argument' or 'counter_argument')
- target_index: Position in the argument (the proposition is extracted from argument[target_index])
- argument: Full list of propositions in the main argument
- counter_argument: Full list of propositions in the counter-argument
- assumptions: List of background assumptions (for context only, not justified)
- formalization_context: Optional formal logical representation to guide your justification

Note: The proposition field is inferred from the argument structure at the specified location and index to ensure consistency. Only propositions in 'argument' or 'counter_argument' can be justified - assumptions are foundational premises that are not justified.

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
counter_argument: []
assumptions: []

Output:
["All men are mortal.", "Socrates is a man."]

Input:
proposition: "The economy will improve"
target_loc: "argument"
target_index: 1
argument: ["Government stimulus measures are effective", "The economy will improve"]
counter_argument: ["Inflation will increase"]
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
You are an AI agent working on logical argumentation. Your task is to evaluate the truth, validity, and soundness of propositions and arguments based on their content.

For the purposes of this task, we define "valid" to accord with its sense in mathematical logic, not its more general and equivocal sense in debate or rhetoric. Validity is strict formal validity, _not_ soundness. The validity of an argument is not affected by the truth of its premises or conclusion.

### Input Format
- argument: List of propositions in the main argument
- counter_argument: List of propositions in the counter-argument  
- assumptions: List of background assumptions
- thesis: The main thesis being argued
- counter_thesis: The opposing thesis (if any)

### Task

You will receive argument data including propositions and context. You will evaluate the propositions and return an array of numbers from 0.0 to 1.0, rounded to nearest 0.05, each corresponding to a given proposition from "argument" in the same order. This array is returned as the "truth" property.

Additionally, concerning the last proposition in the list, you will return one number from 0.0 to 1.0, rounded to the nearest 0.05, corresponding to the validity of the inference from the other propositions to the last one. That is, assuming that the other propositions in "argument", and all those in "assumptions", are certainly true, then this number represents the likelihood that the last proposition in "argument" is true. In case of deduction, set value to 1.0. In case of contradiction, set value to 0.0. Otherwise, determine the implicit premise that would make the inference a deduction. This number is returned as the "valid" property.

### Considerations

For each proposition in "argument", the number returned in the "truth" array should be 1.0 if the proposition is certainly true given the assumptions, 0.0 if it is certainly false given the assumptions, or a value representing the degree of likelihood given the assumptions.

### Examples

# valid but not sound

(A) Socrates is a god.
(B) All gods are immortal.
(C) Socrates is immortal.

truth: [0.0, 1.0, 0.0]
valid: 1.0

# valid and sound

(A) Socrates is a man.
(B) All men are mortal.
(C) Socrates is mortal.

truth: [1.0, 1.0, 1.0]
valid: 1.0

# partly valid

(A) Socrates is a man.
(B) Most men are mortal.
(C) Socrates is mortal.

truth: [1.0, 1.0, 1.0]
valid: 0.7

# deductively invalid though true, abductively reasonable

(A) Socrates is mortal.
(B) All men are mortal
(C) Socrates is a man.

truth: [1.0, 1.0, 1.0]
valid: 0.2

### Output Format
Provide evaluations for:
- Individual proposition assessments (truth values)
- Overall argument validity
- Identified logical issues
- Recommendations for improvement

### Examples

Input:
thesis: "Socrates is mortal"
argument: ["Socrates is a man", "All men are mortal", "Socrates is mortal"]
counter_argument: []
assumptions: []

Output:
{
  "proposition_evaluations": [
    {"proposition": "Socrates is a man", "truth_value": 0.9, "reasoning": "Historical fact"},
    {"proposition": "All men are mortal", "truth_value": 0.95, "reasoning": "Universal biological truth"},
    {"proposition": "Socrates is mortal", "truth_value": 0.9, "reasoning": "Valid conclusion from premises"}
  ],
  "argument_validity": 0.95,
  "logical_issues": [],
  "recommendations": ["Argument is logically sound and well-structured"]
}
"""

# Create GPT instance for content evaluation
agent_gpt_evaluate_content = Gpt(
    instructions=agent_evaluate_content_system_prompt,
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

# Agent-specific system prompt for form evaluation
agent_evaluate_form_system_prompt = """
You are an AI agent working on logical argumentation. Your task is to evaluate ONLY the logical validity of formalized arguments, ignoring the truth of individual propositions.

For the purposes of this task, we define "valid" to accord with its sense in mathematical logic, not its more general and equivocal sense in debate or rhetoric. Validity is strict formal validity, _not_ soundness. The validity of an argument is not affected by the truth of its premises or conclusion.

### Input Format
- argument: List of propositions in the main argument
- counter_argument: List of propositions in the counter-argument  
- assumptions: List of background assumptions
- thesis: The main thesis being argued
- counter_thesis: The opposing thesis (if any)
- formalizations: List of formal logical representations of the propositions

### Task

You will receive argument data including propositions and their formalizations. You will evaluate ONLY the logical validity of the argument structure, ignoring the truth of individual propositions.

For each proposition, set truth_value to 0.5 (neither true nor false by form alone) and focus entirely on whether the logical structure is valid.

The argument_validity should reflect the formal logical validity of the argument structure, not the truth of the premises or conclusion.

### Considerations

- Set all proposition truth_values to 0.5 (neither true nor false by form alone)
- Focus entirely on the logical structure and validity of the argument
- Evaluate whether the conclusion follows logically from the premises
- Ignore the semantic content and truth of individual propositions
- Consider only the formal logical relationships between propositions
- Use the formalizations to assess logical validity

### Examples

# Valid deductive argument

Input:
argument: ["Socrates is a man", "All men are mortal", "Socrates is mortal"]
formalizations: ["P(a)", "forall x. (P(x) -> Q(x))", "Q(a)"]

Output:
{
  "proposition_evaluations": [
    {"proposition": "Socrates is a man", "truth_value": 0.5, "reasoning": "Neither true nor false by form alone"},
    {"proposition": "All men are mortal", "truth_value": 0.5, "reasoning": "Neither true nor false by form alone"},
    {"proposition": "Socrates is mortal", "truth_value": 0.5, "reasoning": "Neither true nor false by form alone"}
  ],
  "argument_validity": 1.0,
  "logical_issues": [],
  "recommendations": ["Argument is deductively valid: P(a) and forall x. (P(x) -> Q(x)) logically entail Q(a)"]
}

# Invalid deductive argument

Input:
argument: ["Socrates is mortal", "All men are mortal", "Socrates is a man"]
formalizations: ["Q(a)", "forall x. (P(x) -> Q(x))", "P(a)"]

Output:
{
  "proposition_evaluations": [
    {"proposition": "Socrates is mortal", "truth_value": 0.5, "reasoning": "Neither true nor false by form alone"},
    {"proposition": "All men are mortal", "truth_value": 0.5, "reasoning": "Neither true nor false by form alone"},
    {"proposition": "Socrates is a man", "truth_value": 0.5, "reasoning": "Neither true nor false by form alone"}
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

### Task: Formalize Propositions

You will receive a proposition that needs formalization. Your goal is to convert the natural language proposition into a formal logical representation that follows the constraints of the logic system.

### Input Format
- proposition: The natural language proposition to formalize
- argument_data: Full argument context including all propositions and structure
- file_ids: List of file IDs for context
- existing_formalizations: List of existing formalizations in the same argument for consistency

### Formal Logic Constraints

The formalization must follow these constraints from core/logic.py:

1. **Terms**:
   - Variables: Must be single letters p-z (lowercase)
   - Constants: Must be single letters a-o (lowercase)

2. **Formulas**:
   - Predicate: P(t1, t2, ...) where P is predicate name, t1, t2, ... are terms
   - PropVar: Single uppercase letter A-Z
   - Equality: t1 = t2 where t1, t2 are terms
   - Not: not φ (negation)
   - BinaryOp: φ and ψ, φ or ψ, φ -> ψ (and, or, implies)
   - Quantifier: forall x.φ, exists x.φ (forall, exists)
   - Modal: []φ, <>φ (box, diamond)

3. **Naming Conventions**:
   - Predicate names: Use abstract, non-descriptive names like "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z" to avoid semantic content that could distract from logical structure
   - Variables: Use p, q, r, s, t, u, v, w, x, y, z
   - Constants: Use a, b, c, d, e, f, g, h, i, j, k, l, m, n, o
   - PropVars: Use A, B, C, D, E, F, G, H, I, J, K, L, M, N, O, P, Q, R, S, T, U, V, W, X, Y, Z

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

### Examples

Input:
proposition: "Socrates is mortal"
argument_data: {"argument": [{"proposition": "Socrates is a man"}, {"proposition": "All men are mortal"}, {"proposition": "Socrates is mortal"}]}

Output:
{
  "formalization": {
    "ascii": "P(a)",
    "json": {"type": "predicate", "name": "P", "args": [{"type": "constant", "name": "a"}]}
  },
  "confidence": 0.95,
  "reasoning": "Direct predicate application for individual property using abstract predicate P"
}

Input:
proposition: "All men are mortal"
argument_data: {"argument": [{"proposition": "Socrates is a man"}, {"proposition": "All men are mortal"}, {"proposition": "Socrates is mortal"}]}

Output:
{
  "formalization": {
    "ascii": "forall x. (P(x) -> Q(x))",
    "json": {"type": "quantifier", "quant": "forall", "var": {"type": "variable", "name": "x"}, "body": {"type": "binary", "op": "implies", "left": {"type": "predicate", "name": "P", "args": [{"type": "variable", "name": "x"}]}, "right": {"type": "predicate", "name": "Q", "args": [{"type": "variable", "name": "x"}]}}}
  },
  "confidence": 0.9,
  "reasoning": "Universal quantification with conditional for 'all' statement using abstract predicates P and Q"
}

Input:
proposition: "It is possible that it will rain tomorrow"
argument_data: {"argument": [{"proposition": "It is possible that it will rain tomorrow"}]}

Output:
{
  "formalization": {
    "ascii": "<>P(a)",
    "json": {"type": "modal", "mod": "diamond", "body": {"type": "predicate", "name": "P", "args": [{"type": "constant", "name": "a"}]}}
  },
  "confidence": 0.85,
  "reasoning": "Modal diamond operator for possibility claim using abstract predicate P"
}

Input:
proposition: "Mice are small"
existing_formalizations: [
  {"proposition": "All mice are small", "formalization": "forall x. (P(x) -> Q(x))", "reasoning": "Universal quantification with conditional using abstract predicates P and Q"}
]

Output:
{
  "formalization": {
    "ascii": "forall x. (P(x) -> Q(x))",
    "json": {"type": "quantifier", "quant": "forall", "var": {"type": "variable", "name": "x"}, "body": {"type": "binary", "op": "implies", "left": {"type": "predicate", "name": "P", "args": [{"type": "variable", "name": "x"}]}, "right": {"type": "predicate", "name": "Q", "args": [{"type": "variable", "name": "x"}]}}}
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
            "formalization": {
                "type": "object",
                "properties": {
                    "ascii": {"type": "string"}
                },
                "required": ["ascii"],
                "additionalProperties": False
            },
            "confidence": {"type": "number"},
            "reasoning": {"type": "string"}
        },
        "required": ["formalization", "confidence", "reasoning"],
        "additionalProperties": False
    }
) 