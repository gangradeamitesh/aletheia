import json

from openai import OpenAI


class LLMClient:
    def __init__(self, api_key, model, base_url="https://integrate.api.nvidia.com/v1"):
        self.model = model
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def chat_text(self, system_prompt, user_prompt) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            top_p=0.8,
            max_tokens=4096,
            stream = False,
        )

        return response.choices[0].message.content
    
    def chat_json(self, system_prompt: str, user_prompt: str) -> dict:
        content = self.chat_text(system_prompt, user_prompt)
        return json.loads(content)