from pydantic import BaseModel
from core.utils import logger, find_index
from services.conversation import gpt_theses, gpt_develop, gpt_justify, gpt_evaluate
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

    def all_steps(self):
        return self.assumptions + self.argument + self.counter_argument

class ThesesPrompt(Theses):
    prompt: str

    def develop(self):
        return gpt_theses.call(self.json())

class ArgumentsPrompt(Theses, Arguments):
    prompt: str

    def develop(self):
        content = gpt_develop.call(self.json())
        args = json.loads(content)
        argument_response = Arguments.parse_obj(args)
        errors = proofread_response(self, argument_response)
        return content, errors

class ArgumentsWithStepPrompt(Arguments):
    step_id: str

    def validate_step_id(self):
        step = next((x for x in self.all_steps() if x.index == self.step_id), None)

        if step == None:
            raise ValueError('step_id does not refer')

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
        new_arg = [s for s in arg if s.index in conclusion.justifiers]
        new_arg.append(conclusion)
        return arg, new_arg

    def add_evaluations(self, arg: list[Step], new_arg: list[Step]):
        props = [s.proposition for s in new_arg]
        content = gpt_evaluate.call(json.dumps(props))
        evaluations = json.loads(content)
        # logger.debug(f"e({evaluations})")
        for new_arg_index, step in enumerate(new_arg):
            arg_index = find_index(arg, lambda x: x.index == step.index)
            arg[arg_index].truth = evaluations["truth"][new_arg_index]
            if new_arg_index == len(new_arg) - 1:
                arg[arg_index].valid = evaluations["valid"]
            else:
                arg[arg_index].valid = 1.0

    def justify(self):
        self.validate_step_id()
        response = gpt_justify.call(self.json())
        new_propositions = json.loads(response)["propositions"]
        for p in new_propositions:
            arg, new_arg = self.insert_proposition(p)
        self.add_evaluations(arg, new_arg)
        return self.json()

    def remove(self):
        self.validate_step_id()
        arg, index = self.find_in_arguments()
        inferences_from = [s for s in arg if s.index in arg[index].justifiers]
        inferences_to = [s for s in arg if self.step_id in s.justifiers]
        # logger.debug(f"from {inferences_from} it {arg[index]} to {inferences_to}")
        premises = []
        for step in inferences_from:
            if step.index in arg[index].justifiers:
                # arg[index].justifiers.remove(step.index)
                premises.append(step.index)
        for step in inferences_to:
            step.justifiers.remove(self.step_id)
            for premise in premises:
                step.justifiers.append(premise)

            new_arg = [s for s in arg if s.index in step.justifiers]
            new_arg.append(step)
            self.add_evaluations(arg, new_arg)

        del arg[index]
        return self.json()

def proofread_response(argument_prompt, argument_response):
    def verify_uniqueness(steps):
        seen = set()
        duplicates = []
        for step in steps:
            if step.proposition in seen:
                duplicates.append(step.index)
            else:
                seen.add(step.proposition)
        return duplicates

    def verify_index_stability(prev_steps, curr_steps):
        prev_map = {step.proposition: step.index for step in prev_steps}
        mismatches = []
        for step in curr_steps:
            if step.proposition in prev_map and step.index != prev_map[step.proposition]:
                mismatches.append((prev_map[step.proposition], step.index))
        return mismatches

    def verify_dependency_order(assumptions, curr_steps):
        all_steps = assumptions + curr_steps
        index_order = {step.index: i for i, step in enumerate(all_steps)}
        violations = []
        for i, step in enumerate(all_steps):
            for justifier in step.justifiers:
                if justifier not in index_order:
                    violations.append((step.index, justifier, "missing justifier"))
                elif index_order[justifier] >= i:
                    violations.append((step.index, justifier, "future dependency"))
        return violations

    def verify_final_conclusion(steps):
        if not steps:
            return None
        return None if steps[-1].justifiers else "Final proposition must be conclusion, not premise"

    def verify_conclusion_dependency(assumptions, curr_steps):
        # Basic check: trace dependencies backward from the final conclusion
        all_steps = assumptions + curr_steps
        if not all_steps:
            return None

        index_map = {step.index: step for step in all_steps}
        reachable = set()
        to_visit = list(all_steps[-1].justifiers)

        while to_visit:
            current = to_visit.pop()
            if current in reachable:
                continue
            reachable.add(current)
            to_visit.extend(index_map.get(
                current,
                Step(index=current, proposition="", justifiers=[], truth=0.0, valid=0.0)
            ).justifiers)

        assumption_indices = {step.index for step in assumptions}
        non_assumption_steps = [step for step in curr_steps[:-1]]  # exclude conclusion
        unused = [step.index for step in non_assumption_steps if step.index not in reachable]

        return unused

    def verify_proposition_limit(prev_steps, curr_steps):
        steps_delta = len(curr_steps) - len(prev_steps)
        if (steps_delta > 3 and prev_steps == 0) or steps_delta > 4:
            return True

    errors = {
        "argument": [],
        "counter_argument": []
    }

    for label in ["argument", "counter_argument"]:
        prev_steps = getattr(argument_prompt, label, [])
        curr_steps = getattr(argument_response, label, [])
        assumptions = getattr(argument_response, 'assumptions', [])

        # Uniqueness
        duplicates = verify_uniqueness(curr_steps)
        if duplicates:
            errors[label].append(f"Duplicate propositions found at indices: {duplicates}")

        # Index stability
        mismatches = verify_index_stability(prev_steps, curr_steps)
        if mismatches:
            errors[label].append(f"Index changes detected: {mismatches}")

        # logger.debug(f"assumptions: {assumptions}")
        # logger.debug(f"curr_steps: {curr_steps}")
        # Contribution to conclusion
        unused = verify_conclusion_dependency(assumptions, curr_steps)
        if unused:
            errors[label].append(f"Propositions not contributing to conclusion: {unused}")

        # Order conformance
        order_violations = verify_dependency_order(assumptions, curr_steps)
        if order_violations:
            formatted = [(s, j, reason) for s, j, reason in order_violations]
            errors[label].append(f"Dependency order violations: {formatted}")

        # Conclusion position
        conclusion_error = verify_final_conclusion(curr_steps)
        if conclusion_error:
            errors[label].append(conclusion_error)

        # # Introduction Limit
        # exceeds_limits = verify_proposition_limit(prev_steps, curr_steps)
        # if exceeds_limits:
        #     errors[label].append(f"Too many new propositions")

    # Agreement of conclusions with theses
    if (len(argument_response.argument) > 0 and
        argument_prompt.thesis != argument_response.argument[-1].proposition):
        errors['argument'].append("Argument conclusion does not match thesis.")

    if (len(argument_response.counter_argument) > 0 and
        argument_prompt.counter_thesis != argument_response.counter_argument[-1].proposition):
        errors['counter_argument'].append("Counter-argument conclusion does not match counter-thesis.")

    return errors
