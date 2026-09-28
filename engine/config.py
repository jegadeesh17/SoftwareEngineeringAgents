"""
Configuration Manager for SoftwareEngineeringAgents
Handles sticky model detection, session persistence, and user model overrides.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

DEFAULT_CONFIG_PATH = Path(".orchestrator") / "config.json"

DEFAULT_MODELS = {
    "gemini": "gemini-2.5-pro",
    "anthropic": "claude-3-7-sonnet",
    "openai": "gpt-4o",
}

AVAILABLE_MODELS = [
    {"provider": "gemini", "model": "gemini-2.5-pro", "desc": "Google Gemini 2.5 Pro (Recommended for reasoning & architecture)"},
    {"provider": "gemini", "model": "gemini-2.5-flash", "desc": "Google Gemini 2.5 Flash (Fast execution)"},
    {"provider": "anthropic", "model": "claude-3-7-sonnet", "desc": "Anthropic Claude 3.7 Sonnet (Hybrid reasoning & coding)"},
    {"provider": "anthropic", "model": "claude-3-5-haiku", "desc": "Anthropic Claude 3.5 Haiku (Fast helper)"},
    {"provider": "openai", "model": "gpt-4o", "desc": "OpenAI GPT-4o (General purpose)"},
    {"provider": "openai", "model": "gpt-4o-mini", "desc": "OpenAI GPT-4o Mini (Fast helper)"},
]

class ConfigManager:
    def __init__(self, config_file: Path = DEFAULT_CONFIG_PATH):
        self.config_file = config_file
        self.config: Dict[str, Any] = self._load()

    def _load(self) -> Dict[str, Any]:
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return self._detect_defaults()

    def _detect_defaults(self) -> Dict[str, Any]:
        """Detect default model from environment variables or sensible default."""
        provider = "gemini"
        model = "gemini-2.5-pro"

        if os.environ.get("ANTHROPIC_API_KEY"):
            provider = "anthropic"
            model = os.environ.get("ANTHROPIC_MODEL", "claude-3-7-sonnet")
        elif os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"):
            provider = "gemini"
            model = os.environ.get("GEMINI_MODEL", "gemini-2.5-pro")
        elif os.environ.get("OPENAI_API_KEY"):
            provider = "openai"
            model = os.environ.get("OPENAI_MODEL", "gpt-4o")

        return {
            "default_provider": provider,
            "default_model": model,
            "agent_models": {
                "orchestrator": model,
                "product_analyst": model,
                "software_architect": model,
                "task_planner": model,
                "software_developer": model,
                "qa_tester": model,
            },
            "last_used": model
        }

    def save(self):
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2)

    def get_active_model(self) -> str:
        return self.config.get("default_model", "gemini-2.5-pro")

    def get_active_provider(self) -> str:
        return self.config.get("default_provider", "gemini")

    def get_agent_model(self, agent_role: str) -> str:
        return self.config.get("agent_models", {}).get(agent_role, self.get_active_model())

    def update_model(self, provider: str, model: str, per_agent: Optional[Dict[str, str]] = None):
        self.config["default_provider"] = provider
        self.config["default_model"] = model
        self.config["last_used"] = model
        if per_agent:
            self.config["agent_models"] = per_agent
        else:
            self.config["agent_models"] = {
                k: model for k in self.config.get("agent_models", {}).keys()
            }
        self.save()
