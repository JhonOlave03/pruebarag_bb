Se desarrolla el proyecto con una mezcla de código híbrido entre:
1. uso de frameworks, 
2. librerías 
3. implementación de código propio.

Objetivo:
 - demostrar capacidades de implementación y manejo tecnicos de herramientas como frameworks.

Razones para desarrollar ciertos bloques con lógica propia vs funcionalidades con frameworks:
- Capacidades de procesamiento del equipo de computo: Algunos frameworks ya vienen optimizados para desarrollar tareas especificas que pueden ser pesadas al procesar paso a paso; lo que significa, mayor rápidez y eficiencia en su cumplimiento.
- Las tareas que no requieren de mucha capacidad de computo y necesitan del manejo de una lógica de desarrollo son abordadas con implementaciones manuales.

Sobre la lectura, limpieza de los archivos y creación de Chunks:

1. Se elige implementar la lógica de estas tareas con código propio por su bajo nivel de dificulta.
2. Se transforman los documentos binarios a formato utf-8 para aplicar ciertos métodos de limpieza (como normalización del texto a minusculas) y también debido a la facilidad de trabajo con este método. 