"""
===========================================================================
 Sistema de Gestión de Tickets de Soporte Técnico
 Flujo: Problema -> AI Agent (MCP Tool Calling) -> Solución + Notificación
----------------------------------------------------------------------------
 Stack:    Python 3.10+ · Streamlit · SQLite · OpenAI-compatible LLM · MCP
 Arquitectura: Agente despachador con Tool Calling (function calling)
               Tools simuladas del lado del cliente (MCP server simulado)
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
    page_title="Soporte Técnico · Agente MCP",
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
</style>
"""

# ============================================================================
# 3. CONFIGURACIÓN DE ENTORNO — Variables .env para el AI Agent
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
    """Persiste la respuesta generada por el AI Agent (LLM) para un ticket."""
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
# 5. SOLUCIÓN PARCIAL ESTÁTICA — Análisis por palabras clave (fallback)
# ============================================================================
def procesar_ticket_con_ia(descripcion: str, categoria: str = "") -> str:
    """
    Simula el procesamiento de un ticket con IA (fallback cuando el agente
    MCP no está disponible). Analiza palabras clave y genera una solución
    parcial sugerida.
    """
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
# 6. MCP — TOOL: get_ticket_handling_guidelines
#    Lee el archivo guidelines.md (base de conocimiento estática)
# ============================================================================
def get_ticket_handling_guidelines() -> str:
    """
    ------------------------------------------------------------------
    MCP Tool: get_ticket_handling_guidelines
    Simula un servidor MCP que expone documentación estática como
    contexto para el agente. Lee guidelines.md desde la raíz del
    proyecto y retorna su contenido completo.
    ------------------------------------------------------------------
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
# 7. MCP — DEFINICIÓN DE TOOLS (OpenAI Function Calling Format)
# ============================================================================
MCP_TOOLS = [
    # --- Tool 1: Consultar directrices de documentación ---
    {
        "type": "function",
        "function": {
            "name": "get_ticket_handling_guidelines",
            "description": (
                "Obtiene las directrices y políticas corporativas de "
                "atención de tickets de soporte desde la base de "
                "conocimiento. DEBE consultarse obligatoriamente ANTES "
                "de proponer una solución al cliente para cumplir con "
                "las políticas de la empresa."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    # --- Tool 2: Resumir ticket ---
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
    # --- Tool 3: Categorizar ticket ---
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
    # --- Tool 4: Proponer solución ---
    {
        "type": "function",
        "function": {
            "name": "propose_solution",
            "description": (
                "Genera una respuesta detallada y profesional para el "
                "cliente, utilizando como contexto las directrices "
                "corporativas obtenidas previamente con "
                "get_ticket_handling_guidelines. La respuesta debe "
                "incluir saludo, resumen del problema, pasos "
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
                            "Directrices corporativas obtenidas de "
                            "get_ticket_handling_guidelines. "
                            "OBLIGATORIO para cumplir las políticas."
                        ),
                    },
                },
                "required": ["titulo", "descripcion", "guidelines"],
            },
        },
    },
    # --- Tool 5: Notificar vía Gmail ---
    {
        "type": "function",
        "function": {
            "name": "notify_via_gmail",
            "description": (
                "Envía una notificación por correo electrónico (Gmail "
                "SMTP) con el resumen, categoría, prioridad y "
                "respuesta propuesta. Debe llamarse al finalizar el "
                "análisis del ticket."
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

# --- Mapeo de tools a información visual para el log de ejecución ---
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
        "label": "Propuesta de solución",
    },
    "notify_via_gmail": {
        "icon": "📧",
        "label": "Enviando notificación",
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


def tool_propose_solution(titulo: str, descripcion: str, guidelines: str) -> str:
    """Ejecuta la tool: genera respuesta al cliente usando guidelines como contexto."""
    try:
        return _llm_call(
            system_prompt=(
                "Eres un especialista de soporte técnico senior. "
                "Genera una respuesta profesional para el cliente "
                "siguiendo ESTRICTAMENTE las directrices corporativas "
                "proporcionadas. La respuesta debe incluir: saludo, "
                "reconocimiento del problema, pasos accionables "
                "numerados y cierre. Adapta el tono según las "
                "directrices."
            ),
            user_prompt=(
                f"=== DIRECTRICES CORPORATIVAS (OBLIGATORIAS) ===\n"
                f"{guidelines}\n\n"
                f"=== TICKET ===\n"
                f"Título: {titulo}\n"
                f"Descripción: {descripcion}\n\n"
                f"Genera la respuesta al cliente cumpliendo las directrices:"
            ),
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
    """
    Recibe el nombre de una tool y sus argumentos (del LLM),
    ejecuta la función correspondiente y retorna el resultado.
    """
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
# 9. MCP — SYSTEM PROMPT DEL AGENTE DESPACHADOR
# ============================================================================
SYSTEM_PROMPT_MCP = """\
Eres un agente despachador de soporte técnico que utiliza el protocolo MCP \
(Model Context Protocol). Analizas el ticket recibido y decides qué \
herramientas (tools) llamar para procesarlo de manera completa.

FLUJO OBLIGATORIO — debes llamar las herramientas en este orden:

1. **get_ticket_handling_guidelines** — Consulta las directrices de \
documentación corporativa. Esto es OBLIGATORIO antes de proponer cualquier \
solución, para cumplir con las políticas de la empresa.

2. **summarize_ticket** — Genera un resumen ejecutivo del problema.

3. **categorize_ticket** — Determina la categoría y prioridad del ticket.

4. **propose_solution** — Genera la respuesta para el cliente. DEBES pasar \
como parámetro 'guidelines' el contenido exacto obtenido en el paso 1. \
Esto es crítico para cumplir las políticas corporativas.

5. **notify_via_gmail** — Envía la notificación por correo con todos los \
resultados obtenidos (summary, category, priority, response).

6. Finalmente, genera un mensaje breve confirmando que el análisis está \
completo y resumiendo lo realizado.

REGLAS:
- Consulta las directrices SIEMPRE antes de proponer la solución.
- Notifica al finalizar el análisis.
- Llama las herramientas en el orden indicado.
- Después de ejecutar todas las herramientas, produce un mensaje final.
"""


# ============================================================================
# 10. MCP — BUQUE DE EJECUCIÓN DEL AGENTE CON TOOL CALLING
# ============================================================================
def run_mcp_agent(ticket_data: dict) -> dict | None:
    """
    ------------------------------------------------------------------
    Ejecuta el agente despachador MCP con tool calling.

    Bucle:
      1. Enviar messages + tools al LLM
      2. Si el LLM retorna tool_calls → ejecutar cada tool
      3. Alimentar resultados de vuelta al LLM (role: "tool")
      4. Repetir hasta que el LLM responda sin tool_calls
      5. Construir resultado estructurado final

    Args:
        ticket_data: dict con titulo, categoria, prioridad, descripcion
    Returns:
        dict con summary, category, priority, proposed_response,
        email_result, execution_log, agent_final_message
        o None si ocurre un error fatal.
    ------------------------------------------------------------------
    """
    if not is_agent_configured():
        return None

    user_message = (
        f"Título del ticket: {ticket_data.get('titulo', 'N/A')}\n"
        f"Categoría reportada: {ticket_data.get('categoria', 'N/A')}\n"
        f"Prioridad reportada: {ticket_data.get('prioridad', 'N/A')}\n"
        f"Estado: {ticket_data.get('estado', 'N/A')}\n"
        f"Descripción del problema:\n"
        f"{ticket_data.get('descripcion', 'N/A')}\n\n"
        f"Analiza este ticket utilizando las herramientas MCP disponibles. "
        f"Sigue el flujo obligatorio: consultar directrices, resumir, "
        f"categorizar, proponer solución y notificar."
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_MCP},
        {"role": "user", "content": user_message},
    ]

    tool_results = {}
    execution_log = []
    max_iterations = 10
    agent_final_message = ""

    try:
        client = OpenAI(base_url=AGENT_API_URL, api_key=AGENT_API_KEY)

        for iteration in range(max_iterations):
            # --- Llamada al LLM con tools ---
            response = client.chat.completions.create(
                model=AGENT_MODEL_NAME,
                messages=messages,
                tools=MCP_TOOLS,
                tool_choice="auto",
                temperature=0.7,
                max_tokens=1024,
            )

            message = response.choices[0].message

            # --- Serializar mensaje del asistente para el historial ---
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
                    "step": iteration + 1,
                    "type": "final",
                    "message": "Agente completó el análisis",
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

                # Ejecutar tool
                result = execute_tool(tool_name, args)
                tool_results[tool_name] = result

                # Registrar en log
                log_entry = {
                    "step": iteration + 1,
                    "tool": tool_name,
                    "args": args,
                    "result": result,
                }
                execution_log.append(log_entry)

                # Alimentar resultado al LLM
                result_str = (
                    json.dumps(result, ensure_ascii=False)
                    if not isinstance(result, str)
                    else result
                )
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result_str,
                })

        # --- Construir resultado estructurado final ---
        return _build_final_result(tool_results, agent_final_message, execution_log)

    except Exception as e:
        return {
            "error": f"Error en el agente MCP: {str(e)}",
            "execution_log": execution_log,
        }


def _build_final_result(
    tool_results: dict,
    agent_final_message: str,
    execution_log: list,
) -> dict:
    """Consolida los resultados de las tools en un dict estructurado."""
    result = {
        "summary": "",
        "category": "",
        "priority": "",
        "proposed_response": "",
        "email_result": {},
        "agent_final_message": agent_final_message,
        "execution_log": execution_log,
    }

    # Summary
    summary = tool_results.get("summarize_ticket", "")
    if isinstance(summary, str):
        result["summary"] = summary

    # Category & Priority
    cat_result = tool_results.get("categorize_ticket", {})
    if isinstance(cat_result, dict):
        result["category"] = cat_result.get("category", "")
        result["priority"] = cat_result.get("priority", "")
    elif isinstance(cat_result, str):
        try:
            parsed = json.loads(cat_result)
            result["category"] = parsed.get("category", "")
            result["priority"] = parsed.get("priority", "")
        except (json.JSONDecodeError, TypeError):
            pass

    # Proposed response
    proposal = tool_results.get("propose_solution", "")
    if isinstance(proposal, str):
        result["proposed_response"] = proposal

    # Email result
    email = tool_results.get("notify_via_gmail", {})
    if isinstance(email, dict):
        result["email_result"] = email

    return result


# ============================================================================
# 11. FALLBACK — AI Agent sin tool calling (JSON directo)
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
    """Fallback: genera respuesta estructurada sin tool calling (JSON directo)."""
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
# 12. NOTIFICACIÓN SMTP — Envío de correo HTML vía Gmail
# ============================================================================
def send_gmail_notification(
    summary: str,
    category: str,
    priority: str,
    response: str,
    ticket_titulo: str = "",
) -> dict:
    """
    Envía una notificación por correo HTML profesional vía Gmail SMTP
    (smtp.gmail.com:587 con TLS).
    """
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
      🛠️ Nuevo Ticket Analizado por AI Agent (MCP)
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
      Generado automáticamente · MCP Agent · {timestamp}
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
# 13. HELPERS DE UI — Badges visuales
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
# 14. VISTA A — Panel de Usuario (Reportar Problema)
# ============================================================================
def panel_usuario() -> None:
    """Formulario estilizado para que el usuario reporte un problema."""

    st.markdown("## 📝 Reportar Problema")
    st.markdown(
        '<p style="color: var(--text-muted); margin-bottom: 2rem;">'
        'Describe el problema que estás experimentando. El sistema lo '
        'procesará y generará una <strong>solución parcial</strong> automáticamente.'
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
        '<strong>Agente MCP</strong> &nbsp;→&nbsp; '
        '<strong>Solución + Notificación</strong>'
        '</p>',
        unsafe_allow_html=True,
    )


# ============================================================================
# 15. VISTA B — Panel de Administración (Gestión y Soporte)
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
    Renderiza una tarjeta visual (card) para un ticket individual.
    Incluye badges, descripción, selector de estado, botón de IA estática
    y el AI Agent MCP con log de ejecución en tiempo real.
    """
    with st.container(border=True):
        # --- Cabecera: ID + Título | Badges ---
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

        # --- Meta: Categoría + Fecha ---
        st.markdown(
            f"<p style='color: var(--text-muted); font-size: 0.8rem; margin: 0.25rem 0 0 0;'>"
            f"📂 {ticket['categoria']} &nbsp;&nbsp;·&nbsp;&nbsp; 🕐 {ticket['creado_en']}"
            f"</p>",
            unsafe_allow_html=True,
        )

        st.markdown("")

        # --- Descripción del problema ---
        st.markdown("**Descripción del problema:**")
        st.caption(ticket["descripcion"])

        st.markdown("")

        # --- Acciones: Cambiar estado | Procesar con IA estática ---
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

        # --- Respuesta de IA estática (si existe) ---
        if ticket["respuesta_ia"]:
            st.markdown("")
            with st.container(border=True):
                st.markdown("#### 🤖 Solución Parcial (IA)")
                st.markdown(ticket["respuesta_ia"])

        # --- AI Agent MCP — Tool Calling ---
        st.markdown("")
        with st.expander("🤖 AI Agent MCP (Tool Calling)", expanded=False):
            if not is_agent_configured():
                st.warning(
                    "El AI Agent no está configurado. Crea un archivo `.env` "
                    "con las variables `AGENT_API_URL`, `AGENT_API_KEY` y "
                    "`AGENT_MODEL_NAME` para activarlo."
                )

            # --- Botón para ejecutar el agente MCP ---
            if st.button(
                "🚀 Ejecutar Agente MCP",
                key=f"agente_{ticket['id']}",
                use_container_width=True,
            ):
                if not is_agent_configured():
                    st.warning(
                        "Falta configurar el archivo `.env` con las variables "
                        "del AI Agent."
                    )
                else:
                    # --- Ejecutar agente y mostrar log en tiempo real ---
                    resultado = _run_mcp_agent_with_ui(ticket)

                    if resultado and resultado.get("proposed_response"):
                        guardar_respuesta_agente(
                            ticket["id"], json.dumps(resultado, ensure_ascii=False)
                        )
                        st.toast("Análisis MCP completado", icon="🤖")
                        st.rerun()
                    elif resultado and resultado.get("error"):
                        st.error(f"Error: {resultado['error']}")
                    else:
                        st.error(
                            "El agente MCP no pudo generar un análisis válido. "
                            "Verifica la configuración del modelo."
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
                        "📋 Resumen y Categoría",
                        "💬 Respuesta Propuesta",
                        "📢 Notificación",
                        "📊 Log de Ejecución MCP",
                    ])

                    # --- Tab 1: Resumen y Categoría ---
                    with tab1:
                        st.markdown("**Resumen ejecutivo:**")
                        st.markdown(agente_data.get("summary", "N/A"))

                        st.markdown("")
                        st.markdown("**Categoría y prioridad calculadas:**")
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

                        # Mensaje final del agente
                        final_msg = agente_data.get("agent_final_message", "")
                        if final_msg:
                            st.markdown("")
                            st.markdown("**Mensaje final del agente:**")
                            with st.chat_message("assistant"):
                                st.markdown(final_msg)

                    # --- Tab 2: Respuesta Propuesta ---
                    with tab2:
                        with st.chat_message("assistant"):
                            st.markdown(agente_data.get("proposed_response", "N/A"))

                    # --- Tab 3: Notificación ---
                    with tab3:
                        email_info = agente_data.get("email_result", {})
                        if email_info.get("success"):
                            st.success(
                                f"✅ Notificación enviada con éxito a "
                                f"{NOTIFICATION_RECEIVER_EMAIL or 'correo configurado'}\n\n"
                                f"🕐 {email_info.get('timestamp', '')}"
                            )
                        else:
                            msg = email_info.get(
                                "message", "No se ha enviado notificación."
                            )
                            st.error(f"❌ {msg}")

                    # --- Tab 4: Log de Ejecución MCP ---
                    with tab4:
                        _render_execution_log(
                            agente_data.get("execution_log", [])
                        )


def _run_mcp_agent_with_ui(ticket_data: dict) -> dict | None:
    """
    Ejecuta el agente MCP y muestra el log de ejecución en tiempo real
    usando st.status() para cada tool call.
    """
    st.markdown("#### 📊 Pasos del Agente MCP")
    st.markdown(
        '<p style="color: var(--text-muted); font-size: 0.8rem; margin-bottom: 1rem;">'
        'El agente está decidiendo qué herramientas llamar...'
        '</p>',
        unsafe_allow_html=True,
    )

    if not is_agent_configured():
        return None

    user_message = (
        f"Título del ticket: {ticket_data.get('titulo', 'N/A')}\n"
        f"Categoría reportada: {ticket_data.get('categoria', 'N/A')}\n"
        f"Prioridad reportada: {ticket_data.get('prioridad', 'N/A')}\n"
        f"Estado: {ticket_data.get('estado', 'N/A')}\n"
        f"Descripción del problema:\n"
        f"{ticket_data.get('descripcion', 'N/A')}\n\n"
        f"Analiza este ticket utilizando las herramientas MCP disponibles. "
        f"Sigue el flujo obligatorio: consultar directrices, resumir, "
        f"categorizar, proponer solución y notificar."
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_MCP},
        {"role": "user", "content": user_message},
    ]

    tool_results = {}
    execution_log = []
    max_iterations = 10
    agent_final_message = ""

    try:
        client = OpenAI(base_url=AGENT_API_URL, api_key=AGENT_API_KEY)

        for iteration in range(max_iterations):
            # --- Status: iteración del agente ---
            with st.status(
                f"🔄 Iteración {iteration + 1}: El agente está decidiendo...",
                expanded=True,
            ) as iter_status:
                response = client.chat.completions.create(
                    model=AGENT_MODEL_NAME,
                    messages=messages,
                    tools=MCP_TOOLS,
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
                        f"El agente decidió llamar: "
                        f"{', '.join(tool_names)}"
                    )
                else:
                    st.write("El agente completó el análisis.")
                    iter_status.update(
                        label=f"✅ Iteración {iteration + 1}: Análisis completado",
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

            # --- Si no hay tool_calls, terminó ---
            if not message.tool_calls:
                agent_final_message = message.content or ""
                execution_log.append({
                    "step": iteration + 1,
                    "type": "final",
                    "message": "Agente completó el análisis",
                    "content": agent_final_message,
                })
                break

            # --- Ejecutar cada tool call con st.status ---
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
                    # Mostrar parámetros
                    if args:
                        st.caption("Parámetros de entrada:")
                        st.json(args)

                    # Ejecutar tool
                    result = execute_tool(tool_name, args)
                    tool_results[tool_name] = result

                    # Mostrar resultado (truncado si es muy largo)
                    result_display = (
                        result if isinstance(result, str)
                        else json.dumps(result, ensure_ascii=False, indent=2)
                    )
                    if len(str(result_display)) > 1000:
                        st.caption("Resultado (truncado):")
                        st.text(str(result_display)[:1000] + "...")
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
                    "step": iteration + 1,
                    "tool": tool_name,
                    "args": args,
                    "result": result,
                })

                # Alimentar resultado al LLM
                result_str = (
                    json.dumps(result, ensure_ascii=False)
                    if not isinstance(result, str)
                    else result
                )
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result_str,
                })

        # --- Mensaje final del agente ---
        if agent_final_message:
            with st.status("🤖 Mensaje final del agente", state="complete"):
                st.write(agent_final_message)

        return _build_final_result(
            tool_results, agent_final_message, execution_log
        )

    except Exception as e:
        with st.status("❌ Error en el agente MCP", state="error"):
            st.write(f"Error: {str(e)}")
        return {
            "error": f"Error en el agente MCP: {str(e)}",
            "execution_log": execution_log,
        }


def _render_execution_log(execution_log: list) -> None:
    """Renderiza el log de ejecución MCP guardado (para visualización posterior)."""
    if not execution_log:
        st.caption("No hay log de ejecución disponible.")
        return

    for entry in execution_log:
        step = entry.get("step", "?")
        tool_name = entry.get("tool", "")
        entry_type = entry.get("type", "")

        if entry_type == "final":
            with st.status(
                f"✅ Paso {step}: Análisis completado",
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
            result_display = (
                result if isinstance(result, str)
                else json.dumps(result, ensure_ascii=False, indent=2)
            )
            if len(str(result_display)) > 1000:
                st.caption("Resultado (truncado):")
                st.text(str(result_display)[:1000] + "...")
            else:
                st.caption("Resultado:")
                if isinstance(result, (dict, list)):
                    st.json(result)
                else:
                    st.text(result)


# ============================================================================
# 16. FUNCIÓN PRINCIPAL — Punto de entrada
# ============================================================================
def main() -> None:
    """Inicializa la base de datos, aplica estilos y renderiza la vista activa."""

    init_db()
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("# 🛠️ Soporte Técnico")
        st.markdown(
            '<p style="color: var(--text-muted); font-size: 0.85rem; margin-top: -0.5rem;">'
            'Sistema de gestión de tickets · Agente MCP</p>',
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

        # --- Indicador de configuración ---
        if is_agent_configured():
            st.markdown(
                '<p style="color: var(--success); font-size: 0.75rem;">'
                '● Agente MCP: <strong>Activo</strong></p>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<p style="color: var(--danger); font-size: 0.75rem;">'
                '● Agente MCP: <strong>No configurado</strong></p>',
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
            'Flujo MCP: Ticket → Tools → Solución</p>',
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
