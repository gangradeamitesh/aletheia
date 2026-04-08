import json
import os

from aletheia.context_builder import ContextBuilder
from aletheia.flask_indexer import FlaskRouteIndexer
from aletheia.ingest import Ingestor
from aletheia.llm_client import LLMClient
from aletheia.llm_planner import LLMScenarioPlanner
from aletheia.llm_test_generator import LLMTestGenerator
from aletheia.prompt import (
    SCENARIO_PLANNER_SYSTEM_PROMPT,
    build_scenario_planner_prompt,
)
from aletheia.scenario_planner import ScenarioPlanner
from aletheia.test_runner import TestRunner
from aletheia.llm_route_reviewer import LLMRouteReviewer
from aletheia.llm_test_repairer import LLMTestRepairer

REPO_ROOT = "/Users/amiteshgangrade/Desktop/aahar/aletheia/test_code"


profile = Ingestor(REPO_ROOT).build_profile()
print("Profile:")
print(json.dumps(profile.to_dict(), indent=2))
indexer = FlaskRouteIndexer(REPO_ROOT).build_index()
print(indexer.to_dict())
#for testing selecting a specific route to review and generate tests for
route = next(
    r for r in indexer.routes
    if r.full_path == "/user/register" and r.method == "POST"
)

print("Selected Route:")
print(json.dumps(route.to_dict(), indent=2))
client = LLMClient(model="moonshotai/kimi-k2-instruct", api_key=api_key)
reviewer = LLMRouteReviewer(client, profile, indexer)
review = reviewer.review_route(route)
print("Route Review Findings:")
print(json.dumps(review.to_dict(), indent=2))
builder = ContextBuilder(indexer)
prompt_context = builder.build_prompt_context(route)

print("Prompt Context:")
print(json.dumps(prompt_context.to_dict(), indent=2))
print()

seed_planner = ScenarioPlanner(profile, indexer)
seed_plan = seed_planner._plan_route(route)
print("Seed Plan:")
print(seed_plan.to_dict())

# # prompt = build_scenario_planner_prompt(
# #     profile,
# #     prompt_context,
# #     seed_plan.scenarios,
# # )

# # results = client.chat_json(SCENARIO_PLANNER_SYSTEM_PROMPT, prompt)

# # print("LLM Results:")
# # print(json.dumps(results, indent=2))
# # print()

planner = LLMScenarioPlanner(client, profile, indexer)
scenarios = planner.plan_route(route)

print("Final Scenarios:")
print(json.dumps([scenario.to_dict() for scenario in scenarios], indent=2))
print()

generator = LLMTestGenerator(client, profile, indexer)
code = generator.generate_tests(route, scenarios)
# print("Generated Test Code:")
# print(code)

repairer = LLMTestRepairer(client, profile, indexer)

runner = TestRunner(REPO_ROOT)
# result = runner.write_and_run("tests/generated_tests/test_user_register_generated.py", code)

max_attempts = 3
test_path = "tests/generated_tests/test_user_register_generated.py"

for attempt in range(1, max_attempts + 1):
    print(f"Attempt {attempt} of {max_attempts}")
    import ast
    ast.parse(code)
    result = runner.write_and_run(test_path, code)
    if result.passed:
        print("Test passed!")
        break
    if attempt == max_attempts:
        print("Test failed. Attempting repair...")
        break
    code = repairer.repair_test(route, scenarios, code, result)
# print("Test Result:")
# print(json.dumps(result.to_dict(), indent=2))
