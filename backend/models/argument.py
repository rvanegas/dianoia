"""models for theses and arguments"""
import json
import re
import time

from pydantic import BaseModel
from core.utils import find_index, logger
from services.conversation import gpt_theses, gpt_justify, gpt_evaluate, gpt_explain
from services.agent_coordinator import coordinator

def clean_citations(proposition: str) -> str:
    """
    Clean citations from propositions by replacing non-ASCII brackets with ASCII brackets
    and keeping only the filename, removing numbers and dagger symbols.
    
    Example: "Mice are small【4:0†small.txt】." -> "Mice are small [small.txt]."
    """
    # Pattern to match citations like 【4:0†small.txt】 or similar
    # This matches the non-ASCII brackets 【】 and the dagger †, and captures the filename
    pattern = r'\u3010[^\u3011]*?([^\u2020]+)\u3011'
    
    def replace_citation(match):
        filename = match.group(1)
        if filename == "source":
            return ""
        return f" [{filename}]"

    replaced = re.sub(pattern, replace_citation, proposition)
    logger.debug(f"proposition: {proposition}")
    logger.debug(f"replaced...: {replaced}")
    return replaced

class Step(BaseModel):
    """steps in arguments or assumptions"""
    symbol: str
    proposition: str
    justifiers: list[str]
    truth: str
    valid: str

class Arguments(BaseModel):
    """theses and arguments as received from and returned to frontend"""
    thesis: str
    counter_thesis: str
    presupposition: str
    assumptions: list[Step]
    argument: list[Step]
    counter_argument: list[Step]
    lastPrompt: str | None = None
    explanation: str | None = None
    file_ids: list[str] = []
    arg: list[Step] = []
    conversation_id: str | None = None  # Format: "session_uuid:conversation_id"

    # pylint: disable=arguments-differ
    def model_post_init(self, __context):
        self.explanation = None

    def gptjsont(self):
        """arguments json to return to frontend used by theses()"""
        return self.json(include={
            "thesis", "counter_thesis",
            "presupposition", "proposition"})

    def gptjson(self):
        """arguments json to return to frontend"""
        return self.json(include={
            "assumptions", "argument", "counter_argument",
            "explanation"})

    def next_symbol(self):
        """picks next available A-Z in a natural order"""
        steps = (self.assumptions +
            self.argument +
            self.counter_argument)
        letters = [step.symbol for step in steps]
        if not all(isinstance(c, str) and len(c) == 1 and
            'A' <= c <= 'Z' for c in letters):
            raise ValueError("All elements must be single lowercase letters A-Z")
        seen = set(letters)
        if len(seen) == 0:
            return 'A'
        if len(seen) == 26:
            raise ValueError("All 26 letters are already present")
        if 'Z' not in seen:
            last = sorted(seen)[-1]
            return chr(ord(last)+1)
        for i in range(ord('A'), ord('Z') + 1):
            c = chr(i)
            if c not in seen:
                return c
        raise RuntimeError("something went wrong")

    def new_step(self, proposition: str):
        """make new step"""
        return Step(symbol=self.next_symbol(), proposition=proposition,
            justifiers=[], truth="0.0", valid="0.0")

    def subargument(self, arg: list[Step], conclusion: Step):
        """extract a few steps by way of a justifiers property"""
        new_arg = [s for s in arg if s.symbol in conclusion.justifiers]
        new_arg.append(conclusion)
        props = {
            "assumptions": [s.json() for s in self.assumptions],
            "argument": [s.json() for s in new_arg]
        }
        return props, new_arg

    def add_evaluations(self, arg: list[Step], conclusion: Step):
        """
        For a given list of steps as premises, and a step as conclusion,
        use gpt to set "truth" and "valid" values according to evaluate_system_prompt
        """
        props, new_arg = self.subargument(arg, conclusion)
        content = gpt_evaluate.call(json.dumps(props), self.file_ids)
        evaluations = json.loads(content)
        for new_arg_index, step in enumerate(new_arg):
            arg_index = find_index(arg, lambda x, step=step: x.symbol == step.symbol)
            arg[arg_index].truth = evaluations["truth"][new_arg_index]
            if new_arg_index == len(new_arg) - 1:
                arg[arg_index].valid = evaluations["valid"]
            else:
                arg[arg_index].valid = "1.0"

    def evaluate(self):
        """Find all the subarguments and evaluate their numbers using add_evaluations()"""
        for step in self.argument:
            if len(step.justifiers) != 0:
                self.add_evaluations(self.argument + self.assumptions, step)
        for step in self.counter_argument:
            if len(step.justifiers) != 0:
                self.add_evaluations(self.counter_argument + self.assumptions, step)
        return self.gptjson()

    def queue_argument_state_change(self, data: dict):
        """Queue analysis and discovery for argument state changes"""
        # Extract argument propositions for analysis
        argument_propositions = []
        for step in self.argument:
            argument_propositions.append(step.proposition)
        
        # Queue content discovery (builder agent)
        discovery_task_data = {
            'argument_data': {
                'argument': [step.dict() for step in self.argument],
                'counter_argument': [step.dict() for step in self.counter_argument],
                'assumptions': [step.dict() for step in self.assumptions],
                'thesis': self.thesis,
                'counter_thesis': self.counter_thesis,
                'presupposition': self.presupposition
            },
            **data
        }
        coordinator.queue_task(
            agent_type='builder',
            conversation_id=self.conversation_id,
            data=discovery_task_data
        )
        
        # Queue argument analysis (content evaluator)
        analysis_task_data = {
            'argument': argument_propositions,
            'thesis': self.thesis,
            'counter_thesis': self.counter_thesis,
            'assumptions': self.assumptions,
            'file_ids': self.file_ids,
            **data
        }
        coordinator.queue_task(
            agent_type='content_evaluator',
            conversation_id=self.conversation_id,
            data=analysis_task_data
        )

class ArgumentsWithLoc(Arguments):
    """arguments with a specific thesis indicated"""
    loc: str

    def model_post_init(self, __context):
        """validate that indicated loc exists, and set self.arg"""
        super().model_post_init(__context)
        assert self.loc in ["argument", "counter_argument"]
        self.arg = getattr(self, self.loc)

    def argue(self):
        """just copy thesis into argument"""
        assert len(self.arg) == 0
        thesis_attr = "thesis" if self.loc == "argument" else "counter_thesis"
        new_proposition = getattr(self, thesis_attr)
        new_step = self.new_step(new_proposition)
        self.arg.append(new_step)
        # Queue analysis and discovery for the argument state change
        self.queue_argument_state_change({
            'proposition': new_proposition,
            'location': self.loc,
            'step_index': 0,
            'file_ids': self.file_ids
        })
        return self.gptjson()

class ArgumentsWithStep(Arguments):
    """arguments with a specific step indicated by position"""
    loc: str
    index: int

    # this is a special pydantic method
    def model_post_init(self, __context):
        """validate that indicated position exists, and set self.arg"""
        super().model_post_init(__context)
        # logger.debug(f"l {self.loc}")
        assert self.loc in ['assumptions', 'argument', 'counter_argument']
        self.arg = getattr(self, self.loc)
        # logger.debug(f"o {len(self.arg)} {self.index}")
        assert len(self.arg) > self.index

    def insert_proposition(self, new_proposition: str):
        """add step and reference to it in indicated justifiers"""
        new_step = self.new_step(new_proposition)
        conclusion = self.arg[self.index]
        conclusion.justifiers.append(new_step.symbol)
        self.arg.insert(self.index, new_step)
        # Queue analysis and discovery for the argument state change
        self.queue_argument_state_change({
            'proposition': new_proposition,
            'location': self.loc,
            'step_index': self.index,
            'file_ids': self.file_ids
        })
        return conclusion

    def ai_justify(self):
        """use gpt to add steps to justify indicated conclusion"""
        response = gpt_justify.call(self.json(), self.file_ids)
        new_propositions = json.loads(response)["propositions"]
        for p in new_propositions:
            # Clean citations from the proposition
            cleaned_proposition = clean_citations(p)
            self.insert_proposition(cleaned_proposition)
            self.index += 1
        return self.gptjson()

    def remove(self):
        """remove step and adjust justifiers and evaluations accordingly"""
        if self.loc != "assumptions":
            # Clean up justifiers for this step
            step_to_remove = self.arg[self.index]
            inferences_to = [s for s in self.arg if step_to_remove.symbol in s.justifiers]
            
            for step in inferences_to:
                step.justifiers.remove(step_to_remove.symbol)
                # Add the removed step's justifiers to the dependent step
                step.justifiers.extend(step_to_remove.justifiers)
        
        del self.arg[self.index]
        # Queue analysis and discovery for the argument state change
        self.queue_argument_state_change({
            'location': self.loc,
            'step_index': self.index,
            'file_ids': self.file_ids
        })
        return self.gptjson()

    def assume(self):
        """move step into assumptions and adjust evaluations accordingly"""
        if self.loc == "assumptions":
            raise ValueError("already assumed")
        if len(self.arg[self.index].justifiers) != 0:
            raise ValueError("cannot assume justified proposition")
        self.arg[self.index].truth = "1.0"
        self.assumptions.append(self.arg[self.index])
        del self.arg[self.index]
        # Queue analysis and discovery for the argument state change
        self.queue_argument_state_change({
            'location': self.loc,
            'step_index': self.index,
            'file_ids': self.file_ids
        })
        return self.gptjson()

    def explain(self):
        """explain the 'valid' property and formalize the propositions."""
        assert len(self.arg[self.index].justifiers) != 0
        props, new_arg = self.subargument(self.arg, self.arg[self.index])
        response = gpt_explain.call(json.dumps(props), self.file_ids)
        content = json.loads(response)
        
        self.explanation = content["explanation"]
        return self.gptjson()

class ArgumentsWithProposition(Arguments):
    """arguments with a proposition"""
    proposition: str

    def theses(self):
        """convert user input into theses using gpt"""
        return gpt_theses.call(self.gptjsont(), self.file_ids)

class ArgumentsWithStepAndProposition(ArgumentsWithStep, ArgumentsWithProposition):
    """arguments with a proposition and location to make a new step"""

    # should use insert_proposition()
    def user_justify(self):
        """add step using proposition attr and adjust justifiers and evaluations accordingly"""
        assert self.loc in ["argument", "counter_argument"]
        new_step = self.new_step(self.proposition)
        conclusion = self.arg[self.index]
        self.arg.insert(self.index, new_step)
        conclusion.justifiers.append(new_step.symbol)
        # Queue analysis and discovery for the argument state change
        self.queue_argument_state_change({
            'proposition': self.proposition,
            'location': self.loc,
            'step_index': self.index,
            'file_ids': self.file_ids
        })
        return self.gptjson()
