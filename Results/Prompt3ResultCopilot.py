"""
Workshop 03 — Agent Automation con Gmail
========================================
Aplicación web para la gestión de tickets de soporte técnico.
Flujo: Problema -> AI Agent (Summarize → Categorize → Propose → Notify) -> Solución + Notificación

Evolución: El AI Agent ejecuta un flujo completo de análisis ramificado en
4 acciones clave e integra el envío real de notificaciones por correo
electrónico a través de Gmail de manera secuencial.

Tecnologías: Python + Streamlit + SQLite + OpenAI API + smtplib (Gmail SMTP)
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

AGENT_API_URL = os.getenv("AGENT_API_URL", "")
AGENT_API_KEY = os.getenv("AGENT_API_KEY", "")
AGENT_MODEL_NAME = os.getenv("AGENT_MODEL_NAME", "")

# Variables SMTP para notificaciones por Gmail
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
            fecha_creacion TEXT NOT NULL,
            notify_status TEXT,
            notify_timestamp TEXT
        )
        """
    )
    # Migración: añadir columnas si la tabla ya existía sin ellas
    cursor.execute("PRAGMA table_info(tickets)")
    existing_cols = {row[1] for row in cursor.fetchall()}
    if "notify_status" not in existing_cols:
        cursor.execute("ALTER TABLE tickets ADD COLUMN notify_status TEXT")
    if "notify_timestamp" not in existing_cols:
        cursor.execute("ALTER TABLE tickets ADD COLUMN notify_timestamp TEXT")
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
    """Guarda el estado y la marca de tiempo de la notificación por correo."""
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
# AI Agent — Lógica del agente con LLM (API compatible con OpenAI)
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """Eres un Agente de Soporte Técnico Senior especializado en \
analizar tickets y generar respuestas automatizadas. Debes procesar el ticket \
y devolver EXCLUSIVAMENTE un objeto JSON válido con la siguiente estructura:

{
  "resumen": "Resumen ejecutivo del problema en un solo párrafo corto.",
  "categoria": "Una de: Técnico, Facturación, Bug, Solicitud de feature",
  "prioridad": "Una de: Alta, Media, Baja",
  "respuesta_propuesta": "Propuesta de respuesta detallada, clara y empática para el cliente."
}

Directrices:
1. Analiza el tono del ticket (urgente, frustrado, informativo) y responde con empatía.
2. Identifica el problema central basándote en el título, categoría, prioridad y descripción.
3. El resumen debe ser conciso (máximo 2-3 líneas).
4. La categoría debe clasificar el ticket entre: Técnico, Facturación, Bug, Solicitud de feature.
5. La prioridad debe reflejar la urgencia real: Alta, Media o Baja.
6. La respuesta propuesta debe ser clara, accionable y empática (máximo 300 palabras).
7. Devuelve SOLO el JSON, sin texto adicional, sin markdown, sin bloques de código.
"""


def is_agent_configured() -> bool:
    """Verifica si las variables de entorno del AI Agent están configuradas."""
    return bool(AGENT_API_URL and AGENT_API_KEY and AGENT_MODEL_NAME)


def is_smtp_configured() -> bool:
    """Verifica si las variables de entorno de SMTP están configuradas."""
    return bool(
        SMTP_SENDER_EMAIL
        and SMTP_APP_PASSWORD
        and NOTIFICATION_RECEIVER_EMAIL
    )


def generate_ticket_response(ticket_data: dict) -> dict | None:
    """
    Genera un análisis estructurado del ticket usando un LLM compatible con
    la API de OpenAI, devolviendo un JSON estricto con:
      - resumen
      - categoria
      - prioridad
      - respuesta_propuesta

    Parámetros:
        ticket_data (dict): Datos del ticket (titulo, categoria, prioridad,
                            descripcion, estado).

    Retorna:
        dict | None: Diccionario con el análisis del agente, o None si falla.
    """
    user_prompt = (
        f"Analiza el siguiente ticket de soporte técnico y devuelve el JSON:\n\n"
        f"**Título:** {ticket_data.get('titulo', 'N/A')}\n"
        f"**Categoría reportada:** {ticket_data.get('categoria', 'N/A')}\n"
        f"**Prioridad reportada:** {ticket_data.get('prioridad', 'N/A')}\n"
        f"**Estado:** {ticket_data.get('estado', 'N/A')}\n"
        f"**Descripción:** {ticket_data.get('descripcion', 'N/A')}\n"
    )

    try:
        client = OpenAI(
            base_url=AGENT_API_URL,
            api_key=AGENT_API_KEY,
        )

        response = client.chat.completions.create(
            model=AGENT_MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=600,
            response_format={"type": "json_object"},
        )

        raw_content = response.choices[0].message.content

        # Parsear el JSON estricto devuelto por el LLM
        try:
            result = json.loads(raw_content)
        except json.JSONDecodeError:
            # Intentar extraer JSON si el modelo lo envolvió en markdown
            import re
            json_match = re.search(r'\{.*\}', raw_content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                raise ValueError("El LLM no devolvió un JSON válido")

        # Validar que el JSON tenga las claves esperadas
        required_keys = {"resumen", "categoria", "prioridad", "respuesta_propuesta"}
        if not required_keys.issubset(result.keys()):
            missing = required_keys - result.keys()
            raise ValueError(f"JSON incompleto. Faltan claves: {missing}")

        return result

    except Exception as e:
        st.error(
            f"⚠️ **Error al conectar con el AI Agent:**\n\n"
            f"No se pudo generar el análisis automatizado. "
            f"Detalle: `{str(e)}`\n\n"
            f"Verifica la configuración del archivo `.env`."
        )
        return None


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

    if not is_smtp_configured():
        return {
            "success": False,
            "message": "SMTP no configurado. Faltan variables en .env.",
            "timestamp": timestamp,
        }

    subject = f"[Soporte AI] Nuevo Ticket - Prioridad {priority}: {category}"

    # Cuerpo HTML limpio y profesional
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
                margin: 0;
                color: #fafafa;
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
            .section {{
                margin-bottom: 1.5rem;
            }}
            .section-title {{
                font-size: 0.8rem;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                color: #737373;
                margin-bottom: 0.5rem;
            }}
            .section-content {{
                color: #a3a3a3;
                line-height: 1.6;
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
                <h1>🎫 Notificación de Soporte Automatizada</h1>
            </div>
            <div class="section">
                <span class="badge badge-priority">Prioridad: {priority}</span>
                <span class="badge badge-category">Categoría: {category}</span>
            </div>
            <div class="section">
                <div class="section-title">🧩 Resumen Ejecutivo</div>
                <div class="section-content">{summary}</div>
            </div>
            <div class="section">
                <div class="section-title">💡 Respuesta Propuesta</div>
                <div class="section-content">{response}</div>
            </div>
            <div class="footer">
                <p>Este correo fue generado automáticamente por el AI Agent de Soporte.</p>
                <p>Fecha: {timestamp}</p>
            </div>
        </div>
    </body>
    </html>
    """

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SMTP_SENDER_EMAIL
        msg["To"] = NOTIFICATION_RECEIVER_EMAIL
        msg.attach(MIMEText(html_body, "html"))

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
            "message": f"Error al enviar el correo: {str(e)}",
            "timestamp": timestamp,
        }


# ---------------------------------------------------------------------------
# Función Placeholder — Simulación de IA (Solución Parcial / Fallback)
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


def _render_priority_badge(priority: str) -> None:
    """Renderiza un badge visual para la prioridad usando st.markdown."""
    color_map = {
        "Alta": ("#ef4444", "rgba(239, 68, 68, 0.15)"),
        "Media": ("#f59e0b", "rgba(245, 158, 11, 0.15)"),
        "Baja": ("#22c55e", "rgba(34, 197, 94, 0.15)"),
    }
    fg, bg = color_map.get(priority, ("#a3a3a3", "rgba(163, 163, 163, 0.15)"))
    st.markdown(
        f'<span style="background-color:{bg}; color:{fg}; '
        f'padding:0.25rem 0.6rem; border-radius:999px; '
        f'font-size:0.75rem; font-weight:500;">{priority}</span>',
        unsafe_allow_html=True,
    )


def _render_category_badge(category: str) -> None:
    """Renderiza un badge visual para la categoría usando st.markdown."""
    st.markdown(
        f'<span style="background-color:rgba(59, 130, 246, 0.15); color:#3b82f6; '
        f'padding:0.25rem 0.6rem; border-radius:999px; '
        f'font-size:0.75rem; font-weight:500;">{category}</span>',
        unsafe_allow_html=True,
    )


def _render_agent_analysis_tabs(ticket: dict, analysis: dict) -> None:
    """
    Renderiza el análisis del AI Agent en pestañas organizadas:
      - Resumen y Categoría
      - Respuesta Propuesta
      - Envío de Alertas
    """
    resumen = analysis.get("resumen", "N/A")
    categoria = analysis.get("categoria", "N/A")
    prioridad = analysis.get("prioridad", "N/A")
    respuesta = analysis.get("respuesta_propuesta", "N/A")

    tab1, tab2, tab3 = st.tabs([
        "📋 Resumen y Categoría",
        "💡 Respuesta Propuesta",
        "📢 Envío de Alertas",
    ])

    # --- Tab 1: Resumen y Categoría ---
    with tab1:
        st.markdown("#### 🧩 Resumen Ejecutivo")
        st.markdown(
            f"<div style='color: #a3a3a3; padding: 0.75rem; "
            f"background-color: #1a1a1a; border-radius: 8px; "
            f"border: 1px solid #262626; margin-bottom: 1rem; line-height: 1.6;'>"
            f"{resumen}</div>",
            unsafe_allow_html=True,
        )

        st.markdown("#### 🏷️ Categorización")
        col_cat, col_pri = st.columns(2)
        with col_cat:
            st.markdown("**Categoría:**")
            _render_category_badge(categoria)
        with col_pri:
            st.markdown("**Prioridad:**")
            _render_priority_badge(prioridad)

    # --- Tab 2: Respuesta Propuesta ---
    with tab2:
        st.markdown("#### 💡 Respuesta Propuesta por la IA")
        with st.chat_message("assistant"):
            st.markdown(respuesta)

    # --- Tab 3: Envío de Alertas ---
    with tab3:
        st.markdown("#### 📢 Notificación por Correo Electrónico")

        notify_status = ticket.get("notify_status")
        notify_timestamp = ticket.get("notify_timestamp")

        if notify_status == "enviado":
            st.success(
                f"✅ Notificación enviada con éxito a "
                f"{NOTIFICATION_RECEIVER_EMAIL or 'N/A'} — {notify_timestamp or ''}"
            )
        elif notify_status == "error":
            st.error(
                f"❌ Error en el último intento de envío ({notify_timestamp or ''}). "
                f"Puedes reintentar con el botón de abajo."
            )
        else:
            if is_smtp_configured():
                st.info(
                    "ℹ️ No se ha enviado ninguna notificación aún para este ticket."
                )
            else:
                st.warning(
                    "⚠️ SMTP no configurado. Configura las variables "
                    "SMTP_SENDER_EMAIL, SMTP_APP_PASSWORD y "
                    "NOTIFICATION_RECEIVER_EMAIL en el archivo `.env`."
                )

        # Botón para reenviar la notificación
        if st.button(
            "📧 Reenviar Notificación",
            key=f"notify_{ticket['id']}",
            type="secondary",
            disabled=not is_smtp_configured(),
        ):
            with st.status(
                "Enviando alerta por correo electrónico...",
                expanded=False,
            ) as status:
                notify_result = send_gmail_notification(
                    summary=resumen,
                    category=categoria,
                    priority=prioridad,
                    response=respuesta,
                )
            if notify_result["success"]:
                update_ticket_notify_status(
                    ticket["id"], "enviado", notify_result["timestamp"]
                )
                status.update(
                    label=f"✅ {notify_result['message']}",
                    state="complete",
                )
            else:
                update_ticket_notify_status(
                    ticket["id"], "error", notify_result["timestamp"]
                )
                status.update(
                    label=f"❌ {notify_result['message']}",
                    state="error",
                )
            st.rerun()


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
                # Contenedor de IA — AI Agent Analysis
                with st.expander("🤖 AI Agent Analysis", expanded=False):
                    # Verificar configuración del .env
                    if not is_agent_configured():
                        st.warning(
                            "⚠️ El AI Agent no está configurado. "
                            "Falta configurar las variables de entorno en el archivo `.env` "
                            "(AGENT_API_URL, AGENT_API_KEY, AGENT_MODEL_NAME). "
                            "Se usará el modo fallback (palabras clave) mientras tanto."
                        )

                    # Mostrar análisis existente si la hay
                    existing_analysis = ticket.get("respuesta_ia", "")
                    if existing_analysis:
                        # Intentar parsear como JSON (Workshop 03)
                        analysis_data = None
                        try:
                            analysis_data = json.loads(existing_analysis)
                        except (json.JSONDecodeError, TypeError):
                            pass  # Es texto del Workshop 02 (fallback)

                        if analysis_data and isinstance(analysis_data, dict):
                            _render_agent_analysis_tabs(
                                ticket, analysis_data
                            )
                        else:
                            # Respuesta legacy (texto plano del Workshop 02)
                            with st.chat_message("assistant"):
                                st.markdown(existing_analysis)
                    else:
                        st.markdown(
                            "<p style='color: #737373;'>"
                            "No se ha generado un análisis aún. "
                            "Presiona el botón para que el AI Agent analice este ticket."
                            "</p>",
                            unsafe_allow_html=True,
                        )

                    # Botón para generar análisis con IA
                    if st.button(
                        "🤖 Analizar con AI Agent",
                        key=f"ia_{ticket['id']}",
                        type="secondary",
                    ):
                        if is_agent_configured():
                            # Usar el AI Agent con LLM (JSON estricto)
                            with st.spinner(
                                "El agente está analizando el ticket..."
                            ):
                                analysis = generate_ticket_response(ticket)

                            if analysis:
                                # Guardar el JSON como string
                                update_ticket_ia_response(
                                    ticket["id"], json.dumps(analysis, ensure_ascii=False)
                                )

                                # Enviar notificación por Gmail automáticamente
                                if is_smtp_configured():
                                    with st.status(
                                        "Enviando alerta por correo electrónico...",
                                        expanded=False,
                                    ) as status:
                                        notify_result = send_gmail_notification(
                                            summary=analysis.get("resumen", ""),
                                            category=analysis.get("categoria", ""),
                                            priority=analysis.get("prioridad", ""),
                                            response=analysis.get("respuesta_propuesta", ""),
                                        )
                                    if notify_result["success"]:
                                        update_ticket_notify_status(
                                            ticket["id"],
                                            "enviado",
                                            notify_result["timestamp"],
                                        )
                                        status.update(
                                            label=f"✅ {notify_result['message']}",
                                            state="complete",
                                        )
                                    else:
                                        update_ticket_notify_status(
                                            ticket["id"],
                                            "error",
                                            notify_result["timestamp"],
                                        )
                                        status.update(
                                            label=f"❌ {notify_result['message']}",
                                            state="error",
                                        )
                                else:
                                    st.warning(
                                        "⚠️ SMTP no configurado. "
                                        "No se pudo enviar la notificación por correo. "
                                        "Configura SMTP_SENDER_EMAIL, SMTP_APP_PASSWORD y "
                                        "NOTIFICATION_RECEIVER_EMAIL en el archivo `.env`."
                                    )

                                st.rerun()
                        else:
                            # Fallback: usar la función placeholder
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
            "Flujo: Problema → IA → Solución + Notificación<br/>"
            "AI Agent: " + ("✅ Configurado" if is_agent_configured() else "⚠️ No configurado") +
            "<br/>SMTP: " + ("✅ Configurado" if is_smtp_configured() else "⚠️ No configurado") +
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
