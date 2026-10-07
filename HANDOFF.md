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
- Fase 7 (dashboard): **terminada en `phase-7-dashboard`, pendiente de revisión**.

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

## Ramas

- `main` (en GitHub): fases 1 a 6.
- `phase-7-dashboard` (local, sin subir).

## Fase 7: hecho

- `frontend/` (React 19 + Vite 8 + TypeScript 7, pnpm 12.9.1, sin librerías de interfaz):
  lista de vacantes, formulario, encabezado con requisitos, carga de CVs con errores por
  archivo, filtros, ranking con barra de puntaje, excepciones (habilidades faltantes,
  experiencia o educación insuficientes), detalle, decisión del reclutador y línea del modelo.
  Tema claro y oscuro; en teléfono la lista se vuelve selector.
- `api.py` sirve `frontend/dist` si existe (un solo proceso; decisión D10).
- Docs: README (compilar y ejecutar, desarrollo, puerto ocupado), arquitectura (D10), AGENTS.

## Verificado

- `pnpm build` (incluye `tsc --noEmit`) sin errores; 189 pruebas de Python pasan.
- Playwright contra el servidor real (1366x860, 390x844, tema oscuro): estado vacío, creación
  de vacante, 8 CVs evaluados y un PDF dañado reportado, detalle, decisión que persiste al
  recargar, filtros, sin desbordamiento horizontal en teléfono, mensaje con la API caída,
  0 errores de consola.
- Proxy de `pnpm dev` hacia la API verificado (con la API en otro puerto, porque el 8000 de
  esta máquina estaba ocupado por otro proceso).

## No verificado

- Instalación en Windows y en Python 3.12 o 3.13.
- CVs reales de formatos complejos; vacante y CVs en idiomas distintos (similitud casi 0).
- Etiquetas del conjunto propio: borrador sin revisar; el resultado en español es optimista.
- Lectores de pantalla (solo se revisaron etiquetas, roles y foco en el código).

## Pendiente de Aldo

- Revisar la fase 7 y autorizar push y merge de `phase-7-dashboard`.
- En la laptop: `work pull` en `~/dotfiles` y `mise install` para tener pnpm.
- Invitar al equipo y pedirles revisar `data/samples/es/labels.csv`.

## Siguientes pasos

1. Fase 8 (cronograma: 2 al 6 de noviembre): integración y pruebas del flujo completo,
   reentrenamiento con la retroalimentación (RF-12), revisión de sesgos (RNF-02: cambiar el
   nombre no cambia el puntaje) y tiempos (RNF-03). Planearla y pedir aprobación.
