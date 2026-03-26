# Proyecto RAG Banco - Guía Técnica

Sistema RAG (Retrieval-Augmented Generation) con orquestación por herramientas para responder preguntas de usuarios sobre tres dominios de conocimiento:

- `BRE-B`
- `Sedes y reseñas`
- `Productos bancarios`

La entrada de preguntas del usuario se realiza desde una **interfaz gráfica (GUI)**, la cual consume el backend de este proyecto por HTTP.

---

## 1) Arquitectura general

El backend está construido con FastAPI y se divide en estos módulos:

- `src/main.py`: inicialización del servicio, carga de recursos y endpoint de preguntas.
- `src/preproccesing/preprocess_file.py`: descubrimiento y limpieza de documentos fuente.
- `src/data_vector/base_vectorice.py`: chunking, embeddings y base vectorial FAISS.
- `src/tools/retrieve.py`: creación de herramientas de recuperación por dominio.
- `src/agentes/model.py`: creación del LLM y orquestación iterativa de llamadas a herramientas.

### Componentes principales

1. **GUI cliente**
   - Recoge la pregunta del usuario.
   - Envía `POST /` al backend con JSON: `{ "question": "..." }`.

2. **API FastAPI**
   - Arranca con `lifespan` para preparar el pipeline RAG.
   - Expone el endpoint principal de preguntas.

3. **Orquestador (agente)**
   - Usa un prompt de decisión para elegir herramienta por dominio.
   - Ejecuta recuperación iterativa (hasta 5 pasos).
   - Construye respuesta final en español.

4. **Capa RAG**
   - Preprocesa archivos heterogéneos (`pdf`, `txt`, `docx`, `csv`, `xlsx`).
   - Genera chunks.
   - Calcula embeddings (`all-mpnet-base-v2`).
   - Almacena/carga índices FAISS por servicio.

---

## 2) Flujo end-to-end (con GUI)

1. El usuario escribe una pregunta en la GUI.
2. La GUI realiza `POST /` al backend.
3. FastAPI recibe la pregunta y llama a `created_agente(...)`.
4. El agente analiza intención y decide una herramienta:
   - `breb_tool`
   - `sedes_review_tool`
   - `productos_tool`
5. La herramienta ejecuta búsqueda semántica `similarity_search(k=3)` en FAISS del dominio.
6. El resultado recuperado se inserta como nuevo contexto en el prompt.
7. El agente decide si:
   - necesita otra herramienta, o
   - responde de forma final.
8. El backend devuelve `{ "answer": "..." }`.
9. La GUI presenta la respuesta al usuario.

---

## 3) Orquestador técnico

Implementación principal en `src/agentes/model.py`.

### Lógica de decisión

- El prompt fija dominios y herramienta asociada.
- Se espera respuesta en JSON para llamadas de tool:
  - `{ "tool": "...", "tool_input": { "question": "..." } }`
- Si la salida no es JSON válido, se asume respuesta final.

### Ciclo iterativo

- Máximo `5` iteraciones (`while max_step <= 5`).
- En cada paso:
  1. invoca LLM,
  2. parsea JSON,
  3. ejecuta herramienta elegida,
  4. añade `Tool result` al prompt,
  5. vuelve a iterar.
- Si se alcanza el máximo sin cierre, retorna `"Max steps reached"`.

### Herramientas disponibles

- `breb_tool`: información BRE-B.
- `sedes_review_tool`: reseñas y sedes.
- `productos_tool`: portafolio y características de productos.

Cada herramienta devuelve texto con:

- metadatos de origen
- contenido de chunks relevantes

---

## 4) Procesamiento RAG técnico

Implementación distribuida en:

- `src/preproccesing/preprocess_file.py`
- `src/data_vector/base_vectorice.py`
- `src/tools/retrieve.py`

### 4.1 Descubrimiento de archivos

`identify_services_and_files(path_resources)` recorre recursivamente `resources/` y agrupa archivos por nombre de carpeta padre (servicio).

Resultado esperado (ejemplo):

- `bre-b` -> lista de rutas de documentos del dominio
- `sedes_review` -> lista de rutas de reseñas
- `productos` -> lista de rutas de productos

### 4.2 Carga por tipo

`save_info_services_files_text_formats(...)` selecciona loader según extensión:

- `.pdf` -> `PyPDFLoader`
- `.txt` -> `TextLoader`
- `.docx` -> `Docx2txtLoader`
- `.csv` -> `CSVLoader`
- `.xlsx` -> lectura con `pandas.read_excel()` y conversión a texto

### 4.3 Limpieza

`clean_text(...)`:

- concatena contenido por servicio
- normaliza a minúsculas
- remueve ruido simple detectado por `is_noise(...)`
- conserva metadato `source`

### 4.4 Chunking

`create_shunks(data)`:

- tamaño de chunk: `250` palabras
- overlap: `50`
- paso: `200`

Cada chunk se guarda como `Document` con metadata:

- `service`
- `source`

### 4.5 Embeddings + FAISS

`db_build_vectorial(...)`:

- embeddings: `sentence-transformers/all-mpnet-base-v2`
- por cada servicio:
  - si existe índice local en `data_vectors/<service>`, lo carga
  - si no existe, lo crea y lo persiste

### 4.6 Recuperación

`create_retriever_tool(...)` crea una función tool que ejecuta:

- `similarity_search(query, k=3)`

Y devuelve un string consolidado con fuente y contenido de los chunks recuperados.

---

## 5) Ciclo de vida del backend

En `src/main.py`, `lifespan` hace al iniciar:

1. preprocesamiento de recursos
2. creación/carga de DB vectorial
3. inicialización de LLM (`Qwen/Qwen2.5-7B-Instruct`)
4. creación de tools de recuperación

Luego expone endpoint:

- `POST /`
  - request: `{ "question": "..." }`
  - response: `{ "answer": "..." }`

---

## 6) Estructura de carpetas

```text
src/
  agentes/
    model.py
  preproccesing/
    preprocess_file.py
  data_vector/
    base_vectorice.py
  tools/
    retrieve.py
  main.py
resources/
  bre-b/
  productos/
  sedes/
  sedes_review/
data_vectors/
  <servicio>/index.faiss
  <servicio>/index.pkl
doc/
  orchestrator_flow.md
  rag_processing_flow.md
```

---

## 7) Variables de entorno

Requeridas:

- `HUGGINGFACEHUB_API_TOKEN`

Recomendado usar archivo `.env` en raíz del proyecto.

---

## 8) Ejecución local

### 8.1 Instalar dependencias

```bash
pip install -r requirements.txt
```

### 8.2 Arrancar API

```bash
uvicorn src.main:app --reload
```

### 8.3 Probar endpoint

```bash
curl -X POST http://127.0.0.1:8000/ -H "Content-Type: application/json" -d '{"question":"¿Qué es Bre-B?"}'
```

---

## 9) Integración con GUI

Para esta solución, la GUI actúa como cliente HTTP del backend:

- Entrada en GUI: texto de pregunta.
- Salida en GUI: texto de respuesta.
- Contrato API:
  - Request: `{ "question": "string" }`
  - Response: `{ "answer": "string" }`

Buenas prácticas para la GUI:

- Mostrar estado de carga mientras el backend procesa.
- Mostrar errores de red/API de forma amigable.
- Limpiar/normalizar la pregunta antes de enviarla.

---

## 10) Consideraciones técnicas y límites actuales

- El orquestador es iterativo, pero depende de que el LLM respete formato JSON cuando decide usar tools.
- El retrieval está fijado a `k=3`, sin reranking adicional.
- La limpieza de texto es básica y puede ampliarse para mejorar precisión.
- El pipeline genera o reutiliza índices locales FAISS para reducir costo en reinicios.

---

## 11) Diagramas

- Diagrama de flujo de información del orquestador: `doc/orchestrator_flow.md`
- Diagrama de procesamiento de datos RAG: `doc/rag_processing_flow.md`
