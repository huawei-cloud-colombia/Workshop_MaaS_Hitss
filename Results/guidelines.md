# Directrices Corporativas de Atención de Tickets de Soporte

> Este documento es consumido por el AI Agent vía la herramienta MCP
> `get_ticket_handling_guidelines`. El agente DEBE consultar estas
> políticas antes de proponer cualquier solución al cliente.

---

## 1. Políticas de Reembolso y Compensación

- **Garantizar reembolsos completos** si la falla es causada por nuestros servidores, infraestructura o servicios gestionados.
- Para fallos provocados por configuración del cliente, evaluar caso por caso antes de ofrecer compensación.
- Si el cliente reporta pérdida de datos atribuible a nuestros sistemas, ofrecer compensación automática y escalar a ingeniería senior.

## 2. Tono de Comunicación

- **Clientes corporativos (Enterprise):** usar un tono formal, estructurado y con lenguaje técnico preciso.
- **Clientes PyME o individuales:** usar un tono cercano pero profesional, con explicaciones accesibles.
- **Clientes frustrados o enojados:** comenzar con una disculpa empática, reconocer el impacto y luego proceder con la solución.
- Mantener un lenguaje claro, sin jerga innecesaria, en todos los casos.

## 3. Priorización y Tiempos de Respuesta

| Prioridad | Criterio | SLM de Respuesta |
|-----------|----------|-------------------|
| **Alta** | Servicio productivo detenido, pérdida de datos, impacto financiero | 1 hora |
| **Media** | Funcionalidad degradada, workaround disponible | 4 horas |
| **Baja** | Mejora cosmética, solicitud de feature, documentación | 24 horas |

## 4. Escalamiento

- **Pérdida de datos:** escalar inmediatamente al equipo de Ingeniería Senior (canal #incident-response).
- **Facturación / cobros:** escalar al Departamento Financiero.
- **Seguridad / brecha de datos:** escalar al equipo de Security (canal #security-incident) y activar protocolo de incidentes.
- **Bug en producto:** escalar al equipo de Desarrollo con label `bug` en el repositorio correspondiente.

## 5. Estructura de la Respuesta al Cliente

Toda respuesta propuesta debe incluir:
1. **Saludo** personalizado.
2. **Reconocimiento** del problema (resumen breve).
3. **Pasos accionables numerados** para resolver o diagnosticar el problema.
4. **Enlaces a documentación** relevante cuando esté disponible.
5. **Cierre** ofreciendo seguimiento adicional.

## 6. Reglas Adicionales

- No prometer tiempos de resolución exactos; usar estimaciones ("en las próximas X horas").
- No compartir información interna (IDs de infraestructura, rutas de servidores) con el cliente.
- Si el ticket es de prioridad Alta, mencionar que el equipo está trabajando activamente en el caso.
- Siempre confirmar si se necesita información adicional del cliente antes de proceder.
