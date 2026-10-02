"""Model routing: score a phase on four signals and derive the model tier.

Usage: python3 routing.py --scope 1 --ambiguity 0 --risk 2 --reasoning 1
Prints the model (haiku | sonnet | opus). Exit 2 if the phase needs more planning.
"""
import argparse
import sys

SIGNALS = ("scope", "ambiguity", "risk", "reasoning")
MODELS = ("haiku", "sonnet", "opus")


class NeedsPlanningError(ValueError):
    """Ambiguity 2: the phase must be specified further, not routed to a bigger model."""


def validate_score(score):
    if not isinstance(score, dict):
        raise ValueError("score must be a map like {scope: 1, ambiguity: 0, risk: 0, reasoning: 1}")
    missing = [s for s in SIGNALS if s not in score]
    extra = [k for k in score if k not in SIGNALS]
    if missing or extra:
        raise ValueError(f"score needs exactly {SIGNALS}; missing={missing} unexpected={extra}")
    for name in SIGNALS:
        value = score[name]
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 2:
            raise ValueError(f"score.{name} must be an integer 0-2, got {value!r}")


def derive_model(score):
    validate_score(score)
    if score["ambiguity"] == 2:
        raise NeedsPlanningError("ambiguity 2: return this phase to planning and specify it further")
    if score["risk"] == 2:
        return "opus"
    total = sum(score[s] for s in SIGNALS)
    if total <= 2:
        return "haiku"
    if total <= 5:
        return "sonnet"
    return "opus"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in SIGNALS:
        parser.add_argument(f"--{name}", type=int, required=True, choices=(0, 1, 2))
    args = parser.parse_args(argv)
    score = {name: getattr(args, name) for name in SIGNALS}
    try:
        print(derive_model(score))
    except NeedsPlanningError as exc:
        print(f"NEEDS-PLANNING: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
