from typing import List, Union
from langchain.chains.base import Chain
from langchain.chains import LLMChain
from langchain.prompts.prompt import PromptTemplate
from langchain.prompts.few_shot import FewShotPromptTemplate
from langchain.chat_models import ChatOpenAI


class FunctionExplanationModel:
    """
    https://python.langchain.com/docs/modules/chains/foundational/llm_chain

    https://python.langchain.com/docs/modules/chains/foundational/sequential_chains
    https://python.langchain.com/docs/modules/model_io/prompts/prompt_templates/few_shot_examples
    TODO: SemanticSimilarityExampleSelector

    https://python.langchain.com/docs/expression_language/cookbook/multiple_chains
    """

    llm_chain: Chain

    def __init__(
        self, api_key: str, organization_id: str, verbose: bool = False
    ) -> None:
        examples = [
            {
                "action": "contract_galahad => token_griffin.transfer(recipient=contract_goliath,amount=27379708648640084)",
                "explanation": "contract_galahad transfer 27379708648640084 token_griffin to contract_goliath",
            },
        ]

        example_prompt = PromptTemplate(
            input_variables=["action", "explanation"],
            template="Function Call: {action}\nExplanation: {explanation}",
        )

        prompt = FewShotPromptTemplate(
            examples=examples,
            example_prompt=example_prompt,
            # prefix="There is Function Call and their Explanation represented in format \"Function Call: caller => object.function(parameters)\" and a line of explanation. Here are some examples:",
            suffix="Function Call: {input}\nExplanation: ",
            input_variables=["input"],
        )

        function_explanation_chain = LLMChain(
            llm=ChatOpenAI(
                temperature=0,
                openai_api_key=api_key,
                openai_organization=organization_id,
            ),
            prompt=prompt,
            output_key="function_explanation",
            verbose=verbose,
        )

        self.llm_chain = function_explanation_chain

        # initial_context = """
        # I have a series of crypto function call. We will have two steps to solve this problem. In step 1 we will explain each function call one by one. In step 2 we will conclude all function calls and their explanation and give an one line summary.
        #
        # Step 1:
        # """

    # def context_initialize():
    #     """
    #     To initialize a chat context for the task
    #     """
    #     pass

    # def function_explain():
    #     """
    #     This is the step one of the chain of thought
    #     """

    # def summary():
    #     """
    #     This is the final step to output summary of all function calls
    #     """

    def __call__(self, raw_normalized_function_call: str) -> dict:
        return self.llm_chain({"input": raw_normalized_function_call})


class ExplanationSummaryModel:
    llm_chain: Chain

    def __init__(
        self, api_key: str, organization_id: str, verbose: bool = False
    ) -> None:
        # examples = [
        #     {
        #         "explanations": """
        #         Function Calls:
        #         1. argonaut => atlas.0x0938b20b
        #         2. atlas => centurion.0x9cb2dade
        #         3. atlas => token_FUC.transferFrom(sender=argonaut,recipient=dragoon,amount=248088055175560597542440)
        #         4. atlas => dragoon.swap(amount0Out=0,amount1Out=27379708648640084,to=atlas,data=b'')
        #         5. dragoon => token_WETH.transfer(recipient=atlas,amount=27379708648640084)
        #         6. atlas => token_WETH.transfer(recipient=centurion,amount=27379708648640084)
        #         7. atlas => centurion.withdraw(receiver=token_WETH,amount=27379708648640084)
        #         8. centurion => token_WETH.withdraw(_amount=27379708648640084)
        #
        #         Explanations:
        #         1. This function call can be ignored
        #         2. This function call can be ignored
        #         3. This function call indicates sender argonaut transfer token FUC to recipient dragoon with amount 248088055175560597542440
        #         4. Based on previous context, this function call indicates swap 248088055175560597542440 from dragoon to atlas, the token is FUC
        #         5. dragoon transfer 27379708648640084 WETH token to atlas
        #         6. atlas transfer 27379708648640084 WETH token to centurion
        #         7. centurion withdraw 27379708648640084 WETH token
        #         8. This function call can be ignored
        #         """,
        #         "summary": "atlas swaps 27379708648640084 of FUC token with dragoon",
        #     },
        # ]

        examples = [
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

        example_prompt = PromptTemplate(
            input_variables=["explanations", "summary"],
            template="Explanations: {explanations}\nOne line summary: {summary}",
        )

        prompt = FewShotPromptTemplate(
            examples=examples,
            example_prompt=example_prompt,
            # prefix="There is Function Call and their Explanation represented in format \"Function Call: caller => object.function(parameters)\" and a line of explanation. Here are some examples:",
            suffix="Explanations: {input}\nOne line summary: ",
            input_variables=["input"],
        )

        summary_chain = LLMChain(
            llm=ChatOpenAI(
                temperature=0,
                openai_api_key=api_key,
                openai_organization=organization_id,
            ),
            prompt=prompt,
            output_key="summary",
            verbose=verbose,
        )

        self.llm_chain = summary_chain

    def __call__(self, explanations: Union[str, List[str]]) -> dict:
        if isinstance(explanations, list):
            lines = []
            for i, explanation in enumerate(explanations):
                lines.append(f"{i + 1}. {explanation}")

            return self.llm_chain({"input": "\n".join(lines)})
        else:
            return self.llm_chain({"input": explanations})


class FullChain:
    step1_model: FunctionExplanationModel
    step2_model: ExplanationSummaryModel

    def __init__(
        self, api_key: str, organization_id: str, verbose: bool = False
    ) -> None:
        self.step1_model = FunctionExplanationModel(api_key, organization_id, verbose)
        self.step2_model = ExplanationSummaryModel(api_key, organization_id, verbose)

    def __call__(self, raw_normalized_function_calls: List[str]) -> dict:
        explanations = []
        for function_call in raw_normalized_function_calls:
            explanation = self.step1_model(function_call)
            explanations.append(explanation)

        return self.step2_model(explanations)


if __name__ == "__main__":
    from dotenv import load_dotenv
    import os

    load_dotenv()

    API_KEY = os.getenv("OPENAI_API_KEY")
    ORGANIZATION_ID = os.getenv("OPENAI_ORGANIZATION")

    model = FunctionExplanationModel(API_KEY, ORGANIZATION_ID, verbose=True)
    print(
        model(
            "atlas => galahad.swap(amount0Out=0,amount1Out=27379708648640084,to=goliath,data=b'')"
        )["function_explanation"]
    )

    model2 = ExplanationSummaryModel(API_KEY, ORGANIZATION_ID, verbose=True)
    print(
        model2(
            """
            1. This function call can be ignored
            2. This function call can be ignored
            3. This function call indicates sender argonaut transfer token FUC to recipient dragoon with amount 248088055175560597542440
            4. Based on previous context, this function call indicates swap 248088055175560597542440 from dragoon to atlas, the token is FUC
            5. dragoon transfer 27379708648640084 WETH token to atlas
            6. atlas transfer 27379708648640084 WETH token to centurion
            7. centurion withdraw 27379708648640084 WETH token
            8. Withdraw function exchange same amount of WETH to ETH
            """
        )["summary"]
    )
