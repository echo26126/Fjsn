import os
import asyncio
import httpx
import json
import logging
import base64
import hashlib
import time
from pathlib import Path
from typing import List, Dict, Any

# Configure logging
logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.config_path = Path(__file__).resolve().parents[1] / "data" / "agent_config.json"
        self.provider = "deepseek"
        self.api_key = ""
        self.base_url = "https://api.deepseek.com"
        self.model = "deepseek-chat"
        self.temperature = 0.5
        self.analysis_channel = "auto"
        self.sql_prompt_template = ""
        self.analysis_prompt_template = ""
        self.timeout = 8.0
        self.secret_key = os.getenv("AGENT_SECRET_KEY", "local-agent-secret")
        self._load_config()

    def _provider_presets(self) -> Dict[str, Dict[str, Any]]:
        return {
            "deepseek": {
                "base_url": "https://api.deepseek.com",
                "models": ["deepseek-chat", "deepseek-reasoner"],
                "default_model": "deepseek-chat",
            },
            "openai-compatible": {
                "base_url": "https://api.openai.com/v1",
                "models": ["gpt-4o-mini", "gpt-4.1"],
                "default_model": "gpt-4o-mini",
            },
        }

    def _normalize_provider_config(self):
        presets = self._provider_presets()
        provider = self.provider if self.provider in presets else "deepseek"
        preset = presets[provider]
        self.provider = provider
        if not self.base_url:
            self.base_url = preset["base_url"]
        if self.model not in preset["models"]:
            self.model = preset["default_model"]

    def _mask_api_key(self, value: str) -> str:
        if not value:
            return ""
        if len(value) <= 8:
            return "*" * len(value)
        return f"{value[:4]}{'*' * (len(value) - 8)}{value[-4:]}"

    def _encrypt_secret(self, plain: str) -> str:
        if not plain:
            return ""
        digest = hashlib.sha256(self.secret_key.encode("utf-8")).digest()
        data = plain.encode("utf-8")
        encrypted = bytes([b ^ digest[i % len(digest)] for i, b in enumerate(data)])
        return base64.urlsafe_b64encode(encrypted).decode("utf-8")

    def _decrypt_secret(self, encrypted: str) -> str:
        if not encrypted:
            return ""
        digest = hashlib.sha256(self.secret_key.encode("utf-8")).digest()
        raw = base64.urlsafe_b64decode(encrypted.encode("utf-8"))
        plain = bytes([b ^ digest[i % len(digest)] for i, b in enumerate(raw)])
        return plain.decode("utf-8")

    def _default_sql_prompt(self) -> str:
        return """You are an expert data analyst.
Your task is to generate a SQL query to answer the user's question based on the provided database schema.

Rules:
1. Return ONLY the SQL query. Do not include markdown formatting.
2. Use standard SQL.
3. If the question cannot be answered with the schema, return "SELECT 'CANNOT ANSWER';"
"""

    def _default_analysis_prompt(self) -> str:
        return """You are a helpful data assistant.
Answer the user's question based on the provided data.

Rules:
1. Be concise and professional.
2. Highlight key insights.
3. If data is empty, state that no information was found.
"""

    def _default_config(self) -> Dict[str, Any]:
        return {
            "provider": "deepseek",
            "base_url": os.getenv("LLM_BASE_URL", "https://api.deepseek.com"),
            "model": os.getenv("LLM_MODEL", "deepseek-chat"),
            "api_key_encrypted": self._encrypt_secret(os.getenv("LLM_API_KEY", "")),
            "has_api_key": bool(os.getenv("LLM_API_KEY", "")),
            "temperature": 0.5,
            "analysis_channel": "auto",
            "sql_prompt": self._default_sql_prompt(),
            "analysis_prompt": self._default_analysis_prompt(),
        }

    def _load_config(self):
        config = self._default_config()
        if self.config_path.exists():
            try:
                file_config = json.loads(self.config_path.read_text(encoding="utf-8"))
                config.update(file_config)
            except Exception as exc:
                logger.warning(f"Load agent config failed: {exc}")
        self.provider = config.get("provider", "deepseek")
        self.base_url = config.get("base_url", "https://api.deepseek.com")
        self.model = config.get("model", "deepseek-chat")
        if config.get("api_key_encrypted"):
            self.api_key = self._decrypt_secret(config.get("api_key_encrypted", ""))
        else:
            self.api_key = str(config.get("api_key", "") or "")
        self.temperature = float(config.get("temperature", 0.5))
        channel = str(config.get("analysis_channel", "auto") or "auto").strip()
        self.analysis_channel = channel if channel in ["auto", "agent", "simulate"] else "auto"
        self.sql_prompt_template = config.get("sql_prompt", self._default_sql_prompt())
        self.analysis_prompt_template = config.get("analysis_prompt", self._default_analysis_prompt())
        self._normalize_provider_config()

    def _persist_config(self):
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "provider": self.provider,
            "base_url": self.base_url,
            "model": self.model,
            "api_key_encrypted": self._encrypt_secret(self.api_key),
            "has_api_key": bool(self.api_key),
            "temperature": self.temperature,
            "analysis_channel": self.analysis_channel,
            "sql_prompt": self.sql_prompt_template,
            "analysis_prompt": self.analysis_prompt_template,
        }
        self.config_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def get_config(self, masked: bool = False) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "base_url": self.base_url,
            "model": self.model,
            "api_key": self._mask_api_key(self.api_key) if masked else self.api_key,
            "has_api_key": bool(self.api_key),
            "temperature": self.temperature,
            "analysis_channel": self.analysis_channel,
            "sql_prompt": self.sql_prompt_template,
            "analysis_prompt": self.analysis_prompt_template,
        }

    def update_config(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        presets = self._provider_presets()
        if "provider" in payload:
            self.provider = str(payload["provider"]).strip()
        if "base_url" in payload:
            self.base_url = str(payload["base_url"]).rstrip("/")
        if "model" in payload:
            self.model = str(payload["model"]).strip()
        if "api_key" in payload and str(payload["api_key"]).strip():
            self.api_key = str(payload["api_key"]).strip()
        if "temperature" in payload:
            self.temperature = max(0.0, min(1.0, float(payload["temperature"])))
        if "analysis_channel" in payload:
            channel = str(payload["analysis_channel"] or "").strip()
            self.analysis_channel = channel if channel in ["auto", "agent", "simulate"] else "auto"
        if "sql_prompt" in payload:
            self.sql_prompt_template = str(payload["sql_prompt"]).strip() or self._default_sql_prompt()
        if "analysis_prompt" in payload:
            self.analysis_prompt_template = str(payload["analysis_prompt"]).strip() or self._default_analysis_prompt()
        if self.provider not in presets:
            self.provider = "deepseek"
        preset = presets[self.provider]
        if not self.base_url:
            self.base_url = preset["base_url"]
        if self.model not in preset["models"]:
            self.model = preset["default_model"]
        self._persist_config()
        return self.get_config(masked=True)

    async def chat_completion(self, messages: List[Dict[str, str]], temperature: float | None = None, model_override: str | None = None) -> str:
        """
        Call the LLM API for chat completion.
        """
        if not self.api_key:
            logger.warning("LLM_API_KEY not set. Returning mock response.")
            return self._get_mock_response(messages)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        model_name = model_override or self.model
        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": self.temperature if temperature is None else temperature,
            "stream": False
        }

        started = time.perf_counter()
        logger.info(f"LLM request start model={model_name} base_url={self.base_url} messages={len(messages)}")
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await asyncio.wait_for(
                    client.post(
                        f"{self.base_url}/chat/completions",
                        headers=headers,
                        json=payload
                    ),
                    timeout=self.timeout
                )
                response.raise_for_status()
                result = response.json()
                elapsed = time.perf_counter() - started
                logger.info(f"LLM request success model={model_name} elapsed={elapsed:.2f}s")
                return result["choices"][0]["message"]["content"]
        except Exception as e:
            elapsed = time.perf_counter() - started
            logger.error(f"Error calling LLM API model={model_name} after {elapsed:.2f}s: {e}")
            return f"Error: Unable to process request. {str(e)}"

    def _get_mock_response(self, messages: List[Dict[str, str]]) -> str:
        """
        Return a mock response when API key is missing.
        """
        last_msg = messages[-1]["content"]
        if "SQL" in last_msg or "sql" in last_msg:
            # Mock SQL generation
            return "SELECT * FROM mock_table LIMIT 10;"
        else:
            return f"I received your message: '{last_msg}'. Please configure LLM_API_KEY to get real responses."

    async def generate_sql(self, question: str, schema_info: str) -> str:
        """
        Generate SQL query from natural language question.
        """
        system_prompt = f"""{self.sql_prompt_template}

Schema Information:
{schema_info}
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ]
        
        response = await self.chat_completion(messages, temperature=0.1, model_override=None)
        if response.strip().upper().find("CANNOT ANSWER") >= 0 and self.provider == "deepseek":
            reinforce_system = f"""{self.sql_prompt_template}

Schema Information:
{schema_info}

补充要求：
1) 对库存/销量/订单/产量类问题必须优先在事实表中选择最相关表并给出可执行SQL。
2) 不要轻易返回 CANNOT ANSWER，只有确实无任何字段可映射时才返回。
"""
            reinforced_messages = [
                {"role": "system", "content": reinforce_system},
                {"role": "user", "content": question}
            ]
            response = await self.chat_completion(reinforced_messages, temperature=0.05, model_override=None)
        # Clean up response if it contains markdown
        response = response.strip()
        if response.startswith("```sql"):
            response = response[6:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
            
        return response.strip()

    async def analyze_data(self, question: str, data: Any) -> str:
        """
        Generate a natural language answer based on the data.
        """
        grounding_rules = """
必须遵守：
1) 仅根据提供的 Data 回答，禁止编造任何基地、数值、同比环比或原因。
2) 若 Data 中没有某指标，必须明确说明“数据未提供该指标”，不得推断。
3) 结论中的每个数字必须可在 Data 中找到。
4) 不要输出与 Data 无关的模板化段落。
"""
        system_prompt = f"{self.analysis_prompt_template}\n\n{grounding_rules}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Question: {question}\nData: {json.dumps(data, ensure_ascii=False)}"}
        ]
        answer = await self.chat_completion(messages, temperature=self.temperature, model_override=None)
        if answer.strip().startswith("Error:") and self.provider == "deepseek":
            answer = await self.chat_completion(messages, temperature=self.temperature, model_override=None)
        return answer

    async def answer_with_file_context(self, question: str, context: Dict[str, Any]) -> str:
        grounding_rules = """
必须遵守：
1) 只能根据“文件上下文”回答，禁止编造基地、日期、指标或原因。
2) 每个数值都必须能在上下文中找到；找不到就明确说“未提供该数据”。
3) 优先按“基地+日期+指标”精准作答，日期缺失时说明按月末或汇总口径回答。
4) 库存优先使用 inventory_daily 的 *_wt（万吨）；若使用 *_ton 必须显式写“吨”。
5) 不输出SQL、不提数据库表结构、不输出与问题无关模板话术。
6) 输出格式：先结论（1-2句），再列2-5条关键数据点。
"""
        system_prompt = f"{self.analysis_prompt_template}\n\n{grounding_rules}"
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"问题：{question}\n文件上下文：{json.dumps(context, ensure_ascii=False)}"
            }
        ]
        answer = await self.chat_completion(messages, temperature=min(self.temperature, 0.2), model_override=None)
        return answer

llm_service = LLMService()
