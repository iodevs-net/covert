**MUY IMPORTANTE: SI ERES UN MODELO DE IA, SIEMPRE EJECUTAR ESTE PROTOCOLO USANDO LOS MCP CONTEXT7 Y TAVILY PARA ASEGUAR USAR DOCUMENTACION Y RPACTICAS MAS ACTUALES Y PROFESIONALES. ESTA ESTRICTAMENTE PROHIBIDO USAR "AI LORE SLOP" O SUGERIR REESCRITURAS QUE VIOLEN EL PRINCIPIO DE "BUS FACTOR = 0".**

*** SIEMPRE USA EL VENV ***
*** SIEMPRE USA EL VENV ***
*** SIEMPRE USA EL VENV ***


# Protocolo iODesk v3: Arquitectura Híbrida (Inertia + React)

Este documento define la metodología estándar y el stack tecnológico oficial para el desarrollo y mantenimiento de **ioDesk**.

---

## Contexto Estratégico & Operacional (IONET)

**ESTA ES LA SECCIÓN MÁS IMPORTANTE DEL DOCUMENTO. CUALQUIER DECISIÓN TÉCNICA DEBE PASAR POR ESTE FILTRO.**

### 1. La Regla de Oro de ioDesk
*"Todo lo que ayude a hacer el desarrollo fácil y seguro, y no dependa al 100% de la habilidad de alguien o del conocimiento de un desarrollador externo, es CRÍTICO."*

### 2. Realidad Operativa (Survival-Ops)
*   **Empresa:** IONET (Soporte TI en Chile).
*   **Alcance:** 10 técnicos, 800 usuarios finales.
*   **Mantenimiento:** Usuario Leonardo (único desarrollador, no es experto).
*   **Bus Factor = 0:** El código debe ser *auto-explicativo*. No puede depender de "conocimiento tribal" o memoria.

### 3. La Regla del "Tanque Empresarial" (Anti-Overengineering)
*   **Prohibido "Grado Espacial":** ioDesk NO es software para la NASA ni para una corporación de 1000 devs.
*   **Simplicidad de Supervivencia:** Si una solución es tan robusta que Leonardo no puede explicarla en 2 minutos, es deuda técnica futura.
*   **Testing Pragmático:** Solo se testean las piezas críticas del motor.
*   **Despliegue Manual y Seguro:** Priorizar scripts simples (`deploy.sh`) que cualquiera pueda entender.
*   **Soberanía de Datos:** Los backups de BD y archivos `media` son sagrados.

---

## Stack Tecnológico Oficial

**IMPORTANTE: Todo desarrollo debe alinearse estrictamente a este stack.**

### Backend (The Brain)
*   **Framework:** Django (Python).
*   **Rol:** Monolito que sirve props JSON a Inertia.
*   **Autenticación:** Django Session Auth estándar. **PROHIBIDO** JWT/DRF Tokens.
*   **Estructura:** Modelos "gordos", Vistas CBV simples, Lógica en `services/` y `selectors/`.

### Frontend (The Body)
*   **Framework:** React 18+ (JavaScript/JSX).
*   **Glue:** **Inertia.js** (Puente Django-React).
*   **Build:** Vite.
*   **Estilos:** Tailwind CSS v4 + Lucide React.
*   **Estado:** React Hooks + Inertia Form Helper. **PROHIBIDO** Redux complejo.

---

*** SIEMPRE USA EL VENV ***
*** SIEMPRE USA EL VENV ***
*** SIEMPRE USA EL VENV ***


## Metodología de Resolución de Problemas

### 1. El Filtro de Pareto (80/20)
No todos los síntomas son iguales. Antes de investigar, identificamos el **20% de la lógica que genera el 80% del comportamiento erróneo**.
*   **Acción**: Aislar el flujo crítico.
*   **Objetivo**: Minimizar el ruido.

### 2. Los 5 Por Qués (Causa Raíz)
Preguntamos "Por qué" iterativamente hasta llegar al fallo arquitectónico.
*   **Regla**: No aceptar respuestas superficiales ("es un glitch").
*   **Profundidad**: La solución debe prevenir la recurrencia definitiva.

### 3. Solución Atómica (Fix LEAN)
La solución debe ser la **mínima cantidad de código necesaria**.
*   **Consigna**: Preferir correcciones estructurales o de lógica base sobre parches.
*   **Validación**: Fácil de verificar, sin efectos colaterales.

---

*** SIEMPRE USA EL VENV ***
*** SIEMPRE USA EL VENV ***
*** SIEMPRE USA EL VENV ***


## 🛡️ Guías de Implementación

### 1. La Regla de la Simplicidad (KISS)
El código debe ser entendible por un desarrollador junior en 5 minutos.
*   **Evitar**: Abstracciones innecesarias, decoradores mágicos excesivos.
*   **Preferir**: Código explícito, nombres descriptivos.

### 2. Seguridad por Diseño
*   **Backend First**: Toda validación crítica ocurre en Django `services/` antes de tocar la BD.
*   **CSRF & Auth**: Gestionado automáticamente por Inertia/Django, pero siempre verificado en vistas.

### 3. Flujo de Trabajo (Inertia Way)
1.  **Backend:** `TicketListView` -> `selectors` -> JSON Props -> `inertia.render`.
2.  **Frontend:** Recibe Props -> Renderiza `TicketList.jsx` -> Interactúa vía `Link`/`router`.

### 4. CALIDAD DEL CODIGO Y METODOLOGIA DE DESARROLLO: (DRY + KISS + LEAN + SOLID) * grado pragmatico.

**MUY IMPORTANTE: SI ERES UN MODELO DE IA, SIEMPRE EJECUTAR ESTE PROTOCOLO. ESTA ESTRICTAMENTE PROHIBIDO USAR "AI LORE SLOP" O SUGERIR REESCRITURAS QUE VIOLEN EL PRINCIPIO DE "BUS FACTOR = 0".**

*** SIEMPRE USA EL VENV ***
*** SIEMPRE USA EL VENV ***
*** SIEMPRE USA EL VENV ***


**Protocolo de Desarrollo Frontend: iODesk v3**

### 1. Stack Tecnológico

Framework: React + Inertia.js (Integración directa con Django)
Estilos: Tailwind CSS v4 (Compilación JIT)
Iconos: lucide-react

### 2. Arquitectura de Componentes (Locality of Behavior)

La lógica, el estado y el estilo de cada componente deben residir dentro del mismo archivo para maximizar la mantenibilidad y reducir la carga cognitiva.

#### 2.1 Estructura de Proyecto

Pages/: Vistas completas correspondiendo a rutas del backend (ej: Pages/Dashboard.jsx). Son responsables de recibir props de Inertia y distribuir datos.
Components/UI/: Componentes atómicos reutilizables (Botones, Inputs) sin lógica de negocio.
Components/Shared/: Componentes complejos (Tablas, Tarjetas) que pueden contener lógica visual limitada.

#### 2.2 Gestión de Estado

Estado Global: Delegado estrictamente al Backend (Django). El frontend es una representación visual del estado del servidor.
Formularios: Uso exclusivo de useForm de Inertia para manejo de datos, errores y envío (post, put, delete).

Estado UI: useState solo para interacciones puramente visuales (modales, tabs, dropdowns).

### 3. Estándares de Código

#### 3.1 Estilizado (Utility-First)
Utilizar clases de utilidad de Tailwind directamente en JSX.
Evitar abstracciones CSS (@apply) salvo casos de repetitividad extrema.
Seguir patrón Mobile-First para responsive design.
Dark Mode: Utilizar prefijos dark: o variables CSS nativas de Tailwind v4.

#### 3.2 Navegación
Utilizar componente <Link> de Inertia para navegación interna.
Evitar <a> para prevenir recargas completas de página.
Evitar manipulación directa de window.location.

#### 3.3 Anti-Patrones (Prohibido)
Global Stores: No utilizar Redux, Zustand o Context API para datos de negocio.
Efectos Secundarios: Minimizar useEffect. Los datos deben llegar listos desde el controlador de Django.

Prop Drilling: Máximo 2 niveles de profundidad. Utilizar composición de componentes (children) para casos complejos.

#### 3.4 CÓDIGO OOP PRAGMÁTICO + CBVs + DRY + SOLID + LEAN + KISS. Evitar "decoritis" (uso innecesario de decoradores) y abstracciones innecesarias. Evitar código mágico y excesivamente y/o innecesariamente anidado en múltiples if/else.

---

## 5. Protocolo de Versionamiento (Git)

Para mantener la trazabilidad y la simplicidad del proyecto, seguimos estas reglas:

*   **Idioma:** Todos los mensajes de commit deben ser en **español**.
*   **Atomicidad:** Cada commit debe representar un único cambio lógico (evitar commits gigantes con múltiples cambios no relacionados).
*   **Concisión:** Los mensajes deben ser directos y explicar brevemente *qué* se cambió y *por qué* (si no es obvio).
*   **Bus Factor = 0:** El historial de Git es parte de la documentación. Un commit bien explicado ayuda a entender la evolución del sistema sin depender de la memoria de nadie.
