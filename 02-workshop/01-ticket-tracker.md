# Workshop 01 — Ticket Tracker

> Creación de la aplicación base de gestión de tickets de soporte técnico con Streamlit, estética minimalista y flujo Problema -> Aplicación con IA -> Solución Parcial

---

## Objetivo

Crear una aplicación web completa y funcional en un único archivo (`app.py`)
utilizando Streamlit para la gestión de tickets de soporte técnico. La aplicación
debe contar con una estética ultra-minimalista inspirada en Gemini/Vercel
(modo oscuro, tarjetas discretas, tipografía limpia), una base de datos local
persistente (SQLite o JSON), navegación por roles mediante la barra lateral
(Panel de Usuario y Panel de Administración) y una función placeholder
`procesar_ticket_con_ia(descripcion)` que simule la "Solución Parcial" del
flujo generando respuestas estáticas basadas en palabras clave del ticket.

---

## Requisitos

- Es necesario tener Python instalado en el entorno local
- Es necesario instalar Streamlit como dependencia principal
- No requiere haber ejecutado prompts previos (este es el prompt inicial de la evolución)

## Cómo usar este prompt

1. Copia el bloque de código siguiente completo.
2. Pégalo como prompt de tu agente de codigo
3. Una vez el agente genere el archivo `app.py`, instala las dependencias indicadas.
4. Levanta la aplicación local e interactúa con ambos paneles: reporta un ticket desde el Panel de Usuario y gestioná su estado desde el Panel de Administración.

---

## Prompt

```
Actúa como un desarrollador Senior Full-Stack experto en Python y diseño de interfaces de usuario (UI/UX) ultra-minimalistas. Necesito crear una aplicación web completa y funcional en un único archivo (`app.py`) utilizando Streamlit. La aplicación servirá para la gestión de tickets de soporte técnico y debe estructurarse estrictamente bajo el flujo: Problema -> Aplicación con IA -> Solución Parcial.

Requerimientos del Sistema:

1. Estética y Estilo Visual (Inspirado en Gemini/Vercel):
   - Configura la aplicación en modo 'wide' (`st.set_page_config`).
   - Aplica CSS personalizado para forzar un Modo Oscuro elegante (fondos oscuros profundos, bordes sutiles con tonalidades grises, tipografía sans-serif limpia y excelente espaciado/padding entre elementos).
   - Evita la saturación visual; usa contenedores ordenados (`st.container`) y tarjetas (`cards`) discretas para los datos.

2. Base de Datos Temporal:
   - Configura una base de datos local usando SQLite (o en su defecto un archivo JSON persistente) que se cree automáticamente si no existe. 
   - La tabla de tickets debe almacenar de forma persistente: ID, Título, Categoría, Prioridad, Descripción, Estado (Abierto, En Progreso, Resuelto) y un campo para la Respuesta de la IA.

3. Sistema de Navegación por Roles:
   - Implementa una barra lateral (`st.sidebar`) limpia y minimalista que permita al usuario alternar entre dos secciones o vistas independientes:
     A) "Panel de Usuario (Reportar Problema)"
     B) "Panel de Administración (Gestión y Soporte)"

4. Sección A: Panel de Usuario (Envío de Tickets)
   - Diseña un formulario estilizado para capturar el "Problema".
   - Campos de entrada: Título del problema, Categoría (Dropdown: Desarrollo, Cloud/Infraestructura, Soporte Técnico), Prioridad (Radio horizontal: Baja, Media, Alta) y Área de texto para la Descripción detallada.
   - Al hacer clic en "Enviar Ticket", la aplicación debe guardar el registro en la base de datos con el estado "Abierto" y mostrar una notificación de éxito limpia que desaparezca a los pocos segundos.

5. Sección B: Panel de Administración (/admin funcional)
   - Vista general: Muestra un contador minimalista con el total de tickets abiertos, en progreso y resueltos.
   - Listado de Gestión: Despliega los tickets en formato de lista usando tarjetas visuales (cards). Cada ticket debe mostrar toda su información detallada de manera organizada.
   - Interacción: 
     * Incluye un selector rápido para cambiar el Estado del ticket en tiempo real en la base de datos.
     * Contenedor de IA (Simulación del Flujo): Cada ticket debe incluir un apartado que ejecute una función placeholder llamada `procesar_ticket_con_ia(descripcion)`. Esta función debe simular la "Solución Parcial" del flujo, generando automáticamente una respuesta o sugerencia técnica estática basada en palabras clave del ticket (ej: si dice 'Cloud', sugerir revisar logs del servidor; si dice 'Desarrollo', sugerir revisar el repositorio). Deja el código modular y documentado para conectar fácilmente un LLM local en el futuro.

Por favor, genera el código completo, limpio, sin omisiones y listo para ejecutar, junto con los comandos necesarios para instalar dependencias y levantar el entorno local.
```

---
