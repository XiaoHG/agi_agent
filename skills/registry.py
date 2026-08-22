"""External skill registry loading helpers."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Any
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .catalog import SkillSpec


DEFAULT_SKILL_REGISTRY_PATH = Path("configs/skill-registry.json")
SKILL_REGISTRY_ENV_VAR = "AGI_AGENT_SKILL_REGISTRY_PATH"

@dataclass(frozen=True)
class SkillRegistrySource:
    name: str                               # 来源名称 builtin / external
    path: str | None                        # 配置文件路径，builtin为None
    loaded_skill_names: tuple[str, ...]     # 该来源加载的skill名称列表

    def to_dict(self) -> dict[str, Any]:
        """Render the registry source as JSON-ready data."""

        return {
            "name": self.name,
            "path": self.path,
            "loaded_skill_names": list(self.loaded_skill_names),
        }


def get_skill_registry_path(root: Path = Path("."), env: dict[str, str] | None = None) -> Path:
    """Return the external skill registry path from env or the default config."""

    resolved_env = env or os.environ
    raw_path = resolved_env.get(SKILL_REGISTRY_ENV_VAR, "").strip()
    if raw_path:
        return Path(raw_path)
    return root / DEFAULT_SKILL_REGISTRY_PATH


def load_external_skill_specs(
    root: Path = Path("."),
    *,
    env: dict[str, str] | None = None,
    registry_path: Path | str | None = None,
) -> list[SkillSpec]:
    """Load external skill definitions from a JSON registry file."""

    from .catalog import SkillSpec

    resolved_path = Path(registry_path) if registry_path is not None else get_skill_registry_path(root, env=env)
    if not resolved_path.exists():
        return []
    payload = json.loads(resolved_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return []
    records = payload.get("skills", [])
    if not isinstance(records, list):
        return []

    specs: list[SkillSpec] = []
    for record in records:
        if not isinstance(record, dict):
            continue
        name = str(record.get("name", "")).strip()
        purpose = str(record.get("purpose", "")).strip()
        output_format = str(record.get("output_format", "")).strip()
        if not name or not purpose or not output_format:
            continue
        steps = tuple(str(step).strip() for step in record.get("steps", []) if str(step).strip())
        if not steps:
            steps = (
                "Inspect the registry entry.",
                "Follow the declared workflow.",
                "Report the result clearly.",
            )
        aliases = tuple(
            dict.fromkeys(
                str(alias).strip()
                for alias in record.get("aliases", [])
                if str(alias).strip()
            )
        )
        declared_tools = tuple(
            dict.fromkeys(
                str(tool).strip()
                for tool in record.get("declared_tools", [])
                if str(tool).strip()
            )
        )
        specs.append(
            SkillSpec(
                name=name,
                purpose=purpose,
                steps=steps,
                output_format=output_format,
                version=str(record.get("version", "v1")).strip() or "v1",
                source="external",
                path=str(resolved_path),
                aliases=aliases,
                declared_tools=declared_tools,
            )
        )
    return specs


def build_skill_registry_sources(root: Path = Path("."), env: dict[str, str] | None = None) -> tuple[SkillRegistrySource, ...]:
    """Build a compact summary of registry sources used by the catalog."""

    from .catalog import get_builtin_skills

    external_specs = load_external_skill_specs(root, env=env)
    registry_path = get_skill_registry_path(root, env=env)
    return (
        SkillRegistrySource(
            name="builtin",
            path=None,
            loaded_skill_names=tuple(spec.name for spec in get_builtin_skills()),
        ),
        SkillRegistrySource(
            name="external",
            path=str(registry_path),
            loaded_skill_names=tuple(spec.name for spec in external_specs),
        ),
    )
