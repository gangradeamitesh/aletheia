# Aletheia

AST-guided backend API test generation for Flask projects.

Aletheia scans a Python backend, indexes its routes, builds route-aware test scenarios, and uses an LLM to generate deterministic pytest cases with enough source context to stay grounded in the codebase instead of guessing from endpoint names alone.

## Why Aletheia

Most AI test generators treat backend APIs like black boxes. Aletheia takes a different route:

- It statically indexes Flask blueprints and handlers from source.
- It profiles the repository to infer framework shape, entrypoints, and external service markers.
- It extracts handler-local dependency context before prompting an LLM.
- It seeds scenario planning with backend-aware heuristics such as auth, not-found, invalid payloads, conflicts, service failures, and state transitions.
- It can generate, run, and repair pytest files in a loop.

The result is a workflow aimed at producing tests that are more realistic, more deterministic, and easier to trust.

## What It Does

Today, Aletheia includes:

- Flask route indexing via AST traversal
- Repository ingestion and backend profiling
- Heuristic scenario planning per endpoint
- LLM-assisted scenario expansion
- LLM-assisted route review for correctness issues before test writing
- LLM-generated pytest code using route and dependency context
- Test execution and feedback-driven repair

## Architecture

The current pipeline looks like this:

1. `Ingestor` builds a repo profile by detecting framework markers, entrypoints, requirements files, and external service hints.
2. `FlaskRouteIndexer` parses Python files and builds a structured index of blueprints and routes.
3. `ScenarioPlanner` creates seed scenarios from route shape and source hints.
4. `ContextBuilder` extracts handler source plus dependency snippets relevant to the route.
5. `LLMScenarioPlanner`, `LLMRouteReviewer`, and `LLMTestGenerator` use grounded prompts to expand scenarios, surface route risks, and generate pytest code.
6. `TestRunner` writes the generated file and runs `pytest`.
7. `LLMTestRepairer` can revise generated tests from the route context plus runtime failure output.

## Example Use Cases

- Bootstrap test coverage for an existing Flask backend
- Triage risky endpoints before writing tests manually
- Generate route-specific pytest skeletons that engineers can refine
- Explore failure paths for auth, validation, and workflow-style endpoints

## CLI

The current CLI exposes route indexing:

```bash
python -m aletheia index /path/to/flask-repo --pretty
```

Example output shape:

```json
{
  "framework": "flask",
  "repo_root": "/path/to/repo",
  "blueprints": [],
  "routes": [
    {
      "method": "POST",
      "full_path": "/users/register",
      "handler_name": "register_user",
      "file_path": "app/routes/users.py",
      "line_number": 42
    }
  ]
}
```

## Programmatic Workflow

The project is currently easiest to explore from Python:

```python
from aletheia.ingest import Ingestor
from aletheia.flask_indexer import FlaskRouteIndexer
from aletheia.llm_client import LLMClient
from aletheia.llm_planner import LLMScenarioPlanner
from aletheia.llm_test_generator import LLMTestGenerator

repo_root = "/path/to/target-repo"

profile = Ingestor(repo_root).build_profile()
index = FlaskRouteIndexer(repo_root).build_index()
route = index.routes[0]

client = LLMClient(
    model="moonshotai/kimi-k2-instruct",
    api_key="YOUR_API_KEY",
)

scenarios = LLMScenarioPlanner(client, profile, index).plan_route(route)
test_code = LLMTestGenerator(client, profile, index).generate_tests(route, scenarios)
print(test_code)
```

## Design Principles

- Ground prompts in source code, not just route metadata
- Prefer deterministic pytest generation over fragile “AI demo” outputs
- Keep the pipeline modular so indexing, planning, generation, review, and repair can evolve independently
- Focus on practical backend failure modes rather than generic test-case inflation

## Current Scope

Aletheia is early-stage and intentionally focused.

- Framework support is currently Flask-only.
- The CLI is minimal and centered on indexing.
- LLM orchestration is available through Python modules and local experimentation scripts.
- Prompting is optimized for backend correctness and deterministic tests, but generated code still benefits from human review.

## Project Structure

```text
aletheia/
└── src/
    ├── my_tester.py              # Local experimentation script
    └── aletheia/
        ├── cli.py                # CLI entrypoint
        ├── flask_indexer.py      # Flask AST indexer
        ├── ingest.py             # Repo profiling
        ├── context_builder.py    # Route/dependency context extraction
        ├── scenario_planner.py   # Heuristic scenario seeding
        ├── llm_planner.py        # LLM scenario planning
        ├── llm_route_reviewer.py # Route review pass
        ├── llm_test_generator.py # Pytest generation
        ├── llm_test_repairer.py  # Repair loop
        ├── test_runner.py        # Pytest execution
        ├── prompt.py             # Prompt templates
        └── models.py             # Shared dataclasses
```

## Setup Notes

The repository currently does not include packaging metadata or a pinned dependency file at the project root, so setup is manual. At minimum, you will want:

- Python 3.11+
- `pytest`
- `openai`

If you plan to use a non-default OpenAI-compatible endpoint, `LLMClient` supports a configurable `base_url`.
