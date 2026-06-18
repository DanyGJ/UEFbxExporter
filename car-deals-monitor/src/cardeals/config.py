"""Carga y validación de la configuración.

La configuración de *qué* buscar vive en un fichero YAML (no secreto, se versiona).
Los *secretos* (credenciales SMTP, destinatarios) vienen de variables de entorno,
para que en GitHub Actions se inyecten como Secrets.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml


@dataclass
class SearchConfig:
    """Una búsqueda concreta en un portal."""

    name: str
    portal: str
    params: dict[str, Any] = field(default_factory=dict)
    max_results: int = 30
    enabled: bool = True

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "SearchConfig":
        if "name" not in d:
            raise ValueError("Cada búsqueda necesita un campo 'name'.")
        if "portal" not in d:
            raise ValueError(f"La búsqueda '{d['name']}' necesita un campo 'portal'.")
        return SearchConfig(
            name=str(d["name"]),
            portal=str(d["portal"]),
            params=dict(d.get("params", {})),
            max_results=int(d.get("max_results", 30)),
            enabled=bool(d.get("enabled", True)),
        )


@dataclass
class EmailConfig:
    """Configuración de envío de email (secretos vía entorno)."""

    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    user: str = ""
    password: str = ""
    sender: str = ""
    recipients: list[str] = field(default_factory=list)

    @staticmethod
    def from_env() -> "EmailConfig":
        user = os.environ.get("SMTP_USER", "").strip()
        recipients_raw = os.environ.get("EMAIL_TO", "").strip()
        recipients = [r.strip() for r in recipients_raw.split(",") if r.strip()]
        return EmailConfig(
            smtp_host=os.environ.get("SMTP_HOST", "smtp.gmail.com").strip(),
            smtp_port=int(os.environ.get("SMTP_PORT", "587")),
            user=user,
            password=os.environ.get("SMTP_PASSWORD", ""),
            sender=os.environ.get("EMAIL_FROM", user).strip() or user,
            recipients=recipients,
        )

    @property
    def is_complete(self) -> bool:
        return bool(self.user and self.password and self.recipients)


@dataclass
class AppConfig:
    searches: list[SearchConfig]
    email: EmailConfig
    state_path: Path

    @staticmethod
    def load(config_path: str | os.PathLike, *, state_path: Optional[str] = None) -> "AppConfig":
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"No se encuentra el fichero de configuración: {path}")
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}

        raw_searches = data.get("searches", [])
        if not isinstance(raw_searches, list):
            raise ValueError("'searches' debe ser una lista.")
        searches = [SearchConfig.from_dict(s) for s in raw_searches]

        resolved_state = (
            state_path
            or os.environ.get("STATE_PATH")
            or data.get("state_path")
            or "data/seen.json"
        )
        return AppConfig(
            searches=searches,
            email=EmailConfig.from_env(),
            state_path=Path(resolved_state),
        )
