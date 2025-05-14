import logging
from typing import List, Dict, Any, Optional, Union

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field # Assuming pydantic_v1 for now

logger = logging.getLogger(__name__)

class EvaluationResult(BaseModel):
    """
    Defines the structured output for the Evaluator LLM.
    """
    overall_success: bool = Field(description="Boolean indicating if the overall original user goal was successfully achieved.")
    assessment: str = Field(description="A concise, human-readable summary of the outcome, explaining why it was or wasn't successful.")
    missing_information: Optional[List[str]] = Field(description="If not successful, a list of specific pieces of information or actions that are still missing or were incorrect.", default=None)
    suggestions_for_replan: Optional[List[str]] = Field(description="If not successful, actionable suggestions for how the plan could be improved or what steps to try next.", default=None)
    confidence_score: float = Field(description="A score from 0.0 to 1.0 indicating the LLM's confidence in this evaluation.", ge=0.0, le=1.0)

EVALUATOR_SYSTEM_PROMPT_TEMPLATE = """You are an expert AI Evaluator. Your task is to assess whether a research agent successfully achieved the user's original goal based on a summary of the executed plan and its outcomes.

You will be given:
1.  The user's original high-level query/goal.
2.  A summary of the executed plan, including:
    - Each step's description.
    - The tool used (if any) and its input.
    - The observed output or result of each step.
    - Any errors encountered during any step.
3.  The final answer or result provided by the agent to the user.

Your responsibilities:
-   Carefully compare the final outcome and the executed steps against the user's original query/goal.
-   Determine if the goal was fully and accurately achieved (`overall_success`).
-   Provide a concise `assessment` explaining your reasoning.
-   If the goal was not fully achieved or if there were significant issues:
    - Identify any `missing_information` or parts of the goal that were not addressed.
    - Provide actionable `suggestions_for_replan` that could help achieve the goal if the agent were to try again (e.g., "Consider using tool X for Y", "The summary for Z was incomplete, try to extract more details", "The Python script failed with error A, it needs to be debugged by checking B").
-   Provide a `confidence_score` (0.0 to 1.0) for your evaluation.

Respond with a single JSON object matching the following schema:
{format_instructions}

Do not include any preamble or explanation outside of the JSON object.
Focus on the substance of the results, not just whether tools ran without crashing. Did the agent *actually* answer the user's request or complete the task as intended?
"""

async def evaluate_plan_outcome(
    original_user_query: str,
    executed_plan_summary: str, # This will be a string summarizing actions, outputs, errors
    final_agent_answer: str, # The final answer given to the user by the plan executor
    llm: BaseChatModel
) -> Optional[EvaluationResult]:
    """
    Evaluates the outcome of an executed plan using an LLM.

    Args:
        original_user_query: The initial query from the user.
        executed_plan_summary: A textual summary of the plan's execution, including steps,
                               outputs, and any errors.
        final_agent_answer: The final answer/output produced by the agent at the end of the plan.
        llm: The language model instance to use for evaluation.

    Returns:
        An EvaluationResult object, or None if an error occurs during evaluation.
    """
    logger.info(f"Evaluator: Evaluating outcome for query: {original_user_query[:100]}...")
    logger.debug(f"Evaluator: Executed Plan Summary:\n{executed_plan_summary}")
    logger.debug(f"Evaluator: Final Agent Answer:\n{final_agent_answer}")


    parser = JsonOutputParser(pydantic_object=EvaluationResult)
    format_instructions = parser.get_format_instructions()

    prompt = ChatPromptTemplate.from_messages([
        ("system", EVALUATOR_SYSTEM_PROMPT_TEMPLATE),
        ("human", "User's Original Query/Goal:\n{original_user_query}\n\n"
                  "Summary of Executed Plan and Outcomes:\n{executed_plan_summary}\n\n"
                  "Final Answer Provided by Agent:\n{final_agent_answer}\n\n"
                  "Please evaluate the outcome.")
    ])

    chain = prompt | llm | parser

    try:
        evaluation_result_dict = await chain.ainvoke({
            "original_user_query": original_user_query,
            "executed_plan_summary": executed_plan_summary,
            "final_agent_answer": final_agent_answer,
            "format_instructions": format_instructions
        })

        if isinstance(evaluation_result_dict, EvaluationResult):
            evaluation = evaluation_result_dict
        else:
            evaluation = EvaluationResult(**evaluation_result_dict)
        
        logger.info(f"Evaluator: Evaluation complete. Success: {evaluation.overall_success}, Confidence: {evaluation.confidence_score:.2f}")
        logger.debug(f"Evaluator: Assessment: {evaluation.assessment}")
        if evaluation.suggestions_for_replan:
            logger.debug(f"Evaluator: Suggestions: {evaluation.suggestions_for_replan}")
        return evaluation

    except Exception as e:
        logger.error(f"Evaluator: Error during evaluation: {e}", exc_info=True)
        try:
            error_chain = prompt | llm | StrOutputParser()
            raw_output = await error_chain.ainvoke({
                "original_user_query": original_user_query,
                "executed_plan_summary": executed_plan_summary,
                "final_agent_answer": final_agent_answer,
                "format_instructions": format_instructions
            })
            logger.error(f"Evaluator: Raw LLM output on error: {raw_output}")
        except Exception as raw_e:
            logger.error(f"Evaluator: Failed to get raw LLM output on error: {raw_e}")
        return None

if __name__ == '__main__':
    # Example Usage (requires async setup and a mock/real LLM)
    async def test_evaluator():
        class MockLLM(BaseChatModel): # Basic mock for structure
            async def _agenerate(self, messages, stop=None, run_manager=None, **kwargs):
                # Simulate LLM response for testing
                # Example 1: Success
                # eval_response_json = EvaluationResult(
                #     overall_success=True,
                #     assessment="The agent successfully found two relevant papers, read the abstract of the first, and wrote a correct summary to 'summary.txt'. Goal achieved.",
                #     confidence_score=0.95
                # ).json()

                # Example 2: Partial Success / Needs Replan
                eval_response_json = EvaluationResult(
                    overall_success=False,
                    assessment="The agent found papers and wrote a summary, but the summary was for the wrong abstract (second paper instead of first). Also, the word cloud generation failed due to a missing library.",
                    missing_information=["Correct summary for the first paper's abstract.", "Generated word cloud image."],
                    suggestions_for_replan=[
                        "Re-run the step to read the abstract, ensuring it targets the *first* PubMed result.",
                        "Before generating the word cloud, ensure the 'wordcloud' Python package is installed using the package installer tool."
                    ],
                    confidence_score=0.85
                ).json()
                from langchain_core.messages import AIMessage
                return AIMessage(content=eval_response_json)

        mock_llm_instance = MockLLM()
        
        test_query = "Find the latest 2 papers on PubMed about 'mRNA vaccine stability', read the abstract of the first result, and write a short summary of that abstract to a file named 'summary.txt'."
        test_plan_summary = """
Step 1: Executed pubmed_search with input 'mRNA vaccine stability latest 2'. Output: Found 2 papers: [Paper A, Paper B].
Step 2: Executed web_page_reader for Paper B's abstract. Output: Abstract of Paper B...
Step 3: Executed write_file with input 'summary.txt:::Summary of Paper B abstract...'. Output: Successfully wrote file: 'summary.txt'.
Step 4: Attempted to run python script for word cloud. Error: ModuleNotFoundError: No module named 'wordcloud'.
        """
        test_final_answer = "I have found two papers and saved a summary of the second paper's abstract to summary.txt. I could not generate the word cloud."

        evaluation = await evaluate_plan_outcome(
            test_query, 
            test_plan_summary, 
            test_final_answer, 
            mock_llm_instance
        )

        if evaluation:
            print("--- Evaluation Result ---")
            print(f"Overall Success: {evaluation.overall_success}")
            print(f"Assessment: {evaluation.assessment}")
            print(f"Confidence: {evaluation.confidence_score}")
            if evaluation.missing_information:
                print(f"Missing Info: {evaluation.missing_information}")
            if evaluation.suggestions_for_replan:
                print(f"Suggestions for Re-plan: {evaluation.suggestions_for_replan}")
        else:
            print("Evaluation failed.")

    asyncio.run(test_evaluator())
