from .models import ScenarioSpec 
from .llm_client import LLMClient
from .scenario_planner import ScenarioPlanner
from .prompt import SCENARIO_PLANNER_SYSTEM_PROMPT, build_scenario_planner_prompt
from pathlib import Path
from .context_builder import ContextBuilder

class LLMScenarioPlanner:
    def __init__(self, llm_client: LLMClient,profile, index):
        self.llm_client = llm_client
        self.profile = profile
        self.index = index
        self.seed_planner = ScenarioPlanner(profile, index)
        self.context_builder = ContextBuilder(index)

    def plan_route(self ,route):
        seed_plan = self.seed_planner._plan_route(route)
        prompt_context = self.context_builder.build_prompt_context(route)
        #source = self._read_route_file(route)
        prompt = build_scenario_planner_prompt(profile=self.profile,prompt_context= prompt_context,seed_scenarios= seed_plan.scenarios)
        data = self.llm_client.chat_json(SCENARIO_PLANNER_SYSTEM_PROMPT, prompt)
        # print("LLM Response:")
        # print(data)
        return self._parse_scenarios(data)
    
    def _read_route_file(self, route) -> str:
        path = Path(self.index.repo_root)/route.file_path
        try:
            return path.read_text(encoding="utf-8")
        except OSError:
            return ""
    
    def _parse_scenarios(self, data) -> tuple[ScenarioSpec]:
        raw_items = data.get("scenarios", [])
        scenarios = []
        for item in raw_items:
            name = item.get("name")
            reason = item.get("reason", "")
            priority = item.get("priority", "medium")
            if not name or not reason:
                print("No name or reason in item:", item)
                continue
            if priority not in {"high", "medium", "low"}:
                print("Invalid priority in item:", item)
                priority = "medium"
            scenarios.append(ScenarioSpec(name=name, reason=reason,
                                           priority=priority))
        return tuple(scenarios)
    

        