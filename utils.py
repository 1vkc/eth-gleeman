from typing import Literal, Dict, List
import json
import os


class ExampleLoader:
    data: List[dict]

    def __init__(self, path: str) -> None:
        with open(path, "r", encoding="utf-8") as fp:
            data = json.load(fp)
            # NOTE: this is adhoc solution to load non-list json
            if isinstance(data, dict):
                data = [data]
            self.data = data

    def get_function_calls(self) -> Dict[str, str]:
        result = {}

        for example in self.data:
            actions = []
            for i, call in enumerate(example["trace"]):
                actions.append(f"{i + 1}. {call['action']}")
            result[example["hash"]] = "\n".join(actions)

        return result

    def get_explanation_examples(self) -> Dict[str, Dict[str, str]]:
        result = {}

        for example in self.data:
            actions = []
            explanations = []
            for i, call in enumerate(example["trace"]):
                actions.append(f"{i + 1}. {call['action']}")
                explanations.append(f"{i + 1}. {call['explanation']}")
            result[example["hash"]] = {
                "function_calls": "\n".join(actions),
                "explanations": "\n".join(explanations),
            }

        return result

    def get_summary_examples(self) -> Dict[str, Dict[str, str]]:
        result = {}

        for example in self.data:
            explanations = []
            for i, call in enumerate(example["trace"]):
                explanations.append(f"{i + 1}. {call['explanation']}")
            result[example["hash"]] = {
                "explanations": "\n".join(explanations),
                "summary": example["summarize"],
            }

        return result

    def get_summaries(self) -> Dict[str, str]:
        result = {}

        for example in self.data:
            result[example["hash"]] = (example["summarize"],)

        return result

    def get_function_calls_to_summaries(self) -> Dict[str, Dict[str, str]]:
        result = {}

        for example in self.data:
            actions = []
            for i, call in enumerate(example["trace"]):
                actions.append(f"{i + 1}. {call['action']}")
            result[example["hash"]] = {
                "function_calls": "\n".join(actions),
                "summary": example["summarize"],
            }

        return result


def get_all_raw_function_calls(base_dir: str) -> Dict[str, Dict[str, str]]:
    """
    TODO: get expected summary
    """
    results = {}
    for filename in os.listdir(base_dir):
        for hash, function_calls in (
            ExampleLoader(os.path.join(base_dir, filename)).get_function_calls().items()
        ):
            results[hash] = {"filename": filename, "function_calls": function_calls}

    return results


if __name__ == "__main__":
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.join(curr_dir, "data/prompt")

    print(os.listdir(base_dir))

    example1 = ExampleLoader(os.path.join(base_dir, "cn-examples.json"))
    print("Function calls:\n", example1.get_function_calls())
    print("Explanation examples:\n", example1.get_explanation_examples())
    print("Summary examples:\n", example1.get_summary_examples())

    example2 = ExampleLoader(os.path.join(base_dir, "v3-add-liquidity.json"))
    print("Function calls:\n", example2.get_function_calls())
    print("Explanation examples:\n", example2.get_explanation_examples())
    print("Summary examples:\n", example2.get_summary_examples())
