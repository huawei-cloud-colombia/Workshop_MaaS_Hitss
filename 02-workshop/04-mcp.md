# Workshop 04 — Integración con MCP (Model Context Protocol)

> Evolucion de la aplicación hacia un agente basado en MCP y Tool Calling

---

## Objetivo

Transformar el AI Agent para que deje de ejecutar tareas de manera
interna y secuencial y pase a interactuar con un entorno MCP mediante
Tool Calling, consumiendo herramientas externas para categorizar, proponer
soluciones, notificar y resumir, además de consultar una base de conocimiento
de directrices corporativas.

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
2 - Lee el archivo llamado 03-mcp.md y ejecuta el prompt que se encuentra en el archivo dentro de la seccion "Prompt"
```
3. Una vez el agente haga las modificaciones necesarias inicia la aplicación.
4. Revisa que en el GUI se muestre el log de ejecución con las herramientas MCP que el agente invoca al analizar un ticket.

---

## Prompt

```
Actúa como un desarrollador senior experto en Python, Streamlit y arquitecturas de agentes basadas en MCP (Model Context Protocol). El AI Agent ya no ejecutará las tareas de manera interna y secuencial, sino que interactuará con un entorno MCP. El agente debe usar "Tools" (herramientas) provistas por el protocolo para Categorizar, Proponer Soluciones, Notificar y Resumir, además de consumir una nueva herramienta de contexto basada en documentación estática ("Ticket handling guidelines"). Por favor, implementa los siguientes cambios en el proyecto:

### 1. Simulación/Conexión del Servidor MCP (Backend)
- Modifica el backend para que el AI Agent use la capacidad de "Tool Calling" (Llamada a funciones/herramientas) compatible con OpenAI / MCP.
- Define las herramientas (tools) del lado del cliente que simulen o se conecten al servidor MCP:
  * `summarize_ticket`: Devuelve el resumen ejecutivo.
  * `categorize_ticket`: Devuelve la categoría y prioridad.
  * `propose_solution`: Genera la respuesta utilizando como contexto los lineamientos de la documentación.
  * `notify_via_gmail`: Ejecuta el envío real de correo que configuramos previamente por SMTP.
- **Nueva Herramienta de Contexto (Documentation):** Implementa una función `get_ticket_handling_guidelines()`. Esta simulará una base de conocimiento leyendo un archivo local (por ejemplo, `guidelines.md` o un diccionario interno de políticas de soporte). El agente DEBE consultar obligatoriamente esta documentación antes de armar la propuesta de solución para asegurarse de cumplir con las políticas de la empresa.

### 2. Flujo del Agente con Tool Calling
- Modifica la llamada al LLM utilizando el parámetro `tools` de la API de OpenAI. El System Prompt ahora debe indicarle al modelo: "Eres un agente despachador que utiliza el protocolo MCP. Analiza el ticket y decide qué herramientas llamar. Debes consultar las directrices de documentación (guidelines) antes de proponer una respuesta al usuario y debes notificar al finalizar".
- Implementa el bucle de ejecución que procesa las llamadas a las herramientas sugeridas por el LLM y le devuelve los resultados al modelo para que genere su respuesta final.

### 3. Actualización de la Interfaz de Usuario en Streamlit
- Mantén la UI limpia y minimalista, pero agrega un componente visual tipo "Log de Ejecución" o "Pasos del Agente".
- Utiliza `st.status()` o un contenedor dinámico para mostrar en tiempo real qué herramientas del MCP está invocando el agente (ej. "🔍 Consultando directrices de documentación...", "🏷️ Clasificando ticket...", "📧 Enviando notificación..."). Esto hará transparente el proceso para el operador de soporte.

### 4. Archivo de Documentación Base
- Crea un archivo de texto o markdown simple llamado `guidelines.md` en la raíz del proyecto con un par de reglas corporativas ficticias (ej. "Garantizar reembolsos si la falla es de nuestro servidor", "Usar un tono formal para clientes corporativos") para que el agente tenga datos reales que recuperar.

Por favor, detalla cómo estructurarás la definición de las herramientas (tools) para la API y cómo manejarás el flujo de respuestas del LLM antes de reescribir el archivo `app.py`.
```

---

