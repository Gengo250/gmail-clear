from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field

Action = Literal["TRASH", "DELETE"]

class AppConfig(BaseModel):
    user_id: str = "me"
    credentials_path: str
    token_path: str
    dry_run: bool = True
    page_size: int = 200

class Rule(BaseModel):
    name: str
    query: str
    action: Action = "TRASH"
    max_results: int = 2000
    include_spam_trash: bool = False

class Settings(BaseModel):
    app: AppConfig
    rules: list[Rule] = Field(default_factory=list)

def load_settings(path: str) -> Settings:
    p = Path(path)
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    return Settings.model_validate(data)