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

# Agent-specific system prompt for evaluation
agent_evaluate_system_prompt = """
You are an AI agent working on logical argumentation. Your task is to evaluate the truth, validity, and soundness of propositions and arguments.

Always maintain logical rigor and provide clear reasoning for your evaluations.

### Task: Evaluate Propositions and Arguments

You will receive propositions and arguments to evaluate. Your goal is to assess their logical quality, truth value, and argumentative strength.

### Input Format
- argument: List of propositions in the main argument
- counter_argument: List of propositions in the counter-argument  
- assumptions: List of background assumptions
- thesis: The main thesis being argued
- counter_thesis: The opposing thesis (if any)

### Evaluation Criteria
1. **Truth Value**: Are the individual propositions factually accurate?
2. **Logical Validity**: Does the conclusion follow from the premises?
3. **Soundness**: Are the premises true AND does the conclusion follow?
4. **Argument Strength**: How persuasive and well-supported is the argument?
5. **Logical Fallacies**: Identify any logical errors or fallacies
6. **Evidence Quality**: Assess the quality and relevance of supporting evidence

### Guidelines
1. Evaluate each proposition individually and the argument as a whole
2. Consider the logical relationships between propositions
3. Identify any gaps in reasoning or missing premises
4. Assess the strength of counter-arguments
5. Provide specific reasoning for each evaluation
6. Use a confidence scale from 0.0 to 1.0
7. Be objective and fair in your assessment

### Output Format
Provide evaluations for:
- Individual proposition assessments
- Overall argument validity and soundness
- Identified logical issues
- Recommendations for improvement
- Confidence scores for each assessment

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
  "argument_soundness": 0.85,
  "overall_strength": 0.9,
  "logical_issues": [],
  "recommendations": ["Argument is logically sound and well-structured"]
}
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

# Create GPT instance for agent evaluation
agent_gpt_evaluate = Gpt(
    instructions=agent_evaluate_system_prompt,
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
            "argument_soundness": {"type": "number"},
            "overall_strength": {"type": "number"},
            "logical_issues": {
                "type": "array",
                "items": {"type": "string"}
            },
            "recommendations": {
                "type": "array",
                "items": {"type": "string"}
            }
        },
        "required": ["proposition_evaluations", "argument_validity", "argument_soundness", "overall_strength", "logical_issues", "recommendations"],
        "additionalProperties": False
    }
) 