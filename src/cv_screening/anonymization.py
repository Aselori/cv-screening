"""Eliminación de datos personales de CVs y vacantes (RF-05).

Se usan dos mecanismos: patrones (correo, teléfono, URL, código postal, domicilio) y la
estructura del CV (el nombre suele ser la primera línea o seguir a "Nombre:"). Cada nombre
encontrado se reemplaza en todo el texto.

El reconocimiento de entidades de spaCy se evaluó y se descartó: en los CVs del conjunto de
entrenamiento casi todas las "personas" que detectaba eran habilidades o empresas ("Google
Cloud", "Microsoft Visio", "Data Warehouse"), y borrarlas dañaría las características.
"""

import re
from collections import Counter
from dataclasses import dataclass, field

EMAIL = "[CORREO]"
PHONE = "[TELEFONO]"
URL = "[URL]"
NAME = "[NOMBRE]"
ADDRESS = "[DOMICILIO]"

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
URL_RE = re.compile(
    r"(?:https?://|www\.)\S+|\b(?:linkedin\.com|github\.com|gitlab\.com)/\S+", re.IGNORECASE
)
# Candidatos a teléfono; se confirman contando dígitos y descartando rangos de años
# ("2011-2015" pegado a otro número parece un teléfono de 10 dígitos). Entre grupos de dígitos
# se aceptan hasta dos separadores, porque en los PDF el número puede partirse en dos líneas:
# "(81) 5555-\n0114".
YEAR_RANGE_RE = re.compile(r"(?:19|20)\d{2}\s*[-–\s]\s*(?:19|20)\d{2}")
PHONE_RE = re.compile(
    r"(?<![\w])(?:\+?\d{1,3}[\s.-]?)?(?:\(\d{2,3}\)|\d{2,3})(?:[\s.-]{0,2}\d){7,8}"
)
POSTAL_CODE_RE = re.compile(
    # México: "C.P. 64000"
    r"\b(?:C\.?\s?P\.?|c[óo]digo postal)\s*:?\s*\d{5}\b"
    # EE. UU.: "Atlanta, GA 30043". Solo una palabra de ciudad, para no borrar texto previo
    # como "Data Analyst"; lo que identifica es el código postal.
    r"|\b[A-Z][a-zA-Z.]+,\s?[A-Z]{2}\s\d{5}(?:-\d{4})?\b"
)
STREET_RE = re.compile(
    r"\b(?:Calle|Av\.|Avenida|Blvd\.|Boulevard|Col\.|Colonia|Fracc\.)\s[^\n,]+(?:,[^\n]*)?",
    re.IGNORECASE,
)
NAME_LABEL_RE = re.compile(r"^\s*(?:Nombre(?: completo)?|Name)\s*:\s*(.+?)\s*$", re.M | re.I)

NAME_PARTICLES = {"de", "del", "la", "las", "los", "y", "van", "von", "da"}
NAME_WORD_RE = re.compile(r"^[A-ZÁÉÍÓÚÑÜ][a-záéíóúñü'-]+$")
# Palabras que indican un encabezado o un puesto, nunca un nombre de persona.
NOT_NAME_WORDS = {
    # secciones
    "resumen", "perfil", "experiencia", "educación", "educacion", "formación", "habilidades",
    "competencias", "idiomas", "certificaciones", "contacto", "datos", "personales", "objetivo",
    "summary", "experience", "education", "skills", "profile", "contact", "objective",
    "curriculum", "vitae", "currículum", "resume", "description", "about", "overview",
    # puestos
    "analista", "ingeniero", "ingeniera", "desarrollador", "desarrolladora", "gerente",
    "auxiliar", "ejecutivo", "ejecutiva", "contador", "contadora", "asistente", "coordinador",
    "coordinadora", "director", "directora", "técnico", "técnica", "especialista", "jefe",
    "analyst", "engineer", "developer", "manager", "assistant", "accountant", "executive",
    "coordinator", "technician", "specialist", "consultant", "representative", "clerk",
}  # fmt: skip


@dataclass
class AnonymizationResult:
    text: str
    replacements: Counter = field(default_factory=Counter)


def _is_name_word(word: str) -> bool:
    # Acepta nombres en mayúsculas ("VALERIA") comparándolos en formato de título.
    return bool(NAME_WORD_RE.match(word.capitalize() if word.isupper() else word))


def looks_like_name(line: str) -> bool:
    """Dos a cinco palabras capitalizadas (con partículas como "de" o "del"), sin dígitos."""
    words = line.strip().split()
    content = [w for w in words if w.lower() not in NAME_PARTICLES]
    if not 2 <= len(content) <= 5 or len(words) > 7:
        return False
    if any(w.lower().strip(":,") in NOT_NAME_WORDS for w in words):
        return False
    return all(_is_name_word(w) for w in content)


def _leading_name(line: str) -> str | None:
    """Nombre al inicio de una línea que sigue con otros datos.

    En los PDF con encabezado a dos columnas, el nombre y el teléfono quedan en la misma
    línea: "Sofía Elizondo Cantú (81) 5555-0102".
    """
    tokens = line.split()
    words = []
    for word in tokens:
        if not (_is_name_word(word) or word.lower() in NAME_PARTICLES):
            break
        words.append(word)
    while words and words[-1].lower() in NAME_PARTICLES:
        words.pop()
    rest = tokens[len(words) :]
    # Solo cuenta si lo que sigue es un dato de contacto; si no, frases como "Built REST
    # APIs" parecerían nombres.
    if not rest or not (rest[0][0] in "(+|·•-," or rest[0][0].isdigit() or "@" in rest[0]):
        return None
    candidate = " ".join(words)
    return candidate if looks_like_name(candidate) else None


def header_name(text: str, max_lines: int = 3) -> str | None:
    """Devuelve el nombre de persona en las primeras líneas del encabezado, si lo hay."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines[:max_lines]:
        if looks_like_name(line):
            return line
        if name := _leading_name(line):
            return name
    return None


def candidate_names(text: str) -> set[str]:
    names = {m.group(1) for m in NAME_LABEL_RE.finditer(text) if looks_like_name(m.group(1))}
    if name := header_name(text):
        names.add(name)
    # Un nombre en mayúsculas en el encabezado puede aparecer en formato de título más abajo.
    names |= {name.title() for name in names if name.isupper()}
    # El nombre de pila solo ("Soy Daniela") también se quita, porque suele revelar el género
    # (RNF-02). Los apellidos no, porque coinciden con empresas ("Garza y Asociados").
    names |= {name.split()[0] for name in names if not name.isupper()}
    return names


def _replace(pattern: re.Pattern, placeholder: str, text: str, counts: Counter, kind: str):
    text, n = pattern.subn(placeholder, text)
    counts[kind] += n
    return text


def _replace_phones(text: str, counts: Counter) -> str:
    def repl(match: re.Match) -> str:
        candidate = match.group(0)
        digits = sum(c.isdigit() for c in candidate)
        if 10 <= digits <= 13 and not YEAR_RANGE_RE.match(candidate):
            counts["phone"] += 1
            return PHONE
        return match.group(0)

    return PHONE_RE.sub(repl, text)


def _remove_names(text: str, names: set[str], counts: Counter) -> str:
    # Primero los nombres más largos para no dejar restos ("Ana López" antes de "Ana").
    for name in sorted(names, key=len, reverse=True):
        pattern = re.compile(rf"(?<!\w){re.escape(name)}(?!\w)")
        text, n = pattern.subn(NAME, text)
        counts["name"] += n
    return text


def anonymize(text: str, *, remove_names: bool = True) -> AnonymizationResult:
    """Reemplaza los datos personales por etiquetas como [CORREO] o [NOMBRE].

    Para vacantes se usa `remove_names=False`: no describen a un candidato, y su primera línea
    suele ser un encabezado como "Job Description" que parecería un nombre.
    """
    counts: Counter = Counter()
    names = candidate_names(text) if remove_names else set()
    text = _replace(EMAIL_RE, EMAIL, text, counts, "email")
    text = _replace(URL_RE, URL, text, counts, "url")
    text = _replace_phones(text, counts)
    text = _replace(POSTAL_CODE_RE, ADDRESS, text, counts, "address")
    text = _replace(STREET_RE, ADDRESS, text, counts, "address")
    text = _remove_names(text, names, counts)
    return AnonymizationResult(text=text, replacements=counts)
