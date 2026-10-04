# Datos

Fase 2 del cronograma. Hay dos conjuntos: uno público en inglés para entrenar y probar los
modelos, y uno propio en español para medir el desempeño en el idioma principal del sistema.

## 1. Conjunto de entrenamiento (inglés)

| Dato | Valor |
|---|---|
| Fuente | [cnamuangtoun/resume-job-description-fit](https://huggingface.co/datasets/cnamuangtoun/resume-job-description-fit) (Hugging Face) |
| Revisión fija | `08978e21714984bb417547d2c0f9b477f5298163` |
| Licencia | No declarada en la página del conjunto. Se usa con fines académicos y se cita la fuente. |
| Contenido | Pares CV-vacante en inglés con la etiqueta `Good Fit`, `Potential Fit` o `No Fit`. |

Los archivos descargados y procesados no se guardan en Git. Para generarlos:

```bash
python -m cv_screening.datasets download   # data/raw/train.csv y test.csv
python -m cv_screening.datasets prepare    # data/processed/train.csv, test.csv y report.json
```

`prepare` hace lo siguiente:

1. Quita los pares duplicados y los pares con etiquetas contradictorias (el mismo CV y la misma
   vacante con dos etiquetas distintas).
2. Anonimiza cada texto (ver sección 3).
3. Asigna identificadores estables por CV (`cv_id`) y por vacante (`vacancy_id`).
4. Valida cada fila contra el esquema `LabeledPair` (`src/cv_screening/schemas.py`).

Resultado (`data/processed/report.json`):

| | Entrenamiento | Prueba |
|---|---|---|
| Filas originales | 6,241 | 1,759 |
| Duplicados exactos quitados | 1 | 0 |
| Filas con etiquetas contradictorias quitadas | 12 (6 pares) | 0 |
| Pares finales | 6,228 | 1,759 |
| No Fit / Potential Fit / Good Fit | 3,136 / 1,554 / 1,538 | 857 / 444 / 458 |
| CVs distintos | 642 | 477 |
| Vacantes distintas | 280 | 71 |

### Hallazgos que afectan a la fase 5

- **CVs repetidos entre entrenamiento y prueba.** 476 de los 477 CVs de prueba también
  aparecen en entrenamiento; solo las vacantes son distintas. Las características del modelo no
  identifican al candidato, así que el efecto debería ser pequeño, pero en la fase 5 también se
  medirá con una partición agrupada por `cv_id`.
- **Clases desbalanceadas.** La mitad de los pares son `No Fit`; se reporta F1 macro.
- **Datos personales.** Los CVs ya traían datos de plantilla (`resumesample@example.com`,
  `(555) 432-1000`). Las vacantes sí traían contactos reales de reclutadores: en entrenamiento,
  35 correos y 21 teléfonos en 280 vacantes distintas.

## 2. Conjunto propio en español

Carpeta `samples/es/`. Todos los datos son ficticios: nombres inventados, correos en el dominio
reservado `example.com`, teléfonos `81 5555 01xx` y empresas inventadas.

| Archivo | Contenido |
|---|---|
| `vacancies.json` | 4 vacantes (esquema `Vacancy`): desarrollo web, análisis de datos, ventas B2B y auxiliar contable. |
| `cvs/cv-01.md` a `cv-24.md` | Fuente de cada CV en Markdown simplificado; es el texto de referencia para probar el parser en la fase 3. |
| `docx/`, `pdf/` | Cada CV en DOCX y en PDF, con uno de tres formatos: estilos de título de Word, texto con títulos en negritas, o encabezado en tabla de dos columnas. |
| `labels.csv` | Etiqueta de cada uno de los 96 pares (24 CVs × 4 vacantes). |

Diseño:

- 6 CVs por área: 2 que cumplen (`Good Fit`), 2 parciales (`Potential Fit`) y 2 que no
  cumplen (`No Fit`). Son los 24 pares **del mismo dominio**.
- Los otros 72 pares cruzan un CV con vacantes de otra área (`pair_type = otro dominio`). Casi
  todos son `No Fit` y son fáciles de clasificar, por eso los resultados se reportan también
  solo con los 24 pares del mismo dominio.
- Incluye casos difíciles a propósito: sinónimos de habilidades ("manejo avanzado de hojas de
  cálculo", "ReactJS", "facturación electrónica" por CFDI), fechas en distintos formatos,
  nombres en mayúsculas, nombres después de "Nombre:" y un nombre de pila suelto en el texto.

**Las etiquetas son un borrador** (`labeled_by = borrador`), con el motivo en la columna
`notes`. El equipo debe revisarlas y cambiar `labeled_by` por quien las revisó. Distribución
del borrador: 77 `No Fit`, 11 `Potential Fit`, 8 `Good Fit`.

Para regenerar los DOCX y PDF después de editar una fuente (requiere LibreOffice):

```bash
python scripts/build_samples.py
```

## 3. Anonimización

`src/cv_screening/anonymization.py` reemplaza los datos personales por etiquetas
(`[NOMBRE]`, `[CORREO]`, `[TELEFONO]`, `[URL]`, `[DOMICILIO]`) con dos mecanismos:

- **Patrones:** correos, URLs, teléfonos (de 10 a 13 dígitos, descartando rangos de años),
  códigos postales de México y EE. UU., y domicilios que empiezan con "Calle", "Av.", "Col.",
  etc.
- **Estructura del CV:** el nombre en las primeras líneas (también en mayúsculas o seguido del
  teléfono en la misma línea) o después de "Nombre:". Ese nombre, su versión en formato de
  título y el nombre de pila solo se reemplazan en todo el texto. Los apellidos solos no, porque
  coinciden con nombres de empresas.

En las vacantes solo se aplican los patrones: su primera línea suele ser un encabezado como
"Job Description" que parecería un nombre.

Mediciones:

| Medición | Resultado |
|---|---|
| CVs en español (24 en DOCX y 24 en PDF) sin nombre, nombre de pila, correo ni teléfono después de anonimizar | 48 de 48 (prueba `tests/test_samples.py`) |
| Nombres falsos detectados en los 642 CVs de entrenamiento | 0 |
| Falsos positivos de teléfono en una muestra revisada a mano (12 de los 33 reemplazos en entrenamiento) | 1, un rango de años pegado a otro número; ya corregido |

**Se descartó el reconocimiento de entidades de spaCy.** En los CVs de entrenamiento casi todas
las "personas" que detectaba eran habilidades o empresas ("Google Cloud", "Microsoft Visio",
"Data Warehouse"); borrarlas dañaría las características. En español, el modelo pequeño marcó
"Cemex" como persona.

**Limitación conocida:** los nombres de otras personas dentro del texto (por ejemplo,
referencias laborales como "Supervisor: Ken Cook") no se eliminan.

## 4. Preprocesamiento (fase 4)

```bash
python -m cv_screening.datasets preprocess   # data/processed/cvs_nlp.csv y vacancies_nlp.csv
```

Lematiza cada CV y vacante distintos, y extrae habilidades (base de conocimiento de
`src/cv_screening/knowledge/skills.json`), años de experiencia y nivel educativo. Tarda unos
50 segundos. Cobertura sobre los 643 CVs y 351 vacantes del conjunto de entrenamiento:

| Medición | Resultado |
|---|---|
| CVs con años de experiencia detectados | 80.9 % |
| CVs con nivel educativo detectado | 85.8 % |
| Habilidades por CV (mediana) | 9 |
| Vacantes con 3 o más habilidades reconocidas | 76.6 % |
| Habilidades por vacante (mediana) | 4 |
| Vacantes con años mínimos detectados | 74.6 % |
| Vacantes con nivel educativo mínimo detectado | 57.0 % |

Limitaciones:

- Los periodos que terminan en "Current" o "Actualidad" se cuentan hasta la fecha de hoy. Los
  CVs del conjunto son de años anteriores, así que su experiencia queda sobreestimada (mediana
  de 13.8 años).
- La base de conocimiento tiene 81 habilidades de las áreas más comunes (software, datos,
  contabilidad, finanzas y ventas); las habilidades de otras áreas no se reconocen.
- La detección de idioma no distingue el portugués del español.
