"""
============================================================================
 Sistema de Gestión de Tickets de Soporte Técnico
 Flujo: Problema -> Aplicación con IA -> Solución Parcial
----------------------------------------------------------------------------
 Stack:    Python 3.10+ · Streamlit · SQLite
 Autor:    Desarrollador Senior Full-Stack
 Estructura: Un único archivo (app.py)
============================================================================
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
# 1. CONFIGURACIÓN DE PÁGINA
# ============================================================================
st.set_page_config(
    page_title="Soporte Técnico · Gestión de Tickets",
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
</style>
"""

# ============================================================================
# 3. CONFIGURACIÓN DE ENTORNO — Variables .env para el AI Agent
# ============================================================================
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

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
DB_PATH = "tickets_soporte.db"


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
        # --- Migración: añadir columna si la tabla es anterior ---
        try:
            conn.execute(
                "ALTER TABLE tickets ADD COLUMN respuesta_agente TEXT"
            )
        except sqlite3.OperationalError:
            pass  # La columna ya existe
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
    ------------------------------------------------------------------
    Simula el procesamiento de un ticket con IA.
    Analiza palabras clave y genera una solución parcial sugerida.
    ------------------------------------------------------------------
    Arquitectura modular: reemplazar el cuerpo de esta función con la
    llamada a un LLM local (Ollama, LM Studio, vLLM, etc.) manteniendo
    la misma firma (descripcion, categoria) -> str.

    Ejemplo de integración futura con Ollama:

        import requests
        resp = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3",
                "prompt": f"Ticket: {descripcion}\\nCategoría: {categoria}\\n"
                          f"Sugiere una solución parcial técnica:",
                "stream": False,
            },
        )
        return resp.json()["response"]
    ------------------------------------------------------------------
    """
    texto = f"{categoria} {descripcion}".lower()

    # --- Cloud / Infraestructura ---
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

    # --- Desarrollo ---
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

    # --- Base de datos ---
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

    # --- Red / Conectividad ---
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

    # --- Autenticación / Acceso ---
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

    # --- Soporte Técnico genérico ---
    return (
        "🔍 **Solución Parcial sugerida por IA:**\n\n"
        "1. Recopilar información adicional del problema\n"
        "2. Reproducir el escenario en un entorno de pruebas\n"
        "3. Revisar la documentación oficial del producto\n"
        "4. Consultar la base de conocimiento interna\n"
        "5. Escalar al equipo especializado si persiste el incidente"
    )


# ============================================================================
# 6. AI AGENT — LLM compatible con OpenAI (4 subtareas: Summarize, Categorize, Propose, Notify)
# ============================================================================

# --- System Prompt robusto para el agente (salida JSON estricta) ---
SYSTEM_PROMPT = """Eres un Especialista de Soporte Técnico Senior con más de 10 años \
de experiencia. Analizarás un ticket de soporte y devolverás SIEMPRE un objeto JSON \
válido con la siguiente estructura exacta:

{
  "summary": "<resumen ejecutivo del problema en un solo párrafo corto, máximo 2-3 frases>",
  "category": "<una de: Técnico, Facturación, Bug, Solicitud de feature>",
  "priority": "<una de: Alta, Media, Baja>",
  "proposed_response": "<respuesta detallada, clara y empática para el cliente, \
con saludo, resumen del problema, pasos accionables numerados y cierre>"
}

Directrices:
1. Analiza el tono del ticket (frustrado, neutral, urgente) y ajusta la empatía.
2. El resumen debe capturar el problema central de forma concisa.
3. La categoría debe ser la más precisa según el contenido real del ticket.
4. La prioridad debe reflejar la urgencia real: Alta = bloqueante/productivo detenido, \
Media = impacto parcial, Baja = cosmético/mejora.
5. La respuesta propuesta debe ser profesional, accionable y con pasos concretos.
6. NO incluyas texto fuera del JSON. Devuelve SOLO el JSON.
"""


def generate_ticket_response(ticket_data: dict) -> dict | None:
    """
    ------------------------------------------------------------------
    AI Agent: analiza un ticket y genera una respuesta estructurada
    utilizando un LLM compatible con la API de OpenAI.
    ------------------------------------------------------------------
    Subtareas del agente:
      🧩 Summarize  — resumen ejecutivo del problema
      🏷️ Categorize — categoría y prioridad calculadas
      💡 Propose    — respuesta propuesta para el cliente
      (📢 Notify se ejecuta por separado vía send_gmail_notification)
    ------------------------------------------------------------------
    Args:
        ticket_data: dict con claves titulo, categoria, prioridad,
                     descripcion (y opcionalmente id, estado).
    Returns:
        dict con keys: summary, category, priority, proposed_response
        o None si ocurre un error.
    ------------------------------------------------------------------
    """
    if not is_agent_configured():
        return None

    user_message = (
        f"Título del ticket: {ticket_data.get('titulo', 'N/A')}\n"
        f"Categoría reportada: {ticket_data.get('categoria', 'N/A')}\n"
        f"Prioridad reportada: {ticket_data.get('prioridad', 'N/A')}\n"
        f"Estado: {ticket_data.get('estado', 'N/A')}\n"
        f"Descripción del problema:\n{ticket_data.get('descripcion', 'N/A')}\n\n"
        f"Analiza este ticket y devuelve el JSON con tu análisis."
    )

    try:
        client = OpenAI(
            base_url=AGENT_API_URL,
            api_key=AGENT_API_KEY,
        )
        completion = client.chat.completions.create(
            model=AGENT_MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.7,
            max_tokens=1024,
            response_format={"type": "json_object"},
        )
        raw = completion.choices[0].message.content
        result = json.loads(raw)
        return result

    except json.JSONDecodeError:
        return None
    except Exception:
        return None


# ============================================================================
# 6b. NOTIFICACIÓN SMTP — Envío de correo HTML vía Gmail
# ============================================================================

def send_gmail_notification(
    summary: str,
    category: str,
    priority: str,
    response: str,
    ticket_titulo: str = "",
) -> dict:
    """
    ------------------------------------------------------------------
    Envía una notificación por correo electrónico HTML profesional
    a través de Gmail SMTP (smtp.gmail.com:587 con TLS).
    ------------------------------------------------------------------
    Args:
        summary:       Resumen ejecutivo del problema.
        category:      Categoría calculada por el agente.
        priority:      Prioridad calculada por el agente.
        response:      Respuesta propuesta por la IA.
        ticket_titulo: Título del ticket (para el asunto).
    Returns:
        dict: {"success": bool, "message": str, "timestamp": str}
    ------------------------------------------------------------------
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

    # --- Construir cuerpo HTML ---
    html_body = f"""\
<html>
<body style="font-family: 'Inter', Arial, sans-serif; background-color: #0a0a0a; \
margin: 0; padding: 20px;">
  <div style="max-width: 600px; margin: 0 auto; background-color: #141414; \
  border: 1px solid #27272a; border-radius: 10px; padding: 24px;">

    <h2 style="color: #fafafa; margin: 0 0 16px 0; font-size: 1.3rem;">
      🛠️ Nuevo Ticket Analizado por AI Agent
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
      Generado automáticamente · {timestamp}
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
# 7. HELPERS DE UI — Badges visuales
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
# 8. VISTA A — Panel de Usuario (Reportar Problema)
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
        # --- Fila 1: Título + Categoría | Prioridad ---
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

        # --- Fila 2: Descripción ---
        descripcion = st.text_area(
            "Descripción detallada",
            placeholder=(
                "Describe el problema con el mayor detalle posible: "
                "pasos para reproducirlo, mensajes de error, contexto..."
            ),
            height=160,
        )

        st.markdown("")

        # --- Botón de envío ---
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

    # --- Pie informativo del flujo ---
    st.markdown("")
    st.markdown("---")
    st.markdown(
        '<p style="color: var(--text-muted); font-size: 0.8rem; text-align: center;">'
        'Flujo: <strong>Problema</strong> &nbsp;→&nbsp; '
        '<strong>Aplicación con IA</strong> &nbsp;→&nbsp; '
        '<strong>Solución Parcial</strong>'
        '</p>',
        unsafe_allow_html=True,
    )


# ============================================================================
# 9. VISTA B — Panel de Administración (Gestión y Soporte)
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

    # --- Contadores minimalistas ---
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

    # --- Listado de tickets ---
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
    Incluye badges, descripción, selector de estado y botón de IA.
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

        # --- Acciones: Cambiar estado | Procesar con IA ---
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
                "🤖 Procesar con IA",
                key=f"ia_{ticket['id']}",
                use_container_width=True,
            ):
                if is_agent_configured():
                    with st.spinner("El agente está analizando el ticket..."):
                        resultado = generate_ticket_response(ticket)
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

        # --- AI Agent Analysis (LLM) — 4 subtareas ---
        st.markdown("")
        with st.expander("🤖 AI Agent Analysis", expanded=False):
            if not is_agent_configured():
                st.warning(
                    "El AI Agent no está configurado. Crea un archivo `.env` "
                    "con las variables `AGENT_API_URL`, `AGENT_API_KEY` y "
                    "`AGENT_MODEL_NAME` para activarlo."
                )

            # --- Botón para ejecutar el análisis completo ---
            if st.button(
                "Analizar con AI Agent",
                key=f"agente_{ticket['id']}",
                use_container_width=True,
            ):
                if not is_agent_configured():
                    st.warning(
                        "Falta configurar el archivo `.env` con las variables "
                        "del AI Agent."
                    )
                else:
                    with st.spinner("El agente está analizando el ticket..."):
                        resultado = generate_ticket_response(ticket)

                    if resultado and "proposed_response" in resultado:
                        # --- 📢 Notify: enviar notificación por Gmail ---
                        email_result = {"success": False, "message": "", "timestamp": ""}
                        if is_smtp_configured():
                            with st.spinner("Enviando alerta por correo electrónico..."):
                                email_result = send_gmail_notification(
                                    summary=resultado.get("summary", ""),
                                    category=resultado.get("category", ""),
                                    priority=resultado.get("priority", ""),
                                    response=resultado.get("proposed_response", ""),
                                    ticket_titulo=ticket.get("titulo", ""),
                                )
                        else:
                            email_result = {
                                "success": False,
                                "message": "SMTP no configurado en .env",
                                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            }

                        # --- Persistir resultado completo (JSON) ---
                        resultado["email_result"] = email_result
                        guardar_respuesta_agente(
                            ticket["id"], json.dumps(resultado, ensure_ascii=False)
                        )
                        st.toast("Análisis del AI Agent completado", icon="🤖")
                        st.rerun()
                    else:
                        st.error(
                            "El agente no pudo generar un análisis válido. "
                            "Verifica la configuración del modelo o intenta nuevamente."
                        )

            # --- Mostrar resultado existente en tabs ---
            if ticket.get("respuesta_agente"):
                try:
                    agente_data = json.loads(ticket["respuesta_agente"])
                except (json.JSONDecodeError, TypeError):
                    agente_data = None

                if agente_data and "proposed_response" in agente_data:
                    st.markdown("")

                    tab1, tab2, tab3 = st.tabs([
                        "📋 Resumen y Categoría",
                        "💬 Respuesta Propuesta",
                        "📢 Envío de Alertas",
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

                    # --- Tab 2: Respuesta Propuesta ---
                    with tab2:
                        with st.chat_message("assistant"):
                            st.markdown(agente_data.get("proposed_response", "N/A"))

                    # --- Tab 3: Envío de Alertas ---
                    with tab3:
                        email_info = agente_data.get("email_result", {})
                        if email_info.get("success"):
                            st.success(
                                f"✅ Notificación enviada con éxito a "
                                f"{NOTIFICATION_RECEIVER_EMAIL or 'correo configurado'}\n\n"
                                f"🕐 {email_info.get('timestamp', '')}"
                            )
                        else:
                            msg = email_info.get("message", "No se ha enviado notificación.")
                            st.error(f"❌ {msg}")


# ============================================================================
# 10. FUNCIÓN PRINCIPAL — Punto de entrada
# ============================================================================
def main() -> None:
    """Inicializa la base de datos, aplica estilos y renderiza la vista activa."""

    # Inicializar base de datos
    init_db()

    # Inyectar CSS personalizado
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    # --- Barra lateral de navegación ---
    with st.sidebar:
        st.markdown("# 🛠️ Soporte Técnico")
        st.markdown(
            '<p style="color: var(--text-muted); font-size: 0.85rem; margin-top: -0.5rem;">'
            'Sistema de gestión de tickets</p>',
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
        st.markdown(
            '<p style="color: var(--text-muted); font-size: 0.75rem;">'
            'Flujo: Problema → IA → Solución Parcial</p>',
            unsafe_allow_html=True,
        )

    # --- Renderizar vista seleccionada ---
    if "Usuario" in vista:
        panel_usuario()
    else:
        panel_admin()


# ============================================================================
# PUNTO DE ENTRADA
# ============================================================================
if __name__ == "__main__":
    main()
