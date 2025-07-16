"""models for theses and arguments"""
import json

from pydantic import BaseModel
from core.utils import find_index # , logger
from services.conversation import gpt_theses, gpt_justify, gpt_evaluate

class Step(BaseModel):
    """steps in arguments or assumptions"""
    symbol: str
    proposition: str
    justifiers: list[str]
    truth: float
    valid: float

class Arguments(BaseModel):
    """theses and arguments as received from and returned to frontend"""
    thesis: str
    counter_thesis: str
    presupposition: str
    assumptions: list[Step]
    argument: list[Step]
    counter_argument: list[Step]
    vector_store_id: str | None = None
    arg: list[Step] | None = None

    def gptjsont(self):
        return self.json(include={"thesis", "counter_thesis", "presupposition", "proposition"})

    def gptjson(self):
        """arguments json to return to frontend"""
        return self.json(include={"assumptions", "argument", "counter_argument"})

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

    # def all_arg_steps(self):
    #     return self.argument + self.counter_argument

    def add_evaluations(self, arg: list[Step], conclusion: Step):
        """
        For a given list of steps as premises, and a step as conclusion,
        use gpt to set "truth" and "valid" values according to evaluate_system_prompt
        """
        new_arg = [s for s in arg if s.symbol in conclusion.justifiers]
        new_arg.append(conclusion)
        props = {
            "assumptions": [s.proposition for s in self.assumptions],
            "argument": [s.proposition for s in new_arg]
        }
        content = gpt_evaluate.call(json.dumps(props), self.vector_store_id)
        evaluations = json.loads(content)
        for new_arg_index, step in enumerate(new_arg):
            arg_index = find_index(arg, lambda x, step=step: x.symbol == step.symbol)
            arg[arg_index].truth = evaluations["truth"][new_arg_index]
            if new_arg_index == len(new_arg) - 1:
                arg[arg_index].valid = evaluations["valid"]
            else:
                arg[arg_index].valid = 1.0

    def evaluate(self):
        """Find all the subarguments and evaluate their numbers using add_evaluations()"""
        for step in self.argument:
            if len(step.justifiers) != 0:
                self.add_evaluations(self.argument, step)
        for step in self.counter_argument:
            if len(step.justifiers) != 0:
                self.add_evaluations(self.counter_argument, step)
        return self.gptjson()

class ArgumentsWithStep(Arguments):
    """arguments with a specific step indicated by position"""
    loc: str
    index: int

    # is there a pydantic way?
    # @model_validator(mode='before')
    # @classmethod
    def validate_init(self):
        """validate that indicated position exists"""
        if self.loc == 'argument':
            self.arg = self.argument
        elif self.loc == 'counter_argument':
            self.arg = self.counter_argument
        elif self.loc == 'assumptions':
            self.arg = self.assumptions
        else:
            raise ValueError('invalid loc')
        if len(self.arg) <= self.index:
            raise ValueError('invalid index')

    def insert_proposition(self, new_proposition: str):
        """add step and reference to it in indicated justifiers"""
        if self.arg == None: # unnecessary if validate_init is in a hook
            raise RuntimeError("invalid arg")
        next_symbol = self.next_symbol()
        new_step = Step(symbol=next_symbol, proposition=new_proposition,
            justifiers=[], truth=0.0, valid=0.0)
        conclusion = self.arg[self.index]
        conclusion.justifiers.append(next_symbol)
        self.arg.insert(self.index, new_step)
        return conclusion

    def ai_justify(self):
        """use gpt to add steps to justify indicated conclusion"""
        self.validate_init()
        response = gpt_justify.call(self.json(), self.vector_store_id)
        new_propositions = json.loads(response)["propositions"]
        for p in new_propositions:
            conclusion = self.insert_proposition(p)
            self.index += 1
        self.add_evaluations(self.arg, conclusion)
        return self.gptjson()

    def remove(self):
        """remove step and adjust justifiers and evaluations accordingly"""
        self.validate_init()
        if self.loc != "assumptions":
            inferences_from = [s for s in self.arg if s.symbol in self.arg[self.index].justifiers]
            inferences_to = [s for s in self.arg if self.arg[self.index].symbol in s.justifiers]
            premises = []
            for step in inferences_from:
                if step.symbol in self.arg[self.index].justifiers:
                    premises.append(step.symbol)
            for step in inferences_to:
                step.justifiers.remove(self.arg[self.index].symbol)
                for premise in premises:
                    step.justifiers.append(premise)
        del self.arg[self.index]
        self.evaluate()
        return self.gptjson()

    def assume(self):
        """move step into assumptions and adjust evaluations accordingly"""
        self.validate_init()
        if self.loc == "assumptions":
            raise ValueError("already assumed")
        if len(self.arg[self.index].justifiers) != 0:
            raise ValueError("cannot assume justified proposition")
        self.assumptions.append(self.arg[self.index])
        del self.arg[self.index]
        self.evaluate()
        return self.gptjson()

    def explain(self):
        self.validate_init()
        assert len(self.arg[self.index].justifiers) != 0
        return self.gptjson(), "I hereby explain."

class ArgumentsWithProposition(Arguments):
    """arguments with a proposition"""

    proposition: str

    def theses(self):
        """convert user input into theses using gpt"""
        return gpt_theses.call(self.gptjsont(), self.vector_store_id)

class ArgumentsWithStepAndProposition(ArgumentsWithStep, ArgumentsWithProposition):
    """arguments with a proposition and location to make a new step"""

    # should use insert_proposition()
    def user_justify(self):
        """add step using proposition attr and adjust justifiers and evaluations accordingly"""
        if self.loc == 'argument':
            arg = self.argument
        elif self.loc == 'counter_argument':
            arg = self.counter_argument
        else:
            raise ValueError('invalid loc')
        next_symbol = self.next_symbol()
        new_step = Step(symbol=next_symbol, proposition=self.proposition,
            justifiers=[], truth=0.0, valid=0.0)
        conclusion = arg[self.index]
        arg.insert(self.index, new_step)
        conclusion.justifiers.append(next_symbol)
        self.add_evaluations(arg, conclusion)
        return self.gptjson()
