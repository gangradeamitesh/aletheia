
from .context_builder import ContextBuilder
from .llm_client import LLMClient
from .models import ProjectIndex, RepoProfile, ScenarioSpec, TestRunResult
from .prompt import TEST_REPAIR_SYSTEM_PROMPT, build_test_repair_prompt


class LLMTestRepairer:

    def __init__(self, llm_client: LLMClient, profile: RepoProfile, index: ProjectIndex):
        self.llm_client = llm_client
        self.profile = profile
        self.index = index
        self.context_builder = ContextBuilder(index)

    def repair_test(self, route, scenario, generated_code, test_result:TestRunResult) -> str:

        prompt_context = self.context_builder.build_prompt_context(route)
        prompt = build_test_repair_prompt(profile=self.profile,prompt_context=prompt_context,scenarios=scenario,generated_code=generated_code,test_result=test_result)
        return self.llm_client.chat_text(TEST_REPAIR_SYSTEM_PROMPT, prompt)

        