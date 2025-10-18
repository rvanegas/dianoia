from pydantic import BaseModel
from core.utils import logger, find_index
from services.conversation import gpt_theses, gpt_justify, gpt_evaluate
import json

class Theses(BaseModel):
    thesis: str
    counter_thesis: str
    presupposition: str

class Step(BaseModel):
    index: str
    proposition: str
    justifiers: list[str]
    truth: float
    valid: float

class Arguments(BaseModel):
    assumptions: list[Step]
    argument: list[Step]
    counter_argument: list[Step]

    def next_id(self):
        steps = (self.assumptions +
            self.argument +
            self.counter_argument)
        letters = [step.index for step in steps]
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
        new_arg = [s for s in arg if s.index in conclusion.justifiers]
        new_arg.append(conclusion)
        props = {
            "assumptions": [s.proposition for s in self.assumptions],
            "argument": [s.proposition for s in new_arg]
        }
        content = gpt_evaluate.call(json.dumps(props))
        logger.debug(f"c({content})")
        evaluations = json.loads(content)
        for new_arg_index, step in enumerate(new_arg):
            arg_index = find_index(arg, lambda x: x.index == step.index)
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
        return self.json()

class ThesesPrompt(Theses):
    prompt: str

    def develop(self):
        return gpt_theses.call(self.json())

class ArgumentsWithPrompt(Arguments):
    loc: str
    index: int
    proposition: str

    def user_justify(self):
        logger.debug(f"loc {self.loc} index {self.index} proposition {self.proposition}")
        if self.loc == 'argument':
            arg = self.argument
        elif self.loc == 'counter_argument':
            arg = self.counter_argument
        else:
            raise ValueError('invalid loc')
        next_id = self.next_id()
        new_step = Step(index=next_id, proposition=self.proposition, justifiers=[], truth=0.0, valid=0.0)
        conclusion = arg[self.index]
        arg.insert(self.index, new_step)
        conclusion.justifiers.append(next_id)
        self.add_evaluations(arg, conclusion)
        return self.json()

class ArgumentsWithStepPrompt(Arguments):
    step_id: str

    def validate_step_id(self):
        step = next((x for x in self.all_arg_steps() if x.index == self.step_id), None)
        if step == None:
            raise ValueError('step_id does not refer')

    def find_in_arguments(self):
        index = find_index(self.argument, lambda x: x.index == self.step_id)
        if index != -1:
            return self.argument, index
        index = find_index(self.counter_argument, lambda x: x.index == self.step_id)
        if index != -1:
            return self.counter_argument, index
        raise ValueError("Invalid step_id")

    def insert_proposition(self, new_proposition: str):
        next_id = self.next_id()
        new_step = Step(index=next_id, proposition=new_proposition, justifiers=[], truth=0.0, valid=0.0)
        arg, index = self.find_in_arguments()
        conclusion = arg[index]
        conclusion.justifiers.append(next_id)
        arg.insert(index, new_step)
        return arg, conclusion

    def justify(self):
        self.validate_step_id()
        response = gpt_justify.call(self.json())
        new_propositions = json.loads(response)["propositions"]
        for p in new_propositions:
            arg, conclusion = self.insert_proposition(p)
        self.add_evaluations(arg, conclusion)
        return self.json()

    def remove(self):
        self.validate_step_id()
        arg, index = self.find_in_arguments()
        inferences_from = [s for s in arg if s.index in arg[index].justifiers]
        inferences_to = [s for s in arg if self.step_id in s.justifiers]
        premises = []
        for step in inferences_from:
            if step.index in arg[index].justifiers:
                premises.append(step.index)
        for step in inferences_to:
            step.justifiers.remove(self.step_id)
            for premise in premises:
                step.justifiers.append(premise)
            self.add_evaluations(arg, step)
        del arg[index]
        return self.json()
