"""Extracción de entidades de CVs y vacantes: años de experiencia y nivel educativo.

Son los datos que usan las características `experience_fit` y `education_fit`
(docs/requisitos.md, sección 5).
"""

import re
from datetime import date

from cv_screening.preprocessing import strip_accents
from cv_screening.schemas import EducationLevel

MONTHS = {
    "ene": 1, "jan": 1, "feb": 2, "mar": 3, "abr": 4, "apr": 4, "may": 5, "jun": 6, "jul": 7,
    "ago": 8, "aug": 8, "sep": 9, "set": 9, "oct": 10, "nov": 11, "dic": 12, "dec": 12,
}  # fmt: skip
_MONTH = r"(?:(?P<{0}m>[a-z]{{3}})[a-z]*\.?\s+|(?P<{0}n>\d{{1,2}})/)?(?P<{0}y>(?:19|20)\d{{2}})"
_PRESENT = r"(?P<present>actualidad|presente|la fecha|present|current|now|today)"
DATE_RANGE_RE = re.compile(
    _MONTH.format("s")
    + r"\s*(?:-|–|a|to|al|hasta)\s*(?:"
    + _MONTH.format("e")
    + "|"
    + _PRESENT
    + ")"
)
EXPLICIT_YEARS_RE = re.compile(
    r"(?P<n>\d{1,2})\+?\s*(?:anos?|years?|yrs)\s+(?:de\s+|of\s+)?(?:experiencia|experience)"
)
VACANCY_YEARS_RE = re.compile(r"(?P<n>\d{1,2})\+?\s*(?:anos?|years?|yrs)\b")
# Palabras que, cerca de un periodo, indican que es de estudios y no de trabajo.
EDUCATION_CONTEXT_RE = re.compile(
    r"licenciatura|ingenieria en|universidad|preparatoria|bachillerato|maestria|doctorado|"
    r"tecnico en|conalep|secundaria|university|college|bachelor|master|degree|high school|school"
)

EDUCATION_PATTERNS = [
    (EducationLevel.DOCTORATE, r"doctorado|ph\.?\s?d|doctor of"),
    (EducationLevel.MASTER, r"maestria|master|mba|m\.?sc"),
    (EducationLevel.BACHELOR, r"licenciatura|ingenieria en|bachelor|b\.?sc|undergraduate degree"),
    (EducationLevel.TECHNICAL, r"tecnico en|tecnico superior|carrera tecnica|associate|conalep"),
    (EducationLevel.HIGH_SCHOOL, r"preparatoria|bachillerato|high school|ged"),
]
EDUCATION_RES = [(level, re.compile(rf"\b(?:{p})")) for level, p in EDUCATION_PATTERNS]
IN_PROGRESS_RE = re.compile(r"en curso|trunca|cursando|in progress|currently pursuing|expected")
# Nivel completado más alto de alguien que todavía estudia (o dejó) cada nivel.
COMPLETED_BEFORE = {
    EducationLevel.DOCTORATE: EducationLevel.MASTER,
    EducationLevel.MASTER: EducationLevel.BACHELOR,
    EducationLevel.BACHELOR: EducationLevel.HIGH_SCHOOL,
    EducationLevel.TECHNICAL: EducationLevel.HIGH_SCHOOL,
    EducationLevel.HIGH_SCHOOL: None,
}


def _normalize(text: str) -> str:
    """Minúsculas y sin acentos, conservando los saltos de línea (cada periodo se evalúa en
    su línea) y sin ñ para que "año" y "ano" coincidan."""
    return strip_accents(text.lower()).replace("ñ", "n")


def _month_index(match: re.Match, prefix: str, end: bool) -> int:
    year = int(match.group(f"{prefix}y"))
    if name := match.group(f"{prefix}m"):
        month = MONTHS.get(name[:3], 1 if not end else 12)
    elif number := match.group(f"{prefix}n"):
        month = int(number)
    else:
        # Solo el año: "2019 - 2023" cuenta de enero de 2019 a enero de 2023.
        month = 1
    return year * 12 + month - 1


def _periods(text: str, today: date) -> list[tuple[int, int]]:
    periods = []
    for match in DATE_RANGE_RE.finditer(text):
        line_start = text.rfind("\n", 0, match.start()) + 1
        line_end = text.find("\n", match.end())
        line = text[line_start : line_end if line_end != -1 else None]
        if EDUCATION_CONTEXT_RE.search(line):
            continue
        start = _month_index(match, "s", end=False)
        end = today.year * 12 + today.month - 1 if match.group("present") else None
        if end is None:
            end = _month_index(match, "e", end=True)
        if start < end:
            periods.append((start, end))
    return periods


def _merged_months(periods: list[tuple[int, int]]) -> int:
    total, current_start, current_end = 0, None, None
    for start, end in sorted(periods):
        if current_end is None or start > current_end:
            if current_end is not None:
                total += current_end - current_start
            current_start, current_end = start, end
        else:
            current_end = max(current_end, end)
    if current_end is not None:
        total += current_end - current_start
    return total


def years_of_experience(text: str, today: date | None = None) -> float | None:
    """Años de experiencia de un CV, o None si no hay evidencia.

    Primero busca una mención explícita ("4 años de experiencia"); si no la hay, suma los
    periodos laborales ("2019 - 2023", "Ene 2021 - Actualidad") sin contar traslapes ni
    periodos de estudios.
    """
    normalized = _normalize(text)
    explicit = [int(m.group("n")) for m in EXPLICIT_YEARS_RE.finditer(normalized)]
    if explicit:
        return float(max(explicit))
    months = _merged_months(_periods(normalized, today or date.today()))
    return round(months / 12, 1) if months else None


def _education_mentions(text: str) -> list[tuple[EducationLevel, bool]]:
    normalized = _normalize(text)
    mentions = []
    for level, pattern in EDUCATION_RES:
        for match in pattern.finditer(normalized):
            nearby = normalized[match.end() : match.end() + 60].split("\n")[0]
            mentions.append((level, bool(IN_PROGRESS_RE.search(nearby))))
    return mentions


def education_level(text: str) -> EducationLevel | None:
    """Nivel educativo completado más alto de un CV; los estudios en curso cuentan como el
    nivel anterior ("Licenciatura (en curso)" equivale a preparatoria)."""
    mentions = _education_mentions(text)
    levels = [COMPLETED_BEFORE[lvl] if ongoing else lvl for lvl, ongoing in mentions]
    levels = [lvl for lvl in levels if lvl is not None]
    return max(levels, key=lambda lvl: lvl.rank) if levels else None


def min_education_required(text: str) -> EducationLevel | None:
    """Nivel mínimo que pide una vacante: el más bajo mencionado ("técnico o licenciatura")."""
    levels = [lvl for lvl, _ in _education_mentions(text)]
    return min(levels, key=lambda lvl: lvl.rank) if levels else None


def min_years_required(text: str) -> float | None:
    """Años de experiencia que pide una vacante; si menciona varios, el mayor."""
    normalized = _normalize(text)
    years = [int(m.group("n")) for m in VACANCY_YEARS_RE.finditer(normalized)]
    years = [y for y in years if y <= 20]
    return float(max(years)) if years else None
