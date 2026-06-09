from pathlib import Path
from services.conversation import ModelAgent

_PROJECT_ROOT = Path(__file__).parent.parent.parent
_LOGIC_ASCII = (_PROJECT_ROOT / "LOGIC-ASCII.md").read_text()
_LOGIC_JSON  = (_PROJECT_ROOT / "LOGIC-JSON.md").read_text()

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
agent_gpt_justify = ModelAgent(
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

# Agent-specific system prompt for truth evaluation
agent_evaluate_truth_system_prompt = """
You are an AI agent working on logical argumentation. Your task is to evaluate the independent truth of each proposition and identify mutually incoherent sets.

Evaluate each proposition entirely on its own merits — empirical evidence, background knowledge, and logical consistency. Do NOT reason about whether propositions support each other or follow from each other; that is a separate task.

### Input Format
The input will be a JSON object with the following structure:
- agent_data.argument: List of Step objects to evaluate
- agent_data.assumptions: List of Step objects taken as true by the user (do NOT evaluate these)

Each Step object contains:
- symbol: String identifier (e.g., "1", "2", "3")
- proposition: The natural language proposition

### Task

1. **Truth Evaluation**: For each argument step, assess the independent truth of its proposition.
   - 1.0 = certainly true, 0.0 = certainly false, intermediate values in increments of 0.1
   - Consider empirical evidence and background knowledge only
   - Do NOT evaluate assumptions

2. **Coherence Analysis**: Identify sets of propositions that cannot all be true simultaneously.
   - 1.0 = logical contradiction, lower values for lesser degrees of incoherence
   - Only report sets where there is genuine incompatibility

### Examples

# Sound argument

Input:
{
  "agent_data": {
    "argument": [
      {"symbol": "1", "proposition": "Socrates is a man"},
      {"symbol": "2", "proposition": "All men are mortal"},
      {"symbol": "3", "proposition": "Socrates is mortal"}
    ],
    "assumptions": []
  }
}

Output:
{
  "truth_evaluations": [
    {"symbol": "1", "truth_value": 0.95, "reasoning": "Historical fact, well-documented"},
    {"symbol": "2", "truth_value": 0.98, "reasoning": "Universal biological truth, no known exceptions"},
    {"symbol": "3", "truth_value": 0.95, "reasoning": "Well-established historical and biological fact"}
  ],
  "incoherent_sets": []
}

# False premise, true conclusion

Input:
{
  "agent_data": {
    "argument": [
      {"symbol": "1", "proposition": "Socrates is a god"},
      {"symbol": "2", "proposition": "All gods are immortal"},
      {"symbol": "3", "proposition": "Socrates is mortal"}
    ],
    "assumptions": []
  }
}

Output:
{
  "truth_evaluations": [
    {"symbol": "1", "truth_value": 0.0, "reasoning": "Contradicts historical and theological knowledge — Socrates was human"},
    {"symbol": "2", "truth_value": 0.7, "reasoning": "Common theological assumption across traditions, though contested"},
    {"symbol": "3", "truth_value": 0.95, "reasoning": "Historical fact — Socrates died in 399 BC"}
  ],
  "incoherent_sets": []
}

# Mutually incoherent propositions

Input:
{
  "agent_data": {
    "argument": [
      {"symbol": "1", "proposition": "All humans are mortal"},
      {"symbol": "2", "proposition": "Socrates is human"},
      {"symbol": "3", "proposition": "Socrates is immortal"}
    ],
    "assumptions": []
  }
}

Output:
{
  "truth_evaluations": [
    {"symbol": "1", "truth_value": 0.98, "reasoning": "Universal biological truth"},
    {"symbol": "2", "truth_value": 0.95, "reasoning": "Historical fact"},
    {"symbol": "3", "truth_value": 0.0, "reasoning": "Contradicts well-established fact — Socrates died in 399 BC"}
  ],
  "incoherent_sets": [
    {"symbols": ["1", "2", "3"], "incoherence_value": 1.0}
  ]
}

# Argument with assumptions (do NOT evaluate assumptions)

Input:
{
  "agent_data": {
    "argument": [
      {"symbol": "2", "proposition": "The sun has legs"}
    ],
    "assumptions": [
      {"symbol": "1", "proposition": "The sun has four legs"}
    ]
  }
}

Output:
{
  "truth_evaluations": [
    {"symbol": "2", "truth_value": 0.0, "reasoning": "False — the sun is a star and has no legs"}
  ],
  "incoherent_sets": []
}
"""

agent_gpt_evaluate_truth = ModelAgent(
    instructions=agent_evaluate_truth_system_prompt,
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
            "incoherent_sets": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "symbols": {"type": "array", "items": {"type": "string"}},
                        "incoherence_value": {"type": "number"}
                    },
                    "required": ["symbols", "incoherence_value"],
                    "additionalProperties": False
                }
            }
        },
        "required": ["truth_evaluations", "incoherent_sets"],
        "additionalProperties": False
    },
    max_tokens=8192
)

# Agent-specific system prompt for content validity evaluation
agent_evaluate_content_validity_system_prompt = """
You are an AI agent working on logical argumentation. Your task is to evaluate the inferential strength of each conclusion in a natural language argument — that is, how well each proposition follows from its stated justifiers.

Do NOT evaluate the independent truth of propositions. Truth is assessed separately. Focus exclusively on the logical relationship between each step and its justifiers.

### Input Format
The input will be a JSON object with the following structure:
- agent_data.argument: List of Step objects in the main argument
- agent_data.assumptions: List of Step objects for background assumptions (taken as true)

Each Step object contains:
- symbol: String identifier (e.g., "1", "2", "3")
- proposition: The natural language proposition
- justifiers: List of symbols that justify this step (empty list = premise, no inference to evaluate)

### Task

1. **Validity Assessment**: For each step WITH justifiers, evaluate the inferential strength from its justifiers to its proposition.
   - 1.0 = deductively valid (conclusion must be true if justifiers are true)
   - 0.0 = contradictory (conclusion contradicts justifiers)
   - Intermediate values for inductive or abductive strength
   - Steps WITHOUT justifiers are premises — do not assign validity values to them

2. **Logical Issues**: Identify structural weaknesses in the argument (missing steps, equivocation, non-sequiturs, etc.)

3. **Recommendations**: Suggest specific improvements to strengthen weak inferences

### Examples

# Deductively valid argument

Input:
{
  "agent_data": {
    "argument": [
      {"symbol": "1", "proposition": "Socrates is a man", "justifiers": []},
      {"symbol": "2", "proposition": "All men are mortal", "justifiers": []},
      {"symbol": "3", "proposition": "Socrates is mortal", "justifiers": ["1", "2"]}
    ],
    "assumptions": []
  }
}

Output:
{
  "validity_evaluations": [
    {"symbol": "3", "validity_value": 1.0, "reasoning": "Valid deduction: if Socrates is a man and all men are mortal, Socrates must be mortal"}
  ],
  "logical_issues": [],
  "recommendations": ["Argument is deductively valid"]
}

# Contradictory conclusion

Input:
{
  "agent_data": {
    "argument": [
      {"symbol": "1", "proposition": "All humans are mortal", "justifiers": []},
      {"symbol": "2", "proposition": "Socrates is human", "justifiers": []},
      {"symbol": "3", "proposition": "Socrates is immortal", "justifiers": ["1", "2"]}
    ],
    "assumptions": []
  }
}

Output:
{
  "validity_evaluations": [
    {"symbol": "3", "validity_value": 0.0, "reasoning": "Contradiction: justifiers 1 and 2 entail Socrates is mortal, the opposite of the stated conclusion"}
  ],
  "logical_issues": ["Conclusion contradicts what the premises entail"],
  "recommendations": ["Correct the conclusion to match what follows from the premises"]
}

# Weak analogical inference

Input:
{
  "agent_data": {
    "argument": [
      {"symbol": "1", "proposition": "The policy worked in another country", "justifiers": []},
      {"symbol": "2", "proposition": "Our country is similar", "justifiers": []},
      {"symbol": "3", "proposition": "The policy will work here", "justifiers": ["1", "2"]}
    ],
    "assumptions": []
  }
}

Output:
{
  "validity_evaluations": [
    {"symbol": "3", "validity_value": 0.5, "reasoning": "Weak analogical inference: similarity is asserted vaguely and policy success may depend on factors not captured by general similarity"}
  ],
  "logical_issues": ["Analogical inference relies on an underspecified similarity claim"],
  "recommendations": [
    "Specify which features of similarity are relevant to policy success (2)",
    "Address potential disanalogies between the two countries"
  ]
}
"""

agent_gpt_evaluate_content_validity = ModelAgent(
    instructions=agent_evaluate_content_validity_system_prompt,
    response_format_base={
        "type": "object",
        "properties": {
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
            "logical_issues": {
                "type": "array",
                "items": {"type": "string"}
            },
            "recommendations": {
                "type": "array",
                "items": {"type": "string"}
            }
        },
        "required": ["validity_evaluations", "logical_issues", "recommendations"],
        "additionalProperties": False
    },
    max_tokens=8192
)

# Agent-specific system prompt for content evaluation (removed — replaced by truth_evaluator and content_validity_evaluator)
agent_evaluate_content_system_prompt = """
You are an AI agent working on logical argumentation. Your task is to evaluate the truth, validity, coherence, and identify weak inferences in natural language content.

For the purposes of this task, we define "valid" to accord with its sense in mathematical logic, not its more general and equivocal sense in debate or rhetoric. Validity is strict formal validity, _not_ soundness. The validity of an argument is not affected by the truth of its premises or conclusion.

### Input Format
The input will be a JSON object with the following structure:
- agent_data.argument: List of Step objects in the main argument (evaluate these for truth)
- agent_data.assumptions: List of Step objects for background assumptions (do NOT evaluate these - they are taken as true)
- agent_data.target_type: Type of content being evaluated (e.g., "argument", "proposition")
- agent_data.target_content: Specific content being targeted (if applicable)

Each Step object contains:
- symbol: String identifier (e.g., "1", "2", "3")
- proposition: The natural language proposition
- justifiers: List of symbols that justify this step
- content_validity: Content validity from previous evaluation (optional)
- formal_validity: Formal validity from previous evaluation (optional)
- formalization: Formal logic representation (optional)

### Task

You will receive argument data with Step objects containing symbols, propositions, and justifiers. You will evaluate and return comprehensive assessments including:

1. **Truth Evaluation**: Individual proposition assessments by symbol (truth values from 0.0 to 1.0)
2. **Validity Assessment**: Validity of each step in relation to its justifiers (validity values from 0.0 to 1.0)
3. **Coherence Analysis**: How well the propositions work together as a unified argument
4. **Weak Inference Identification**: Steps with the lowest validity scores

### Considerations

**Truth Evaluation**:
- For each Step in the argument, assess the truth value of its proposition given the assumptions
- IMPORTANT: Do NOT evaluate assumptions - they are taken as true by the user
- 1.0 = certainly true, 0.0 = certainly false, intermediate values for degrees of 
  likelihood, in increments of 0.1
- Consider empirical evidence, logical consistency, and background knowledge
- Return truth values indexed by Step symbol (only for argument steps, not assumptions)

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
        "symbol": "1",
        "proposition": "Socrates is a god",
        "justifiers": []
      },
      {
        "symbol": "2",
        "proposition": "All gods are immortal",
        "justifiers": []
      },
      {
        "symbol": "3",
        "proposition": "Socrates is immortal",
        "justifiers": ["1", "2"]
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
          {"symbol": "1", "truth_value": "0.0", "reasoning": "Contradicts historical and theological knowledge"},
      {"symbol": "2", "truth_value": "0.8", "reasoning": "Common theological assumption, though debatable"},
      {"symbol": "3", "truth_value": "0.0", "reasoning": "False conclusion from false premise"}
  ],
  "validity_evaluations": [
          {"symbol": "3", "validity_value": "1.0", "reasoning": "Valid deduction from 1 and 2, though premises are false"}
  ],

  "incoherent_sets": [],
  "logical_issues": ["Argument is valid but unsound due to false premise"],
  "recommendations": [
    "Replace false premise 1 with true statement about Socrates",
    "Provide evidence for theological assumptions in 2 if used"
  ]
}

# Argument with assumptions (assumptions are NOT evaluated)

Input:
{
  "agent_data": {
    "argument": [
      {
        "symbol": "2",
        "proposition": "The sun has legs",
        "justifiers": []
      }
    ],
    "assumptions": [
      {
        "symbol": "1",
        "proposition": "The sun has four legs",
        "justifiers": []
      }
    ],
    "target_type": "argument",
    "target_content": null
  }
}

Output:
{
  "truth_evaluations": [
          {"symbol": "2", "truth_value": "1.0", "reasoning": "True given the assumption that the sun has four legs"}
  ],
  "validity_evaluations": [],
  "incoherent_sets": [],
  "logical_issues": [],
  "recommendations": ["Argument is valid given the assumptions"]
}

# Coherent and sound argument

Input:
{
  "agent_data": {
    "argument": [
      {
        "symbol": "1",
        "proposition": "Socrates is a man",
        "justifiers": []
      },
      {
        "symbol": "2",
        "proposition": "All men are mortal",
        "justifiers": []
      },
      {
        "symbol": "3",
        "proposition": "Socrates is mortal",
        "justifiers": ["1", "2"]
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
          {"symbol": "1", "truth_value": "0.95", "reasoning": "Historical fact, well-documented"},
      {"symbol": "2", "truth_value": "0.98", "reasoning": "Universal biological truth, no known exceptions"},
      {"symbol": "3", "truth_value": "0.95", "reasoning": "Valid conclusion from true premises"}
  ],
  "validity_evaluations": [
          {"symbol": "3", "validity_value": "1.0", "reasoning": "Valid deduction from 1 and 2"}
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
        "symbol": "1",
        "proposition": "All humans are mortal",
        "justifiers": []
      },
      {
        "symbol": "2",
        "proposition": "Socrates is human",
        "justifiers": []
      },
      {
        "symbol": "3",
        "proposition": "Socrates is immortal",
        "justifiers": ["1", "2"]
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
          {"symbol": "1", "truth_value": "0.98", "reasoning": "Universal biological truth"},
      {"symbol": "2", "truth_value": "0.95", "reasoning": "Historical fact"},
      {"symbol": "3", "truth_value": "0.0", "reasoning": "Contradicts premises 1 and 2"}
  ],
  "validity_evaluations": [
          {"symbol": "3", "validity_value": "0.0", "reasoning": "Logical contradiction with premises"}
  ],
  "incoherent_sets": [
    {
      "symbols": ["1", "2", "3"],
      "incoherence_value": "1.0"
    }
  ],
  "logical_issues": ["Contains logical contradiction"],
  "recommendations": [
    "Fix contradiction in 3 - Socrates cannot be both mortal (from 1+2) and immortal"
  ]
}

# Argument with weak inferences
{
  "agent_data": {
    "argument": [
      {
        "symbol": "1",
        "proposition": "The policy worked in another country",
        "justifiers": []
      },
      {
        "symbol": "2",
        "proposition": "Our country is similar",
        "justifiers": []
      },
      {
        "symbol": "3",
        "proposition": "The policy will work here",
        "justifiers": ["1", "2"]
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
          {"symbol": "1", "truth_value": "0.7", "reasoning": "Limited evidence, context-dependent"},
      {"symbol": "2", "truth_value": "0.6", "reasoning": "Vague similarity claim, needs specification"},
      {"symbol": "3", "truth_value": "0.5", "reasoning": "Weak conclusion from weak premises"}
  ],
  "validity_evaluations": [
          {"symbol": "3", "validity_value": "0.6", "reasoning": "Weak analogical inference from 1 and 2"}
  ],

  "incoherent_sets": [
    {
      "symbols": ["1", "2", "3"],
      "incoherence_value": "0.7"
    }
  ],
  "logical_issues": ["Relies on weak analogical reasoning"],
  "recommendations": [
    "Provide specific evidence of policy success in other country (1)",
    "Specify relevant similarities and differences between countries (2)",
    "Strengthen analogical reasoning in 3"
  ]
}
"""

# Agent-specific system prompt for form evaluation
agent_evaluate_form_system_prompt = """
You are an AI agent working on logical argumentation. Your task is to evaluate ONLY the logical validity of formalized arguments, ignoring the truth of individual propositions.

For the purposes of this task, we define "valid" to accord with its sense in mathematical logic, not its more general and equivocal sense in debate or rhetoric. Validity is strict formal validity, _not_ soundness. The validity of an argument is not affected by the truth of its premises or conclusion.

### Notation Reference

Formalizations use the following ASCII notation. Read this carefully before evaluating any formulas.

""" + _LOGIC_ASCII + """

### Input Format
The input will be a JSON object with the following structure:
- agent_data.argument: List of Step objects in the main argument
- agent_data.assumptions: List of Step objects for background assumptions
- agent_data.target_type: Type of content being evaluated (e.g., "argument")
- agent_data.target_content: Specific content being targeted (if applicable)

Each Step object contains:
- symbol: String identifier (e.g., "1", "2", "3")
- justifiers: List of symbols that justify this step
- formalization: Formal logic representation object with 'ascii' and 'json_structure' fields
- endorsed: Boolean indicating if the formalization is endorsed by the user

A step has a formalization when `formalization` is non-null, `formalization.endorsed` is true, and `formalization.ascii` is non-empty. Use `ascii` as the authoritative representation; `json_structure` may be null and should be ignored when it is.

### Task

You will receive argument data with Step objects containing formal logic representations. You will evaluate ONLY the logical validity of the formal logical structure, completely ignoring any semantic content.

**IMPORTANT**: The assumptions are additional premises in the argument. Treat assumptions as regular premises for the purposes of formal logical evaluation.

For each formalization, focus entirely on whether the logical structure is valid. Do not evaluate truth values.

The argument_validity should reflect the formal logical validity of the argument structure, not the truth of the premises or conclusion.

### Considerations

- Do not evaluate truth values - focus only on logical validity
- Focus entirely on the logical structure and validity of the argument
- Evaluate whether the conclusion follows logically from the premises
- Ignore the semantic content and truth of individual propositions
- Consider only the formal logical relationships between propositions
- Use the formalizations to assess logical validity
- **IMPORTANT**: Pay attention to variable renaming and the transitivity of implication
- When premises use different variable names (e.g., `forall y. Py implies Qy` and `forall x. Px implies Qx`), the argument can still be valid if the logical structure supports the conclusion
- The transitivity of implication means: if `forall x. Px implies Qx` and `forall y. Qy implies Ry`, then `forall x. Px implies Rx` is valid
- Variable names can be renamed consistently without affecting validity

### Examples

# Valid deductive argument with assumptions

Input:
{
  "agent_data": {
    "argument": [
      {
        "symbol": "2",
        "justifiers": [],
        "formalization": {
          "ascii": "Pa",
          "json_structure": "{\"type\": \"predicate\", \"name\": \"P\", \"args\": [{\"type\": \"constant\", \"name\": \"a\"}]}",
          "endorsed": true
        }
      },
      {
        "symbol": "3",
        "justifiers": ["1", "2"],
        "formalization": {
          "ascii": "Qa",
          "json_structure": "{\"type\": \"predicate\", \"name\": \"Q\", \"args\": [{\"type\": \"constant\", \"name\": \"a\"}]}",
          "endorsed": true
        }
      }
    ],
    "assumptions": [
      {
        "symbol": "1",
        "justifiers": [],
        "formalization": {
          "ascii": "forall x. Px implies Qx",
          "json_structure": "{\"type\": \"quantifier\", \"quant\": \"forall\", \"vars\": [{\"type\": \"variable\", \"name\": \"x\"}], \"body\": {\"type\": \"connective\", \"op\": \"implies\", \"args\": [{\"type\": \"predicate\", \"name\": \"P\", \"args\": [{\"type\": \"variable\", \"name\": \"x\"}]}, {\"type\": \"predicate\", \"name\": \"Q\", \"args\": [{\"type\": \"variable\", \"name\": \"x\"}]}]}}",
          "endorsed": true
        }
      }
    ],
    "target_type": "argument",
    "target_content": null
  }
}

Output:
{
  "proposition_evaluations": [
    {"symbol": "1", "validity": "1.0", "reasoning": "Premise - no validity to evaluate"},
    {"symbol": "2", "validity": "1.0", "reasoning": "Premise - no validity to evaluate"},
    {"symbol": "3", "validity": "1.0", "reasoning": "Valid conclusion from premises 1 and 2"}
  ],
  "argument_validity": "1.0",
  "logical_issues": [],
  "recommendations": ["Argument is deductively valid: Pa and forall x. Px implies Qx logically entail Qa"]
}

# Invalid deductive argument

Input:
{
  "agent_data": {
    "argument": [
      {
        "symbol": "1",
        "justifiers": [],
        "formalization": {
          "ascii": "forall x. Px implies Qx",
          "json_structure": "{\"type\": \"quantifier\", \"quant\": \"forall\", \"vars\": [{\"type\": \"variable\", \"name\": \"x\"}], \"body\": {\"type\": \"connective\", \"op\": \"implies\", \"args\": [{\"type\": \"predicate\", \"name\": \"P\", \"args\": [{\"type\": \"variable\", \"name\": \"x\"}]}, {\"type\": \"predicate\", \"name\": \"Q\", \"args\": [{\"type\": \"variable\", \"name\": \"x\"}]}]}}",
          "endorsed": true
        }
      },
      {
        "symbol": "2",
        "justifiers": [],
        "formalization": {
          "ascii": "Qa",
          "json_structure": "{\"type\": \"predicate\", \"name\": \"Q\", \"args\": [{\"type\": \"constant\", \"name\": \"a\"}]}",
          "endorsed": true
        }
      },
      {
        "symbol": "3",
        "justifiers": ["1", "2"],
        "formalization": {
          "ascii": "Pa",
          "json_structure": "{\"type\": \"predicate\", \"name\": \"P\", \"args\": [{\"type\": \"constant\", \"name\": \"a\"}]}",
          "endorsed": true
        }
      }
    ],
    "assumptions": [],
    "target_type": "argument",
    "target_content": null
  }
}

Output:
{
  "proposition_evaluations": [
    {"symbol": "1", "validity": "1.0", "reasoning": "Premise - no validity to evaluate"},
    {"symbol": "2", "validity": "1.0", "reasoning": "Premise - no validity to evaluate"},
    {"symbol": "3", "validity": "0.0", "reasoning": "Invalid conclusion - premises do not support this conclusion"}
  ],
  "argument_validity": "0.0",
  "logical_issues": ["Invalid argument: Qa and forall x. Px implies Qx do not logically entail Pa"],
  "recommendations": ["The premises do not logically support the conclusion"]
}

### Output Format
Provide evaluations for:
- Individual proposition validity assessments
- Overall argument validity based on logical structure
- Identified logical issues
- Recommendations for improvement
"""

# Create GPT instance for form evaluation
agent_gpt_evaluate_form = ModelAgent(
    instructions=agent_evaluate_form_system_prompt,
    response_format_base={
        "type": "object",
        "properties": {
            "proposition_evaluations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string"},
                        "validity": {"type": "number"},
                        "reasoning": {"type": "string"}
                    },
                    "required": ["symbol", "validity", "reasoning"],
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
You are an AI agent working on logical argumentation. Your task is to formalize natural language propositions into formal logical representations.

### Task: Formalize Arguments

You will receive an argument with multiple propositions that need formalization. Convert **all** propositions — both assumption steps and argument steps — into formal logical representations. **CRITICAL**: Do not skip assumptions.

### Input Format
- agent_data.argument: List of Step objects — **must be formalized**
- agent_data.assumptions: List of Step objects — **must also be formalized**

Each Step contains: symbol, proposition, justifiers, and optionally formalization (with endorsed flag).

### Formula JSON Structure

""" + _LOGIC_JSON + """

**Note on naming**: The guide above uses canonical single-letter symbols (P, Q, R, x, y, a, ...).
When writing your formalizations, use **descriptive semantic names** (`is_man`, `individual`, `socrates`, etc.) instead — Python normalization assigns canonical symbols automatically.
The `ascii` field you write is a human-readable hint and is replaced by a canonical representation; only `json_structure` is machine-read.

### Naming — use descriptive semantic names

Use **descriptive snake_case names** that capture the meaning of each concept:
- **Predicate names**: e.g., `is_man`, `is_mortal`, `runs_faster_than`, `is_raining` (for atomic propositions, use zero args)
- **Constant names**: e.g., `socrates`, `plato`, `the_earth`
- **Variable names**: any descriptive lowercase name, e.g., `individual`, `entity`, `thing`

Do **not** use abstract single-letter names (P, Q, R, a, b, x) — Python will assign canonical letters. Your job is to capture the correct logical structure and semantic meaning.

### Guidelines
1. Preserve the logical meaning of the original proposition
2. Use quantifiers for universal/existential claims (`forall individual. (...)`)
3. Use modal operators for necessity/possibility (`nec`, `pos`)
4. Use zero-argument predicates for atomic propositions (e.g., `is_raining()`)
5. For abstract claims that resist quantifier structure, use zero-argument predicates to name the key concepts: e.g., "authority is discovered not created" → `discovered_not_created_authority()`, or conjoin several: `grounded_in_practical_rationality() and not_grounded_in_command() and is_discovered()`
6. Ensure the same semantic concept uses the same predicate name across all steps
7. Include confidence and reasoning

**ENDORSED FORMALIZATIONS**: Steps with `endorsed: true` already have a correct formalization. Copy their `ascii` and `json_structure` fields into your output exactly as given — do not alter or re-derive them.

**COMPLETE RESPONSE**: Your `formalizations` array MUST contain one entry for every step in both `agent_data.argument` and `agent_data.assumptions`, no exceptions. If a step is very abstract, use zero-argument predicates to capture its key claims rather than omitting it.

### Justification-Aware Formalization

**The ideal**: every derived step (a step with one or more justifiers) should receive a formalization that is formally derivable from the formalizations of its justifier steps by standard first-order logic rules — modus ponens, universal instantiation, conjunction introduction/elimination, existential introduction, etc. Many arguments will fall short of this ideal, but it should be the target.

**Procedure for each derived step**:

1. Collect the formalizations of all justifier steps (endorsed formalizations are authoritative; use them as-is).
2. Determine what formula is logically entailed by those justifier formalizations — this is the target conclusion for the derived step.
3. Where possible, formalize the derived step as that entailed formula, using the same predicate names already introduced by the justifiers (consistent variable renaming is fine).
4. If the natural language content introduces a concept not yet expressed by any justifier's predicates, you face an enthymematic gap. Prefer a formalization that makes the connection to the justifiers' predicates explicit — for instance, by incorporating a universally quantified bridge principle that links the justifiers' predicates to the new concept. Note in your `reasoning` field when you are making an implicit bridge principle explicit. If no such connection is possible, assign the most faithful formalization of the natural language content and note the gap.

**Avoid** mechanically translating the surface meaning of a derived step into entirely fresh predicate names when the justifiers already provide predicates that could carry the inference. A formalization with no shared predicates between a derived step and its justifiers will score as formally invalid.

**Example**: Justifiers give `forall x. is_belief(x) implies mind_independent_truth(x)` (step 1) and `is_belief(institution_a)` (step 2). The derived step "institution A has a mind-independent truth condition" should be formalized as `mind_independent_truth(institution_a)` — reusing the justifiers' predicates via modus ponens — rather than `has_truth_condition(institution_a)` with a fresh predicate.

### Examples

Input:
```json
{
  "agent_data": {
    "argument": [
      {"symbol": "2", "proposition": "Socrates is a man", "justifiers": []},
      {"symbol": "3", "proposition": "Socrates is mortal", "justifiers": ["1", "2"]}
    ],
    "assumptions": [
      {"symbol": "1", "proposition": "All men are mortal", "justifiers": []}
    ]
  }
}
```

Output:
```json
{
  "formalizations": [
    {
      "symbol": "1",
      "ascii": "forall individual. (is_man(individual) implies is_mortal(individual))",
      "json_structure": "{\"type\": \"quantifier\", \"quant\": \"forall\", \"vars\": [{\"type\": \"variable\", \"name\": \"individual\"}], \"body\": {\"type\": \"connective\", \"op\": \"implies\", \"args\": [{\"type\": \"predicate\", \"name\": \"is_man\", \"args\": [{\"type\": \"variable\", \"name\": \"individual\"}]}, {\"type\": \"predicate\", \"name\": \"is_mortal\", \"args\": [{\"type\": \"variable\", \"name\": \"individual\"}]}]}}"
    },
    {
      "symbol": "2",
      "ascii": "is_man(socrates)",
      "json_structure": "{\"type\": \"predicate\", \"name\": \"is_man\", \"args\": [{\"type\": \"constant\", \"name\": \"socrates\"}]}"
    },
    {
      "symbol": "3",
      "ascii": "is_mortal(socrates)",
      "json_structure": "{\"type\": \"predicate\", \"name\": \"is_mortal\", \"args\": [{\"type\": \"constant\", \"name\": \"socrates\"}]}"
    }
  ],
  "confidence": 0.95,
  "reasoning": "Classic syllogism: universal premise 1, particular premise 2, conclusion 3"
}
```

Input (with endorsed formalization):
```json
{
  "agent_data": {
    "argument": [
      {
        "symbol": "1",
        "proposition": "All mice are small",
        "justifiers": [],
        "formalization": {"ascii": "forall x. Px implies Qx", "endorsed": true}
      },
      {"symbol": "2", "proposition": "Mice are small", "justifiers": []}
    ],
    "assumptions": []
  }
}
```

Output:
```json
{
  "formalizations": [
    {
      "symbol": "1",
      "ascii": "forall x. Px implies Qx",
      "json_structure": "{\"type\": \"quantifier\", \"quant\": \"forall\", \"vars\": [{\"type\": \"variable\", \"name\": \"x\"}], \"body\": {\"type\": \"connective\", \"op\": \"implies\", \"args\": [{\"type\": \"predicate\", \"name\": \"is_mouse\", \"args\": [{\"type\": \"variable\", \"name\": \"x\"}]}, {\"type\": \"predicate\", \"name\": \"is_small\", \"args\": [{\"type\": \"variable\", \"name\": \"x\"}]}]}}"
    },
    {
      "symbol": "2",
      "ascii": "forall entity. (is_mouse(entity) implies is_small(entity))",
      "json_structure": "{\"type\": \"quantifier\", \"quant\": \"forall\", \"vars\": [{\"type\": \"variable\", \"name\": \"entity\"}], \"body\": {\"type\": \"connective\", \"op\": \"implies\", \"args\": [{\"type\": \"predicate\", \"name\": \"is_mouse\", \"args\": [{\"type\": \"variable\", \"name\": \"entity\"}]}, {\"type\": \"predicate\", \"name\": \"is_small\", \"args\": [{\"type\": \"variable\", \"name\": \"entity\"}]}]}}"
    }
  ],
  "confidence": 0.95,
  "reasoning": "Step 1 has an endorsed formalization included as-is; step 2 formalized consistently using the same semantic predicate names"
}
```
"""

# Create GPT instance for agent formalization
agent_gpt_formalize = ModelAgent(
    instructions=agent_formalize_system_prompt,
    thinking={"type": "enabled", "budget_tokens": 5000},
    response_format_base={
        "type": "object",
        "properties": {
            "formalizations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "symbol":        {"type": "string"},
                        "ascii":         {"type": "string"},
                        "json_structure": {"type": "string"}
                    },
                    "required": ["symbol", "ascii", "json_structure"],
                    "additionalProperties": False
                }
            },
            "confidence": {"type": "number"},
            "reasoning":  {"type": "string"}
        },
        "required": ["formalizations", "confidence", "reasoning"],
        "additionalProperties": False
    },
    max_tokens=32768
)

# Agent-specific system prompt for improvement
agent_improvement_system_prompt = """
You are an AI agent working on logical argumentation. Your task is to analyze evaluation results and provide intelligent recommendations for argument enhancement that will improve the concluding proposition's scores.

### Task: Generate Improvement Recommendations

You will receive argument data with evaluation results and generate cohesive recommendation sets that work together to strengthen the argument structure. Each recommendation targets a specific proposition and demonstrates how it contributes to improving that proposition's scores, which in turn strengthens the overall argument and ultimately improves the concluding proposition's scores.

### Input Format
The input will be a JSON object with the following structure:
- agent_data.argument: List of Step objects in the main argument
- agent_data.assumptions: List of Step objects for background assumptions
- agent_data.target_type: Type of content being improved (e.g., "argument")
- agent_data.target_content: Specific content being targeted (if applicable)
- evaluation_results: Content and/or formal evaluation results with truth/validity scores
- conclusion_proposition: The concluding proposition (first entered, last in argument list)
- current_conclusion_scores: Current truth, content validity, and formal validity scores of the conclusion

Each Step object contains:
- symbol: String identifier (e.g., "1", "2", "3")
- proposition: The natural language proposition
- justifiers: List of symbols that justify this step
- truth_score: Truth evaluation score (0.0 to 1.0)
- content_validity: Content validity score (0.0 to 1.0)
- formal_validity: Formal validity score (0.0 to 1.0)
- formalization: Formal logic representation (optional)

### Improvement Types
Generate cohesive recommendation sets that work together to strengthen the argument structure:

1. **Conclusion-Supporting Premises**: New propositions that provide evidence or reasoning to directly support the concluding proposition
2. **Proposition Strengthening**: New propositions that support any existing proposition (conclusion, lemmas, or intermediate conclusions), thereby strengthening the overall argument structure
3. **Proposition Refinements**: Rewrites of existing propositions to improve clarity, logic, or precision. For concluding propositions, rewrites must preserve truth conditions and only improve clarity or precision.
4. **Mixed Recommendations**: Combinations of new supporting propositions and refined existing propositions
5. **Justification Sets**: Multiple propositions that together provide comprehensive justification for any target proposition

### Guidelines
1. **Focus on Argument Strengthening**: All recommendations must ultimately strengthen the argument structure and improve the concluding proposition's scores
2. **Cohesive Sets**: Each recommendation should be a complete, self-contained improvement set where propositions work together
3. **Evaluation-Driven**: Base recommendations on actual evaluation results, not generic suggestions
4. **Target Weaknesses**: Identify specific weaknesses in any proposition or argument structure and address them
5. **Impact Assessment**: Estimate the expected improvement in target proposition scores and overall argument strength
6. **Detailed Reasoning**: Explain why each improvement is suggested and how it will help strengthen the argument
7. **Avoid Repetition**: Don't suggest improvements that duplicate existing propositions
8. **Consider Context**: Use assumptions and existing argument structure to inform recommendations
9. **Conclusion Rewrite Prohibition**: NEVER rewrite or modify the concluding proposition under any circumstances. The conclusion must remain exactly as provided.
10. **Single Proposition Arguments**: When an argument contains only one proposition (the conclusion), recommendations must ONLY suggest new propositions to add as supporting premises. Do not suggest any rewrites or refinements of the existing proposition.
11. **New Proposition Positioning**: All new propositions must be inserted BEFORE the conclusion in the argument structure and must directly justify the existing conclusion.

### Output Structure
Each recommendation should include:
- **reasoning**: Why this improvement is suggested based on evaluation results
- **impact**: Expected impact level ('high', 'medium', 'low')
- **target_proposition**: Symbol of the proposition this recommendation supports
- **expected_conclusion_improvement**: Detailed prediction of how this will improve conclusion scores (use '+' notation, e.g., '+0.4')
- **propositions**: Array of propositions in this recommendation set

### Examples

# Low conclusion truth score scenario - Conclusion-Supporting Premises

Input:
{
  "agent_data": {
    "argument": [
      {
        "symbol": "1",
        "proposition": "The policy will reduce crime",
        "justifiers": [],
        "truth_score": "0.3",
        "content_validity": "0.4",
        "formal_validity": null
      }
    ],
    "assumptions": [],
    "target_type": "argument",
    "target_content": null
  },
  "evaluation_results": {
    "truth_evaluations": [
      {"symbol": "1", "truth_value": "0.3", "reasoning": "Vague claim without evidence"}
    ]
  },
  "conclusion_proposition": "The policy will reduce crime",
  "current_conclusion_scores": {
    "truth": "0.3",
    "content_validity": "0.4",
    "formal_validity": null
  }
}

Output:
{
  "recommendations": [
    {
      "id": "rec_001",
      "reasoning": "The conclusion has a very low truth score (0.3) because it lacks supporting evidence. Adding specific evidence about the policy's effectiveness will significantly improve the conclusion's credibility.",
      "impact": "high",
      "target_proposition": "1",
      "expected_conclusion_improvement": {
        "truth_score_improvement": "+0.4",
        "content_validity_improvement": "+0.3",
        "formal_validity_improvement": "+0.2"
      },
      "propositions": [
        {
          "symbol": null,
          "proposition": "Similar policies have reduced crime by 25% in comparable cities",
          "type": "new",
          "placement": "argument",
          "justifies_symbol": "1",
          "justification_suggestions": ["Statistical evidence from peer-reviewed studies", "Case studies from similar urban areas"]
        },
        {
          "symbol": null,
          "proposition": "The policy targets root causes of crime through community engagement",
          "type": "new",
          "placement": "argument",
          "justifies_symbol": "1",
          "justification_suggestions": ["Policy analysis documents", "Expert testimony on crime prevention"]
        }
      ]
    }
  ]
}

# Low validity score scenario

Input:
{
  "agent_data": {
    "argument": [
      {
        "symbol": "1",
        "proposition": "The economy is growing",
        "justifiers": []
      },
      {
        "symbol": "2",
        "proposition": "Therefore, unemployment will decrease",
        "justifiers": ["1"],
        "truth_score": "0.6",
        "content_validity": "0.3",
        "formal_validity": null
      }
    ],
    "assumptions": [],
    "target_type": "argument",
    "target_content": null
  },
  "evaluation_results": {
    "validity_evaluations": [
      {"symbol": "2", "validity_value": "0.3", "reasoning": "Weak inference - economic growth doesn't always reduce unemployment"}
    ]
  },
  "conclusion_proposition": "Unemployment will decrease",
  "current_conclusion_scores": {
    "truth": "0.6",
    "content_validity": "0.3",
    "formal_validity": null
  }
}

Output:
{
  "recommendations": [
    {
      "id": "rec_002",
      "reasoning": "The conclusion has a low validity score (0.3) because the inference from economic growth to unemployment reduction is weak. Adding a bridging premise will strengthen the logical connection.",
      "impact": "high",
      "target_proposition": "2",
      "expected_conclusion_improvement": {
        "truth_score_improvement": "+0.1",
        "content_validity_improvement": "+0.5",
        "formal_validity_improvement": "+0.4"
      },
      "propositions": [
        {
          "symbol": null,
          "proposition": "Economic growth creates new job opportunities in expanding sectors",
          "type": "new",
          "placement": "argument",
          "justifies_symbol": "2",
          "justification_suggestions": ["Economic theory on job creation", "Historical data on employment growth"]
        }
      ]
    }
  ]
}

# Mixed recommendation scenario - Proposition Refinements + New Supporting Premises

Input:
{
  "agent_data": {
    "argument": [
      {
        "symbol": "1",
        "proposition": "Climate change is real",
        "justifiers": [],
        "truth_score": "0.9",
        "content_validity": "0.8",
        "formal_validity": null
      },
      {
        "symbol": "2",
        "proposition": "We should take action",
        "justifiers": ["1"],
        "truth_score": "0.7",
        "content_validity": "0.5",
        "formal_validity": null
      }
    ],
    "assumptions": [],
    "target_type": "argument",
    "target_content": null
  },
  "evaluation_results": {
    "truth_evaluations": [
      {"symbol": "1", "truth_value": "0.9", "reasoning": "Strong scientific consensus"},
      {"symbol": "2", "truth_value": "0.7", "reasoning": "Vague conclusion needs more specific reasoning"}
    ],
    "validity_evaluations": [
      {"symbol": "2", "validity_value": "0.5", "reasoning": "Weak inference - doesn't specify what action or why"}
    ]
  },
  "conclusion_proposition": "We should take action",
  "current_conclusion_scores": {
    "truth": "0.7",
    "content_validity": "0.5",
    "formal_validity": null
  }
}

Output:
{
  "recommendations": [
    {
      "id": "rec_003",
      "reasoning": "The conclusion has moderate scores but could be significantly improved by making it more precise and adding supporting evidence. The conclusion rewrite improves clarity by specifying the type of action (decisive) and the target (climate change) without changing the fundamental claim. This mixed approach will strengthen both the conclusion and its justification.",
      "impact": "medium",
      "target_proposition": "2",
      "expected_conclusion_improvement": {
        "truth_score": "0.2",
        "content_validity": "0.4",
        "formal_validity": "0.3"
      },
      "propositions": [
        {
          "symbol": "2",
          "proposition": "We should take decisive action to address climate change",
          "type": "rewrite",
          "original_symbol": "2",
          "original_proposition": "We should take action",
          "placement": "argument",
          "justification_suggestions": ["Policy analysis documents", "Expert testimony on climate action"]
        },
        {
          "symbol": null,
          "proposition": "Carbon pricing has been effective in reducing emissions in other countries",
          "type": "new",
          "placement": "argument",
          "justifies_symbol": "2",
          "justification_suggestions": ["Case studies from European countries", "Economic research on carbon pricing"]
        },
        {
          "symbol": null,
          "proposition": "Reducing emissions will mitigate the worst effects of climate change",
          "type": "new",
          "placement": "argument",
          "justifies_symbol": "2",
          "justification_suggestions": ["Climate science research", "IPCC reports on emission reduction impacts"]
        }
      ]
    }
  ]
}

# Proposition Strengthening scenario - Supporting existing propositions

Input:
{
  "agent_data": {
    "argument": [
      {
        "symbol": "1",
        "proposition": "The new drug shows promise in clinical trials",
        "justifiers": [],
        "truth_score": "0.6",
        "content_validity": "0.7",
        "formal_validity": null
      },
      {
        "symbol": "2",
        "proposition": "Therefore, the drug should be approved",
        "justifiers": ["1"],
        "truth_score": "0.5",
        "content_validity": "0.4",
        "formal_validity": null
      }
    ],
    "assumptions": [],
    "target_type": "argument",
    "target_content": null
  },
  "evaluation_results": {
    "truth_evaluations": [
      {"symbol": "1", "truth_value": "0.6", "reasoning": "Moderate evidence, needs more supporting data"},
      {"symbol": "2", "truth_value": "0.5", "reasoning": "Weak conclusion from weak premise"}
    ],
    "validity_evaluations": [
      {"symbol": "2", "validity_value": "0.4", "reasoning": "Premise 1 is too weak to support approval conclusion"}
    ]
  },
  "conclusion_proposition": "The drug should be approved",
  "current_conclusion_scores": {
    "truth": "0.5",
    "content_validity": "0.4",
    "formal_validity": null
  }
}

Output:
{
  "recommendations": [
    {
      "id": "rec_004",
      "reasoning": "The conclusion has low scores because premise 1 is too weak to support the approval conclusion. Adding supporting evidence for the premise will strengthen the overall argument.",
      "impact": "high",
      "target_proposition": "1",
      "expected_conclusion_improvement": {
        "truth_score": "0.3",
        "content_validity": "0.4",
        "formal_validity": "0.2"
      },
      "propositions": [
        {
          "symbol": null,
          "proposition": "Phase II trials showed 70% effectiveness rate",
          "type": "new",
          "placement": "argument",
          "justifies_symbol": "1",
          "justification_suggestions": ["Clinical trial reports", "Peer-reviewed medical journals"]
        },
        {
          "symbol": null,
          "proposition": "Safety profile meets FDA requirements",
          "type": "new",
          "placement": "argument",
          "justifies_symbol": "1",
          "justification_suggestions": ["Safety analysis reports", "FDA regulatory guidelines"]
        },
        {
          "symbol": null,
          "proposition": "The drug addresses an unmet medical need",
          "type": "new",
          "placement": "argument",
          "justifies_symbol": "1",
          "justification_suggestions": ["Medical literature review", "Healthcare provider surveys"]
        }
      ]
    }
  ]
}

# Conclusion Rewrite Constraints - What NOT to do

Input:
{
  "agent_data": {
    "argument": [
      {
        "symbol": "1",
        "proposition": "We should take action on climate change",
        "justifiers": [],
        "truth_score": "0.6",
        "content_validity": "0.5",
        "formal_validity": null
      }
    ],
    "assumptions": [],
    "target_type": "argument",
    "target_content": null
  },
  "evaluation_results": {
    "truth_evaluations": [
      {"symbol": "1", "truth_value": "0.6", "reasoning": "Vague conclusion needs more specificity"}
    ]
  },
  "conclusion_proposition": "We should take action on climate change",
  "current_conclusion_scores": {
    "truth": "0.6",
    "content_validity": "0.5",
    "formal_validity": null
  }
}

CORRECT Output (preserves truth conditions):
{
  "recommendations": [
    {
      "id": "rec_clarity",
      "reasoning": "The conclusion has moderate scores due to vagueness. A clarity-focused rewrite will improve precision without changing the fundamental claim.",
      "impact": "medium",
      "target_proposition": "1",
      "expected_conclusion_improvement": {
        "truth_score_improvement": "+0.1",
        "content_validity_improvement": "+0.3",
        "formal_validity_improvement": "+0.2"
      },
      "propositions": [
        {
          "symbol": "1",
          "proposition": "We should take decisive action to address climate change",
          "type": "rewrite",
          "original_symbol": "1",
          "original_proposition": "We should take action on climate change",
          "placement": "argument",
          "justification_suggestions": ["Policy analysis documents", "Expert testimony on climate action"]
        }
      ]
    }
  ]
}

INCORRECT Output (changes truth conditions - DO NOT DO THIS):
{
  "recommendations": [
    {
      "id": "rec_wrong",
      "reasoning": "The conclusion needs more specificity",
      "impact": "high",
      "target_proposition": "1",
      "expected_conclusion_improvement": {
        "truth_score_improvement": "+0.4",
        "content_validity_improvement": "+0.5",
        "formal_validity_improvement": "+0.3"
      },
      "propositions": [
        {
          "symbol": "1",
          "proposition": "We should implement carbon pricing policies to reduce emissions",
          "type": "rewrite",
          "original_symbol": "1",
          "original_proposition": "We should take action on climate change",
          "placement": "argument",
          "justification_suggestions": ["Economic analysis", "Policy documents"]
        }
      ]
    }
  ]
}

# Justification Sets scenario - Multiple propositions working together

Input:
{
  "agent_data": {
    "argument": [
      {
        "symbol": "1",
        "proposition": "The company should expand internationally",
        "justifiers": [],
        "truth_score": "0.4",
        "content_validity": "0.3",
        "formal_validity": null
      }
    ],
    "assumptions": [],
    "target_type": "argument",
    "target_content": null
  },
  "evaluation_results": {
    "truth_evaluations": [
      {"symbol": "1", "truth_value": "0.4", "reasoning": "Vague claim without supporting evidence or reasoning"}
    ]
  },
  "conclusion_proposition": "The company should expand internationally",
  "current_conclusion_scores": {
    "truth": "0.4",
    "content_validity": "0.3",
    "formal_validity": null
  }
}

Output:
{
  "recommendations": [
    {
      "id": "rec_005",
      "reasoning": "The conclusion has very low scores because it lacks comprehensive justification. A complete justification set will provide multiple supporting reasons that work together to make the conclusion compelling.",
      "impact": "high",
      "target_proposition": "1",
      "expected_conclusion_improvement": {
        "truth_score": "0.5",
        "content_validity": "0.6",
        "formal_validity": "0.4"
      },
      "propositions": [
        {
          "symbol": null,
          "proposition": "International markets show strong demand for our products",
          "type": "new",
          "placement": "argument",
          "justifies_symbol": "1",
          "justification_suggestions": ["Market research reports", "International sales data", "Customer surveys"]
        },
        {
          "symbol": null,
          "proposition": "Expansion will diversify our revenue streams",
          "type": "new",
          "placement": "argument",
          "justifies_symbol": "1",
          "justification_suggestions": ["Financial analysis", "Risk assessment reports", "Industry benchmarks"]
        },
        {
          "symbol": null,
          "proposition": "We have the operational capacity to support international growth",
          "type": "new",
          "placement": "argument",
          "justifies_symbol": "1",
          "justification_suggestions": ["Capacity analysis", "Resource planning documents", "Expert assessments"]
        },
        {
          "symbol": null,
          "proposition": "Competitors are already expanding internationally",
          "type": "new",
          "placement": "argument",
          "justifies_symbol": "1",
          "justification_suggestions": ["Competitive analysis", "Industry reports", "Market intelligence"]
        }
      ]
    }
  ]
}

# Lemma Strengthening scenario - Supporting intermediate conclusions

Input:
{
  "agent_data": {
    "argument": [
      {
        "symbol": "1",
        "proposition": "The new policy will reduce traffic congestion",
        "justifiers": [],
        "truth_score": "0.6",
        "content_validity": "0.5",
        "formal_validity": null
      },
      {
        "symbol": "2",
        "proposition": "Reduced congestion will improve air quality",
        "justifiers": ["1"],
        "truth_score": "0.7",
        "content_validity": "0.6",
        "formal_validity": null
      },
      {
        "symbol": "3",
        "proposition": "Therefore, the policy should be implemented",
        "justifiers": ["2"],
        "truth_score": "0.5",
        "content_validity": "0.4",
        "formal_validity": null
      }
    ],
    "assumptions": [],
    "target_type": "argument",
    "target_content": null
  },
  "evaluation_results": {
    "truth_evaluations": [
      {"symbol": "1", "truth_value": "0.6", "reasoning": "Moderate evidence, needs more supporting data"},
      {"symbol": "2", "truth_value": "0.7", "reasoning": "Reasonable inference, but premise 1 is weak"},
      {"symbol": "3", "truth_value": "0.5", "reasoning": "Weak conclusion from weak intermediate premise"}
    ]
  },
  "conclusion_proposition": "The policy should be implemented",
  "current_conclusion_scores": {
    "truth": "0.5",
    "content_validity": "0.4",
    "formal_validity": null
  }
}

Output:
{
  "recommendations": [
    {
      "id": "rec_006",
      "reasoning": "The conclusion has low scores because the intermediate premise 2 relies on weak premise 1. Strengthening premise 1 will improve the entire argument chain and ultimately strengthen the conclusion.",
      "impact": "high",
      "target_proposition": "1",
      "expected_conclusion_improvement": {
        "truth_score_improvement": "+0.2",
        "content_validity_improvement": "+0.3",
        "formal_validity_improvement": "+0.2"
      },
      "propositions": [
        {
          "symbol": null,
          "proposition": "Similar policies have reduced congestion by 30% in comparable cities",
          "type": "new",
          "placement": "argument",
          "justifies_symbol": "1",
          "justification_suggestions": ["Transportation studies", "City planning reports", "Traffic analysis data"]
        },
        {
          "symbol": null,
          "proposition": "The policy includes specific congestion reduction mechanisms",
          "type": "new",
          "placement": "argument",
          "justifies_symbol": "1",
          "justification_suggestions": ["Policy documents", "Engineering analysis", "Expert testimony"]
        }
      ]
    }
  ]
}
"""

# Create GPT instance for improvement agent
agent_gpt_improvement = ModelAgent(
    instructions=agent_improvement_system_prompt,
    response_format_base={
        "type": "object",
        "properties": {
            "recommendations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "reasoning": {"type": "string"},
                        "impact": {"type": "string", "enum": ["high", "medium", "low"]},
                        "target_proposition": {"type": "string"},
                        "expected_conclusion_improvement": {
                            "type": "object",
                            "properties": {
                                "truth_score_improvement": {"type": "string"},
                                "content_validity_improvement": {"type": "string"},
                                "formal_validity_improvement": {"type": "string"}
                            },
                            "required": ["truth_score_improvement", "content_validity_improvement", "formal_validity_improvement"],
                            "additionalProperties": False
                        },
                        "propositions": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "symbol": {"type": ["string", "null"]},
                                    "proposition": {"type": "string"},
                                    "type": {"type": "string", "enum": ["new", "rewrite"]},
                                    "original_symbol": {"type": ["string", "null"]},
                                    "original_proposition": {"type": ["string", "null"]},
                                    "placement": {"type": "string", "enum": ["assumption", "argument"]},
                                    "justifies_symbol": {"type": ["string", "null"]},
                                    "justification_suggestions": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    }
                                },
                                "required": ["symbol","proposition","type","original_symbol","original_proposition","placement","justifies_symbol","justification_suggestions"],
                                "additionalProperties": False
                            }
                        }
                    },
                    "required": ["id", "reasoning", "impact", "target_proposition", "expected_conclusion_improvement", "propositions"],
                    "additionalProperties": False
                }
            }
        },
        "required": ["recommendations"],
        "additionalProperties": False
    },
    max_tokens=16384
)