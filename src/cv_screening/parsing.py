"""División del texto de un CV en secciones (RF-03).

Un encabezado de sección es una línea corta que, sin acentos, mayúsculas ni dos puntos,
coincide exactamente con un título conocido en español o inglés. La coincidencia exacta evita
confundir una viñeta como "Experiencia en ventas" con un encabezado. Lo que aparece antes del
primer encabezado (nombre, puesto y contacto) y las secciones sin categoría van a `other`; si no
se reconoce ningún encabezado, todo el texto queda en `other`.
"""

import hashlib
import re
import unicodedata

from cv_screening.schemas import CV, CVSections

SECTION_TITLES = {
    "summary": [
        "resumen", "resumen profesional", "perfil", "perfil profesional", "objetivo",
        "objetivo profesional", "acerca de mi", "sobre mi",
        "summary", "professional summary", "profile", "professional profile", "objective",
        "career objective", "about me", "executive profile",
    ],
    "experience": [
        "experiencia", "experiencia laboral", "experiencia profesional", "historial laboral",
        "trayectoria profesional",
        "experience", "work experience", "professional experience", "employment history",
        "work history",
    ],
    "education": [
        "educacion", "formacion", "formacion academica", "estudios", "preparacion academica",
        "education", "academic background", "education and training",
    ],
    "skills": [
        "habilidades", "habilidades tecnicas", "competencias", "conocimientos",
        "conocimientos tecnicos", "aptitudes", "herramientas",
        "skills", "technical skills", "core competencies", "core qualifications", "expertise",
    ],
    "other": [
        "idiomas", "certificaciones", "cursos", "proyectos", "proyectos escolares", "logros",
        "premios", "referencias", "voluntariado", "intereses",
        "languages", "certifications", "courses", "projects", "accomplishments", "awards",
        "references", "volunteer work", "interests", "additional information",
    ],
}  # fmt: skip

_TITLE_TO_SECTION = {
    title: section for section, titles in SECTION_TITLES.items() for title in titles
}
MAX_HEADING_CHARS = 40


def normalize_heading(line: str) -> str:
    """Minúsculas, sin acentos ni puntuación final: "EDUCACIÓN:" -> "educacion"."""
    without_accents = "".join(
        c for c in unicodedata.normalize("NFKD", line) if not unicodedata.combining(c)
    )
    return re.sub(r"\s+", " ", without_accents.lower().strip(" :.-•\t"))


def section_of(line: str) -> str | None:
    """Sección a la que corresponde un encabezado, o None si la línea no es encabezado."""
    if len(line.strip()) > MAX_HEADING_CHARS:
        return None
    return _TITLE_TO_SECTION.get(normalize_heading(line))


def parse_cv(text: str, file_name: str | None = None) -> CV:
    parts: dict[str, list[str]] = {name: [] for name in SECTION_TITLES}
    current = "other"
    for line in text.splitlines():
        if not line.strip():
            continue
        if section := section_of(line):
            current = section
            continue
        parts[current].append(line.strip())
    sections = CVSections(**{name: "\n".join(lines) for name, lines in parts.items()})
    candidate_id = f"cand-{hashlib.sha1(text.encode()).hexdigest()[:10]}"
    return CV(candidate_id=candidate_id, file_name=file_name, raw_text=text, sections=sections)
