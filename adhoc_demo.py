from utils import ExampleLoader
from combined_model import FullChain
from pprint import pprint
import os

curr_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(curr_dir, "data/prompt")

from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
ORGANIZATION_ID = os.getenv("OPENAI_ORGANIZATION")


def uni_v2_liquidity_demo():
    # Example
    uni_v2_liquidity_example_1 = ExampleLoader(
        os.path.join(base_dir, "uni-v2-liquidity/example-1.json")
    )
    uni_v2_liquidity_example_2 = ExampleLoader(
        os.path.join(base_dir, "uni-v2-liquidity/example-2.json")
    )
    # Test
    uni_v2_liquidity_example_3 = ExampleLoader(
        os.path.join(base_dir, "uni-v2-liquidity/example-3.json")
    )

    uni_v2_liquidity_explanation_examples = []
    uni_v2_liquidity_explanation_examples.extend(
        uni_v2_liquidity_example_1.get_explanation_examples().values()
    )
    uni_v2_liquidity_explanation_examples.extend(
        uni_v2_liquidity_example_2.get_explanation_examples().values()
    )

    uni_v2_liquidity_summary_examples = []
    uni_v2_liquidity_summary_examples.extend(
        uni_v2_liquidity_example_1.get_summary_examples().values()
    )
    uni_v2_liquidity_summary_examples.extend(
        uni_v2_liquidity_example_2.get_summary_examples().values()
    )

    llm = FullChain(
        API_KEY,
        ORGANIZATION_ID,
        explanation_examples=uni_v2_liquidity_explanation_examples,
        summary_examples=uni_v2_liquidity_summary_examples,
        verbose=True,
    )

    for (
        hash,
        data,
    ) in uni_v2_liquidity_example_3.get_function_calls_to_summaries().items():
        pprint(
            {
                "hash": hash,
                "result": llm(data["function_calls"])["output"],
                "expected": data["summary"],
            }
        )


def uni_v3_liquidity_demo():
    # Example
    uni_v3_liquidity_example_1 = ExampleLoader(
        os.path.join(base_dir, "uni-v3-liquidity/example-1.json")
    )
    uni_v3_liquidity_example_2 = ExampleLoader(
        os.path.join(base_dir, "uni-v3-liquidity/example-2.json")
    )
    # Test
    uni_v3_liquidity_example_3 = ExampleLoader(
        os.path.join(base_dir, "uni-v3-liquidity/example-3.json")
    )

    uni_v3_liquidity_explanation_examples = []
    uni_v3_liquidity_explanation_examples.extend(
        uni_v3_liquidity_example_1.get_explanation_examples().values()
    )
    uni_v3_liquidity_explanation_examples.extend(
        uni_v3_liquidity_example_2.get_explanation_examples().values()
    )

    uni_v3_liquidity_summary_examples = []
    uni_v3_liquidity_summary_examples.extend(
        uni_v3_liquidity_example_1.get_summary_examples().values()
    )
    uni_v3_liquidity_summary_examples.extend(
        uni_v3_liquidity_example_2.get_summary_examples().values()
    )

    llm = FullChain(
        API_KEY,
        ORGANIZATION_ID,
        explanation_examples=uni_v3_liquidity_explanation_examples,
        summary_examples=uni_v3_liquidity_summary_examples,
        verbose=True,
    )

    for (
        hash,
        data,
    ) in uni_v3_liquidity_example_3.get_function_calls_to_summaries().items():
        pprint(
            {
                "hash": hash,
                "result": llm(data["function_calls"])["output"],
                "expected": data["summary"],
            }
        )


def uni_v3_swap_v2_inference_demo():
    # Example
    uni_v3_swap_example_1 = ExampleLoader(
        os.path.join(base_dir, "uni-v3-swap/example-1.json")
    )

    # Test
    uni_v2_swap_example_1 = ExampleLoader(
        os.path.join(base_dir, "uni-v2-swap/example-1.json")
    )

    uni_v3_liquidity_explanation_examples = list(
        uni_v3_swap_example_1.get_explanation_examples().values()
    )

    uni_v3_liquidity_summary_examples = list(
        uni_v3_swap_example_1.get_summary_examples().values()
    )

    llm = FullChain(
        API_KEY,
        ORGANIZATION_ID,
        explanation_examples=uni_v3_liquidity_explanation_examples,
        summary_examples=uni_v3_liquidity_summary_examples,
        verbose=True,
    )

    for (
        hash,
        data,
    ) in uni_v2_swap_example_1.get_function_calls_to_summaries().items():
        pprint(
            {
                "hash": hash,
                "result": llm(data["function_calls"])["output"],
                "expected": data["summary"],
            }
        )


if __name__ == "__main__":
    # uni_v2_liquidity_demo()
    # uni_v3_liquidity_demo()
    uni_v3_swap_v2_inference_demo()
