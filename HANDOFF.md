# HANDOFF

Punto de recuperación del trabajo. Actualizado: 2026-10-02.

## Objetivo

Avanzar el proyecto fase por fase con revisión de Aldo entre fases. **Alcance: lo que pide el
curso, sin crecer más.** No se trata de recortar lo planeado, sino de no agregar funciones ni
pulido más allá del proyecto de clase; Aldo no lo seguirá después de aprobar la materia.

- Fases 1 a 3 (requerimientos, datos, carga y parsing): **aprobadas, en `main`**.
- Fase 4 (preprocesamiento PLN): **aprobada, en `main`**.
- Fase 5 (características y modelos): **aprobada, en `main`**.
- Fase 6 (motor de puntuación y API): **aprobada, en `main`**.
- Fase 7 (dashboard): **aprobada, en `main`**.
- Fase 8 (integración, sesgos, tiempos, reentrenamiento): **aprobada, en `main`**.
- Fase 9 (ajustes finales y documentación): **aprobada, en `main`**.
  Con esto, las 9 fases del cronograma están hechas en código.

## Decisiones de Aldo

- Repositorio de código separado del repositorio del curso; público en la cuenta Aselori.
- Stack: FastAPI + React/Vite (Next.js sigue como opción; se fija en la fase 7).
- Enfoque en español con inglés también soportado; entrenamiento con características
  independientes del idioma (D7).
- No descargar `es_core_news_md`; se usa `es_core_news_sm` (su NER no se usa, D8).
- Los roles de la actividad 1.3 son nominales; no se asignan responsables por módulo.
- Aldo no entrega los reportes del curso; el equipo ya entregó al menos la fase 1.
- Fase 4 aprobada (2026-10-04): base de conocimiento de unas 80 habilidades y reportar la
  cobertura en lugar de perseguir una meta.
- Fase 5 aprobada (2026-10-05) con las 3 características relativas; sin ajustar métricas más
  allá de superar las líneas base.
- Fase 6 aprobada (2026-10-07), incluida la base SQLite en `data/app.db` y `httpx` en dev.
- Dashboard (fase 7): Aldo deja la elección a Claude; se usa React + Vite + TypeScript con
  pnpm (su gestor de paquetes por defecto), servido por FastAPI como un solo proceso.
- Fase 7 aprobada (2026-10-07): estructura y maqueta del dashboard, y crear
  `frontend/package.json`. pnpm 12.9.1 instalado globalmente con mise (en `~/dotfiles`).
- 2026-10-09: Aldo no tiene preferencias sobre el proyecto. Continuar las fases sin pedir
  aprobación entre ellas; detenerse solo en preguntas donde su opinión importe. Push y merge
  siguen esperando su autorización: se acumulan en ramas y se pide una sola vez.

## Ramas

- `main` (en GitHub): fases 1 a 9.

## Fase 8: hecho

- Sesgos (RNF-02): cambiar el nombre no cambia ningún puntaje; los puestos en femenino sí lo
  cambiaban (hasta 5 puntos). `preprocessing.GENDERED_FORMS` lleva 32 puestos a una sola
  forma, revisando la palabra escrita antes que su lema; diferencia restante: 0.1 puntos.
  `tests/test_fairness.py` cubre ambos casos.
- Reentrenamiento (RF-12): `models.retrain_with_feedback`, `POST /model/retrain` y botón en el
  detalle del modelo del dashboard. Peso 5 por decisión, mínimo 3 decisiones, se acepta si el
  F1 en inglés no baja más de 0.01; respaldo `model.previous.joblib` e historial
  `models/retraining.json` (fuera de Git). Tras aceptar, se re-evalúan todas las vacantes.
- `pipeline.process_text` (procesar texto ya extraído).
- Modelo base reentrenado: inglés igual (0.415); español 0.676 (antes 0.652).
- Docs: `docs/resultados.md` secciones 5 (sesgos), 6 (tiempos) y 7 (reentrenamiento); API en
  arquitectura.

## Fase 9: hecho

- `models/model.joblib` (2 KB) en Git: la demo corre después de clonar, sin datos.
- README reorganizado (qué hace, correr la demo en Linux/macOS/Windows, uso, entrenamiento,
  pruebas, documentación, estructura); requisito de Node.js leído del `engines` de Vite.
- `docs/demo.md`: guion del video del PIA con la vacante de analista de datos.

## Verificado

- 192 pruebas pasan, `ruff` limpio, `pnpm build` sin errores.
- Tiempos (RNF-03) con la API y 48 documentos: 0.05 s por CV, lote de 48 en 2.3 s.
- Playwright (versión 1.63; la 1.64 global no tiene navegador descargado): botón de
  reentrenar con 0 decisiones (mensaje de mínimo) y con 4 (modelo actualizado, 0.415 a 0.411).
- Clon limpio de `phase-9-final` siguiendo el README en Linux: instalación, modelos de spaCy,
  `pnpm build`, 191 pruebas pasan y 1 se omite (reentrenamiento sin datos); el servidor
  evalúa CVs con el modelo guardado.

## No verificado

- Instalación en Windows y en Python 3.12 o 3.13.
- CVs reales de formatos complejos; vacante y CVs en idiomas distintos (similitud casi 0).
- Etiquetas del conjunto propio: borrador sin revisar; el resultado en español es optimista.
- Lectores de pantalla.

## Pendiente de Aldo

- Decidir si Claude redacta el documento del PIA o los reportes de avance (los entrega otra
  persona del equipo).
- Opcional: `playwright install` para descargar el navegador de Playwright 1.64.
- En la laptop: `work pull` en `~/dotfiles` y `mise install` para tener pnpm.
- Invitar al equipo y pedirles revisar `data/samples/es/labels.csv`.

## Siguientes pasos

1. Según lo que decida Aldo: documento del PIA (portada con logos, índice, introducción,
   resumen, metodología, desarrollo, resultados, conclusiones, bibliografía APA) a partir de
   `docs/`, o nada más.
