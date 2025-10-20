from pydantic import BaseModel
from core.utils import logger, find_index
from services.conversation import gpt_theses, gpt_justify, gpt_evaluate
import json

class Theses(BaseModel):
    thesis: str
    counter_thesis: str
    presupposition: str
    prompt: str

    def develop(self):
        return gpt_theses.call(self.json())

class Step(BaseModel):
    symbol: str
    proposition: str
    justifiers: list[str]
    truth: float
    valid: float

class Arguments(BaseModel):
    assumptions: list[Step]
    argument: list[Step]
    counter_argument: list[Step]
    arg: list[Step] | None = None

    def argsjson(self):
        return self.json(include={"assumptions", "argument", "counter_argument"})

    def next_symbol(self):
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

    def all_arg_steps(self):
        return self.argument + self.counter_argument

    def add_evaluations(self, arg: list[Step], conclusion: Step):
        new_arg = [s for s in arg if s.symbol in conclusion.justifiers]
        new_arg.append(conclusion)
        props = {
            "assumptions": [s.proposition for s in self.assumptions],
            "argument": [s.proposition for s in new_arg]
        }
        content = gpt_evaluate.call(json.dumps(props))
        evaluations = json.loads(content)
        for new_arg_index, step in enumerate(new_arg):
            arg_index = find_index(arg, lambda x: x.symbol == step.symbol)
            arg[arg_index].truth = evaluations["truth"][new_arg_index]
            if new_arg_index == len(new_arg) - 1:
                arg[arg_index].valid = evaluations["valid"]
            else:
                arg[arg_index].valid = 1.0

    def evaluate(self):
        for step in self.argument:
            if len(step.justifiers) != 0:
                self.add_evaluations(self.argument, step)
        for step in self.counter_argument:
            if len(step.justifiers) != 0:
                self.add_evaluations(self.counter_argument, step)
        return self.argsjson()

class ArgumentsWithStep(Arguments):
    loc: str
    index: int

    # is there a pydantic way?
    # @model_validator(mode='before')
    # @classmethod
    def validate_init(self):
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
        next_symbol = self.next_symbol()
        new_step = Step(symbol=next_symbol, proposition=new_proposition,
            justifiers=[], truth=0.0, valid=0.0)
        conclusion = self.arg[self.index]
        conclusion.justifiers.append(next_symbol)
        self.arg.insert(self.index, new_step)
        return conclusion

    def justify(self):
        self.validate_init()
        response = gpt_justify.call(self.json())
        new_propositions = json.loads(response)["propositions"]
        for p in new_propositions:
            conclusion = self.insert_proposition(p)
            self.index += 1
        self.add_evaluations(self.arg, conclusion)
        return self.argsjson()

    def remove(self):
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
        return self.argsjson()

    def assume(self):
        self.validate_init()
        if self.loc == "assumptions":
            raise "already assumed"
        self.assumptions.append(self.arg[self.index])
        del self.arg[self.index]
        self.evaluate()
        return self.argsjson()

class ArgumentsWithProposition(ArgumentsWithStep):
    proposition: str

    def user_justify(self):
        if self.loc == 'argument':
            arg = self.argument
        elif self.loc == 'counter_argument':
            arg = self.counter_argument
        else:
            raise ValueError('invalid loc')
        next_symbol = self.next_symbol()
        new_step = Step(symbol=next_symbol, proposition=self.proposition, justifiers=[], truth=0.0, valid=0.0)
        conclusion = arg[self.index]
        arg.insert(self.index, new_step)
        conclusion.justifiers.append(next_symbol)
        self.add_evaluations(arg, conclusion)
        return self.argsjson()
