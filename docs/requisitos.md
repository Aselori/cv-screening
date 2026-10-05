# Documento de requerimientos

Proyecto: Selección y Filtrado de Currículums para Recursos Humanos.
Fase 1 del cronograma (definición de requerimientos, criterios de evaluación de perfiles y
arquitectura). La arquitectura se describe en [arquitectura.md](arquitectura.md).

## 1. Propósito y alcance

El sistema apoya al reclutador en la evaluación inicial de candidaturas. Recibe los currículums
de una vacante, extrae su información, la compara con los requisitos del puesto y devuelve un
ranking de candidatos con un puntaje de idoneidad de 0 a 100 y la explicación de ese puntaje.
La decisión final de contratación siempre es del reclutador: el sistema prioriza, no descarta.

Idioma: el sistema está enfocado en **español**. La interfaz, la documentación, los
currículums y las vacantes son en español como caso principal, y los documentos en **inglés**
también se aceptan. Como los únicos datos etiquetados públicos disponibles están en inglés, los
modelos se entrenan con características que no dependen del idioma (sección 5), y el
desempeño en español se mide con un conjunto propio del equipo (sección 6).

## 2. Usuarios y flujo de uso

Usuario principal: reclutador de Recursos Humanos.

1. **Configuración del perfil de puesto.** El reclutador registra la vacante: título,
   descripción, habilidades requeridas, habilidades deseables, años mínimos de experiencia y
   nivel educativo mínimo.
2. **Carga y parsing de documentos.** Sube en lote los CVs en PDF o DOCX. El sistema extrae el
   texto, lo divide en secciones y lo convierte en datos estructurados.
3. **Evaluación inteligente.** El sistema anonimiza cada CV, normaliza sus habilidades con la
   base de conocimiento, calcula las características de comparación CV-vacante y obtiene el
   puntaje con el modelo entrenado.
4. **Dashboard de ranking.** El reclutador ve a los candidatos ordenados por puntaje, filtra,
   revisa la explicación de cada puntaje y marca su decisión.
5. **Retroalimentación.** Las decisiones del reclutador se guardan y se usan para reentrenar el
   modelo.

## 3. Requerimientos funcionales

| ID | Requerimiento | Fase | Prioridad |
|---|---|---|---|
| RF-01 | Registrar, editar y consultar vacantes con: título, descripción, habilidades requeridas, habilidades deseables, años mínimos de experiencia y nivel educativo mínimo. | 6-7 | Alta |
| RF-02 | Cargar en lote currículums PDF y DOCX (hasta 50 archivos por lote, máximo 5 MB cada uno). | 3 | Alta |
| RF-03 | Extraer el texto de cada documento y dividirlo en secciones: resumen, experiencia, educación, habilidades y otros. Entregar el resultado en JSON con el esquema `CV`. | 3 | Alta |
| RF-04 | Informar por archivo los errores de carga: formato no soportado, archivo dañado o PDF sin texto extraíble (por ejemplo, escaneado). Un error no detiene el resto del lote. | 3 | Alta |
| RF-05 | Anonimizar cada CV antes de evaluarlo: eliminar nombre, correo, teléfono, dirección y URLs personales. | 2-4 | Alta |
| RF-06 | Preprocesar el texto con PLN: limpieza, normalización, tokenización, eliminación de palabras vacías y lematización. | 4 | Alta |
| RF-07 | Normalizar habilidades con una base de conocimiento de sinónimos y equivalencias en español e inglés (por ejemplo, "manejo de hojas de cálculo", "Excel avanzado" y "spreadsheets" se reconocen como la habilidad `excel`). | 4-6 | Alta |
| RF-08 | Calcular para cada par CV-vacante las características de la sección 5 y un puntaje de idoneidad de 0 a 100. | 5-6 | Alta |
| RF-09 | Explicar cada puntaje: habilidades requeridas encontradas y faltantes, años de experiencia detectados y nivel educativo detectado. | 6-7 | Alta |
| RF-10 | Mostrar el ranking de candidatos por vacante, con ordenamiento, búsqueda y filtros por rango de puntaje, habilidades y experiencia. | 7 | Alta |
| RF-11 | Registrar la decisión del reclutador por candidato: Apto, Posible o No apto. | 7 | Media |
| RF-12 | Reentrenar el modelo con el conjunto base más la retroalimentación acumulada, bajo demanda, y conservar la versión anterior si la nueva tiene peores métricas. | 8 | Media |
| RF-13 | Mostrar las métricas del modelo vigente: accuracy, precision, recall y F1. | 7-8 | Media |
| RF-14 | Detectar el idioma de cada CV y vacante (español o inglés) y procesarlo con el modelo de PLN correspondiente. Un documento en otro idioma se rechaza con un mensaje claro. | 4 | Alta |

## 4. Requerimientos no funcionales

| ID | Categoría | Requerimiento |
|---|---|---|
| RNF-01 | Privacidad | Los datos personales no se usan como características del modelo. Los datos se procesan y guardan solo en el equipo local; no se envían a servicios externos. |
| RNF-02 | Equidad | El modelo no recibe nombre, género, edad, fotografía, estado civil ni dirección. Prueba de sesgo: cambiar el nombre de un CV no debe cambiar su puntaje. |
| RNF-03 | Rendimiento (meta) | Procesar y evaluar un CV en 2 segundos o menos, y un lote de 50 CVs en menos de 2 minutos, en las laptops del equipo. Se mide en la fase 8. |
| RNF-04 | Reproducibilidad | Los datos se descargan y preparan con scripts versionados. El entrenamiento usa una semilla fija y el modelo guarda sus métricas y la fecha de entrenamiento. |
| RNF-05 | Portabilidad | El sistema se instala y ejecuta en Linux y Windows con Python 3.12 o superior. |
| RNF-06 | Mantenibilidad | Pruebas automatizadas con pytest y estilo verificado con ruff en cada cambio. |
| RNF-07 | Usabilidad | Interfaz en español. Un reclutador sin conocimientos técnicos puede crear una vacante, cargar CVs y leer el ranking sin ayuda. Se valida con pruebas de usabilidad en la fase 7. |
| RNF-08 | Transparencia | Cada puntaje se acompaña de su explicación (RF-09); el sistema nunca muestra un puntaje sin justificación. |

## 5. Criterios de evaluación de perfiles

Cada CV se evalúa contra una vacante con siete características: cuatro absolutas y tres
relativas a los demás candidatos de la misma vacante. Todas se calculan después de
anonimizar el CV y **no dependen del idioma**: cada una compara el CV con su propia vacante, y
el resultado es un número que significa lo mismo en español o en inglés. Por eso un modelo
entrenado con pares en inglés puede evaluar pares en español.

| Característica | Cálculo | Rango |
|---|---|---|
| `text_similarity` | Similitud coseno entre los vectores TF-IDF del CV y de la vacante, con el texto preprocesado y lematizado en su idioma. | 0 a 1 |
| `skill_coverage` | Habilidades de la vacante presentes en el CV, normalizadas con la base de conocimiento. Las deseables pesan la mitad: (requeridas encontradas + 0.5 × deseables encontradas) / (requeridas + 0.5 × deseables). Si la vacante no lista habilidades, vale 1. | 0 a 1 |
| `experience_fit` | Años de experiencia detectados en el CV ("5 años", "5 years" o periodos como "2021-2024") entre los años mínimos requeridos, con tope en 1. Si la vacante no indica años, vale 1. | 0 a 1 |
| `education_fit` | 1 si el nivel educativo detectado alcanza el mínimo requerido o si la vacante no pide uno, 0.5 si es un nivel inferior, 0 si no se detecta. Niveles: bachillerato, técnico, licenciatura, maestría, doctorado, con sus equivalentes en inglés (high school, associate, bachelor, master, PhD). | 0, 0.5 o 1 |
| `similarity_rank` | Percentil de `text_similarity` entre los candidatos de la misma vacante (agregada en la fase 5). | 0 a 1 |
| `coverage_rank` | Percentil de `skill_coverage` entre los candidatos de la misma vacante (fase 5). | 0 a 1 |
| `matched_skills` | Número de habilidades requeridas encontradas, con tope en 10, dividido entre 10 (fase 5). | 0 a 1 |

**Clases.** Cada par CV-vacante pertenece a una de tres clases: `Good Fit`, `Potential Fit` o
`No Fit` (las etiquetas del conjunto de datos). En la interfaz se muestran como Apto, Posible y
No apto.

**Puntaje de idoneidad.** El modelo de Regresión Logística estima la probabilidad de cada clase
a partir de las siete características anteriores. No usa las palabras del texto como
características directas, porque esas sí dependen del idioma. El puntaje es:

```
puntaje = 100 × ( P(Good Fit) + 0.5 × P(Potential Fit) )
```

El ranking ordena por puntaje; en empate, por `skill_coverage`. La fórmula es la
propuesta inicial y se revisa en la fase 5 con las métricas reales.

**Modelos.** La Regresión Logística es el modelo principal y Naive Bayes (gaussiano, sobre las
mismas características) es el modelo de comparación. Ambos se comparan contra una línea base sin
aprendizaje que solo usa `text_similarity`. El modelo elegido debe superar a la línea base en F1
macro; la meta numérica se fija en la fase 5 al medir las líneas base. Si en la fase 5 se
necesitan más características, se agregan solo si tampoco dependen del idioma.

## 6. Datos

| Uso | Fuente | Contenido |
|---|---|---|
| Entrenamiento y prueba | [cnamuangtoun/resume-job-description-fit](https://huggingface.co/datasets/cnamuangtoun/resume-job-description-fit) (Hugging Face) | 8,000 pares CV-vacante en inglés: 6,241 de entrenamiento y 1,759 de prueba. Etiquetas en el entrenamiento: No Fit 3,143, Potential Fit 1,556, Good Fit 1,542. |
| Evaluación en español | Conjunto propio: 4 vacantes y 24 CVs ficticios en español, en PDF y DOCX, con etiquetas que el equipo revisa | 96 pares (cada CV contra las 4 vacantes); 24 son del mismo dominio. También sirve para probar el parser. Detalle en `data/README.md`. |

Limitaciones conocidas, que se documentan en el reporte:

- La licencia del conjunto de datos no está declarada en su página, y el origen de las
  etiquetas no está documentado. Se usa con fines académicos y se cita la fuente.
- Las clases están desbalanceadas (la mitad son No Fit), por lo que se reporta F1 macro y no
  solo accuracy.
- El entrenamiento es en inglés. El desempeño en español se mide solo con el conjunto propio
  de 96 pares, que es pequeño (y de esos, solo 24 son del mismo dominio); el reporte presenta
  ese resultado como indicativo, no como definitivo.

## 7. Medidas de rendimiento del agente

Tomadas de la actividad 2.1:

- Accuracy, precision, recall y F1 (macro y por clase), reportadas por separado para el
  conjunto de prueba en inglés (1,759 pares) y el conjunto propio en español.
- Tiempo de procesamiento por CV (RNF-03).
- Satisfacción de los reclutadores, medida en las pruebas de usabilidad (RNF-07).

## 8. Fuera de alcance

- Reconocimiento óptico de caracteres (OCR) para CVs escaneados: se reportan como error (RF-04).
- Currículums en idiomas distintos al español y al inglés.
- Cuentas de usuario, permisos y despliegue en la nube: el sistema se ejecuta localmente para
  la demostración.
- Integración con sistemas de RH de terceros.

## 9. Supuestos y riesgos

| Riesgo | Mitigación |
|---|---|
| Las etiquetas del conjunto de datos no reflejan criterios reales de una empresa. | Se presenta como limitación; la retroalimentación del reclutador (RF-11, RF-12) adapta el modelo a criterios propios. |
| Las características calculadas en español se distribuyen distinto que en inglés (por ejemplo, la similitud de textos), y el modelo entrenado en inglés pierde precisión. | Se mide con el conjunto propio en español; si la diferencia es grande, se ajustan las características o se reentrena con la retroalimentación en español (RF-12). |
| El reconocimiento de entidades de spaCy confunde personas con empresas y habilidades (medido en la fase 2). | Se descartó para anonimizar; se usan patrones y la estructura del CV. Medición: 48 de 48 documentos del conjunto propio quedan sin datos personales y 0 nombres falsos en los CVs de entrenamiento (`data/README.md`). |
| Los CVs tienen formatos muy variados y el parser no detecta todas las secciones. | Si no se detectan secciones, el CV completo se trata como un solo bloque y se evalúa igual. |
| El equipo va atrasado respecto al cronograma original (fases 2 y 3 vencían en septiembre). | Se propone recuperar las fases 1 a 3 al regresar del periodo de exámenes de medio curso (pendiente de confirmar con el equipo); el reporte de avance 3.2 presenta el cronograma ajustado. |
