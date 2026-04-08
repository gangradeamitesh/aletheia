import json

TEST_REPAIR_SYSTEM_PROMPT = """
You are a senior Python Backend QA engineer fixing pytest tests.
Return only valid Python code.
Do not include markdown fences.
Do not include explanations.
Use the route context and pytest failure output as the source of truth.
Fix only what is necessary test.
Fix only the broken assertion or mocking logic and the failed test cases.
Preserve tests that are already passing.
""".strip()


SCENARIO_PLANNER_SYSTEM_PROMPT = """
You are a senior backend API test planner.
Return only valid JSON.
Do not include markdown.
Do not include explanations outside JSON.
Prefer realistic, deterministic backend test scenarios.
""".strip()

TEST_GENERATION_SYSTEM_PROMPT = """
You are a senior Python backend QA engineer
Write pytest code only.
Do not include markdown fences.
Do not include explanations.
Perfer deterministic tests that don't rely on external services.
Mock external services when needed.
""".strip()

ROUTE_REVIEWER_SYSTEM_PROMPT = """
You are a senior backend engineer performing a code review.
Review one route handler for likely bugs, ambiguous behavior, validation-order issues, inconsistent responses, and test-relevant correctness problems.
Review that code can fail and should be fixed before writing tests.
Return only valid JSON.
Do not include markdown.
Do not give style-only feedback.
""".strip()

def build_test_generation_prompt(profile, prompt_context, scenario):
    scenario_data = [ scenario.to_dict() if hasattr(scenario, "to_dict") else scenario for scenario in scenario]

    return f"""Write a pytest test function for this scenario.
    If you need context use the provided repo profile, prompt context, handler source, and helper snippets.
    Repo profile:
    {json.dumps(profile.to_dict(), indent=2)}

    Prompt Context:
    {json.dumps(prompt_context.to_dict(), indent=2)}

    Scenario to implement:
    {json.dumps(scenario_data, indent=2)}

    Handler source:
    {prompt_context.handler_source}
    
    Requirements:
    - Return only valid Python code.
    - Do not use markdown fences.
    - Use pytest test functions.
    - Assume a Flask `client` fixture exists.
    - Mock external services at the correct import seam in the route module.
    - Keep tests deterministic.
    - Do not invent unavailable fixtures unless clearly marked as assumptions.
    - Align assertions exactly with the handler logic and helper snippets.
    """.strip()



def build_scenario_planner_prompt(profile, prompt_context, seed_scenarios) -> str:
    seed_data = [
        scenario.to_dict() if hasattr(scenario, "to_dict") else scenario
        for scenario in seed_scenarios
    ]

    return f"""
    Generate test scenarios for this backend endpoint.

    Repo profile:
    {json.dumps(profile.to_dict(), indent=2)}

    Prompt Context:
    {json.dumps(prompt_context.to_dict(), indent=2)}

    Seed scenarios:
    {json.dumps(seed_data, indent=2)}

    Handler source:
    {prompt_context.handler_source}

    Return JSON in this exact shape:
    {{
      "scenarios": [
        {{
          "name": "snake_case_name",
          "reason": "short reason",
          "priority": "high|medium|low"
        }}
      ]
    }}

    Rules:
    - Focus on auth, validation, not found, conflicts, service failures, and state transitions.
    - Do not invent unsupported business rules.
    - Use the handler source and dependency snippets as the source of truth.
    - Prefer scenarios that can be implemented in pytest.
    """.strip()

def build_route_reviewer_prompt(profile, prompt_context) -> str:
    return f"""
    Review this backend route handler for likely bugs, ambiguous behavior, validation-order issues, inconsistent responses, and test-relevant correctness problems.

    Repo profile:
    {json.dumps(profile.to_dict(), indent=2)}

    Prompt Context:
    {json.dumps(prompt_context.to_dict(), indent=2)}

    Return JSON in this exact shape:
    {{
      "findings": [
        {{
          "severity": "critical|major|minor",
          "finding_type": "validation_order|logic_bug|ambiguous_behavior|status_code|error_message|data_integrity|external_dependency",
          "message": "specific finding grounded in the route logic",
          "confidence": "high|medium|low",
          "code_snippet": "exact or near-exact buggy code snippet"
        }}
      ]
    }}

    Rules:
    - Focus on correctness and API behavior.
    - Use the handler source and dependency snippets as the source of truth.
    - Prefer concrete findings over generic advice.
    - If the behavior may be intentional but problematic, use finding_type "ambiguous_behavior".
    - Do not include line numbers.
    - Do not comment on style unless it affects correctness.
    """.strip()

def build_test_repair_prompt(profile,scenarios, generated_code , test_result, prompt_context):
    scenario_data = [
        scenario.to_dict() if hasattr(scenario, "to_dict") else scenario
        for scenario in scenarios
    ]

    result_data = test_result.to_dict() if hasattr(test_result, "to_dict") else test_result
    return f"""
      Repair this generated pytest file.

      Repo profile:
      {json.dumps(profile.to_dict(), indent=2)}

      Prompt context:
      {json.dumps(prompt_context.to_dict(), indent=2)}

      Target scenarios:
      {json.dumps(scenario_data, indent=2)}

      Current generated pytest code:
      {generated_code}

      Pytest result:
      {json.dumps(result_data, indent=2)}

      Requirements:
      - Return only valid Python code.
      - Fix test failures using the route logic and runtime evidence.
      - Preserve passing tests unless they conflict with the route behavior.
      - Do not invent unsupported fixtures or helpers.
      - Patch external dependencies at the correct import seam.
      - Keep tests deterministic.
      """.strip()