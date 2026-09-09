"""
Workshop 04 — Integración con MCP (Model Context Protocol)
==========================================================
Aplicación web para la gestión de tickets de soporte técnico.
Flujo: Problema -> Aplicación con IA -> Solución Parcial

Evolución: El AI Agent ahora usa Tool Calling (MCP) para interactuar
con herramientas externas: summarize_ticket, categorize_ticket,
propose_solution, notify_via_gmail y get_ticket_handling_guidelines.

Tecnologías: Python + Streamlit + SQLite + OpenAI API (Tool Calling) + Gmail SMTP
Estética: Ultra-minimalista inspirada en Gemini/Vercel (modo oscuro)
"""

import json
import os
import smtplib
import sqlite3
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# ---------------------------------------------------------------------------
# Carga de variables de entorno (.env)
# ---------------------------------------------------------------------------
load_dotenv()

# Variables para el LLM (Compatible con OpenAI)
AGENT_API_URL = os.getenv("AGENT_API_URL", "")
AGENT_API_KEY = os.getenv("AGENT_API_KEY", "")
AGENT_MODEL_NAME = os.getenv("AGENT_MODEL_NAME", "")

# Variables para las Notificaciones (Gmail SMTP)
SMTP_SENDER_EMAIL = os.getenv("SMTP_SENDER_EMAIL", "")
SMTP_APP_PASSWORD = os.getenv("SMTP_APP_PASSWORD", "")
NOTIFICATION_RECEIVER_EMAIL = os.getenv("NOTIFICATION_RECEIVER_EMAIL", "")

# ---------------------------------------------------------------------------
# Configuración de la página (debe ser el primer comando de Streamlit)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Ticket Tracker",
    page_icon="🎫",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Estilos CSS personalizados — Modo oscuro minimalista (Gemini/Vercel)
# ---------------------------------------------------------------------------
CUSTOM_CSS = """
<style>
    /* Importar tipografía sans-serif limpia */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Variables de color */
    :root {
        --bg-deep: #0a0a0a;
        --bg-card: #141414;
        --bg-input: #1a1a1a;
        --border-subtle: #262626;
        --border-hover: #333333;
        --text-primary: #fafafa;
        --text-secondary: #a3a3a3;
        --text-muted: #737373;
        --accent: #3b82f6;
        --accent-hover: #2563eb;
        --success: #22c55e;
        --warning: #f59e0b;
        --danger: #ef4444;
        --radius: 8px;
    }

    /* Reset general */
    .stApp {
        background-color: var(--bg-deep);
        color: var(--text-primary);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: var(--bg-deep);
        border-right: 1px solid var(--border-subtle);
    }

    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2 {
        color: var(--text-primary);
        font-weight: 600;
        letter-spacing: -0.02em;
    }

    /* Títulos principales */
    h1, h2, h3 {
        color: var(--text-primary) !important;
        font-weight: 600 !important;
        letter-spacing: -0.02em;
    }

    /* Texto secundario */
    .stMarkdown p, .stText {
        color: var(--text-secondary);
    }

    /* Contenedores / Cards */
    .stContainer {
        background-color: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius);
        padding: 1.25rem;
    }

    /* Inputs */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > div {
        background-color: var(--bg-input) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: var(--radius) !important;
        color: var(--text-primary) !important;
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 1px var(--accent) !important;
    }

    /* Botones */
    .stButton > button {
        background-color: var(--accent);
        color: #ffffff;
        border: none;
        border-radius: var(--radius);
        font-weight: 500;
        padding: 0.5rem 1.25rem;
        transition: background-color 0.2s ease;
    }

    .stButton > button:hover {
        background-color: var(--accent-hover);
    }

    /* Botón secundario */
    .stButton > button[kind="secondary"] {
        background-color: var(--bg-input);
        color: var(--text-primary);
        border: 1px solid var(--border-subtle);
    }

    .stButton > button[kind="secondary"]:hover {
        background-color: var(--bg-card);
        border-color: var(--border-hover);
    }

    /* Métricas */
    .stMetric {
        background-color: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius);
        padding: 1rem;
    }

    .stMetric label {
        color: var(--text-muted) !important;
        font-size: 0.8rem !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .stMetric value {
        color: var(--text-primary) !important;
        font-weight: 600 !important;
    }

    /* Selectbox */
    .stSelectbox label {
        color: var(--text-secondary) !important;
    }

    /* Radio */
    .stRadio label {
        color: var(--text-secondary) !important;
    }

    /* Expander */
    .stExpander {
        background-color: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius);
    }

    /* Alertas / Notificaciones */
    .stAlert {
        border-radius: var(--radius);
    }

    /* Divider */
    .stDivider {
        border-color: var(--border-subtle) !important;
    }

    /* Tabla de datos */
    .stDataFrame {
        border-radius: var(--radius);
    }

    /* Ocultar elementos innecesarios */
    #MainMenu, footer {
        visibility: hidden;
    }

    /* Card personalizada para tickets */
    .ticket-card {
        background-color: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius);
        padding: 1.25rem;
        margin-bottom: 1rem;
    }

    .ticket-card:hover {
        border-color: var(--border-hover);
    }

    /* Badges de estado */
    .badge-abierto {
        background-color: rgba(239, 68, 68, 0.15);
        color: var(--danger);
        padding: 0.25rem 0.6rem;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 500;
    }

    .badge-progreso {
        background-color: rgba(245, 158, 11, 0.15);
        color: var(--warning);
        padding: 0.25rem 0.6rem;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 500;
    }

    .badge-resuelto {
        background-color: rgba(34, 197, 94, 0.15);
        color: var(--success);
        padding: 0.25rem 0.6rem;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 500;
    }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Base de datos SQLite — Inicialización y operaciones
# ---------------------------------------------------------------------------
DB_PATH = Path(__file__).parent / "tickets.db"


def init_db() -> None:
    """Crea la base de datos y la tabla de tickets si no existen."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            categoria TEXT NOT NULL,
            prioridad TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            estado TEXT NOT NULL DEFAULT 'Abierto',
            respuesta_ia TEXT,
            fecha_creacion TEXT NOT NULL
        )
        """
    )
    # Migración: añadir columnas de notificación si no existen (Workshop 03)
    try:
        cursor.execute("ALTER TABLE tickets ADD COLUMN notify_status TEXT")
    except sqlite3.OperationalError:
        pass  # La columna ya existe
    try:
        cursor.execute("ALTER TABLE tickets ADD COLUMN notify_timestamp TEXT")
    except sqlite3.OperationalError:
        pass  # La columna ya existe
    conn.commit()
    conn.close()


def insert_ticket(
    titulo: str,
    categoria: str,
    prioridad: str,
    descripcion: str,
) -> None:
    """Inserta un nuevo ticket en la base de datos con estado 'Abierto'."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO tickets
            (titulo, categoria, prioridad, descripcion, estado, fecha_creacion)
        VALUES (?, ?, ?, ?, 'Abierto', ?)
        """,
        (titulo, categoria, prioridad, descripcion, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    )
    conn.commit()
    conn.close()


def get_all_tickets() -> list[dict]:
    """Retorna todos los tickets ordenados por fecha de creación descendente."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, titulo, categoria, prioridad, descripcion, estado,
               respuesta_ia, fecha_creacion, notify_status, notify_timestamp
        FROM tickets
        ORDER BY fecha_creacion DESC
        """
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_ticket_state(ticket_id: int, nuevo_estado: str) -> None:
    """Actualiza el estado de un ticket específico."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE tickets SET estado = ? WHERE id = ?",
        (nuevo_estado, ticket_id),
    )
    conn.commit()
    conn.close()


def update_ticket_ia_response(ticket_id: int, respuesta: str) -> None:
    """Guarda la respuesta generada por la IA en el ticket."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE tickets SET respuesta_ia = ? WHERE id = ?",
        (respuesta, ticket_id),
    )
    conn.commit()
    conn.close()


def update_ticket_notify_status(
    ticket_id: int, status: str, timestamp: str
) -> None:
    """Guarda el estado del envío de notificación por Gmail."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE tickets SET notify_status = ?, notify_timestamp = ? WHERE id = ?",
        (status, timestamp, ticket_id),
    )
    conn.commit()
    conn.close()


def count_tickets_by_state() -> dict[str, int]:
    """Retorna un diccionario con el conteo de tickets por estado."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT estado, COUNT(*) as total
        FROM tickets
        GROUP BY estado
        """
    )
    rows = cursor.fetchall()
    conn.close()
    counts = {"Abierto": 0, "En Progreso": 0, "Resuelto": 0}
    for estado, total in rows:
        counts[estado] = total
    return counts


# ---------------------------------------------------------------------------
# AI Agent — Lógica del agente con flujo de decisión ramificado (4 acciones)
# ---------------------------------------------------------------------------
# El agente ejecuta: Summarize → Categorize → Propose → Notify
# Devuelve un JSON estricto con la estructura:
# {
#   "resumen": "Resumen ejecutivo del problema en un párrafo corto.",
#   "categoria": "Técnico|Bug|Facturación|Solicitud de feature",
#   "prioridad": "Alta|Media|Baja",
#   "respuesta_propuesta": "Propuesta de respuesta detallada, clara y empática."
# }

SYSTEM_PROMPT = """Eres un agente despachador que utiliza el protocolo MCP \
(Model Context Protocol). Analiza el ticket de soporte y decide qué \
herramientas (tools) llamar para procesarlo.

Flujo obligatorio:
1. Primero, consulta SIEMPRE las directrices de documentación corporativa \
usando la herramienta `get_ticket_handling_guidelines` antes de proponer \
cualquier solución. Esto es obligatorio para cumplir con las políticas de la empresa.
2. Usa `summarize_ticket` para generar un resumen ejecutivo del problema.
3. Usa `categorize_ticket` para determinar la categoría y prioridad del ticket.
4. Usa `propose_solution` para generar la respuesta propuesta, utilizando como \
contexto las directrices recuperadas.
5. Usa `notify_via_gmail` para enviar la notificación por correo al finalizar.

Directrices:
- Analiza el tono del ticket (urgente, frustrado, informativo) y responde con \
empatía y profesionalismo.
- Identifica el problema central basándote en el título, categoría, prioridad y \
descripción.
- Estructura una respuesta clara y accionable con pasos concretos.
- Mantén un lenguaje técnico preciso pero accesible.

**IMPORTANTE:** Después de ejecutar todas las herramientas, devuelve ÚNICAMENTE \
un JSON válido con la siguiente estructura, sin texto adicional antes o después:

{
  "resumen": "Resumen ejecutivo del problema en un párrafo corto.",
  "categoria": "Técnico|Bug|Facturación|Solicitud de feature",
  "prioridad": "Alta|Media|Baja",
  "respuesta_propuesta": "Propuesta de respuesta detallada, clara y empática."
}
"""

# ---------------------------------------------------------------------------
# Definición de Tools (herramientas MCP) para la API de OpenAI
# ---------------------------------------------------------------------------
MCP_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "summarize_ticket",
            "description": "Genera un resumen ejecutivo del ticket de soporte técnico.",
            "parameters": {
                "type": "object",
                "properties": {
                    "titulo": {
                        "type": "string",
                        "description": "Título del ticket",
                    },
                    "descripcion": {
                        "type": "string",
                        "description": "Descripción detallada del problema",
                    },
                },
                "required": ["titulo", "descripcion"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "categorize_ticket",
            "description": "Determina la categoría y prioridad del ticket.",
            "parameters": {
                "type": "object",
                "properties": {
                    "titulo": {
                        "type": "string",
                        "description": "Título del ticket",
                    },
                    "descripcion": {
                        "type": "string",
                        "description": "Descripción del problema",
                    },
                },
                "required": ["titulo", "descripcion"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "propose_solution",
            "description": (
                "Genera una propuesta de respuesta detallada utilizando como "
                "contexto las directrices de documentación corporativa."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "titulo": {
                        "type": "string",
                        "description": "Título del ticket",
                    },
                    "descripcion": {
                        "type": "string",
                        "description": "Descripción del problema",
                    },
                    "guidelines": {
                        "type": "string",
                        "description": "Directrices corporativas recuperadas",
                    },
                    "categoria": {
                        "type": "string",
                        "description": "Categoría determinada",
                    },
                    "prioridad": {
                        "type": "string",
                        "description": "Prioridad determinada",
                    },
                },
                "required": ["titulo", "descripcion", "guidelines"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "notify_via_gmail",
            "description": "Envía una notificación por correo electrónico vía Gmail SMTP.",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string",
                        "description": "Resumen ejecutivo del ticket",
                    },
                    "category": {
                        "type": "string",
                        "description": "Categoría del ticket",
                    },
                    "priority": {
                        "type": "string",
                        "description": "Prioridad del ticket",
                    },
                    "response": {
                        "type": "string",
                        "description": "Respuesta propuesta",
                    },
                },
                "required": ["summary", "category", "priority", "response"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_ticket_handling_guidelines",
            "description": (
                "Recupera las directrices y políticas corporativas de soporte "
                "desde la base de conocimiento. Debe consultarse SIEMPRE antes "
                "de proponer una solución."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
]


# ---------------------------------------------------------------------------
# Implementación de las herramientas (ejecución local)
# ---------------------------------------------------------------------------
GUIDELINES_PATH = Path(__file__).parent / "guidelines.md"


def tool_summarize_ticket(titulo: str, descripcion: str) -> str:
    """Tool: Genera un resumen ejecutivo del ticket."""
    resumen = f"{titulo}. {descripcion}"
    if len(resumen) > 200:
        resumen = resumen[:200] + "..."
    return f"Resumen ejecutivo: {resumen}"


def tool_categorize_ticket(titulo: str, descripcion: str) -> str:
    """Tool: Determina la categoría y prioridad basándose en palabras clave."""
    texto = f"{titulo} {descripcion}".lower()

    if any(k in texto for k in ["cloud", "servidor", "red", "infraestructura", "conexion"]):
        return "Categoría: Técnico, Prioridad: Alta"
    elif any(k in texto for k in ["bug", "error", "codigo", "fallo", "excepcion"]):
        return "Categoría: Bug, Prioridad: Media"
    elif any(k in texto for k in ["pago", "factura", "reembolso", "cobro"]):
        return "Categoría: Facturación, Prioridad: Alta"
    elif any(k in texto for k in ["feature", "mejora", "solicitud", "nueva"]):
        return "Categoría: Solicitud de feature, Prioridad: Baja"
    elif any(k in texto for k in ["auth", "login", "seguridad", "acceso"]):
        return "Categoría: Técnico, Prioridad: Media"
    else:
        return "Categoría: Técnico, Prioridad: Media"


def tool_propose_solution(
    titulo: str,
    descripcion: str,
    guidelines: str,
    categoria: str = "",
    prioridad: str = "",
) -> str:
    """Tool: Genera una propuesta de solución usando las directrices como contexto."""
    return (
        f"Propuesta de solución para el ticket '{titulo}':\n\n"
        f"Basándonos en las directrices corporativas:\n{guidelines[:500]}...\n\n"
        f"Categoría: {categoria}\nPrioridad: {prioridad}\n\n"
        f"Recomendación: Analizar el problema descrito y aplicar los pasos "
        f"de solución correspondientes según las políticas de soporte."
    )


def tool_notify_via_gmail(
    summary: str,
    category: str,
    priority: str,
    response: str,
) -> str:
    """Tool: Envía notificación por Gmail SMTP."""
    result = send_gmail_notification(summary, category, priority, response)
    if result["success"]:
        return f"Notificación enviada con éxito a {NOTIFICATION_RECEIVER_EMAIL} a las {result['timestamp']}."
    else:
        return f"Error al enviar notificación: {result['message']}"


def tool_get_ticket_handling_guidelines() -> str:
    """Tool: Recupera las directrices corporativas desde guidelines.md."""
    try:
        if GUIDELINES_PATH.exists():
            return GUIDELINES_PATH.read_text(encoding="utf-8")
        else:
            return "No se encontró el archivo guidelines.md. Usando directrices por defecto."
    except Exception as e:
        return f"Error al leer guidelines.md: {str(e)}"


# Mapa de nombres de tools a funciones ejecutables
TOOL_FUNCTIONS = {
    "summarize_ticket": tool_summarize_ticket,
    "categorize_ticket": tool_categorize_ticket,
    "propose_solution": tool_propose_solution,
    "notify_via_gmail": tool_notify_via_gmail,
    "get_ticket_handling_guidelines": tool_get_ticket_handling_guidelines,
}


def is_agent_configured() -> bool:
    """Verifica si las variables de entorno del AI Agent están configuradas."""
    return bool(AGENT_API_URL and AGENT_API_KEY and AGENT_MODEL_NAME)


def is_smtp_configured() -> bool:
    """Verifica si las variables de entorno de Gmail SMTP están configuradas."""
    return bool(
        SMTP_SENDER_EMAIL
        and SMTP_APP_PASSWORD
        and NOTIFICATION_RECEIVER_EMAIL
    )


def generate_ticket_response(ticket_data: dict, execution_log: list = None) -> dict:
    """
    Genera un análisis estructurado (JSON) para un ticket usando un LLM
    con Tool Calling (MCP).

    El agente usa un bucle de ejecución que:
    1. Envía el request con tools al LLM.
    2. Si el LLM sugiere tool_calls, ejecuta cada herramienta localmente.
    3. Devuelve los resultados al LLM para que continúe.
    4. Repite hasta que el LLM devuelva una respuesta final sin tool_calls.

    Parámetros:
        ticket_data (dict): Datos del ticket.
        execution_log (list, opcional): Lista para registrar los pasos del agente.

    Retorna:
        dict: Análisis estructurado con keys: resumen, categoria,
              prioridad, respuesta_propuesta, notify_result.
    """
    if execution_log is None:
        execution_log = []

    user_prompt = (
        f"Analiza el siguiente ticket de soporte técnico usando las herramientas "
        f"MCP disponibles. Recuerda consultar primero las directrices de "
        f"documentación antes de proponer una solución.\n\n"
        f"**Título:** {ticket_data.get('titulo', 'N/A')}\n"
        f"**Categoría:** {ticket_data.get('categoria', 'N/A')}\n"
        f"**Prioridad:** {ticket_data.get('prioridad', 'N/A')}\n"
        f"**Estado:** {ticket_data.get('estado', 'N/A')}\n"
        f"**Descripción:** {ticket_data.get('descripcion', 'N/A')}\n"
    )

    try:
        client = OpenAI(
            base_url=AGENT_API_URL,
            api_key=AGENT_API_KEY,
        )

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        notify_result = None
        max_iterations = 10  # Límite de seguridad para el bucle

        for iteration in range(max_iterations):
            response = client.chat.completions.create(
                model=AGENT_MODEL_NAME,
                messages=messages,
                tools=MCP_TOOLS,
                temperature=0.7,
                max_tokens=1000,
            )

            message = response.choices[0].message

            # Si no hay tool_calls, el agente terminó su análisis
            if not message.tool_calls:
                raw_content = message.content or ""

                # Registrar finalización
                execution_log.append({
                    "step": f"✅ Análisis completado",
                    "detail": "El agente ha finalizado su análisis.",
                })

                # Parsear el JSON final
                try:
                    clean_content = raw_content.strip()
                    if clean_content.startswith("```"):
                        lines = clean_content.split("\n")
                        lines = [l for l in lines if not l.strip().startswith("```")]
                        clean_content = "\n".join(lines)

                    result = json.loads(clean_content)

                    required_keys = {"resumen", "categoria", "prioridad", "respuesta_propuesta"}
                    if not required_keys.issubset(result.keys()):
                        raise ValueError(f"Faltan keys. Esperadas: {required_keys}")

                    # Añadir resultado de notificación si existe
                    if notify_result:
                        result["notify_result"] = notify_result

                    return result

                except (json.JSONDecodeError, ValueError) as parse_err:
                    return {
                        "resumen": "No se pudo parsear la respuesta final del LLM.",
                        "categoria": ticket_data.get("categoria", "N/A"),
                        "prioridad": ticket_data.get("prioridad", "N/A"),
                        "respuesta_propuesta": (
                            f"La respuesta del modelo no estaba en formato JSON válido.\n\n"
                            f"**Respuesta cruda:**\n\n{raw_content}\n\n"
                            f"**Error:** `{str(parse_err)}`"
                        ),
                        "notify_result": notify_result,
                    }

            # Procesar cada tool_call sugerido por el LLM
            messages.append(message)

            for tool_call in message.tool_calls:
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments)

                # Registrar el paso en el log de ejecución
                step_icons = {
                    "summarize_ticket": "📝",
                    "categorize_ticket": "🏷️",
                    "propose_solution": "💡",
                    "notify_via_gmail": "📧",
                    "get_ticket_handling_guidelines": "🔍",
                }
                icon = step_icons.get(func_name, "⚙️")
                execution_log.append({
                    "step": f"{icon} Ejecutando: {func_name}",
                    "detail": f"Argumentos: {json.dumps(func_args, ensure_ascii=False)[:200]}",
                })

                # Ejecutar la herramienta localmente
                if func_name in TOOL_FUNCTIONS:
                    try:
                        tool_result = TOOL_FUNCTIONS[func_name](**func_args)

                        # Capturar resultado de notificación
                        if func_name == "notify_via_gmail":
                            notify_result = tool_result

                        execution_log.append({
                            "step": f"   ↳ Resultado de {func_name}",
                            "detail": tool_result[:300],
                        })
                    except Exception as tool_err:
                        tool_result = f"Error ejecutando {func_name}: {str(tool_err)}"
                        execution_log.append({
                            "step": f"   ↳ Error en {func_name}",
                            "detail": str(tool_err),
                        })
                else:
                    tool_result = f"Herramienta desconocida: {func_name}"

                # Añadir el resultado de la tool al historial de mensajes
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result,
                })

        # Si se alcanza el límite de iteraciones
        execution_log.append({
            "step": "⚠️ Límite de iteraciones alcanzado",
            "detail": "El agente no completó el análisis en el número máximo de iteraciones.",
        })
        return {
            "resumen": "El agente no completó el análisis.",
            "categoria": ticket_data.get("categoria", "N/A"),
            "prioridad": ticket_data.get("prioridad", "N/A"),
            "respuesta_propuesta": "El agente excedió el límite de iteraciones.",
            "notify_result": notify_result,
        }

    except Exception as e:
        return {
            "resumen": "Error al conectar con el AI Agent.",
            "categoria": ticket_data.get("categoria", "N/A"),
            "prioridad": ticket_data.get("prioridad", "N/A"),
            "respuesta_propuesta": (
                f"⚠️ No se pudo generar la respuesta automatizada.\n\n"
                f"**Detalle del error:** `{str(e)}`\n\n"
                f"Verifica la configuración del archivo `.env`."
            ),
            "notify_result": None,
        }


# ---------------------------------------------------------------------------
# Notificación por Gmail (SMTP) — Función dedicada
# ---------------------------------------------------------------------------
def send_gmail_notification(
    summary: str,
    category: str,
    priority: str,
    response: str,
) -> dict:
    """
    Envía una notificación por correo electrónico vía Gmail SMTP.

    Construye un correo HTML profesional con el resumen, categoría/prioridad
    y la respuesta propuesta por la IA.

    Parámetros:
        summary (str): Resumen ejecutivo del ticket.
        category (str): Categoría determinada por el agente.
        priority (str): Prioridad determinada por el agente.
        response (str): Respuesta propuesta por la IA.

    Retorna:
        dict: {"success": bool, "message": str, "timestamp": str}
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Construir el asunto dinámico
    subject = f"[Soporte AI] Nuevo Ticket - Prioridad {priority}: {category}"

    # Construir el cuerpo HTML profesional
    html_body = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background-color: #0a0a0a;
                color: #fafafa;
                margin: 0;
                padding: 2rem;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: #141414;
                border: 1px solid #262626;
                border-radius: 8px;
                padding: 2rem;
            }}
            .header {{
                border-bottom: 1px solid #262626;
                padding-bottom: 1rem;
                margin-bottom: 1.5rem;
            }}
            .header h1 {{
                font-size: 1.25rem;
                font-weight: 600;
                color: #fafafa;
                margin: 0;
            }}
            .section {{
                margin-bottom: 1.5rem;
            }}
            .section-title {{
                font-size: 0.75rem;
                font-weight: 600;
                color: #737373;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                margin-bottom: 0.5rem;
            }}
            .section-content {{
                color: #a3a3a3;
                line-height: 1.6;
            }}
            .badge {{
                display: inline-block;
                padding: 0.25rem 0.6rem;
                border-radius: 999px;
                font-size: 0.75rem;
                font-weight: 500;
                margin-right: 0.5rem;
            }}
            .badge-priority {{
                background-color: rgba(59, 130, 246, 0.15);
                color: #3b82f6;
            }}
            .badge-category {{
                background-color: rgba(34, 197, 94, 0.15);
                color: #22c55e;
            }}
            .footer {{
                border-top: 1px solid #262626;
                padding-top: 1rem;
                margin-top: 1.5rem;
                font-size: 0.75rem;
                color: #737373;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎫 Notificación de Ticket — AI Agent</h1>
            </div>

            <div class="section">
                <div class="section-title">Categoría y Prioridad</div>
                <div class="section-content">
                    <span class="badge badge-category">{category}</span>
                    <span class="badge badge-priority">Prioridad: {priority}</span>
                </div>
            </div>

            <div class="section">
                <div class="section-title">Resumen Ejecutivo</div>
                <div class="section-content">{summary}</div>
            </div>

            <div class="section">
                <div class="section-title">Respuesta Propuesta por IA</div>
                <div class="section-content">{response}</div>
            </div>

            <div class="footer">
                <p>Notificación generada automáticamente por el AI Agent — Ticket Tracker</p>
                <p>Fecha: {timestamp}</p>
            </div>
        </div>
    </body>
    </html>
    """

    try:
        # Construir el mensaje MIME
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SMTP_SENDER_EMAIL
        msg["To"] = NOTIFICATION_RECEIVER_EMAIL

        # Adjuntar versión HTML
        msg.attach(MIMEText(html_body, "html"))

        # Conectar al servidor SMTP de Gmail y enviar
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SMTP_SENDER_EMAIL, SMTP_APP_PASSWORD)
            server.sendmail(
                SMTP_SENDER_EMAIL,
                NOTIFICATION_RECEIVER_EMAIL,
                msg.as_string(),
            )

        return {
            "success": True,
            "message": f"Notificación enviada con éxito a {NOTIFICATION_RECEIVER_EMAIL}",
            "timestamp": timestamp,
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Error al enviar la notificación: {str(e)}",
            "timestamp": timestamp,
        }


# ---------------------------------------------------------------------------
# Función Placeholder — Simulación de IA (Solución Parcial / Fallback)
# ---------------------------------------------------------------------------
def procesar_ticket_con_ia(descripcion: str) -> dict:
    """
    Simula la 'Solución Parcial' del flujo generando una respuesta estática
    basada en palabras clave del ticket. Usado como fallback cuando el LLM
    no está configurado.

    Parámetros:
        descripcion (str): La descripción del problema reportado.

    Retorna:
        dict: Análisis estructurado con keys: resumen, categoria,
              prioridad, respuesta_propuesta.
    """
    descripcion_lower = descripcion.lower()

    # Diccionario de palabras clave -> (categoria, prioridad, respuesta)
    sugerencias = {
        "cloud": (
            "Cloud/Infraestructura",
            "Alta",
            "☁️ **Sugerencia Cloud/Infraestructura:**\n\n"
            "1. Verificar los logs del servidor en la consola de administración.\n"
            "2. Revisar el estado de los recursos (CPU, memoria, disco).\n"
            "3. Comprobar la conectividad de red y las reglas de firewall.\n"
            "4. Validar que las variables de entorno y credenciales estén configuradas correctamente.",
        ),
        "servidor": (
            "Técnico",
            "Alta",
            "🖥️ **Sugerencia de Servidor:**\n\n"
            "1. Revisar el estado del servicio con `systemctl status <servicio>`.\n"
            "2. Comprobar los logs en `/var/log/` para identificar errores recientes.\n"
            "3. Verificar el uso de recursos y reiniciar el servicio si es necesario.",
        ),
        "desarrollo": (
            "Bug",
            "Media",
            "💻 **Sugerencia de Desarrollo:**\n\n"
            "1. Revisar el repositorio de código en busca de cambios recientes (`git log`).\n"
            "2. Ejecutar las pruebas unitarias para identificar fallos.\n"
            "3. Verificar que las dependencias estén actualizadas (`pip freeze`).\n"
            "4. Comprobar la configuración del entorno de desarrollo local.",
        ),
        "codigo": (
            "Bug",
            "Media",
            "💻 **Sugerencia de Código:**\n\n"
            "1. Revisar el stack trace del error para identificar la línea problemática.\n"
            "2. Verificar la lógica del código afectado.\n"
            "3. Ejecutar un linter para detectar problemas de sintaxis.",
        ),
        "red": (
            "Técnico",
            "Alta",
            "🌐 **Sugerencia de Red:**\n\n"
            "1. Verificar la conectividad con `ping` y `traceroute`.\n"
            "2. Revisar la configuración DNS (`nslookup`).\n"
            "3. Comprobar los puertos abiertos con `netstat` o `ss`.\n"
            "4. Validar las reglas de enrutamiento y proxy.",
        ),
        "conexion": (
            "Técnico",
            "Alta",
            "🌐 **Sugerencia de Conexión:**\n\n"
            "1. Verificar que el endpoint esté disponible.\n"
            "2. Comprobar credenciales y tokens de autenticación.\n"
            "3. Revisar timeouts y reintentos en la configuración.",
        ),
        "db": (
            "Técnico",
            "Alta",
            "🗄️ **Sugerencia de Base de Datos:**\n\n"
            "1. Verificar la conexión a la base de datos.\n"
            "2. Revisar las consultas recientes en busca de bloqueos (`SHOW PROCESSLIST`).\n"
            "3. Comprobar el espacio en disco y los índices.\n"
            "4. Validar los backups más recientes.",
        ),
        "database": (
            "Técnico",
            "Alta",
            "🗄️ **Sugerencia de Base de Datos:**\n\n"
            "1. Verificar la conexión a la base de datos.\n"
            "2. Revisar las consultas recientes en busca de bloqueos.\n"
            "3. Comprobar el espacio en disco y los índices.\n"
            "4. Validar los backups más recientes.",
        ),
        "auth": (
            "Técnico",
            "Media",
            "🔐 **Sugerencia de Autenticación:**\n\n"
            "1. Verificar que las credenciales sean correctas.\n"
            "2. Comprobar la expiración del token o sesión.\n"
            "3. Revisar los logs de autenticación para intentos fallidos.\n"
            "4. Validar la configuración de OAuth/SAML si aplica.",
        ),
        "login": (
            "Técnico",
            "Media",
            "🔐 **Sugerencia de Login:**\n\n"
            "1. Verificar usuario y contraseña.\n"
            "2. Comprobar si la cuenta está bloqueada o deshabilitada.\n"
            "3. Revisar la configuración del proveedor de identidad.",
        ),
        "error": (
            "Bug",
            "Alta",
            "⚠️ **Sugerencia de Error General:**\n\n"
            "1. Capturar el stack trace completo del error.\n"
            "2. Reproducir el escenario en un entorno de pruebas.\n"
            "3. Revisar la documentación oficial del componente afectado.\n"
            "4. Buscar el código de error en la base de conocimiento.",
        ),
        "rendimiento": (
            "Técnico",
            "Media",
            "⚡ **Sugerencia de Rendimiento:**\n\n"
            "1. Monitorear el uso de CPU, memoria y I/O.\n"
            "2. Identificar cuellos de botella con herramientas de profiling.\n"
            "3. Revisar consultas o procesos costosos.\n"
            "4. Considerar escalado horizontal o vertical.",
        ),
        "performance": (
            "Técnico",
            "Media",
            "⚡ **Sugerencia de Performance:**\n\n"
            "1. Monitorear el uso de recursos.\n"
            "2. Identificar cuellos de botella con profiling.\n"
            "3. Optimizar consultas y procesos costosos.",
        ),
        "seguridad": (
            "Técnico",
            "Alta",
            "🛡️ **Sugerencia de Seguridad:**\n\n"
            "1. Revisar los permisos y roles del usuario afectado.\n"
            "2. Comprobar los logs de auditoría.\n"
            "3. Verificar la configuración de cifrado y certificados.\n"
            "4. Escalar al equipo de seguridad si es un incidente crítico.",
        ),
    }

    # Buscar la primera palabra clave que coincida
    for keyword, (categoria, prioridad, respuesta) in sugerencias.items():
        if keyword in descripcion_lower:
            return {
                "resumen": descripcion[:150] + ("..." if len(descripcion) > 150 else ""),
                "categoria": categoria,
                "prioridad": prioridad,
                "respuesta_propuesta": respuesta,
            }

    # Respuesta por defecto si no hay coincidencias
    return {
        "resumen": descripcion[:150] + ("..." if len(descripcion) > 150 else ""),
        "categoria": "Solicitud de feature",
        "prioridad": "Baja",
        "respuesta_propuesta": (
            "📋 **Sugerencia General:**\n\n"
            "1. Recopilar información adicional sobre el problema.\n"
            "2. Reproducir el escenario en un entorno controlado.\n"
            "3. Documentar los pasos para reproducir el issue.\n"
            "4. Escalar al equipo correspondiente si persiste el problema."
        ),
    }


# ---------------------------------------------------------------------------
# Renderizado de badges de estado
# ---------------------------------------------------------------------------
def render_estado_badge(estado: str) -> str:
    """Retorna el HTML de un badge según el estado del ticket."""
    badge_map = {
        "Abierto": '<span class="badge-abierto">Abierto</span>',
        "En Progreso": '<span class="badge-progreso">En Progreso</span>',
        "Resuelto": '<span class="badge-resuelto">Resuelto</span>',
    }
    return badge_map.get(estado, f'<span>{estado}</span>')


# ---------------------------------------------------------------------------
# Sección A: Panel de Usuario (Reportar Problema)
# ---------------------------------------------------------------------------
def panel_usuario() -> None:
    """Renderiza el formulario para que los usuarios reporten problemas."""
    st.markdown("## 🎫 Panel de Usuario — Reportar Problema")
    st.markdown(
        "<p style='color: #737373; margin-bottom: 2rem;'>"
        "Completa el formulario para reportar un incidente de soporte técnico."
        "</p>",
        unsafe_allow_html=True,
    )

    with st.container():
        st.markdown("### 📝 Nuevo Ticket")

        # Campos del formulario
        titulo = st.text_input(
            "Título del problema",
            placeholder="Ej: Error de conexión a la base de datos",
            key="form_titulo",
        )

        col_cat, col_pri = st.columns(2)

        with col_cat:
            categoria = st.selectbox(
                "Categoría",
                options=["Desarrollo", "Cloud/Infraestructura", "Soporte Técnico"],
                key="form_categoria",
            )

        with col_pri:
            prioridad = st.radio(
                "Prioridad",
                options=["Baja", "Media", "Alta"],
                horizontal=True,
                key="form_prioridad",
            )

        descripcion = st.text_area(
            "Descripción detallada",
            placeholder="Describe el problema con el mayor detalle posible...",
            height=150,
            key="form_descripcion",
        )

        # Botón de envío
        if st.button("Enviar Ticket", type="primary", use_container_width=True):
            if not titulo.strip():
                st.error("⚠️ El título del problema es obligatorio.")
            elif not descripcion.strip():
                st.error("⚠️ La descripción del problema es obligatoria.")
            else:
                insert_ticket(titulo, categoria, prioridad, descripcion)
                st.success("✅ Ticket enviado correctamente. El equipo de soporte lo revisará pronto.")
                st.balloons()
                # Limpiar el formulario recargando
                st.rerun()


# ---------------------------------------------------------------------------
# Sección B: Panel de Administración (Gestión y Soporte)
# ---------------------------------------------------------------------------
def panel_administracion() -> None:
    """Renderiza el panel de administración para gestionar tickets."""
    st.markdown("## 🛠️ Panel de Administración — Gestión y Soporte")
    st.markdown(
        "<p style='color: #737373; margin-bottom: 2rem;'>"
        "Visualiza y gestiona todos los tickets de soporte técnico."
        "</p>",
        unsafe_allow_html=True,
    )

    # Contadores minimalistas
    counts = count_tickets_by_state()
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(label="Abiertos", value=counts["Abierto"])
    with col2:
        st.metric(label="En Progreso", value=counts["En Progreso"])
    with col3:
        st.metric(label="Resueltos", value=counts["Resuelto"])

    st.markdown("---")

    # Listado de tickets
    st.markdown("### 📋 Tickets")

    tickets = get_all_tickets()

    if not tickets:
        st.markdown(
            "<div style='text-align: center; padding: 3rem; color: #737373;'>"
            "No hay tickets registrados. Los tickets aparecerán aquí cuando se reporten."
            "</div>",
            unsafe_allow_html=True,
        )
        return

    for ticket in tickets:
        with st.container():
            # Cabecera del ticket: ID + Título + Badge de estado
            col_header, col_estado = st.columns([4, 1])

            with col_header:
                st.markdown(
                    f"**#{ticket['id']} — {ticket['titulo']}**",
                )

            with col_estado:
                st.markdown(
                    render_estado_badge(ticket["estado"]),
                    unsafe_allow_html=True,
                )

            # Metadatos del ticket
            col_meta1, col_meta2, col_meta3 = st.columns(3)
            with col_meta1:
                st.markdown(f"**Categoría:** {ticket['categoria']}")
            with col_meta2:
                st.markdown(f"**Prioridad:** {ticket['prioridad']}")
            with col_meta3:
                st.markdown(f"**Fecha:** {ticket['fecha_creacion']}")

            # Descripción
            st.markdown("**Descripción:**")
            st.markdown(
                f"<div style='color: #a3a3a3; padding: 0.75rem; "
                f"background-color: #1a1a1a; border-radius: 8px; "
                f"border: 1px solid #262626; margin-bottom: 1rem;'>"
                f"{ticket['descripcion']}"
                f"</div>",
                unsafe_allow_html=True,
            )

            # Interacción: Cambiar estado
            col_estado_sel, col_ia = st.columns([1, 2])

            with col_estado_sel:
                nuevo_estado = st.selectbox(
                    "Cambiar estado",
                    options=["Abierto", "En Progreso", "Resuelto"],
                    index=["Abierto", "En Progreso", "Resuelto"].index(ticket["estado"]),
                    key=f"estado_{ticket['id']}",
                )
                if nuevo_estado != ticket["estado"]:
                    update_ticket_state(ticket["id"], nuevo_estado)
                    st.success(f"Estado actualizado a: {nuevo_estado}")
                    st.rerun()

            with col_ia:
                # Contenedor de IA — AI Agent Analysis (Workshop 03)
                with st.expander("🤖 AI Agent Analysis", expanded=False):
                    # Verificar configuración del .env
                    if not is_agent_configured():
                        st.warning(
                            "⚠️ El AI Agent no está configurado. "
                            "Falta configurar las variables de entorno en el archivo `.env` "
                            "(AGENT_API_URL, AGENT_API_KEY, AGENT_MODEL_NAME). "
                            "Se usará el modo fallback (palabras clave) mientras tanto."
                        )

                    # Mostrar respuesta existente si la hay
                    if ticket["respuesta_ia"]:
                        try:
                            analysis = json.loads(ticket["respuesta_ia"])
                            # Mostrar resultado organizado en pestañas
                            tab1, tab2, tab3 = st.tabs([
                                "📋 Resumen y Categoría",
                                "💡 Respuesta Propuesta",
                                "📢 Envío de Alertas",
                            ])

                            with tab1:
                                # Badges visuales para categoría y prioridad
                                col_badge1, col_badge2 = st.columns(2)
                                with col_badge1:
                                    st.markdown(
                                        f"<div style='text-align: center; padding: 0.5rem; "
                                        f"background-color: rgba(34, 197, 94, 0.15); "
                                        f"border-radius: 8px; color: #22c55e; "
                                        f"font-weight: 500;'>"
                                        f"🏷️ {analysis.get('categoria', 'N/A')}"
                                        f"</div>",
                                        unsafe_allow_html=True,
                                    )
                                with col_badge2:
                                    priority_color = {
                                        "Alta": "#ef4444",
                                        "Media": "#f59e0b",
                                        "Baja": "#22c55e",
                                    }.get(analysis.get("prioridad", ""), "#737373")
                                    st.markdown(
                                        f"<div style='text-align: center; padding: 0.5rem; "
                                        f"background-color: rgba(59, 130, 246, 0.15); "
                                        f"border-radius: 8px; color: {priority_color}; "
                                        f"font-weight: 500;'>"
                                        f"⚡ Prioridad: {analysis.get('prioridad', 'N/A')}"
                                        f"</div>",
                                        unsafe_allow_html=True,
                                    )

                                st.markdown("")
                                st.markdown("**Resumen Ejecutivo:**")
                                st.markdown(
                                    f"<div style='color: #a3a3a3; padding: 0.75rem; "
                                    f"background-color: #1a1a1a; border-radius: 8px; "
                                    f"border: 1px solid #262626;'>"
                                    f"{analysis.get('resumen', 'N/A')}"
                                    f"</div>",
                                    unsafe_allow_html=True,
                                )

                            with tab2:
                                st.markdown("**Respuesta Propuesta por la IA:**")
                                with st.chat_message("assistant"):
                                    st.markdown(
                                        analysis.get("respuesta_propuesta", "N/A")
                                    )

                            with tab3:
                                # Mostrar estado del envío de notificación
                                notify_status = ticket.get("notify_status", "")
                                if notify_status == "success":
                                    st.success(
                                        f"✅ Notificación enviada con éxito a "
                                        f"{NOTIFICATION_RECEIVER_EMAIL} — "
                                        f"{ticket.get('notify_timestamp', '')}"
                                    )
                                elif notify_status == "error":
                                    st.error(
                                        f"❌ Error al enviar la notificación. "
                                        f"Verifica las credenciales SMTP en el `.env`."
                                    )
                                else:
                                    st.markdown(
                                        "<p style='color: #737373;'>"
                                        "No se ha enviado ninguna notificación para este ticket."
                                        "</p>",
                                        unsafe_allow_html=True,
                                    )

                                # Botón para reenviar notificación
                                if st.button(
                                    "📢 Reenviar Notificación",
                                    key=f"notify_{ticket['id']}",
                                    type="secondary",
                                ):
                                    if not is_smtp_configured():
                                        st.error(
                                            "❌ Las variables de Gmail SMTP no están "
                                            "configuradas en el `.env`."
                                        )
                                    else:
                                        with st.spinner(
                                            "Enviando alerta por correo electrónico..."
                                        ):
                                            notify_result = send_gmail_notification(
                                                summary=analysis.get("resumen", ""),
                                                category=analysis.get("categoria", ""),
                                                priority=analysis.get("prioridad", ""),
                                                response=analysis.get(
                                                    "respuesta_propuesta", ""
                                                ),
                                            )
                                        if notify_result["success"]:
                                            update_ticket_notify_status(
                                                ticket["id"],
                                                "success",
                                                notify_result["timestamp"],
                                            )
                                            st.success(notify_result["message"])
                                            st.rerun()
                                        else:
                                            update_ticket_notify_status(
                                                ticket["id"],
                                                "error",
                                                notify_result["timestamp"],
                                            )
                                            st.error(notify_result["message"])
                                            st.rerun()

                        except json.JSONDecodeError:
                            # Respuesta anterior (no JSON) — mostrar como texto
                            with st.chat_message("assistant"):
                                st.markdown(ticket["respuesta_ia"])
                    else:
                        st.markdown(
                            "<p style='color: #737373;'>"
                            "No se ha generado una respuesta aún. "
                            "Presiona el botón para que el AI Agent analice este ticket."
                            "</p>",
                            unsafe_allow_html=True,
                        )

                    # Botón para generar respuesta con IA (MCP Tool Calling)
                    if st.button(
                        "🤖 Analizar con AI Agent (MCP)",
                        key=f"ia_{ticket['id']}",
                        type="secondary",
                    ):
                        if is_agent_configured():
                            # Usar el AI Agent con Tool Calling (MCP)
                            execution_log = []
                            with st.spinner("El agente MCP está analizando el ticket..."):
                                analysis = generate_ticket_response(
                                    ticket, execution_log=execution_log
                                )

                            # Guardar el log de ejecución en session_state
                            st.session_state[f"exec_log_{ticket['id']}"] = execution_log

                            # Guardar el análisis como JSON en la BD
                            update_ticket_ia_response(
                                ticket["id"], json.dumps(analysis, ensure_ascii=False)
                            )

                            # Procesar resultado de notificación
                            notify_info = analysis.get("notify_result", "")
                            if notify_info and "éxito" in str(notify_info).lower():
                                update_ticket_notify_status(
                                    ticket["id"], "success",
                                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                )
                            elif is_smtp_configured() and not notify_info:
                                # Si el agente no notificó, enviar manualmente
                                with st.spinner(
                                    "Enviando alerta por correo electrónico..."
                                ):
                                    notify_result = send_gmail_notification(
                                        summary=analysis.get("resumen", ""),
                                        category=analysis.get("categoria", ""),
                                        priority=analysis.get("prioridad", ""),
                                        response=analysis.get("respuesta_propuesta", ""),
                                    )
                                if notify_result["success"]:
                                    update_ticket_notify_status(
                                        ticket["id"], "success",
                                        notify_result["timestamp"],
                                    )
                                else:
                                    update_ticket_notify_status(
                                        ticket["id"], "error",
                                        notify_result["timestamp"],
                                    )
                            else:
                                update_ticket_notify_status(ticket["id"], "error", "")
                        else:
                            # Fallback: usar la función placeholder
                            analysis = procesar_ticket_con_ia(ticket["descripcion"])
                            update_ticket_ia_response(
                                ticket["id"], json.dumps(analysis, ensure_ascii=False)
                            )
                            update_ticket_notify_status(ticket["id"], "error", "")

                        st.rerun()

                    # Mostrar log de ejecución del MCP si existe
                    exec_log_key = f"exec_log_{ticket['id']}"
                    if exec_log_key in st.session_state and st.session_state[exec_log_key]:
                        with st.expander("📋 Log de Ejecución MCP", expanded=False):
                            for log_entry in st.session_state[exec_log_key]:
                                st.markdown(
                                    f"<div style='padding: 0.4rem 0; "
                                    f"border-bottom: 1px solid #262626; "
                                    f"color: #a3a3a3; font-size: 0.85rem;'>"
                                    f"<strong style='color: #fafafa;'>"
                                    f"{log_entry['step']}</strong><br/>"
                                    f"<span style='color: #737373;'>"
                                    f"{log_entry['detail']}"
                                    f"</span></div>",
                                    unsafe_allow_html=True,
                                )

                        st.rerun()

            st.markdown("---")


# ---------------------------------------------------------------------------
# Navegación principal — Barra lateral
# ---------------------------------------------------------------------------
def main() -> None:
    """Punto de entrada de la aplicación."""
    # Inicializar la base de datos
    init_db()

    # Barra lateral — Navegación por roles
    with st.sidebar:
        st.markdown("# 🎫 Ticket Tracker")
        st.markdown(
            "<p style='color: #737373; font-size: 0.85rem;'>"
            "Sistema de gestión de tickets de soporte técnico"
            "</p>",
            unsafe_allow_html=True,
        )
        st.markdown("---")

        st.markdown("### Navegación")
        vista = st.radio(
            "Selecciona una vista",
            options=[
                "Panel de Usuario (Reportar Problema)",
                "Panel de Administración (Gestión y Soporte)",
            ],
            label_visibility="collapsed",
        )

        st.markdown("---")
        # Estado de configuración del AI Agent y SMTP
        agent_status = "✅ Configurado" if is_agent_configured() else "⚠️ No configurado"
        smtp_status = "✅ Configurado" if is_smtp_configured() else "⚠️ No configurado"
        st.markdown(
            f"<p style='color: #737373; font-size: 0.75rem;'>"
            f"Flujo: Problema → Aplicación con IA → Solución Parcial<br/>"
            f"AI Agent: {agent_status}<br/>"
            f"Gmail SMTP: {smtp_status}"
            f"</p>",
            unsafe_allow_html=True,
        )

    # Renderizar la vista seleccionada
    if vista == "Panel de Usuario (Reportar Problema)":
        panel_usuario()
    else:
        panel_administracion()


if __name__ == "__main__":
    main()
