"""
============================================================================
 Sistema de Gestión de Tickets de Soporte Técnico — Workshop 02: AI Agent
 Flujo: Problema -> Aplicación con IA -> Solución Parcial -> Respuesta IA
----------------------------------------------------------------------------
 Stack:    Python 3.10+ · Streamlit · SQLite · OpenAI-compatible LLM
 Estructura: Un único archivo (app.py)
============================================================================
"""

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime

from dotenv import load_dotenv
import streamlit as st

# Cargar variables de entorno desde .env
load_dotenv()

# ============================================================================
# 1. CONFIGURACIÓN DE PÁGINA
# ============================================================================
st.set_page_config(
    page_title="Soporte Técnico · AI Agent",
    page_icon="🤖",
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
</style>
"""

# ============================================================================
# 3. BASE DE DATOS — SQLite (persistente, auto-creada)
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
    """Crea la tabla de tickets si no existe."""
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tickets (
                id           TEXT PRIMARY KEY,
                titulo       TEXT NOT NULL,
                categoria    TEXT NOT NULL,
                prioridad    TEXT NOT NULL,
                descripcion  TEXT NOT NULL,
                estado       TEXT NOT NULL DEFAULT 'Abierto',
                respuesta_ia TEXT,
                creado_en    TEXT NOT NULL
            )
            """
        )
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


def contar_por_estado() -> dict[str, int]:
    """Retorna un diccionario {estado: cantidad} con los conteos agrupados."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT estado, COUNT(*) AS total FROM tickets GROUP BY estado"
        ).fetchall()
    return {r["estado"]: r["total"] for r in rows}


# ============================================================================
# 4. MOTOR DE IA — Solución Parcial (placeholder modular)
# ============================================================================
def procesar_ticket_con_ia(descripcion: str, categoria: str = "") -> str:
    """
    Simula el procesamiento de un ticket con IA.
    Analiza palabras clave y genera una solución parcial sugerida.
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
# 5. AI AGENT — Integración con LLM compatible con OpenAI
# ============================================================================
# System Prompt robusto para el agente
SYSTEM_PROMPT = """Eres un Especialista de Soporte Técnico Senior con amplia experiencia \
en resolución de incidentes de TI. Tu objetivo es analizar tickets de soporte y generar \
respuestas claras, empáticas y accionables.

Cuando recibas un ticket, debes:

1. **Analizar el tono**: Determina si el usuario está frustrado, confundido o tranquilo. \
Ajusta el tono de tu respuesta para ser empático y profesional.

2. **Identificar el problema central**: Extrae el problema técnico real más allá de los \
síntomas descritos. Considera la categoría y prioridad del ticket.

3. **Estructurar la respuesta**:
   - Comienza con un reconocimiento empático del problema.
   - Proporciona un diagnóstico breve del problema identificado.
   - Lista pasos accionables numerados para resolver o mitigar el problema.
   - Si es necesario, incluye comandos o referencias técnicas específicas.
   - Termina con una oferta de asistencia adicional.

4. **Consideraciones**:
   - Sé conciso pero completo. No uses más de 200 palabras.
   - Usa formato Markdown para mejorar la legibilidad.
   - Si el problema es ambiguo, pide aclaración al usuario.
   - Mantén un tono profesional pero cercano en español.

Formato de salida:
- **Diagnóstico**: Breve análisis del problema.
- **Pasos recomendados**: Lista numerada de acciones.
- **Notas adicionales**: Cualquier contexto relevante.
"""


def _get_env_config() -> dict[str, str | None]:
    """Retorna la configuración del agente desde variables de entorno."""
    return {
        "api_url": os.getenv("AGENT_API_URL"),
        "api_key": os.getenv("AGENT_API_KEY"),
        "model": os.getenv("AGENT_MODEL_NAME", "gpt-4o-mini"),
    }


def _is_agent_configured() -> bool:
    """Verifica si las variables de entorno del agente están configuradas."""
    config = _get_env_config()
    return bool(config["api_url"] and config["api_key"])


def generate_ticket_response(ticket_data: dict) -> str:
    """
    Genera una respuesta automatizada para un ticket usando un LLM
    compatible con OpenAI.

    Args:
        ticket_data: Diccionario con los campos del ticket
            (titulo, categoria, prioridad, descripcion, estado, id).

    Returns:
        str: Respuesta generada por el LLM.

    Raises:
        RuntimeError: Si las variables de entorno no están configuradas.
        Exception: Si la llamada a la API falla.
    """
    from openai import OpenAI

    config = _get_env_config()

    if not config["api_url"] or not config["api_key"]:
        raise RuntimeError(
            "Variables de entorno no configuradas. "
            "Define AGENT_API_URL, AGENT_API_KEY y AGENT_MODEL_NAME en .env"
        )

    client = OpenAI(
        base_url=config["api_url"],
        api_key=config["api_key"],
    )

    # Construir el prompt del usuario con los datos del ticket
    user_prompt = (
        f"Analiza el siguiente ticket de soporte y genera una respuesta:\n\n"
        f"**ID del ticket:** {ticket_data.get('id', 'N/A')}\n"
        f"**Título:** {ticket_data.get('titulo', 'N/A')}\n"
        f"**Categoría:** {ticket_data.get('categoria', 'N/A')}\n"
        f"**Prioridad:** {ticket_data.get('prioridad', 'N/A')}\n"
        f"**Estado:** {ticket_data.get('estado', 'N/A')}\n"
        f"**Descripción del problema:**\n{ticket_data.get('descripcion', 'N/A')}\n\n"
        f"Genera una respuesta técnica estructurada y empática."
    )

    response = client.chat.completions.create(
        model=config["model"],
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
        max_tokens=500,
    )

    return response.choices[0].message.content


# ============================================================================
# 6. HELPERS DE UI — Badges visuales
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
# 7. VISTA A — Panel de Usuario (Reportar Problema)
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
        '<strong>Aplicación con IA</strong> &nbsp;→&nbsp; '
        '<strong>Solución Parcial</strong>'
        '</p>',
        unsafe_allow_html=True,
    )


# ============================================================================
# 8. VISTA B — Panel de Administración (Gestión y Soporte)
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

    # --- Advertencia si el agente no está configurado ---
    if not _is_agent_configured():
        st.warning(
            "⚠️ El AI Agent no está configurado. "
            "Crea un archivo `.env` con las variables `AGENT_API_URL`, "
            "`AGENT_API_KEY` y `AGENT_MODEL_NAME` para habilitar el análisis con IA.",
            icon="⚠️",
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
    Incluye badges, descripción, selector de estado, botón de IA placeholder
    y sección colapsable del AI Agent con LLM.
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

        # --- Acciones: Cambiar estado | Procesar con IA (placeholder) ---
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
                respuesta = procesar_ticket_con_ia(
                    ticket["descripcion"], ticket["categoria"]
                )
                guardar_respuesta_ia(ticket["id"], respuesta)
                st.toast("Respuesta de IA generada", icon="🤖")
                st.rerun()

        # --- Respuesta de IA placeholder (si existe) ---
        if ticket["respuesta_ia"]:
            st.markdown("")
            with st.container(border=True):
                st.markdown("#### 🤖 Solución Parcial (IA)")
                st.markdown(ticket["respuesta_ia"])

        # --- AI Agent Analysis (LLM) — Sección colapsable ---
        st.markdown("")
        with st.expander("🤖 AI Agent Analysis — Generar Respuesta con IA", expanded=False):
            st.markdown(
                '<p style="color: var(--text-muted); font-size: 0.85rem;">'
                'El AI Agent analizará este ticket y generará una respuesta '
                'automatizada usando un LLM compatible con OpenAI.'
                '</p>',
                unsafe_allow_html=True,
            )

            if not _is_agent_configured():
                st.warning(
                    "Configura las variables de entorno en `.env` para usar el AI Agent.",
                    icon="⚠️",
                )
            else:
                if st.button(
                    "Generar Respuesta con IA",
                    key=f"agent_{ticket['id']}",
                    type="secondary",
                    use_container_width=True,
                ):
                    try:
                        with st.spinner("El agente está analizando el ticket..."):
                            respuesta_agent = generate_ticket_response(ticket)
                        # Guardar la respuesta del agente en BD
                        guardar_respuesta_ia(ticket["id"], respuesta_agent)
                        st.toast("Respuesta del AI Agent generada", icon="🤖")

                        # Mostrar resultado en un contenedor destacado
                        with st.chat_message("assistant"):
                            st.markdown("### 🤖 Respuesta del AI Agent")
                            st.markdown("---")
                            st.markdown(respuesta_agent)
                    except RuntimeError as e:
                        st.error(f"Error de configuración: {e}")
                    except Exception as e:
                        st.error(
                            f"Error al conectar con el LLM: {e}\n\n"
                            "Verifica que `AGENT_API_URL` y `AGENT_API_KEY` "
                            "sean correctos y que el modelo esté disponible."
                        )

                # Mostrar respuesta guardada del agente si existe
                if ticket["respuesta_ia"]:
                    st.markdown("")
                    with st.chat_message("assistant"):
                        st.markdown("### 🤖 Respuesta guardada")
                        st.markdown("---")
                        st.markdown(ticket["respuesta_ia"])


# ============================================================================
# 9. FUNCIÓN PRINCIPAL — Punto de entrada
# ============================================================================
def main() -> None:
    """Inicializa la base de datos, aplica estilos y renderiza la vista activa."""

    init_db()
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    # --- Barra lateral de navegación ---
    with st.sidebar:
        st.markdown("# 🤖 Soporte Técnico · AI Agent")
        st.markdown(
            '<p style="color: var(--text-muted); font-size: 0.85rem; margin-top: -0.5rem;">'
            'Sistema de gestión de tickets con IA</p>',
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

        # --- Indicador de estado del AI Agent ---
        if _is_agent_configured():
            config = _get_env_config()
            st.markdown(
                '<p style="color: var(--success); font-size: 0.8rem;">'
                '✅ AI Agent configurado</p>',
                unsafe_allow_html=True,
            )
            st.caption(f"Modelo: `{config['model']}`")
        else:
            st.markdown(
                '<p style="color: var(--warning); font-size: 0.8rem;">'
                '⚠️ AI Agent no configurado</p>',
                unsafe_allow_html=True,
            )

        st.markdown("---")
        st.markdown(
            '<p style="color: var(--text-muted); font-size: 0.75rem;">'
            'Flujo: Problema → IA → Solución Parcial → AI Agent</p>',
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
