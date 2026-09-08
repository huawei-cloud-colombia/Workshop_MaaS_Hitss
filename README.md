# 🚀 Workshop: Building Agentic Applications with MaaS

Bienvenido al Workshop de **Inteligencia Artificial, AI Coding Agents y Model as a Service (MaaS)**.

Durante este workshop utilizaremos MaaS como proveedor de modelos de IA y herramientas de desarrollo asistidas por agentes, como **GitHub Copilot** u **OpenCode**, para construir y evolucionar progresivamente una aplicación real.

El objetivo será desarrollar una aplicación de gestión de tickets y transformarla paso a paso en un sistema basado en **AI Agents, Tool Calling, MCP y Multi-Agent Systems**.

---

# 🎯 Objetivo del Workshop

Explorar cómo los modelos de IA disponibles a través de MaaS pueden utilizarse junto con AI Coding Agents para acelerar el desarrollo de software y construir aplicaciones cada vez más avanzadas.

Durante el workshop evolucionaremos una misma aplicación a través de diferentes etapas:

```text
Aplicación
    ↓
AI Agent
    ↓
AI Agent + Automatización
    ↓
AI Agent + MCP
    ↓
Multi-Agent System
```

---

# 🗺️ Workshop Flow

## 1️⃣ Connect MaaS

Configuraremos el acceso a MaaS y conectaremos el modelo con la herramienta de desarrollo que utilizaremos durante el workshop.

En esta etapa configuraremos:

* Endpoint (Base URL).
* API Key.
* Modelo(s).
* Verificación de la conexión.

👉 [Comenzar configuración](./01-Setup/README.md)

---

## 🧪 2️⃣ Build an Agentic Application

Durante el workshop construiremos y evolucionaremos una aplicación de gestión de tickets.

Cada etapa parte del resultado de la etapa anterior.

---

### 🏗️ Step 1 — Build the Ticket Tracker

Comenzaremos construyendo una aplicación completa de gestión de tickets utilizando Streamlit.

🎯 **Objetivo:** Explorar cómo un AI Coding Agent puede generar una aplicación funcional a partir de requisitos detallados.

👉 [Ir al Step 1](./02-workshop/01-ticket-tracker.md)

---

### 🤖 Step 2 — Add an AI Agent

Evolucionaremos la aplicación existente integrando un AI Agent conectado a un modelo disponible a través de MaaS.

🎯 **Objetivo:** Integrar un LLM real dentro de una aplicación existente.

👉 [Ir al Step 2](./02-workshop/02-ai-agent.md)

---

### ⚡ Step 3 — AI Agent + Automation

Ampliaremos las capacidades del agente para que pueda ejecutar un flujo completo de análisis y automatización.

🎯 **Objetivo:** Explorar cómo un AI Agent puede formar parte de un workflow que combina IA y automatizaciones.

👉 [Ir al Step 3](./02-workshop/03-agent-automation.md)

---

### 🔧 Step 4 — AI Agent + MCP

Transformaremos el flujo interno del agente para utilizar herramientas externas mediante un entorno compatible con MCP.

🎯 **Objetivo:** Entender cómo los agentes utilizan Tools y Context para interactuar con sistemas externos.

👉 [Ir al Step 4](./02-workshop/04-mcp.md)

---

### 🤝 Step 5 — Multi-Agent System

Finalmente, evolucionaremos el agente único hacia un sistema compuesto por dos agentes especializados.

#### 🤖 AI Agent for Analyze

Responsable de:

* Analizar el ticket.
* Resumir.
* Categorizar.
* Consultar documentación.

#### ⚙️ AI Agent for Action

Responsable de:

* Generar una propuesta de solución.
* Ejecutar acciones.
* Enviar notificaciones.

🎯 **Objetivo:** Explorar cómo múltiples agentes especializados pueden colaborar para resolver una tarea.

👉 [Ir al Step 5](./02-workshop/05-multi-agent.md)

---

# 🧭 Arquitectura de Evolución

```text
┌──────────────────────────────┐
│      Ticket Tracker          │
│      Streamlit + SQLite      │
└───────────────┬──────────────┘
                │
                ▼
┌──────────────────────────────┐
│          AI Agent            │
│         + MaaS LLM           │
└───────────────┬──────────────┘
                │
                ▼
┌──────────────────────────────┐
│   AI Agent + Automation      │
│      + Gmail / SMTP          │
└───────────────┬──────────────┘
                │
                ▼
┌──────────────────────────────┐
│        AI Agent + MCP        │
│   Tools + Documentation      │
└───────────────┬──────────────┘
                │
                ▼
┌──────────────────────────────┐
│      Multi-Agent System      │
│     Analyze + Action         │
└──────────────────────────────┘
```

---

# 💡 Cómo utilizar este repositorio

Sigue las etapas en orden.

Cada etapa:

1. Parte del código generado anteriormente.
2. Introduce un nuevo concepto.
3. Utiliza un prompt para evolucionar la aplicación.
4. Permite observar cómo el AI Coding Agent modifica el proyecto.
5. Añade nuevas capacidades al sistema.

```text
01-connect
     │
     ▼
02-workshop
     │
     ├── Step 1: Ticket Tracker
     │
     ├── Step 2: AI Agent
     │
     ├── Step 3: Automation
     │
     ├── Step 4: MCP
     │
     └── Step 5: Multi-Agent
```
