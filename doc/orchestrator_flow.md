# Diagrama del diseño del flujo de información (Orquestador)

```mermaid
flowchart TD
    A["Usuario en GUI"] --> B["GUI envía POST / question"]
    B --> C["FastAPI src/main.py"]
    C --> D["created_agente(llm, tools, question)"]

    D --> E[["LOOP INTERNO (max 5 iteraciones)"]]

    E --> F["LLM genera respuesta (JSON o texto)"]

    F --> G{"¿JSON válido con tool?"}

    G -- "No" --> H["Respuesta final en texto"]
    H --> I["API retorna answer"]
    I --> J["GUI muestra respuesta"]

    G -- "Sí" --> K["Parse JSON"]

    K --> L{"tool == ?"}
    L --> L1["breb_tool"]
    L --> L2["sedes_review_tool"]
    L --> L3["productos_tool"]

    L1 --> M["FAISS similarity_search k=3"]
    L2 --> M
    L3 --> M

    M --> N["Tool result + metadata"]

    N --> O["Agregar resultado al prompt"]

    O --> E

    E --> P{"¿max_steps alcanzado?"}
    P -- "Sí" --> Q["Max steps reached"]
    Q --> I

    
    classDef gui fill:#E3F2FD,stroke:#1E88E5,color:#0D47A1;
    classDef api fill:#BBDEFB,stroke:#1565C0,color:#0D47A1;
    classDef agent fill:#EDE7F6,stroke:#5E35B1,color:#311B92;
    classDef rag fill:#E8F5E9,stroke:#43A047,color:#1B5E20;
    classDef tools fill:#FFF3E0,stroke:#FB8C00,color:#E65100;
    classDef decision fill:#ECEFF1,stroke:#607D8B,color:#263238;

   
    class A,B,J gui;
    class C,I api;
    class D,E,F,K,O agent;
    class M,N rag;
    class L1,L2,L3 tools;
    class G,L,P decision;
```
