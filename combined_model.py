from typing import List, Union, Dict
from langchain.chains.base import Chain
from langchain.chains import LLMChain, SequentialChain, SimpleSequentialChain
from langchain.prompts.prompt import PromptTemplate
from langchain.prompts.few_shot import FewShotPromptTemplate
from langchain.prompts.example_selector.length_based import LengthBasedExampleSelector
from langchain.chat_models import ChatOpenAI
from utils import ExampleLoader
import os

curr_dir = os.path.dirname(os.path.abspath(__file__))


class FullChain:
    """
    TODO: able to determine function calls type and choose specific examples
    """

    llm_chain: Chain

    def __init__(
        self,
        api_key: str,
        organization_id: str,
        explanation_examples: List[Dict[str, str]] = None,
        summary_examples: List[Dict[str, str]] = None,
        verbose: bool = False,
    ) -> None:
        if explanation_examples is None:
            explanation_examples = [
                {
                    "function_calls": """
                    1. argonaut => atlas.0x0938b20b
                    2. atlas => centurion.0x9cb2dade
                    3. atlas => token_FUC.transferFrom(sender=argonaut,recipient=dragoon,amount=248088055175560597542440)
                    4. atlas => dragoon.swap(amount0Out=0,amount1Out=27379708648640084,to=atlas,data=b'')
                    5. dragoon => token_WETH.transfer(recipient=atlas,amount=27379708648640084)
                    6. atlas => token_WETH.transfer(recipient=centurion,amount=27379708648640084)
                    7. atlas => centurion.withdraw(receiver=token_WETH,amount=27379708648640084)
                    8. centurion => token_WETH.withdraw(_amount=27379708648640084)
                    """,
                    "explanations": """
                    1. This function call can be ignored
                    2. This function call can be ignored
                    3. This function call indicates sender argonaut transfer token FUC to recipient dragoon with amount 248088055175560597542440
                    4. Based on previous context, this function call indicates swap 248088055175560597542440 from dragoon to atlas, the token is FUC
                    5. dragoon transfer 27379708648640084 WETH token to atlas
                    6. atlas transfer 27379708648640084 WETH token to centurion
                    7. centurion withdraw 27379708648640084 WETH token
                    8. Withdraw function exchange same amount of WETH to ETH
                """,
                }
            ]

            example1 = ExampleLoader(os.path.join(curr_dir, "data/prompt/v2-swap.json"))
            example2 = ExampleLoader(
                os.path.join(curr_dir, "data/prompt/v3-add-liquidity.json")
            )
            example3 = ExampleLoader(os.path.join(curr_dir, "data/prompt/v3-swap.json"))

            explanation_examples.extend(example1.get_explanation_examples().values())
            explanation_examples.extend(example2.get_explanation_examples().values())
            explanation_examples.extend(example3.get_explanation_examples().values())

        explanation_example_prompt = PromptTemplate(
            input_variables=["function_calls", "explanations"],
            template="Function Calls:\n{function_calls}\nExplanations:\n{explanations}",
        )

        explanation_example_selector = LengthBasedExampleSelector(
            # The examples it has available to choose from.
            examples=explanation_examples,
            # The PromptTemplate being used to format the examples.
            example_prompt=explanation_example_prompt,
            # The maximum length that the formatted examples should be.
            # Length is measured by the get_text_length function below.
            max_length=500,
            # The function used to get the length of a string, which is used
            # to determine which examples to include. It is commented out because
            # it is provided as a default value if none is specified.
            # get_text_length: Callable[[str], int] = lambda x: len(re.split("\n| ", x))
        )

        explanation_prompt = FewShotPromptTemplate(
            example_selector=explanation_example_selector,
            example_prompt=explanation_example_prompt,
            prefix="There will be a series of functions calls and their explanations. Each items might refer to others item's context. For all the specific amount preferred to have the number itself. \n",  #  So try to infer non-specified token from each others.
            suffix="Function Calls:\n{input}\nExplanations:\n",
            input_variables=["input"],
        )

        function_explanation_chain = LLMChain(
            llm=ChatOpenAI(
                temperature=0,
                openai_api_key=api_key,
                openai_organization=organization_id,
            ),
            prompt=explanation_prompt,
            output_key="function_explanations",
            verbose=verbose,
        )

        if summary_examples is None:
            summary_examples = [
                {
                    "explanations": """
                    1. This function call can be ignored
                    2. This function call can be ignored
                    3. This function call indicates sender argonaut transfer token FUC to recipient dragoon with amount 248088055175560597542440
                    4. Based on previous context, this function call indicates swap 248088055175560597542440 from dragoon to atlas, the token is FUC
                    5. dragoon transfer 27379708648640084 WETH token to atlas
                    6. atlas transfer 27379708648640084 WETH token to centurion
                    7. centurion withdraw 27379708648640084 WETH token
                    8. Withdraw function exchange same amount of WETH to ETH
                    """,
                    "summary": "atlas swaps 248088055175560597542440 token FUC to 27379708648640084 token ETH with dragoon",
                },
            ]

            summary_examples.extend(example1.get_summary_examples().values())
            summary_examples.extend(example2.get_summary_examples().values())
            summary_examples.extend(example3.get_summary_examples().values())

        # print(summary_examples)

        summary_example_prompt = PromptTemplate(
            input_variables=["explanations", "summary"],
            template="Explanations:\n{explanations}\nOne line summary:\n{summary}",
        )

        summary_example_selector = LengthBasedExampleSelector(
            # The examples it has available to choose from.
            examples=summary_examples,
            # The PromptTemplate being used to format the examples.
            example_prompt=summary_example_prompt,
            # The maximum length that the formatted examples should be.
            # Length is measured by the get_text_length function below.
            max_length=500,
            # The function used to get the length of a string, which is used
            # to determine which examples to include. It is commented out because
            # it is provided as a default value if none is specified.
            # get_text_length: Callable[[str], int] = lambda x: len(re.split("\n| ", x))
        )
        summary_prompt = FewShotPromptTemplate(
            example_selector=summary_example_selector,
            example_prompt=summary_example_prompt,
            prefix="There are explanations of function calls and an one line summary. The tokens and numbers are very important try hard to keep them in the summary.\n",
            suffix="Explanations:\n{function_explanations}\nOne line summary:\n",
            input_variables=["function_explanations"],
        )

        summary_chain = LLMChain(
            llm=ChatOpenAI(
                temperature=0,
                openai_api_key=api_key,
                openai_organization=organization_id,
            ),
            prompt=summary_prompt,
            output_key="summary",
            verbose=verbose,
        )

        # self.llm_chain = SequentialChain(
        #     chains=[function_explanation_chain, summary_chain],
        #     input_variables=["input"],
        #     output_variables=["function_explanations", "summary"],
        #     verbose=verbose,
        # )

        # NOTE: verbose is prettier than SequentialChain
        self.llm_chain = SimpleSequentialChain(
            chains=[function_explanation_chain, summary_chain],
            verbose=verbose,
        )

    def __call__(self, explanations: Union[str, List[str]]) -> dict:
        if isinstance(explanations, list):
            lines = []
            for i, explanation in enumerate(explanations):
                lines.append(f"{i + 1}. {explanation}")

            return self.llm_chain({"input": "\n".join(lines)})
        else:
            return self.llm_chain({"input": explanations})


if __name__ == "__main__":
    from dotenv import load_dotenv
    import os

    load_dotenv()

    API_KEY = os.getenv("OPENAI_API_KEY")
    ORGANIZATION_ID = os.getenv("OPENAI_ORGANIZATION")

    model = FullChain(API_KEY, ORGANIZATION_ID, verbose=True)
    print(
        model(
            """
            1. galahad => goliath.swapExactETHForTokens(amountOutMin=13846600923975796559,path=['0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2', '0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9'],to=galahad,deadline=1697359671)
            2. goliath => token_WETH.deposit()
            3. goliath => token_WETH.transfer(recipient=griffin,amount=580093856500020300)
            4. goliath => griffin.swap(amount0Out=13846600923975796559,amount1Out=0,to=galahad,data=b'')
            5. griffin => token_AAVE.transfer(recipient=galahad,amount=13846600923975796559)
            """
        )
    )

    # TODO: Add this as an example

    # 1. galahad swaps exact amount of ETH for tokens. The minimum amount of tokens to receive is 13846600923975796559. The path indicates the token pair to swap, from WETH to AAVE. The tokens will be sent to galahad. The deadline for the swap is 1697359671.
    # 2. goliath deposits WETH tokens.
    # 3. goliath transfers 580093856500020300 WETH tokens to griffin.
    # 4. goliath swaps 13846600923975796559 tokens from griffin to galahad. The token being swapped is AAVE.
    # 5. griffin transfers 13846600923975796559 AAVE tokens to galahad.

    # 'goliath swaps 580093856500020300 token WETH to 13846600923975796559 token AAVE with griffin'
