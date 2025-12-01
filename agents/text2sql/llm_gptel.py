from dataclasses import dataclass
import aiohttp

@dataclass
class GPTELResponse:
    content: str
    usage_metadata: dict | None = None


class GPTELChatLLM:
    def __init__(self, api_key: str, endpoint: str, model: str = "gptel-chat", temperature = 0):
        self.api_key = api_key
        self.endpoint = endpoint
        self.model = model
        self.temperature = temperature

    async def ainvoke(self, prompt: str) -> GPTELResponse:
        payload = {
            "model": self.model,
            "temperature": self.temperature,
            "messages": [
                {"role": "system", "content": "You are SQL expert"},
                {"role": "user", "content": prompt}
            ]
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self.endpoint, json=payload, headers=headers) as resp:
                data = await resp.json()

                # --- SAFETY GUARD ---
                if "choices" not in data:
                    raise Exception(f"GPTEL Error: {data}")

                message = data["choices"][0]["message"]["content"]

                usage = data.get("usage", {})  # GPTEL might return it, might not

                return GPTELResponse(
                    content=message,
                    usage_metadata=usage
                )
