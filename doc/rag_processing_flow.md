# Diagrama del diseño del procesamiento de datos (RAG)

```mermaid
flowchart TD
    A["resources por dominio"] --> B["identify_services_and_files"]
    B --> C["Mapa servicio -> lista archivos"]

    C --> D["Carga de archivos por tipo"]

    D --> D1["PDF → PyPDFLoader"]
    D --> D2["TXT → TextLoader"]
    D --> D3["DOCX → Docx2txtLoader"]
    D --> D4["CSV → CSVLoader"]
    D --> D5["XLSX → pandas.read_excel"]

    D1 --> E["Documentos cargados"]
    D2 --> E
    D3 --> E
    D4 --> E
    D5 --> E

    E --> F["clean_text (por servicio)"]

    F --> F1["Concatenación de contenido"]
    F --> F2["Normalización a minúsculas"]
    F --> F3["Filtro de ruido (is_noise)"]
    F --> F4["Conserva metadata source"]

    F4 --> G["create_chunks"]

    G --> G1["Chunks de 250 palabras"]
    G --> G2["Overlap de 50"]

    G2 --> H["Embeddings (all-mpnet-base-v2)"]

    H --> I["FAISS por servicio"]

    I --> J{"¿Índice local existe?"}

    J -- "Sí" --> K["load_local"]
    J -- "No" --> L["from_documents + save_local"]

    K --> M["Vector DB lista"]
    L --> M
```
