"""
===========================================================================
 Sistema de Gestión de Tickets de Soporte Técnico
 Flujo: Ticket → Agent Analyze → Agent Action → Solución + Notificación
----------------------------------------------------------------------------
 Stack:    Python 3.10+ · Streamlit · SQLite · OpenAI-compatible LLM · MCP
 Arquitectura: Multi-Agente (2 agentes especializados colaborando)
   · Agent for Analyze — toolkit MCP-Analyze (guidelines, summarize, categorize)
   · Agent for Action  — toolkit MCP-Action  (propose_solution, notify_via_gmail)
   Comunicación: payload JSON estructurado entre agentes
 Estructura: Un único archivo (app.py) + guidelines.md (base de conocimiento)
===========================================================================
"""

import json
import os
import smtplib
import ssl
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv
from openai import OpenAI

import streamlit as st

# ============================================================================
# 0. DIRECTORIO BASE — para localizar guidelines.md
# ============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ============================================================================
# 1. CONFIGURACIÓN DE PÁGINA
# ============================================================================
st.set_page_config(
    page_title="Soporte Técnico · Multi-Agente MCP",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================================
# 2. CSS PERSONALIZADO — MODO OSCURO ELEGANTE (Inspirado en Gemini / Vercel)
# ============================================================================
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

:root {
    --bg-primary:   #0a0a0a;
    --bg-secondary: #141414;
    --bg-tertiary:  #1c1c1c;
    --bg-elevated:  #232323;
    --border-subtle:#27272a;
    --border-default:#3f3f46;
    --text-primary: #fafafa;
    --text-secondary:#a1a1aa;
    --text-muted:   #71717a;
    --accent:       #3b82f6;
    --accent-hover: #2563eb;
    --accent-soft:  rgba(59,130,246,0.12);
    --success:      #22c55e;
    --warning:      #f59e0b;
    --danger:       #ef4444;
    --radius:       10px;
}

/* --- Base --- */
html, body, .stApp {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background-color: var(--bg-primary);
    color: var(--text-primary);
}
.stApp { padding-top: 2.5rem; }

/* --- Sidebar --- */
section[data-testid="stSidebar"] {
    background-color: var(--bg-secondary);
    border-right: 1px solid var(--border-subtle);
}
section[data-testid="stSidebar"] * {
    font-family: 'Inter', sans-serif !important;
}

/* --- Tipografía --- */
h1, h2, h3, h4 {
    color: var(--text-primary) !important;
    font-weight: 600 !important;
    letter-spacing: -0.02em;
}
h1 { font-size: 1.85rem !important; }
h2 { font-size: 1.4rem  !important; }
h3 { font-size: 1.15rem !important; }
h4 { font-size: 1rem    !important; }
p, li, span { color: var(--text-secondary); }

/* --- Inputs --- */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div > div {
    background-color: var(--bg-tertiary) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 8px !important;
    color: var(--text-primary) !important;
    font-family: 'Inter', sans-serif !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px var(--accent-soft) !important;
}

/* --- Labels --- */
.stTextInput label, .stTextArea label, .stSelectbox label, .stRadio label {
    color: var(--text-secondary) !important;
    font-weight: 500 !important;
    font-size: 0.875rem !important;
}

/* --- Radio --- */
.stRadio > div { gap: 0.75rem; }
.stRadio > div > label[data-checked="true"] {
    background-color: var(--accent-soft) !important;
    border-color: var(--accent) !important;
    color: var(--accent) !important;
}

/* --- Botones --- */
.stButton > button {
    background-color: var(--accent) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    font-family: 'Inter', sans-serif !important;
    padding: 0.5rem 1.5rem !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    background-color: var(--accent-hover) !important;
    box-shadow: 0 4px 14px rgba(59,130,246,0.35);
}
.stButton > button[kind="secondary"] {
    background-color: var(--bg-elevated) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border-default) !important;
}
.stButton > button[kind="secondary"]:hover {
    border-color: var(--accent) !important;
}

/* --- Métricas --- */
div[data-testid="stMetric"] {
    background-color: var(--bg-secondary);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius);
    padding: 1rem 1.25rem;
}
div[data-testid="stMetric"] label {
    color: var(--text-muted) !important;
    font-size: 0.75rem !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
    color: var(--text-primary) !important;
    font-weight: 700 !important;
    font-size: 1.6rem !important;
}

/* --- Dividers --- */
hr, div[data-testid="stDivider"] {
    border-color: var(--border-subtle) !important;
}

/* --- Contenedores con borde (cards) --- */
div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: var(--radius) !important;
    border-color: var(--border-subtle) !important;
    background-color: var(--bg-secondary) !important;
}

/* --- Expanders --- */
details[data-testid="stExpander"] {
    border: 1px solid var(--border-subtle) !important;
    border-radius: 8px !important;
    background-color: var(--bg-tertiary) !important;
}
details[data-testid="stExpander"] summary {
    color: var(--text-primary) !important;
    font-weight: 500 !important;
}

/* --- Captions --- */
.stCaption > p {
    color: var(--text-muted) !important;
    font-size: 0.85rem !important;
}

/* --- Scrollbar --- */
::-webkit-scrollbar       { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: var(--bg-secondary); }
::-webkit-scrollbar-thumb { background: var(--border-default); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }

/* --- Badges personalizados --- */
.badge {
    display: inline-block;
    padding: 0.2rem 0.65rem;
    border-radius: 6px;
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    font-family: 'Inter', sans-serif;
}
.badge-alta     { background: rgba(239,68,68,0.15);  color: #ef4444; }
.badge-media    { background: rgba(245,158,11,0.15); color: #f59e0b; }
.badge-baja     { background: rgba(34,197,94,0.15);  color: #22c55e; }
.badge-abierto  { background: rgba(59,130,246,0.15); color: #3b82f6; }
.badge-progreso { background: rgba(245,158,11,0.15); color: #f59e0b; }
.badge-resuelto { background: rgba(34,197,94,0.15);  color: #22c55e; }
.badge-success  { background: rgba(34,197,94,0.15);  color: #22c55e; }
.badge-fail     { background: rgba(239,68,68,0.15);  color: #ef4444; }

/* --- Utilidad: texto centrado --- */
.center-muted {
    text-align: center;
    color: var(--text-muted);
    padding: 3rem 0;
    font-size: 0.95rem;
}

/* --- Chat messages (AI Agent) --- */
div[data-testid="stChatMessage"] {
    border-radius: var(--radius) !important;
    border: 1px solid var(--border-subtle) !important;
    background-color: var(--bg-tertiary) !important;
    padding: 1rem 1.25rem !important;
}
div[data-testid="stChatMessage"] p {
    color: var(--text-secondary) !important;
    line-height: 1.6;
}

/* --- Spinner --- */
div[data-testid="stSpinner"] {
    color: var(--accent) !important;
}

/* --- Status widgets (log de ejecución MCP) --- */
div[data-testid="stStatusContainer"] {
    background-color: var(--bg-tertiary) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 8px !important;
    margin-bottom: 0.5rem !important;
}
div[data-testid="stStatusContainer"] summary {
    color: var(--text-primary) !important;
    font-weight: 500 !important;
}

/* --- Agent phase header --- */
.agent-phase-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin: 1.5rem 0 0.75rem 0;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--border-subtle);
}
.agent-phase-header h4 {
    margin: 0 !important;
    font-size: 0.95rem !important;
}
.agent-phase-header .phase-tag {
    font-size: 0.7rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
</style>
"""

# ============================================================================
# 3. CONFIGURACIÓN DE ENTORNO — Variables .env
# ============================================================================
load_dotenv(os.path.join(BASE_DIR, ".env"))

AGENT_API_URL     = os.getenv("AGENT_API_URL", "")
AGENT_API_KEY     = os.getenv("AGENT_API_KEY", "")
AGENT_MODEL_NAME  = os.getenv("AGENT_MODEL_NAME", "gpt-4o-mini")

SMTP_SENDER_EMAIL       = os.getenv("SMTP_SENDER_EMAIL", "")
SMTP_APP_PASSWORD       = os.getenv("SMTP_APP_PASSWORD", "")
NOTIFICATION_RECEIVER_EMAIL = os.getenv("NOTIFICATION_RECEIVER_EMAIL", "")


def is_agent_configured() -> bool:
    """Verifica que las variables de entorno del agente estén configuradas."""
    return bool(AGENT_API_URL and AGENT_API_KEY)


def is_smtp_configured() -> bool:
    """Verifica que las variables de entorno de SMTP estén configuradas."""
    return bool(SMTP_SENDER_EMAIL and SMTP_APP_PASSWORD and NOTIFICATION_RECEIVER_EMAIL)


# ============================================================================
# 4. BASE DE DATOS — SQLite (persistente, auto-creada)
# ============================================================================
DB_PATH = os.path.join(BASE_DIR, "tickets_soporte.db")


@contextmanager
def get_db():
    """Context manager para gestionar conexiones SQLite de forma segura."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    """Crea la tabla de tickets si no existe y migra esquemas previos."""
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tickets (
                id              TEXT PRIMARY KEY,
                titulo          TEXT NOT NULL,
                categoria       TEXT NOT NULL,
                prioridad       TEXT NOT NULL,
                descripcion     TEXT NOT NULL,
                estado          TEXT NOT NULL DEFAULT 'Abierto',
                respuesta_ia    TEXT,
                respuesta_agente TEXT,
                creado_en       TEXT NOT NULL
            )
            """
        )
        try:
            conn.execute(
                "ALTER TABLE tickets ADD COLUMN respuesta_agente TEXT"
            )
        except sqlite3.OperationalError:
            pass
        conn.commit()


def crear_ticket(titulo: str, categoria: str, prioridad: str, descripcion: str) -> str:
    """Inserta un nuevo ticket y retorna su ID generado."""
    ticket_id = datetime.now().strftime("%Y%m%d%H%M%S")
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO tickets
                (id, titulo, categoria, prioridad, descripcion, estado, creado_en)
            VALUES (?, ?, ?, ?, ?, 'Abierto', ?)
            """,
            (ticket_id, titulo, categoria, prioridad, descripcion,
             datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )
        conn.commit()
    return ticket_id


def obtener_tickets() -> list[dict]:
    """Retorna todos los tickets ordenados del más reciente al más antiguo."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM tickets ORDER BY creado_en DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def actualizar_estado(ticket_id: str, nuevo_estado: str) -> None:
    """Actualiza el estado de un ticket en la base de datos."""
    with get_db() as conn:
        conn.execute(
            "UPDATE tickets SET estado = ? WHERE id = ?",
            (nuevo_estado, ticket_id),
        )
        conn.commit()


def guardar_respuesta_ia(ticket_id: str, respuesta: str) -> None:
    """Persiste la respuesta generada por la IA para un ticket."""
    with get_db() as conn:
        conn.execute(
            "UPDATE tickets SET respuesta_ia = ? WHERE id = ?",
            (respuesta, ticket_id),
        )
        conn.commit()


def guardar_respuesta_agente(ticket_id: str, respuesta: str) -> None:
    """Persiste la respuesta generada por el multi-agente para un ticket."""
    with get_db() as conn:
        conn.execute(
            "UPDATE tickets SET respuesta_agente = ? WHERE id = ?",
            (respuesta, ticket_id),
        )
        conn.commit()


def contar_por_estado() -> dict[str, int]:
    """Retorna un diccionario {estado: cantidad} con los conteos agrupados."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT estado, COUNT(*) AS total FROM tickets GROUP BY estado"
        ).fetchall()
    return {r["estado"]: r["total"] for r in rows}


# ============================================================================
# 5. SOLUCIÓN PARCIAL ESTÁTICA — Fallback por palabras clave
# ============================================================================
def procesar_ticket_con_ia(descripcion: str, categoria: str = "") -> str:
    """Fallback: analiza palabras clave y genera una solución parcial sugerida."""
    texto = f"{categoria} {descripcion}".lower()

    if any(k in texto for k in [
        "cloud", "infra", "servidor", "deploy", "despliegue",
        "contenedor", "docker", "kubernetes", "k8s", "escalado",
    ]):
        return (
            "🔍 **Solución Parcial sugerida por IA:**\n\n"
            "1. Verificar logs del servidor: `tail -f /var/log/syslog`\n"
            "2. Comprobar estado de servicios: `systemctl status <servicio>`\n"
            "3. Revisar métricas de CPU / RAM en el panel de monitoreo\n"
            "4. Validar conectividad de red: `ping` y `traceroute`\n"
            "5. Verificar espacio en disco: `df -h`"
        )

    if any(k in texto for k in [
        "desarrollo", "código", "codigo", "repositorio", "git",
        "bug", "error", "build", "compil", "merge", "commit",
    ]):
        return (
            "🔍 **Solución Parcial sugerida por IA:**\n\n"
            "1. Revisar historial de commits: `git log --oneline -10`\n"
            "2. Verificar estado del build: `npm run build` / `pytest`\n"
            "3. Comprobar conflictos en ramas: `git status`\n"
            "4. Revisar cambios recientes: `git diff`\n"
            "5. Ejecutar tests locales antes de hacer push"
        )

    if any(k in texto for k in [
        "base de datos", "sql", "query", "consulta", "db",
        "índice", "indice", "transacción", "transaccion",
    ]):
        return (
            "🔍 **Solución Parcial sugerida por IA:**\n\n"
            "1. Verificar conexión a la base de datos\n"
            "2. Analizar queries lentas: `EXPLAIN ANALYZE <query>`\n"
            "3. Comprobar índices de las tablas afectadas\n"
            "4. Validar permisos del usuario de BD\n"
            "5. Revisar logs de transacciones"
        )

    if any(k in texto for k in [
        "red", "conexión", "conexion", "puerto", "firewall",
        "dns", "vpn", "latencia", "timeout",
    ]):
        return (
            "🔍 **Solución Parcial sugerida por IA:**\n\n"
            "1. Verificar conectividad: `ping <host>`\n"
            "2. Revisar puertos abiertos: `netstat -tulpn`\n"
            "3. Comprobar reglas de firewall: `iptables -L`\n"
            "4. Validar configuración DNS: `nslookup <dominio>`\n"
            "5. Revisar archivo hosts: `cat /etc/hosts`"
        )

    if any(k in texto for k in [
        "contraseña", "password", "login", "acceso", "permiso",
        "autenticación", "autenticacion", "token", "sesión", "sesion",
    ]):
        return (
            "🔍 **Solución Parcial sugerida por IA:**\n\n"
            "1. Verificar credenciales en el gestor de contraseñas\n"
            "2. Comprobar política de contraseñas (complejidad, expiración)\n"
            "3. Revisar logs de autenticación\n"
            "4. Validar permisos y roles del usuario\n"
            "5. Considerar restablecer la contraseña si es necesario"
        )

    return (
        "🔍 **Solución Parcial sugerida por IA:**\n\n"
        "1. Recopilar información adicional del problema\n"
        "2. Reproducir el escenario en un entorno de pruebas\n"
        "3. Revisar la documentación oficial del producto\n"
        "4. Consultar la base de conocimiento interna\n"
        "5. Escalar al equipo especializado si persiste el incidente"
    )


# ============================================================================
# 6. MCP — TOOL: get_ticket_handling_guidelines (base de conocimiento)
# ============================================================================
def get_ticket_handling_guidelines() -> str:
    """
    MCP Tool: lee guidelines.md desde la raíz del proyecto y retorna
    las políticas corporativas completas.
    """
    guidelines_path = os.path.join(BASE_DIR, "guidelines.md")
    try:
        with open(guidelines_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return (
            "# Directrices no disponibles\n"
            "No se encontró el archivo guidelines.md. "
            "Operar con políticas por defecto: tono profesional, "
            "pasos accionables numerados, empatía con el cliente."
        )


# ============================================================================
# 7. MCP — TOOLKITS SEPARADOS (Analyze vs Action)
# ============================================================================

# --- Toolkit MCP-Analyze: análisis, clasificación y documentación ---
MCP_ANALYZE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_ticket_handling_guidelines",
            "description": (
                "Obtiene las directrices y políticas corporativas de "
                "atención de tickets desde la base de conocimiento. "
                "Debe consultarse al inicio del análisis."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "summarize_ticket",
            "description": (
                "Genera un resumen ejecutivo conciso del problema "
                "reportado en el ticket. Devuelve un párrafo corto "
                "(máximo 2-3 frases) capturando el problema central."
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
            "description": (
                "Analiza el ticket y determina su categoría y nivel "
                "de prioridad. Devuelve un JSON con 'category' "
                "(Técnico, Facturación, Bug, Solicitud de feature) y "
                "'priority' (Alta, Media, Baja)."
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
                        "description": "Descripción detallada del problema",
                    },
                },
                "required": ["titulo", "descripcion"],
            },
        },
    },
]

# --- Toolkit MCP-Action: resolución y notificación ---
MCP_ACTION_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "propose_solution",
            "description": (
                "Genera una respuesta detallada y profesional para el "
                "cliente, utilizando como contexto el diagnóstico del "
                "Agente Analista (summary, category, priority) y las "
                "directrices corporativas (guidelines). La respuesta "
                "debe incluir saludo, resumen del problema, pasos "
                "accionables numerados y cierre."
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
                        "description": "Descripción del problema reportado",
                    },
                    "guidelines": {
                        "type": "string",
                        "description": (
                            "Directrices corporativas obtenidas por el "
                            "Agente Analista. OBLIGATORIO."
                        ),
                    },
                    "summary": {
                        "type": "string",
                        "description": "Resumen ejecutivo del análisis previo",
                    },
                    "category": {
                        "type": "string",
                        "description": "Categoría calculada por el análisis previo",
                    },
                    "priority": {
                        "type": "string",
                        "description": "Prioridad calculada por el análisis previo",
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
            "description": (
                "Envía una notificación por correo electrónico (Gmail "
                "SMTP) con el resumen, categoría, prioridad y "
                "respuesta propuesta. Debe llamarse después de generar "
                "la propuesta de solución."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string",
                        "description": "Resumen ejecutivo del problema",
                    },
                    "category": {
                        "type": "string",
                        "description": "Categoría calculada del ticket",
                    },
                    "priority": {
                        "type": "string",
                        "description": "Prioridad calculada del ticket",
                    },
                    "response": {
                        "type": "string",
                        "description": "Respuesta propuesta para el cliente",
                    },
                    "ticket_titulo": {
                        "type": "string",
                        "description": "Título del ticket (para el asunto)",
                    },
                },
                "required": ["summary", "category", "priority", "response"],
            },
        },
    },
]

# --- Mapeo de tools a información visual ---
TOOL_UI_INFO = {
    "get_ticket_handling_guidelines": {
        "icon": "🔍",
        "label": "Consultando directrices de documentación",
    },
    "summarize_ticket": {
        "icon": "📝",
        "label": "Generando resumen ejecutivo",
    },
    "categorize_ticket": {
        "icon": "🏷️",
        "label": "Clasificando ticket",
    },
    "propose_solution": {
        "icon": "💡",
        "label": "Generando propuesta de solución",
    },
    "notify_via_gmail": {
        "icon": "📧",
        "label": "Enviando notificación por correo",
    },
}


# ============================================================================
# 8. MCP — FUNCIONES EJECUTORAS DE CADA TOOL
# ============================================================================
def _llm_call(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.3,
    max_tokens: int = 512,
    json_mode: bool = False,
) -> str:
    """Helper: llamada enfocada al LLM para sub-tareas de tools."""
    client = OpenAI(base_url=AGENT_API_URL, api_key=AGENT_API_KEY)
    kwargs = {
        "model": AGENT_MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    completion = client.chat.completions.create(**kwargs)
    return completion.choices[0].message.content or ""


def tool_get_ticket_handling_guidelines() -> str:
    """Ejecuta la tool: lee guidelines.md y retorna las políticas."""
    return get_ticket_handling_guidelines()


def tool_summarize_ticket(titulo: str, descripcion: str) -> str:
    """Ejecuta la tool: genera un resumen ejecutivo via LLM."""
    try:
        return _llm_call(
            system_prompt=(
                "Eres un asistente que resume tickets de soporte técnico. "
                "Devuelve SOLO el resumen ejecutivo, un párrafo corto "
                "de máximo 2-3 frases capturando el problema central."
            ),
            user_prompt=(
                f"Título: {titulo}\n"
                f"Descripción: {descripcion}\n\n"
                f"Genera el resumen ejecutivo:"
            ),
            temperature=0.3,
            max_tokens=256,
        )
    except Exception as e:
        return f"Error al generar resumen: {str(e)}"


def tool_categorize_ticket(titulo: str, descripcion: str) -> dict:
    """Ejecuta la tool: categoriza y prioriza el ticket via LLM."""
    try:
        raw = _llm_call(
            system_prompt=(
                "Eres un clasificador de tickets de soporte. "
                "Devuelve SOLO un JSON válido: "
                '{"category": "<una de: Técnico, Facturación, Bug, '
                'Solicitud de feature>", "priority": "<una de: Alta, '
                'Media, Baja>"}. '
                "Alta = bloqueante/productivo detenido, "
                "Media = impacto parcial, Baja = cosmético/mejora."
            ),
            user_prompt=(
                f"Título: {titulo}\n"
                f"Descripción: {descripcion}\n\n"
                f"Clasifica este ticket:"
            ),
            temperature=0.2,
            max_tokens=128,
            json_mode=True,
        )
        return json.loads(raw)
    except (json.JSONDecodeError, Exception) as e:
        return {
            "category": "Técnico",
            "priority": "Media",
            "error": f"Fallback usado: {str(e)}",
        }


def tool_propose_solution(
    titulo: str,
    descripcion: str,
    guidelines: str,
    summary: str = "",
    category: str = "",
    priority: str = "",
) -> str:
    """
    Ejecuta la tool: genera respuesta al cliente usando el diagnóstico
    del Agente Analista (summary, category, priority) y las directrices
    corporativas (guidelines) como contexto.
    """
    try:
        context_parts = ["=== DIAGNÓSTICO DEL AGENTE ANALISTA ==="]
        if summary:
            context_parts.append(f"Resumen ejecutivo: {summary}")
        if category:
            context_parts.append(f"Categoría: {category}")
        if priority:
            context_parts.append(f"Prioridad: {priority}")
        context_parts.append("")
        context_parts.append("=== DIRECTRICES CORPORATIVAS (OBLIGATORIAS) ===")
        context_parts.append(guidelines)
        context_parts.append("")
        context_parts.append("=== TICKET ===")
        context_parts.append(f"Título: {titulo}")
        context_parts.append(f"Descripción: {descripcion}")
        context = "\n".join(context_parts)

        return _llm_call(
            system_prompt=(
                "Eres un especialista de soporte técnico senior. "
                "Genera una respuesta profesional para el cliente "
                "siguiendo ESTRICTAMENTE las directrices corporativas "
                "proporcionadas y utilizando el diagnóstico previo. "
                "La respuesta debe incluir: saludo, reconocimiento del "
                "problema, pasos accionables numerados y cierre. "
                "Adapta el tono según las directrices."
            ),
            user_prompt=f"{context}\n\nGenera la respuesta al cliente:",
            temperature=0.7,
            max_tokens=1024,
        )
    except Exception as e:
        return f"Error al generar propuesta: {str(e)}"


def tool_notify_via_gmail(
    summary: str,
    category: str,
    priority: str,
    response: str,
    ticket_titulo: str = "",
) -> dict:
    """Ejecuta la tool: envía notificación por Gmail SMTP."""
    return send_gmail_notification(
        summary=summary,
        category=category,
        priority=priority,
        response=response,
        ticket_titulo=ticket_titulo,
    )


# --- Dispatcher: ejecuta la tool según su nombre ---
def execute_tool(tool_name: str, args: dict) -> any:
    """Recibe el nombre de una tool y sus argumentos, ejecuta y retorna."""
    if tool_name == "get_ticket_handling_guidelines":
        return tool_get_ticket_handling_guidelines()
    elif tool_name == "summarize_ticket":
        return tool_summarize_ticket(
            args.get("titulo", ""),
            args.get("descripcion", ""),
        )
    elif tool_name == "categorize_ticket":
        return tool_categorize_ticket(
            args.get("titulo", ""),
            args.get("descripcion", ""),
        )
    elif tool_name == "propose_solution":
        return tool_propose_solution(
            args.get("titulo", ""),
            args.get("descripcion", ""),
            args.get("guidelines", ""),
            args.get("summary", ""),
            args.get("category", ""),
            args.get("priority", ""),
        )
    elif tool_name == "notify_via_gmail":
        return tool_notify_via_gmail(
            args.get("summary", ""),
            args.get("category", ""),
            args.get("priority", ""),
            args.get("response", ""),
            args.get("ticket_titulo", ""),
        )
    else:
        return {"error": f"Tool desconocida: {tool_name}"}


# ============================================================================
# 9. SYSTEM PROMPTS — Un prompt por cada agente especializado
# ============================================================================

SYSTEM_PROMPT_ANALYZE = """\
Eres un Agente Analista experto en Clasificación de Soporte. Tu único \
objetivo es entender e interpretar el ticket entrante.

Tienes acceso exclusivo al toolkit MCP-Analyze con las siguientes herramientas:

1. **get_ticket_handling_guidelines** — Consulta las directrices y políticas \
corporativas de atención de tickets.
2. **summarize_ticket** — Genera un resumen ejecutivo del problema.
3. **categorize_ticket** — Determina la categoría y prioridad del ticket.

FLUJO OBLIGATORIO:
1. Consulta las directrices con get_ticket_handling_guidelines.
2. Genera el resumen con summarize_ticket.
3. Clasifica el ticket con categorize_ticket.
4. Produce un mensaje final breve confirmando el diagnóstico completado.

IMPORTANTE:
- Tu salida será utilizada por otro agente (Agente Ejecutor) para generar \
la respuesta al cliente y enviar notificaciones.
- Asegúrate de que el diagnóstico sea completo y preciso.
- Consulta las directrices SIEMPRE, ya que el Agente Ejecutor las necesita.
- Llama las herramientas en el orden indicado.
"""


SYSTEM_PROMPT_ACTION = """\
Eres un Agente Ejecutor de Soporte. Tu objetivo es tomar el análisis \
estructurado de un ticket (producido por el Agente Analista) y proceder \
con la resolución y comunicación.

Tienes acceso exclusivo al toolkit MCP-Action con las siguientes herramientas:

1. **propose_solution** — Genera la respuesta profesional para el cliente. \
DEBES pasar como 'guidelines' el contenido de directrices obtenido por el \
Agente Analista. Pasa también 'summary', 'category' y 'priority' del \
diagnóstico previo.

2. **notify_via_gmail** — Envía la notificación por correo con todos los \
resultados. DEBES llamarla DESPUÉS de generar la propuesta de solución.

FLUJO OBLIGATORIO:
1. Genera la propuesta de solución con propose_solution, usando el \
diagnóstico previo y las directrices.
2. Envía la notificación con notify_via_gmail (summary, category, \
priority, response, ticket_titulo).
3. Produce un mensaje final confirmando la resolución completada.

REGLAS:
- Usa SIEMPRE el diagnóstico previo como contexto.
- Pasa las directrices (guidelines) a propose_solution.
- Notifica al finalizar.
- Llama las herramientas en el orden indicado.
"""


# ============================================================================
# 10. MULTI-AGENTE — HELPERS DE PAYLOAD Y VALIDACIÓN
# ============================================================================
def _build_analysis_payload(
    ticket_data: dict,
    analyze_tool_results: dict,
) -> dict:
    """
    Construye el payload estructurado que se pasa del Agent Analyze
    al Agent Action. Incluye el ticket original + los resultados del análisis.
    """
    payload = {
        "ticket_titulo": ticket_data.get("titulo", ""),
        "ticket_descripcion": ticket_data.get("descripcion", ""),
        "summary": "",
        "category": "",
        "priority": "",
        "guidelines": "",
    }

    # Summary
    summary = analyze_tool_results.get("summarize_ticket", "")
    if isinstance(summary, str):
        payload["summary"] = summary

    # Category & Priority
    cat_result = analyze_tool_results.get("categorize_ticket", {})
    if isinstance(cat_result, dict):
        payload["category"] = cat_result.get("category", "")
        payload["priority"] = cat_result.get("priority", "")
    elif isinstance(cat_result, str):
        try:
            parsed = json.loads(cat_result)
            payload["category"] = parsed.get("category", "")
            payload["priority"] = parsed.get("priority", "")
        except (json.JSONDecodeError, TypeError):
            pass

    # Guidelines
    guidelines = analyze_tool_results.get("get_ticket_handling_guidelines", "")
    if isinstance(guidelines, str):
        payload["guidelines"] = guidelines

    return payload


def _validate_analysis(payload: dict) -> tuple[bool, str]:
    """
    Valida que el payload del análisis tenga los campos requeridos
    antes de pasarlo al Agent Action.
    Returns: (is_valid, error_message)
    """
    missing = []
    if not payload.get("summary"):
        missing.append("summary")
    if not payload.get("category"):
        missing.append("category")
    if not payload.get("priority"):
        missing.append("priority")
    if not payload.get("guidelines"):
        missing.append("guidelines")

    if missing:
        return False, f"Campos faltantes en el análisis: {', '.join(missing)}"
    return True, ""


def _build_final_result(
    analyze_results: dict,
    action_results: dict,
    analyze_message: str,
    action_message: str,
    execution_log: list,
) -> dict:
    """Consolida los resultados de ambos agentes en un dict estructurado."""
    # From analyze
    summary = ""
    s = analyze_results.get("summarize_ticket", "")
    if isinstance(s, str):
        summary = s

    category = ""
    priority = ""
    cat = analyze_results.get("categorize_ticket", {})
    if isinstance(cat, dict):
        category = cat.get("category", "")
        priority = cat.get("priority", "")
    elif isinstance(cat, str):
        try:
            parsed = json.loads(cat)
            category = parsed.get("category", "")
            priority = parsed.get("priority", "")
        except (json.JSONDecodeError, TypeError):
            pass

    guidelines = ""
    g = analyze_results.get("get_ticket_handling_guidelines", "")
    if isinstance(g, str):
        guidelines = g

    # From action
    proposed_response = ""
    p = action_results.get("propose_solution", "")
    if isinstance(p, str):
        proposed_response = p

    email_result = {}
    e = action_results.get("notify_via_gmail", {})
    if isinstance(e, dict):
        email_result = e

    return {
        "summary": summary,
        "category": category,
        "priority": priority,
        "guidelines": guidelines,
        "proposed_response": proposed_response,
        "email_result": email_result,
        "agent_analyze_message": analyze_message,
        "agent_action_message": action_message,
        "execution_log": execution_log,
        "multi_agent": True,
    }


# ============================================================================
# 11. MULTI-AGENTE — LOOP GENÉRICO CON UI (reutilizable por ambos agentes)
# ============================================================================
def _run_agent_with_ui(
    system_prompt: str,
    user_message: str,
    tools: list[dict],
    agent_label: str,
    execution_log: list,
    step_offset: int = 0,
) -> tuple[dict, str, list, bool]:
    """
    ------------------------------------------------------------------
    Ejecuta un agente con tool calling y muestra st.status() por cada
    tool invocada. Función genérica reutilizable por ambos agentes.

    Returns:
        tool_results: dict {tool_name: result}
        final_message: str (mensaje final del agente)
        execution_log: list (log acumulado)
        success: bool
    ------------------------------------------------------------------
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    tool_results = {}
    agent_final_message = ""
    max_iterations = 8
    success = True

    try:
        client = OpenAI(base_url=AGENT_API_URL, api_key=AGENT_API_KEY)

        for iteration in range(max_iterations):
            # --- Llamada al LLM ---
            with st.status(
                f"🔄 {agent_label} — Iteración {iteration + 1}: "
                f"decidiendo qué herramientas llamar...",
                expanded=True,
            ) as iter_status:
                response = client.chat.completions.create(
                    model=AGENT_MODEL_NAME,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                    temperature=0.7,
                    max_tokens=1024,
                )

                message = response.choices[0].message

                tool_names = (
                    [tc.function.name for tc in message.tool_calls]
                    if message.tool_calls
                    else []
                )

                if tool_names:
                    st.write(
                        f"El agente decidió llamar: **{', '.join(tool_names)}**"
                    )
                else:
                    st.write(f"El agente completó su trabajo.")
                    iter_status.update(
                        label=f"✅ {agent_label} — Iteración {iteration + 1} completada",
                        state="complete",
                    )

            # --- Serializar mensaje del asistente ---
            assistant_msg = {
                "role": "assistant",
                "content": message.content or "",
            }
            if message.tool_calls:
                assistant_msg["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in message.tool_calls
                ]
            messages.append(assistant_msg)

            # --- Si no hay tool_calls, el agente terminó ---
            if not message.tool_calls:
                agent_final_message = message.content or ""
                execution_log.append({
                    "step": step_offset + iteration + 1,
                    "agent": agent_label,
                    "type": "final",
                    "message": f"{agent_label} completado",
                    "content": agent_final_message,
                })
                break

            # --- Ejecutar cada tool call ---
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                try:
                    args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    args = {}

                ui_info = TOOL_UI_INFO.get(
                    tool_name, {"icon": "⚙️", "label": tool_name}
                )
                icon = ui_info["icon"]
                label = ui_info["label"]

                # --- Status block para esta tool ---
                with st.status(
                    f"{icon} {label}...",
                    expanded=True,
                ) as tool_status:
                    if args:
                        st.caption("Parámetros de entrada:")
                        st.json(args)

                    result = execute_tool(tool_name, args)
                    tool_results[tool_name] = result

                    # Mostrar resultado
                    result_str = (
                        result if isinstance(result, str)
                        else json.dumps(result, ensure_ascii=False, indent=2)
                    )
                    if len(str(result_str)) > 1000:
                        st.caption("Resultado (truncado):")
                        st.text(str(result_str)[:1000] + "...")
                    else:
                        st.caption("Resultado:")
                        if isinstance(result, (dict, list)):
                            st.json(result)
                        else:
                            st.text(result)

                    tool_status.update(
                        label=f"{icon} {label} ✓",
                        state="complete",
                    )

                # Registrar en log
                execution_log.append({
                    "step": step_offset + iteration + 1,
                    "agent": agent_label,
                    "tool": tool_name,
                    "args": args,
                    "result": result,
                })

                # Alimentar resultado al LLM
                result_content = (
                    json.dumps(result, ensure_ascii=False)
                    if not isinstance(result, str)
                    else result
                )
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result_content,
                })

        # --- Mensaje final del agente ---
        if agent_final_message:
            with st.status(
                f"🤖 {agent_label} — Mensaje final",
                state="complete",
                expanded=False,
            ):
                st.write(agent_final_message)

    except Exception as e:
        with st.status(f"❌ Error en {agent_label}", state="error"):
            st.write(f"Error: {str(e)}")
        success = False

    return tool_results, agent_final_message, execution_log, success


# ============================================================================
# 12. MULTI-AGENTE — ORQUESTACIÓN CON UI (Agent Analyze → Agent Action)
# ============================================================================
def _run_multi_agent_with_ui(ticket_data: dict) -> dict | None:
    """
    ------------------------------------------------------------------
    Orquesta la ejecución secuencial de los dos agentes:

    1. Agent for Analyze (MCP-Analyze toolkit)
       → consulta guidelines, resume, categoriza
       → produce analysis_payload

    2. Validación del payload
       → si falla, Agent Action NO se ejecuta

    3. Agent for Action (MCP-Action toolkit)
       → recibe analysis_payload como contexto
       → propone solución, notifica por Gmail
       → produce resultado final

    Muestra el progreso de cada agente con st.status() en tiempo real.
    ------------------------------------------------------------------
    """
    if not is_agent_configured():
        return None

    execution_log = []
    ticket_titulo = ticket_data.get("titulo", "N/A")
    ticket_descripcion = ticket_data.get("descripcion", "N/A")

    # ================================================================
    # FASE 1: AI Agent for Analyze
    # ================================================================
    st.markdown(
        '<div class="agent-phase-header">'
        '<h4>🤖 Fase 1: AI Agent for Analyze</h4>'
        '<span class="phase-tag">Toolkit MCP-Analyze</span>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p style="color: var(--text-muted); font-size: 0.85rem; margin-bottom: 1rem;">'
        'El Agente Analista está interpretando el ticket...</p>',
        unsafe_allow_html=True,
    )

    analyze_user_msg = (
        f"Título del ticket: {ticket_titulo}\n"
        f"Categoría reportada: {ticket_data.get('categoria', 'N/A')}\n"
        f"Prioridad reportada: {ticket_data.get('prioridad', 'N/A')}\n"
        f"Estado: {ticket_data.get('estado', 'N/A')}\n"
        f"Descripción del problema:\n{ticket_descripcion}\n\n"
        f"Analiza este ticket utilizando las herramientas MCP-Analyze. "
        f"Sigue el flujo: consultar directrices, resumir y categorizar."
    )

    analyze_results, analyze_msg, execution_log, analyze_ok = \
        _run_agent_with_ui(
            system_prompt=SYSTEM_PROMPT_ANALYZE,
            user_message=analyze_user_msg,
            tools=MCP_ANALYZE_TOOLS,
            agent_label="Agent for Analyze",
            execution_log=execution_log,
            step_offset=0,
        )

    # --- Verificar que el agente analizó correctamente ---
    if not analyze_ok:
        st.error(
            "❌ **El Agente Analista falló.** "
            "El Agente Ejecutor NO se ejecutará para evitar operar "
            "con datos vacíos."
        )
        return {
            "error": "Agent for Analyze failed",
            "execution_log": execution_log,
        }

    # --- Construir y validar payload ---
    analysis_payload = _build_analysis_payload(ticket_data, analyze_results)
    is_valid, validation_msg = _validate_analysis(analysis_payload)

    if not is_valid:
        st.error(
            f"❌ **Análisis inválido.** {validation_msg}\n\n"
            f"El Agente Ejecutor NO se ejecutará."
        )
        return {
            "error": f"Invalid analysis: {validation_msg}",
            "execution_log": execution_log,
        }

    # --- Renderizar resultados del Analista ---
    st.markdown("")
    with st.container(border=True):
        st.markdown("##### 📋 Diagnóstico del Agente Analista")

        col_sum, col_cat, col_pri = st.columns([2, 1, 1])
        with col_sum:
            st.caption("Resumen ejecutivo")
            st.markdown(analysis_payload["summary"])
        with col_cat:
            st.caption("Categoría")
            cat = analysis_payload["category"]
            st.markdown(
                f'<span class="badge badge-abierto">📂 {cat}</span>',
                unsafe_allow_html=True,
            )
        with col_pri:
            st.caption("Prioridad")
            pri = analysis_payload["priority"]
            st.markdown(
                f"{badge_prioridad(pri)}",
                unsafe_allow_html=True,
            )

    # ================================================================
    # FASE 2: AI Agent for Action
    # ================================================================
    st.markdown("")
    st.markdown(
        '<div class="agent-phase-header">'
        '<h4>⚙️ Fase 2: AI Agent for Action</h4>'
        '<span class="phase-tag">Toolkit MCP-Action</span>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p style="color: var(--text-muted); font-size: 0.85rem; margin-bottom: 1rem;">'
        'El Agente Ejecutor está generando la solución y notificando...</p>',
        unsafe_allow_html=True,
    )

    action_user_msg = (
        f"=== DIAGNÓSTICO DEL AGENTE ANALISTA ===\n"
        f"Título del ticket: {analysis_payload['ticket_titulo']}\n"
        f"Descripción: {analysis_payload['ticket_descripcion']}\n"
        f"Resumen ejecutivo: {analysis_payload['summary']}\n"
        f"Categoría: {analysis_payload['category']}\n"
        f"Prioridad: {analysis_payload['priority']}\n\n"
        f"=== DIRECTRICES CORPORATIVAS ===\n"
        f"{analysis_payload['guidelines']}\n\n"
        f"Utiliza este diagnóstico para ejecutar las acciones necesarias. "
        f"Genera la propuesta de solución con propose_solution (pasa las "
        f"directrices como 'guidelines' y el summary, category, priority "
        f"del diagnóstico) y luego envía la notificación con "
        f"notify_via_gmail."
    )

    action_results, action_msg, execution_log, action_ok = \
        _run_agent_with_ui(
            system_prompt=SYSTEM_PROMPT_ACTION,
            user_message=action_user_msg,
            tools=MCP_ACTION_TOOLS,
            agent_label="Agent for Action",
            execution_log=execution_log,
            step_offset=100,
        )

    if not action_ok:
        st.error(
            "❌ **El Agente Ejecutor falló.** "
            "El diagnóstico del=Análisis está disponible arriba."
        )
        return _build_final_result(
            analyze_results, action_results,
            analyze_msg, action_msg, execution_log,
        )

    # --- Construir resultado final ---
    final_result = _build_final_result(
        analyze_results, action_results,
        analyze_msg, action_msg, execution_log,
    )

    # --- Renderizar Propuesta de Solución ---
    st.markdown("")
    with st.container(border=True):
        st.markdown("##### 💡 Propuesta de Solución Final")
        with st.chat_message("assistant"):
            st.markdown(final_result.get("proposed_response", "N/A"))

    # --- Renderizar badge de notificación ---
    email_info = final_result.get("email_result", {})
    st.markdown("")
    if email_info.get("success"):
        st.markdown(
            f'<div style="text-align: center; margin: 1rem 0;">'
            f'<span class="badge badge-success" '
            f'style="font-size: 0.85rem; padding: 0.4rem 1rem;">'
            f'✅ Notificación Enviada por Correo · '
            f'{email_info.get("timestamp", "")}'
            f'</span></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div style="text-align: center; margin: 1rem 0;">'
            f'<span class="badge badge-fail" '
            f'style="font-size: 0.85rem; padding: 0.4rem 1rem;">'
            f'❌ Notificación No Enviada · '
            f'{email_info.get("message", "Error desconocido")}'
            f'</span></div>',
            unsafe_allow_html=True,
        )

    return final_result


# ============================================================================
# 13. FALLBACK — AI Agent sin tool calling (JSON directo)
# ============================================================================
SYSTEM_PROMPT_FALLBACK = """Eres un Especialista de Soporte Técnico Senior. \
Analizarás un ticket y devolverás SIEMPRE un JSON válido:

{
  "summary": "<resumen ejecutivo, máximo 2-3 frases>",
  "category": "<una de: Técnico, Facturación, Bug, Solicitud de feature>",
  "priority": "<una de: Alta, Media, Baja>",
  "proposed_response": "<respuesta detallada con saludo, pasos numerados y cierre>"
}

NO incluyas texto fuera del JSON.
"""


def generate_ticket_response_fallback(ticket_data: dict) -> dict | None:
    """Fallback: genera respuesta estructurada sin tool calling."""
    if not is_agent_configured():
        return None

    user_message = (
        f"Título: {ticket_data.get('titulo', 'N/A')}\n"
        f"Categoría: {ticket_data.get('categoria', 'N/A')}\n"
        f"Prioridad: {ticket_data.get('prioridad', 'N/A')}\n"
        f"Descripción:\n{ticket_data.get('descripcion', 'N/A')}\n\n"
        f"Analiza y devuelve el JSON."
    )

    try:
        client = OpenAI(base_url=AGENT_API_URL, api_key=AGENT_API_KEY)
        completion = client.chat.completions.create(
            model=AGENT_MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_FALLBACK},
                {"role": "user", "content": user_message},
            ],
            temperature=0.7,
            max_tokens=1024,
            response_format={"type": "json_object"},
        )
        return json.loads(completion.choices[0].message.content)
    except (json.JSONDecodeError, Exception):
        return None


# ============================================================================
# 14. NOTIFICACIÓN SMTP — Envío de correo HTML vía Gmail
# ============================================================================
def send_gmail_notification(
    summary: str,
    category: str,
    priority: str,
    response: str,
    ticket_titulo: str = "",
) -> dict:
    """Envía notificación por correo HTML profesional vía Gmail SMTP."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not is_smtp_configured():
        return {
            "success": False,
            "message": "Falta configurar SMTP en el archivo .env",
            "timestamp": timestamp,
        }

    asunto = f"[Soporte AI] Nuevo Ticket - Prioridad {priority}: {category}"
    if ticket_titulo:
        asunto = f"[Soporte AI] {ticket_titulo} - Prioridad {priority}: {category}"

    html_body = f"""\
<html>
<body style="font-family: 'Inter', Arial, sans-serif; background-color: #0a0a0a; \
margin: 0; padding: 20px;">
  <div style="max-width: 600px; margin: 0 auto; background-color: #141414; \
  border: 1px solid #27272a; border-radius: 10px; padding: 24px;">

    <h2 style="color: #fafafa; margin: 0 0 16px 0; font-size: 1.3rem;">
      🛠️ Ticket Analizado · Multi-Agente MCP
    </h2>

    <div style="background-color: #1c1c1c; border-radius: 8px; padding: 16px; \
    margin-bottom: 16px;">
      <p style="color: #71717a; font-size: 0.75rem; text-transform: uppercase; \
      letter-spacing: 0.05em; margin: 0 0 4px 0;">Resumen</p>
      <p style="color: #a1a1aa; font-size: 0.9rem; line-height: 1.5; margin: 0;">
        {summary}
      </p>
    </div>

    <div style="display: flex; gap: 12px; margin-bottom: 16px;">
      <span style="background-color: rgba(59,130,246,0.15); color: #3b82f6; \
      padding: 4px 12px; border-radius: 6px; font-size: 0.75rem; font-weight: 600;">
        📂 {category}
      </span>
      <span style="background-color: rgba(245,158,11,0.15); color: #f59e0b; \
      padding: 4px 12px; border-radius: 6px; font-size: 0.75rem; font-weight: 600;">
        ⚡ {priority}
      </span>
    </div>

    <div style="background-color: #1c1c1c; border-radius: 8px; padding: 16px; \
    margin-bottom: 16px;">
      <p style="color: #71717a; font-size: 0.75rem; text-transform: uppercase; \
      letter-spacing: 0.05em; margin: 0 0 8px 0;">Respuesta Propuesta</p>
      <p style="color: #a1a1aa; font-size: 0.9rem; line-height: 1.6; margin: 0; \
      white-space: pre-wrap;">
        {response}
      </p>
    </div>

    <p style="color: #71717a; font-size: 0.75rem; margin: 0; text-align: center;">
      Generado por Multi-Agente MCP · {timestamp}
    </p>
  </div>
</body>
</html>
"""

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = asunto
        msg["From"] = SMTP_SENDER_EMAIL
        msg["To"] = NOTIFICATION_RECEIVER_EMAIL
        msg.attach(MIMEText(html_body, "html"))

        context = ssl.create_default_context()
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls(context=context)
            server.login(SMTP_SENDER_EMAIL, SMTP_APP_PASSWORD)
            server.sendmail(
                SMTP_SENDER_EMAIL, NOTIFICATION_RECEIVER_EMAIL, msg.as_string()
            )

        return {
            "success": True,
            "message": f"Notificación enviada a {NOTIFICATION_RECEIVER_EMAIL}",
            "timestamp": timestamp,
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Error al enviar correo: {str(e)}",
            "timestamp": timestamp,
        }


# ============================================================================
# 15. HELPERS DE UI — Badges visuales
# ============================================================================
def badge_prioridad(prioridad: str) -> str:
    """Genera el HTML de un badge coloreado para la prioridad."""
    cls = {
        "Alta":  "badge-alta",
        "Media": "badge-media",
        "Baja":  "badge-baja",
    }.get(prioridad, "badge-baja")
    return f'<span class="badge {cls}">{prioridad}</span>'


def badge_estado(estado: str) -> str:
    """Genera el HTML de un badge coloreado para el estado."""
    cls = {
        "Abierto":     "badge-abierto",
        "En Progreso": "badge-progreso",
        "Resuelto":    "badge-resuelto",
    }.get(estado, "badge-abierto")
    return f'<span class="badge {cls}">{estado}</span>'


# ============================================================================
# 16. VISTA A — Panel de Usuario (Reportar Problema)
# ============================================================================
def panel_usuario() -> None:
    """Formulario estilizado para que el usuario reporte un problema."""

    st.markdown("## 📝 Reportar Problema")
    st.markdown(
        '<p style="color: var(--text-muted); margin-bottom: 2rem;">'
        'Describe el problema que estás experimentando. El sistema lo '
        'procesará con el <strong>Multi-Agente MCP</strong> automáticamente.'
        '</p>',
        unsafe_allow_html=True,
    )

    with st.container():
        col_izq, col_der = st.columns([1.4, 1])

        with col_izq:
            titulo = st.text_input(
                "Título del problema",
                placeholder="Ej: Error 500 al acceder al dashboard",
            )
            categoria = st.selectbox(
                "Categoría",
                ["Desarrollo", "Cloud / Infraestructura", "Soporte Técnico"],
            )

        with col_der:
            st.markdown("&nbsp;", unsafe_allow_html=True)
            prioridad = st.radio(
                "Prioridad",
                ["Baja", "Media", "Alta"],
                horizontal=True,
            )

        descripcion = st.text_area(
            "Descripción detallada",
            placeholder=(
                "Describe el problema con el mayor detalle posible: "
                "pasos para reproducirlo, mensajes de error, contexto..."
            ),
            height=160,
        )

        st.markdown("")

        if st.button("Enviar Ticket", type="primary"):
            if not titulo.strip():
                st.toast("El título es obligatorio", icon="⚠️")
            elif not descripcion.strip():
                st.toast("La descripción es obligatoria", icon="⚠️")
            else:
                ticket_id = crear_ticket(
                    titulo.strip(), categoria, prioridad, descripcion.strip()
                )
                st.toast(f"Ticket #{ticket_id} creado correctamente", icon="✅")

    st.markdown("")
    st.markdown("---")
    st.markdown(
        '<p style="color: var(--text-muted); font-size: 0.8rem; text-align: center;">'
        'Flujo: <strong>Problema</strong> &nbsp;→&nbsp; '
        '<strong>Agent Analyze</strong> &nbsp;→&nbsp; '
        '<strong>Agent Action</strong> &nbsp;→&nbsp; '
        '<strong>Solución + Notificación</strong>'
        '</p>',
        unsafe_allow_html=True,
    )


# ============================================================================
# 17. VISTA B — Panel de Administración
# ============================================================================
def panel_admin() -> None:
    """Panel de administración con contadores, listado de tickets y gestión."""

    st.markdown("## 🎛️ Panel de Administración")
    st.markdown(
        '<p style="color: var(--text-muted); margin-bottom: 2rem;">'
        'Gestiona y da soporte a los tickets reportados por los usuarios.'
        '</p>',
        unsafe_allow_html=True,
    )

    conteos = contar_por_estado()
    abiertos  = conteos.get("Abierto", 0)
    progreso  = conteos.get("En Progreso", 0)
    resueltos = conteos.get("Resuelto", 0)
    total     = abiertos + progreso + resueltos

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total", total)
    with col2:
        st.metric("Abiertos", abiertos)
    with col3:
        st.metric("En Progreso", progreso)
    with col4:
        st.metric("Resueltos", resueltos)

    st.markdown("")
    st.markdown("---")

    tickets = obtener_tickets()

    if not tickets:
        st.markdown(
            '<div class="center-muted">📭 No hay tickets registrados.</div>',
            unsafe_allow_html=True,
        )
        return

    st.markdown(f"### 📋 Tickets ({len(tickets)})")
    st.markdown("")

    for ticket in tickets:
        _render_ticket_card(ticket)


def _render_ticket_card(ticket: dict) -> None:
    """
    Renderiza una tarjeta visual para un ticket individual.
    Incluye el Multi-Agente MCP con log de ejecución en tiempo real.
    """
    with st.container(border=True):
        # --- Cabecera ---
        col_header_izq, col_header_der = st.columns([4, 2])
        with col_header_izq:
            st.markdown(f"### #{ticket['id']} · {ticket['titulo']}")
        with col_header_der:
            st.markdown(
                f"<div style='text-align: right; padding-top: 0.35rem;'>"
                f"{badge_prioridad(ticket['prioridad'])} "
                f"&nbsp; {badge_estado(ticket['estado'])}"
                f"</div>",
                unsafe_allow_html=True,
            )

        st.markdown(
            f"<p style='color: var(--text-muted); font-size: 0.8rem; margin: 0.25rem 0 0 0;'>"
            f"📂 {ticket['categoria']} &nbsp;&nbsp;·&nbsp;&nbsp; 🕐 {ticket['creado_en']}"
            f"</p>",
            unsafe_allow_html=True,
        )

        st.markdown("")

        # --- Descripción ---
        st.markdown("**Descripción del problema:**")
        st.caption(ticket["descripcion"])

        st.markdown("")

        # --- Acciones ---
        col_accion_izq, col_accion_der = st.columns([1, 1])

        with col_accion_izq:
            estados = ["Abierto", "En Progreso", "Resuelto"]
            nuevo_estado = st.selectbox(
                "Cambiar estado",
                estados,
                index=estados.index(ticket["estado"]),
                key=f"estado_{ticket['id']}",
            )
            if nuevo_estado != ticket["estado"]:
                actualizar_estado(ticket["id"], nuevo_estado)
                st.toast(f"Estado actualizado a: {nuevo_estado}", icon="🔄")
                st.rerun()

        with col_accion_der:
            st.markdown("&nbsp;", unsafe_allow_html=True)
            if st.button(
                "🤖 Solución Parcial (IA)",
                key=f"ia_{ticket['id']}",
                use_container_width=True,
            ):
                if is_agent_configured():
                    with st.spinner("Generando solución parcial..."):
                        resultado = generate_ticket_response_fallback(ticket)
                    if resultado and "proposed_response" in resultado:
                        respuesta = resultado["proposed_response"]
                    else:
                        respuesta = procesar_ticket_con_ia(
                            ticket["descripcion"], ticket["categoria"]
                        )
                else:
                    respuesta = procesar_ticket_con_ia(
                        ticket["descripcion"], ticket["categoria"]
                    )
                guardar_respuesta_ia(ticket["id"], respuesta)
                st.toast("Solución parcial generada", icon="🤖")
                st.rerun()

        # --- Respuesta IA estática (si existe) ---
        if ticket["respuesta_ia"]:
            st.markdown("")
            with st.container(border=True):
                st.markdown("#### 🤖 Solución Parcial (IA)")
                st.markdown(ticket["respuesta_ia"])

        # --- Multi-Agente MCP ---
        st.markdown("")
        with st.expander("🤖 Multi-Agente MCP (Analyze → Action)", expanded=False):
            if not is_agent_configured():
                st.warning(
                    "El Multi-Agente no está configurado. Crea un archivo "
                    "`.env` con las variables `AGENT_API_URL`, "
                    "`AGENT_API_KEY` y `AGENT_MODEL_NAME`."
                )

            if st.button(
                "🚀 Ejecutar Multi-Agente",
                key=f"agente_{ticket['id']}",
                use_container_width=True,
            ):
                if not is_agent_configured():
                    st.warning(
                        "Falta configurar el archivo `.env` con las "
                        "variables del agente."
                    )
                else:
                    resultado = _run_multi_agent_with_ui(ticket)

                    if resultado and resultado.get("proposed_response"):
                        guardar_respuesta_agente(
                            ticket["id"],
                            json.dumps(resultado, ensure_ascii=False),
                        )
                        st.toast("Multi-Agente completado", icon="🤖")
                        st.rerun()
                    elif resultado and resultado.get("error"):
                        st.error(f"Error: {resultado['error']}")
                    else:
                        st.error(
                            "El Multi-Agente no pudo generar un resultado "
                            "válido. Verifica la configuración."
                        )

            # --- Mostrar resultado existente ---
            if ticket.get("respuesta_agente"):
                try:
                    agente_data = json.loads(ticket["respuesta_agente"])
                except (json.JSONDecodeError, TypeError):
                    agente_data = None

                if agente_data and agente_data.get("proposed_response"):
                    st.markdown("")

                    tab1, tab2, tab3, tab4 = st.tabs([
                        "📋 Diagnóstico (Analyze)",
                        "💬 Solución (Action)",
                        "📢 Notificación",
                        "📊 Log Multi-Agente",
                    ])

                    # --- Tab 1: Diagnóstico ---
                    with tab1:
                        st.markdown("**Resumen ejecutivo:**")
                        st.markdown(agente_data.get("summary", "N/A"))

                        st.markdown("")
                        st.markdown("**Categoría y prioridad:**")
                        col_cat, col_pri = st.columns(2)
                        with col_cat:
                            cat = agente_data.get("category", "N/A")
                            st.markdown(
                                f'<span class="badge badge-abierto">📂 {cat}</span>',
                                unsafe_allow_html=True,
                            )
                        with col_pri:
                            pri = agente_data.get("priority", "N/A")
                            st.markdown(
                                f"{badge_prioridad(pri)}",
                                unsafe_allow_html=True,
                            )

                        analyze_msg = agente_data.get(
                            "agent_analyze_message", ""
                        )
                        if analyze_msg:
                            st.markdown("")
                            st.markdown("**Mensaje del Agente Analista:**")
                            with st.chat_message("assistant"):
                                st.markdown(analyze_msg)

                    # --- Tab 2: Solución ---
                    with tab2:
                        with st.chat_message("assistant"):
                            st.markdown(
                                agente_data.get("proposed_response", "N/A")
                            )

                        action_msg = agente_data.get(
                            "agent_action_message", ""
                        )
                        if action_msg:
                            st.markdown("")
                            st.markdown("**Mensaje del Agente Ejecutor:**")
                            st.caption(action_msg)

                    # --- Tab 3: Notificación ---
                    with tab3:
                        email_info = agente_data.get("email_result", {})
                        if email_info.get("success"):
                            st.success(
                                f"✅ Notificación enviada a "
                                f"{NOTIFICATION_RECEIVER_EMAIL or 'correo'}\n\n"
                                f"🕐 {email_info.get('timestamp', '')}"
                            )
                        else:
                            msg = email_info.get(
                                "message",
                                "No se ha enviado notificación.",
                            )
                            st.error(f"❌ {msg}")

                    # --- Tab 4: Log ---
                    with tab4:
                        _render_execution_log(
                            agente_data.get("execution_log", [])
                        )


# ============================================================================
# 18. RENDERIZADO DEL LOG DE EJECUCIÓN MULTI-AGENTE
# ============================================================================
def _render_execution_log(execution_log: list) -> None:
    """Renderiza el log de ejecución guardado (visualización posterior)."""
    if not execution_log:
        st.caption("No hay log de ejecución disponible.")
        return

    current_agent = None

    for entry in execution_log:
        step = entry.get("step", "?")
        tool_name = entry.get("tool", "")
        entry_type = entry.get("type", "")
        agent = entry.get("agent", "")

        # --- Agent phase separator ---
        if agent and agent != current_agent:
            current_agent = agent
            st.markdown("")
            st.markdown(f"**{agent}**")

        if entry_type == "final":
            with st.status(
                f"✅ Paso {step}: {agent or 'Agente'} completado",
                state="complete",
                expanded=False,
            ):
                content = entry.get("content", "")
                if content:
                    st.write(content)
            continue

        ui_info = TOOL_UI_INFO.get(
            tool_name, {"icon": "⚙️", "label": tool_name}
        )
        icon = ui_info["icon"]
        label = ui_info["label"]

        with st.status(
            f"{icon} Paso {step}: {label} ✓",
            state="complete",
            expanded=False,
        ):
            args = entry.get("args", {})
            if args:
                st.caption("Parámetros:")
                st.json(args)

            result = entry.get("result", "")
            result_str = (
                result if isinstance(result, str)
                else json.dumps(result, ensure_ascii=False, indent=2)
            )
            if len(str(result_str)) > 1000:
                st.caption("Resultado (truncado):")
                st.text(str(result_str)[:1000] + "...")
            else:
                st.caption("Resultado:")
                if isinstance(result, (dict, list)):
                    st.json(result)
                else:
                    st.text(result)


# ============================================================================
# 19. FUNCIÓN PRINCIPAL
# ============================================================================
def main() -> None:
    """Inicializa la base de datos, aplica estilos y renderiza la vista."""

    init_db()
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("# 🛠️ Soporte Técnico")
        st.markdown(
            '<p style="color: var(--text-muted); font-size: 0.85rem; margin-top: -0.5rem;">'
            'Sistema Multi-Agente MCP</p>',
            unsafe_allow_html=True,
        )
        st.markdown("---")

        vista = st.radio(
            "Navegación",
            [
                "📝  Panel de Usuario",
                "🎛️  Panel de Administración",
            ],
            label_visibility="collapsed",
        )

        st.markdown("---")

        # --- Indicadores de configuración ---
        if is_agent_configured():
            st.markdown(
                '<p style="color: var(--success); font-size: 0.75rem;">'
                '● Multi-Agente: <strong>Activo</strong></p>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<p style="color: var(--danger); font-size: 0.75rem;">'
                '● Multi-Agente: <strong>No configurado</strong></p>',
                unsafe_allow_html=True,
            )

        if is_smtp_configured():
            st.markdown(
                '<p style="color: var(--success); font-size: 0.75rem;">'
                '● SMTP Gmail: <strong>Activo</strong></p>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<p style="color: var(--warning); font-size: 0.75rem;">'
                '● SMTP Gmail: <strong>No configurado</strong></p>',
                unsafe_allow_html=True,
            )

        st.markdown("---")
        st.markdown(
            '<p style="color: var(--text-muted); font-size: 0.75rem;">'
            '<strong>Agent Analyze</strong>: guidelines, summarize, categorize<br>'
            '<strong>Agent Action</strong>: propose, notify</p>',
            unsafe_allow_html=True,
        )

    if "Usuario" in vista:
        panel_usuario()
    else:
        panel_admin()


# ============================================================================
# PUNTO DE ENTRADA
# ============================================================================
if __name__ == "__main__":
    main()
