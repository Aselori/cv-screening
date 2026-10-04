"""Base de conocimiento de habilidades en español e inglés (RF-07).

Cada habilidad tiene un identificador, un nombre para mostrar, alias en ambos idiomas y,
opcionalmente, otras habilidades que implica (`implies`): quien sabe MySQL sabe SQL y quien usa
Salesforce maneja un CRM. Esa regla es el razonamiento basado en conocimiento del sistema.
"""

import json
import re
from dataclasses import dataclass
from functools import cache
from pathlib import Path

from cv_screening.preprocessing import strip_accents

SKILLS_FILE = Path(__file__).with_name("skills.json")


@dataclass(frozen=True)
class Skill:
    id: str
    name: str
    aliases: tuple[str, ...]
    implies: tuple[str, ...] = ()


def normalize(text: str) -> str:
    """Minúsculas, sin acentos (conserva la ñ) y con espacios simples."""
    return re.sub(r"\s+", " ", strip_accents(text.lower()))


@cache
def load_skills() -> dict[str, Skill]:
    raw = json.loads(SKILLS_FILE.read_text(encoding="utf-8"))
    return {
        s["id"]: Skill(s["id"], s["name"], tuple(normalize(a) for a in s["aliases"]),
                       tuple(s.get("implies", ())))
        for s in raw
    }  # fmt: skip


@cache
def _matcher() -> tuple[re.Pattern, dict[str, str]]:
    alias_to_id = {alias: skill.id for skill in load_skills().values() for alias in skill.aliases}
    # Alias más largos primero: "sql server" gana sobre "sql" y "excel avanzado" sobre "excel".
    aliases = sorted(alias_to_id, key=len, reverse=True)
    pattern = re.compile(
        r"(?<![a-z0-9ñ])(" + "|".join(re.escape(a) for a in aliases) + r")(?![a-z0-9ñ+#])"
    )
    return pattern, alias_to_id


def _with_implied(ids: set[str]) -> set[str]:
    skills = load_skills()
    pending, result = list(ids), set(ids)
    while pending:
        for implied in skills[pending.pop()].implies:
            if implied not in result:
                result.add(implied)
                pending.append(implied)
    return result


def extract_skills(text: str) -> set[str]:
    """Identificadores de las habilidades mencionadas en el texto, más las que implican."""
    pattern, alias_to_id = _matcher()
    return _with_implied({alias_to_id[m.group(1)] for m in pattern.finditer(normalize(text))})


def skill_name(skill_id: str) -> str:
    return load_skills()[skill_id].name
