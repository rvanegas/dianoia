"""dianoia extract / dianoia evaluate CLI commands."""

import argparse
import json
import logging
import sys
import time
import uuid
from pathlib import Path


class _PydanticEncoder(json.JSONEncoder):
    """Serialize Pydantic models (e.g. Step) embedded in result_content."""
    def default(self, obj):
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        return super().default(obj)


def cmd_extract(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"Error: '{path}' does not exist.", file=sys.stderr)
        return 1
    text = path.read_text(encoding="utf-8")
    max_props = getattr(args, "max_props", None)
    try:
        from services.extraction import extract_argument
        result = extract_argument(text, max_props=max_props)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


def cmd_evaluate(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"Error: '{path}' does not exist.", file=sys.stderr)
        return 1

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON in '{path}': {e}", file=sys.stderr)
        return 1

    from schemas.arguments import ArgumentData
    from schemas.step import Step
    from services.agent_coordinator import coordinator

    # core/utils.py sets the dianoia logger to DEBUG; silence it for CLI use
    logging.getLogger("dianoia").setLevel(logging.WARNING)

    try:
        argument_data = ArgumentData(
            assumptions=[Step(**s) for s in raw.get("assumptions", [])],
            argument=[Step(**s) for s in raw.get("argument", [])],
        )
    except Exception as e:
        print(f"Error: could not parse argument data: {e}", file=sys.stderr)
        return 1

    step_symbol = getattr(args, "step", None)
    if step_symbol is not None:
        all_steps = list(argument_data.assumptions) + list(argument_data.argument)
        target = next((s for s in all_steps if s.symbol == step_symbol), None)
        if target is None:
            print(f"Error: step '{step_symbol}' not found in argument.", file=sys.stderr)
            return 1
        keep = {step_symbol} | set(target.justifiers or [])
        argument_data = ArgumentData(
            assumptions=[s for s in argument_data.assumptions if s.symbol in keep],
            argument=[s for s in argument_data.argument if s.symbol in keep],
        )

    conversation_id = f"{uuid.uuid4()}:cli"
    snapshot_id = "1"
    timeout = getattr(args, "timeout", 300)

    coordinator.react_to_user_argument_change(conversation_id, snapshot_id, argument_data)

    seen_agents: set[str] = set()
    deadline = time.time() + timeout

    while time.time() < deadline:
        time.sleep(2)

        # Report newly completed agents
        results = coordinator.result_manager.get_results(conversation_id)
        for r in results:
            if r.agent_type not in seen_agents:
                seen_agents.add(r.agent_type)
                print(f"{r.agent_type} done", file=sys.stderr)

        if coordinator.are_conversation_tasks_complete(conversation_id, snapshot_id):
            break
    else:
        print("Warning: timed out waiting for agents", file=sys.stderr)

    output = coordinator.result_manager.get_formatted_results(
        conversation_id, snapshot_id, coordinator
    )
    print(json.dumps(output, indent=2, cls=_PydanticEncoder))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dianoia",
        description="Dianoia argument tools",
    )
    sub = parser.add_subparsers(dest="command")

    p_extract = sub.add_parser("extract", help="Extract argument from a text file, print JSON")
    p_extract.add_argument("file", help="Plain text or markdown file to extract from")
    p_extract.add_argument("-m", "--max-props", type=int, default=None, metavar="N",
                           help="Maximum total number of propositions (assumptions + argument steps)")

    p_evaluate = sub.add_parser("evaluate", help="Evaluate an argument JSON file with AI agents")
    p_evaluate.add_argument("file", help="JSON file containing arguments dict")
    p_evaluate.add_argument("--timeout", type=int, default=300, metavar="N",
                            help="Seconds to wait for agents (default 300)")
    p_evaluate.add_argument("--step", type=str, default=None, metavar="SYMBOL",
                            help="Evaluate only this step and its direct justifiers")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "extract":
        return cmd_extract(args)
    if args.command == "evaluate":
        return cmd_evaluate(args)

    parser.print_help()
    return 1
