"""
Workshop 01 — Ticket Tracker
============================
Aplicación web para la gestión de tickets de soporte técnico.
Flujo: Problema -> Aplicación con IA -> Solución Parcial

Tecnologías: Python + Streamlit + SQLite
Estética: Ultra-minimalista inspirada en Gemini/Vercel (modo oscuro)
"""

import sqlite3
from datetime import datetime
from pathlib import Path

import streamlit as st

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
               respuesta_ia, fecha_creacion
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
# Función Placeholder — Simulación de IA (Solución Parcial)
# ---------------------------------------------------------------------------
def procesar_ticket_con_ia(descripcion: str) -> str:
    """
    Simula la 'Solución Parcial' del flujo generando una respuesta estática
    basada en palabras clave del ticket.

    Esta función está diseñada de forma modular para conectar fácilmente
    un LLM local en el futuro (ej: modelo de Huawei Cloud MaaS).

    Parámetros:
        descripcion (str): La descripción del problema reportado.

    Retorna:
        str: Una sugerencia técnica generada automáticamente.
    """
    descripcion_lower = descripcion.lower()

    # Diccionario de palabras clave -> sugerencias técnicas
    sugerencias = {
        "cloud": (
            "☁️ **Sugerencia Cloud/Infraestructura:**\n\n"
            "1. Verificar los logs del servidor en la consola de administración.\n"
            "2. Revisar el estado de los recursos (CPU, memoria, disco).\n"
            "3. Comprobar la conectividad de red y las reglas de firewall.\n"
            "4. Validar que las variables de entorno y credenciales estén configuradas correctamente."
        ),
        "servidor": (
            "🖥️ **Sugerencia de Servidor:**\n\n"
            "1. Revisar el estado del servicio con `systemctl status <servicio>`.\n"
            "2. Comprobar los logs en `/var/log/` para identificar errores recientes.\n"
            "3. Verificar el uso de recursos y reiniciar el servicio si es necesario."
        ),
        "desarrollo": (
            "💻 **Sugerencia de Desarrollo:**\n\n"
            "1. Revisar el repositorio de código en busca de cambios recientes (`git log`).\n"
            "2. Ejecutar las pruebas unitarias para identificar fallos.\n"
            "3. Verificar que las dependencias estén actualizadas (`pip freeze`).\n"
            "4. Comprobar la configuración del entorno de desarrollo local."
        ),
        "codigo": (
            "💻 **Sugerencia de Código:**\n\n"
            "1. Revisar el stack trace del error para identificar la línea problemática.\n"
            "2. Verificar la lógica del código afectado.\n"
            "3. Ejecutar un linter para detectar problemas de sintaxis."
        ),
        "red": (
            "🌐 **Sugerencia de Red:**\n\n"
            "1. Verificar la conectividad con `ping` y `traceroute`.\n"
            "2. Revisar la configuración DNS (`nslookup`).\n"
            "3. Comprobar los puertos abiertos con `netstat` o `ss`.\n"
            "4. Validar las reglas de enrutamiento y proxy."
        ),
        "conexion": (
            "🌐 **Sugerencia de Conexión:**\n\n"
            "1. Verificar que el endpoint esté disponible.\n"
            "2. Comprobar credenciales y tokens de autenticación.\n"
            "3. Revisar timeouts y reintentos en la configuración."
        ),
        "db": (
            "🗄️ **Sugerencia de Base de Datos:**\n\n"
            "1. Verificar la conexión a la base de datos.\n"
            "2. Revisar las consultas recientes en busca de bloqueos (`SHOW PROCESSLIST`).\n"
            "3. Comprobar el espacio en disco y los índices.\n"
            "4. Validar los backups más recientes."
        ),
        "database": (
            "🗄️ **Sugerencia de Base de Datos:**\n\n"
            "1. Verificar la conexión a la base de datos.\n"
            "2. Revisar las consultas recientes en busca de bloqueos.\n"
            "3. Comprobar el espacio en disco y los índices.\n"
            "4. Validar los backups más recientes."
        ),
        "auth": (
            "🔐 **Sugerencia de Autenticación:**\n\n"
            "1. Verificar que las credenciales sean correctas.\n"
            "2. Comprobar la expiración del token o sesión.\n"
            "3. Revisar los logs de autenticación para intentos fallidos.\n"
            "4. Validar la configuración de OAuth/SAML si aplica."
        ),
        "login": (
            "🔐 **Sugerencia de Login:**\n\n"
            "1. Verificar usuario y contraseña.\n"
            "2. Comprobar si la cuenta está bloqueada o deshabilitada.\n"
            "3. Revisar la configuración del proveedor de identidad."
        ),
        "error": (
            "⚠️ **Sugerencia de Error General:**\n\n"
            "1. Capturar el stack trace completo del error.\n"
            "2. Reproducir el escenario en un entorno de pruebas.\n"
            "3. Revisar la documentación oficial del componente afectado.\n"
            "4. Buscar el código de error en la base de conocimiento."
        ),
        "rendimiento": (
            "⚡ **Sugerencia de Rendimiento:**\n\n"
            "1. Monitorear el uso de CPU, memoria y I/O.\n"
            "2. Identificar cuellos de botella con herramientas de profiling.\n"
            "3. Revisar consultas o procesos costosos.\n"
            "4. Considerar escalado horizontal o vertical."
        ),
        "performance": (
            "⚡ **Sugerencia de Performance:**\n\n"
            "1. Monitorear el uso de recursos.\n"
            "2. Identificar cuellos de botella con profiling.\n"
            "3. Optimizar consultas y procesos costosos."
        ),
        "seguridad": (
            "🛡️ **Sugerencia de Seguridad:**\n\n"
            "1. Revisar los permisos y roles del usuario afectado.\n"
            "2. Comprobar los logs de auditoría.\n"
            "3. Verificar la configuración de cifrado y certificados.\n"
            "4. Escalar al equipo de seguridad si es un incidente crítico."
        ),
    }

    # Buscar la primera palabra clave que coincida
    for keyword, sugerencia in sugerencias.items():
        if keyword in descripcion_lower:
            return sugerencia

    # Respuesta por defecto si no hay coincidencias
    return (
        "📋 **Sugerencia General:**\n\n"
        "1. Recopilar información adicional sobre el problema.\n"
        "2. Reproducir el escenario en un entorno controlado.\n"
        "3. Documentar los pasos para reproducir el issue.\n"
        "4. Escalar al equipo correspondiente si persiste el problema."
    )


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
                # Contenedor de IA — Simulación del flujo
                with st.expander("🤖 Solución Parcial (IA)", expanded=False):
                    if ticket["respuesta_ia"]:
                        st.markdown(ticket["respuesta_ia"])
                    else:
                        st.markdown(
                            "<p style='color: #737373;'>"
                            "No se ha generado una sugerencia aún."
                            "</p>",
                            unsafe_allow_html=True,
                        )

                    if st.button(
                        "Generar sugerencia con IA",
                        key=f"ia_{ticket['id']}",
                        type="secondary",
                    ):
                        respuesta = procesar_ticket_con_ia(ticket["descripcion"])
                        update_ticket_ia_response(ticket["id"], respuesta)
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
        st.markdown(
            "<p style='color: #737373; font-size: 0.75rem;'>"
            "Flujo: Problema → Aplicación con IA → Solución Parcial"
            "</p>",
            unsafe_allow_html=True,
        )

    # Renderizar la vista seleccionada
    if vista == "Panel de Usuario (Reportar Problema)":
        panel_usuario()
    else:
        panel_administracion()


if __name__ == "__main__":
    main()
