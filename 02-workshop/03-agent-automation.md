# Workshop 03 — Agent Automation con Gmail

> Evolucion de la aplicación hacia un agente con flujo de decision y notificaciones reales por Gmail

---

## Objetivo

Modificar la aplicación de Streamlit para que el AI Agent ejecute un flujo
completo de análisis y decision ramificado en 4 acciones clave (resumir,
categorizar, proponer y notificar), integrando el envío real de
notificaciones por correo electrónico a través de Gmail de manera secuencial.

---

## Requisitos

- Es necesario haber ejecutado los anteriores prompts para seguir la evolución planteada para la aplicación
- Es necesario tener un archivo .env con las siguientes variables definidas:
  - AGENT_API_URL= Url base
  - AGENT_API_KEY= API key para llamar al modelo
  - AGENT_MODEL_NAME=glm-5.2
  - SMTP_SENDER_EMAIL= Correo desde el cual se enviaran las alertas
  - SMTP_APP_PASSWORD= Contraseña SMTP para el envio de correos
  - NOTIFICATION_RECEIVER_EMAIL= Correo del receptor de las alertas

## Cómo usar este prompt

1. Copia el bloque de código siguiente completo.
2. Pégalo como prompt de tu agente de codigo
3. Una vez el agente haga las modificaciones necesarias inicia la aplicación.
4. Revisa que al analizar un ticket el agente resuma, categorice, proponga una respuesta y envie una notificación real por Gmail.

---

## Prompt

```
Actúa como un desarrollador experto en Python, Streamlit, arquitecturas avanzadas de Agentes de IA y automatizaciones con Google Workspace. Hemos evolucionado el diseño de nuestra aplicación de rastreo de tickets (Ticket Tracker). Necesito que modifiques nuestra aplicación de Streamlit (`app.py`) para que el "AI Agent" ejecute un flujo completo de análisis y decisión ramificado en 4 acciones clave basadas en el contenido de un ticket, integrando además el envío real de notificaciones por correo electrónico a través de Gmail de manera secuencial.

Por favor, implementa los siguientes requerimientos técnicos y de interfaz:

### 1. Variables de Entorno (.env)
Asegúrate de cargar y soportar de forma segura las siguientes variables en el archivo `.env` usando `python-dotenv`:
- **Para el LLM (Compatible con OpenAI):**
  * `AGENT_API_URL`: La URL base del endpoint compatible.
  * `AGENT_API_KEY`: La clave de autenticación del modelo.
  * `AGENT_MODEL_NAME`: El nombre del modelo a utilizar.
- **Para las Notificaciones (Gmail SMTP):**
  * `SMTP_SENDER_EMAIL`: El correo de Gmail que enviará las notificaciones.
  * `SMTP_APP_PASSWORD`: La contraseña de aplicación de Google de 16 caracteres (sin espacios) para autenticarse de forma segura.
  * `NOTIFICATION_RECEIVER_EMAIL`: El correo del administrador o equipo de soporte que recibirá la alerta.

### 2. Capacidades del AI Agent y Lógica del Backend
Modifica la lógica del agente para que procese el ticket y genere una respuesta estructurada (idealmente usando JSON estricto mediante la API oficial de `openai`). El agente debe resolver las siguientes subtareas:
- 🧩 **Summarize (Resumir):** Generar un resumen ejecutivo del problema en un solo párrafo corto.
- 🏷️ **Categorize (Categorizar):** Determinar la categoría del ticket (ej. Técnico, Facturación, Bug, Solicitud de feature) y su nivel de prioridad (Alta, Media, Baja).
- 💡 **Propose (Proponer):** Generar una propuesta de respuesta detallada, clara y empática para el cliente.
- 📢 **Notify (Notificar vía Gmail Real):** Crea una función dedicada `send_gmail_notification(summary, category, priority, response)`. Inmediatamente después de que el LLM devuelva el análisis, esta función debe enviar un correo electrónico HTML profesional y bien espaciado utilizando `smtplib` con los siguientes datos:
  * **Asunto:** Dinámico, ej: `[Soporte AI] Nuevo Ticket - Prioridad {priority}: {category}`.
  * **Cuerpo:** Un diseño HTML limpio que estructure visualmente el Resumen, la Categoría/Prioridad y la Respuesta Propuesta por la IA.

### 3. Interfaz de Usuario en Streamlit (UI/UX Minimalista)
Quiero mantener una estética profesional, limpia y scannable inspirada en interfaces tipo Gemini o Vercel, cuidando la tipografía y los espacios:
- **Organización del Resultado:** Al presionar el botón "Analizar con AI Agent", no muestres un bloque denso de texto. Organiza el resultado usando componentes limpios como pestañas (`st.tabs(["Resumen y Categoría", "Respuesta Propuesta", "Envío de Alertas"])`) o columnas bien distribuidas.
- **Badges Visuales:** Muestra la categoría y prioridad calculadas utilizando formatos destacados y elegantes (por ejemplo, usando `st.pills` o cajas markdown con fondos sutiles).
- **Feedback del Correo:** En la sección de notificación, muestra un estado visual claro:
  * Mientras se envía, usa un mensaje de estado sutil (ej. "Enviando alerta por correo electrónico...").
  * Al completarse con éxito, muestra un componente `st.success("Notificación enviada con éxito a {correo_receptor}")` con la hora exacta.

### 4. Robustez y Manejo de Errores
- Envuelve la lectura del JSON del LLM en un bloque `try-except` para evitar fallos si el modelo devuelve un formato inesperado.
- Envuelve la conexión SMTP de Gmail en un bloque `try-except`. Si el envío falla (por ejemplo, por credenciales incorrectas), muestra un mensaje de error amigable (`st.error`) en la sección correspondiente sin tumbar ni bloquear el resto de la aplicación.

Por favor, muestra primero la estructura de datos en JSON que esperas del agente y el diseño de la función de envío de correo antes de proceder a modificar el archivo `app.py`.
```

---
