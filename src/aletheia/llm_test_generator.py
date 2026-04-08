from pathlib import Path

from aletheia.prompt import TEST_GENERATION_SYSTEM_PROMPT
from .llm_client import LLMClient
from .models import *
from .prompt import build_test_generation_prompt
import ast
from .context_builder import ContextBuilder

class LLMTestGenerator:

    def __init__(self , llm_client , profile, index):
        self.llm_client = llm_client
        self.profile = profile
        self.index = index
        self.context_builder = ContextBuilder(index)

    def generate_tests(self , route , scenarios):
        prompt_context = self.context_builder.build_prompt_context(route)
        prompt = build_test_generation_prompt(self.profile ,prompt_context, scenarios)
        code = self.llm_client.chat_text(TEST_GENERATION_SYSTEM_PROMPT, prompt)
        ast.parse(code)  # Validate syntax
        return code
    
    def _read_route_file(self, route) -> str:
        path = Path(self.index.repo_root)/route.file_path
        try:
            return path.read_text(encoding="utf-8")
        except OSError:\
            print("Error reading file:", path)
        return ""