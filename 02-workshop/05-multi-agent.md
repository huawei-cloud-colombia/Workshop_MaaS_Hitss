# Workshop 05 — Orquestación Multi-Agente

> Evolucion de la aplicación hacia Multi-Agente

---

## Objetivo

Demostrar cómo dividir una tarea compleja (atender un ticket de soporte
corporativo) entre agentes con responsabilidades especificas.

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

1. Copie y pegue el siguiente mensaje en su agente de codigo 
```
Sigue estas instrucciones:
1 - Accede al siguiente repositorio de GitHub a traves de su URL: https://github.com/huawei-cloud-colombia/Workshop_MaaS_Hitss/tree/main/02-workshop
2 - Lee el archivo llamado 05-multi-agent.md y ejecuta el prompt que se encuentra en el archivo dentro de la seccion "Prompt"
```
3. Una vez el agente haga las modificaciones necesarias inicia la aplicación.
4. Revisa que en el GUI se muestre la división de las tareas entre ambos agentes cuando se analiza un ticket.

---

## Prompt

```
Actúa como un arquitecto de software senior experto en sistemas Multi-Agente, Python, Streamlit y el protocolo MCP.

Hemos llegado a la fase final de nuestra aplicación. Necesito refactorizar por completo la lógica del backend de `app.py` para transformar nuestro agente único en un sistema de dos agentes especializados que colaboran de manera secuencial, interactuando cada uno con su respectivo toolkit de MCP.

Por favor, implementa la siguiente arquitectura de software:

### 1. Separación de Toolkits MCP (Estructura de Herramientas)
Divide las herramientas (tools) de la API de OpenAI/MCP en dos grupos independientes y bien definidos:
- **MCP - Analyze (Analysis toolkit and docs):** Contiene las funciones de `summarize_ticket`, `categorize_ticket` y `get_ticket_handling_guidelines`.
- **MCP - Action (Action toolkit):** Contiene las funciones de `propose_solution` (que consume el análisis previo) y `notify_via_gmail` (nuestro módulo SMTP).

### 2. Definición y Orquestación de los Dos Agentes (Backend)
Implementa el flujo de colaboración entre los dos agentes de la siguiente manera:

- **Paso 1: AI Agent for Analyze**
  * **Rol / System Prompt:** "Eres un Agente Analista experto en Clasificación de Soporte. Tu único objetivo es entender e interpretar el ticket entrante".
  * **Flujo:** Recibe el ticket, tiene acceso exclusivo al toolkit `MCP - Analyze`. Invoca las herramientas para resumir, categorizar y leer la documentación. Retorna un objeto estructurado (JSON) con el diagnóstico del ticket.

- **Paso 2: Comunicación entre Agentes**
  * Pasa el resultado del *Agent for Analyze* como contexto de entrada directo al *Agent for Action*.

- **Paso 3: AI Agent for Action**
  * **Rol / System Prompt:** "Eres un Agente Ejecutor de Soporte. Tu objetivo es tomar el análisis estructurado de un ticket y proceder con la resolución y comunicación".
  * **Flujo:** Recibe el JSON del Analista, tiene acceso exclusivo al toolkit `MCP - Action`. Invoca la herramienta para generar la propuesta de solución corporativa final y gatilla automáticamente la notificación real por Gmail.

### 3. Interfaz de Usuario Multi-Agente en Streamlit (UI/UX)
Para reflejar visualmente esta colaboración avanzada manteniendo una estética ultra-limpia (tipo Vercel/Gemini), diseña la sección de procesamiento de la siguiente forma:
- Al presionar el botón de ejecución, muestra un flujo secuencial usando estados de carga independientes:
  1. `st.status("🤖 AI Agent for Analyze trabajando...")` -> Muestra cuándo consulta las guías, resume y categoriza. Al finalizar, renderiza el resumen y las etiquetas/pills de categoría de forma elegante.
  2. `st.status("⚙️ AI Agent for Action ejecutando...")` -> Muestra el progreso de la generación de la respuesta y el envío del correo electrónico.
- Al final del flujo, muestra en contenedores destacados la **Propuesta de Solución** final lista para el operador y un badge verde de **"Notificación Enviada por Correo"**.

### 4. Manejo de Errores y Trazabilidad
- Asegúrate de capturar cualquier fallo en la cadena de comunicación (por ejemplo, si el Agente 1 falla, el Agente 2 no debe ejecutarse con datos vacíos).
- Sigue utilizando de forma segura las variables del archivo `.env` para las conexiones de las APIs y SMTP.

Por favor, detalla primero la arquitectura de las funciones de ambos agentes y cómo estructurarás el paso de información (payload) entre ellos antes de modificar el código de la aplicación de Streamlit.

```

---


