# Workshop 02 — AI Agent

> Evolución de la aplicación para integrar un AI Agent interno que analice tickets y genere respuestas automatizadas mediante un LLM compatible con OpenAI

---

## Objetivo

Evolucionar la aplicación de rastreo de tickets (Ticket Tracker) en Streamlit
para integrar un "AI Agent" interno que, al visualizar o seleccionar un ticket
específico, analice automáticamente su contenido (título, descripción, categoría,
etc.) y genere una propuesta de respuesta automatizada para el usuario mediante
una API compatible con OpenAI, manteniendo la estética minimalista y el manejo
robusto de errores.

---

## Requisitos

- Es necesario haber ejecutado el prompt 1 (Workshop 01 — Ticket Tracker) para contar con la aplicación base en `app.py`
- Es necesario tener un archivo .env con las siguientes variables definidas:
  - AGENT_API_URL= Url base del endpoint compatible con OpenAI
  - AGENT_API_KEY= API key para autenticarse con el modelo
  - AGENT_MODEL_NAME= Nombre del modelo a utilizar

## Cómo usar este prompt

1. Copia el bloque de código siguiente completo.
2. Pégalo como prompt de tu agente de codigo
3. Una vez el agente haga las modificaciones necesarias, verifica que el archivo `.env` esté configurado correctamente.
4. Inicia la aplicación, selecciona un ticket en el Panel de Administración y presiona el botón de análisis del AI Agent para generar la respuesta automatizada.

---

## Prompt

```
Actúa como un desarrollador experto en Python, Streamlit y arquitecturas de agentes de IA. 

Necesito evolucionar nuestra aplicación actual de rastreo de tickets (Ticket Tracker) en Streamlit para integrar un "AI Agent" interno, siguiendo exactamente el flujo adjunto. El objetivo es que, al visualizar o seleccionar un ticket específico, el agente analice automáticamente su contenido (título, descripción, categoría, etc.) y genere una propuesta de respuesta automatizada para el usuario.

Por favor, implementa los siguientes requerimientos técnicos y de interfaz:

### 1. Configuración de Variables de Entorno (.env)
El agente debe interactuar con un LLM a través de una API compatible con OpenAI. Asume que ya existen las siguientes variables en un archivo `.env` y usa `python-dotenv` para cargarlas de forma segura:
- `AGENT_API_URL`: La URL base del endpoint compatible con OpenAI.
- `AGENT_API_KEY`: La clave de autenticación.
- `AGENT_MODEL_NAME`: El nombre del modelo a utilizar (por defecto usa uno genérico o el que esté configurado).

### 2. Lógica del AI Agent (Backend)
- Crea una función dedicada (o una clase simple si es más limpio) para el agente, por ejemplo: `generate_ticket_response(ticket_data)`.
- Utiliza la librería oficial de `openai` (configurando `base_url=os.getenv("AGENT_API_URL")` y `api_key=os.getenv("AGENT_API_KEY")`) para realizar la llamada al modelo.
- Diseña un prompt del sistema (System Prompt) robusto para el agente. El agente debe actuar como un "Especialista de Soporte Técnico Senior", analizar el tono del ticket, identificar el problema central y estructurar una respuesta clara, empática y accionable.

### 3. Interfaz de Usuario en Streamlit (Frontend)
Quiero mantener una estética minimalista, profesional y limpia (inspirada en interfaces tipo Gemini/Vercel) con excelente manejo de espacios y tipografía:
- **Disparador del Agente:** Agrega un botón visualmente sutil o una sección colapsable (`st.expander`) dentro del detalle de cada ticket llamada "🤖 AI Agent Analysis" o "Generar Respuesta con IA".
- **Estado de Carga:** Muestra un spinner limpio (`st.spinner("El agente está analizando el ticket...")`) mientras el LLM procesa la respuesta.
- **Visualización del Resultado:** Muestra la respuesta sugerida por el agente dentro de un contenedor destacado (por ejemplo, usando `st.chat_message("assistant")` o un bloque de markdown bien espaciado) para que el operador pueda copiarla o editarla fácilmente.

### 4. Manejo de Errores y Edge Cases
- Si las variables de entorno no están configuradas, muestra un mensaje de advertencia amigable (`st.warning`) indicando que falta configurar el archivo `.env`.
- Envuelve la llamada de la API en un bloque `try-except` para capturar errores de conexión y evitar que la app de Streamlit se rompa.

Por favor, muéstrame primero qué cambios o refactorizaciones planeas hacer en el `app.py` actual antes de escribir el código final, asegurándote de no romper la persistencia de datos actual de los tickets.
```

---
