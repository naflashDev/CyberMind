# Arquitectura del Frontend Desacoplado (CyberMind)

Este documento detalla la estructura, decisiones tecnológicas e integración de la Single Page Application (SPA) desacoplada de CyberMind, diseñada siguiendo la **Guía de Diseño Transversal de naflashDev** (Trilium nota `ogiJM5enymmK`).

---

## 🎨 Principios Visuales y Sistema de Diseño

El frontend cuenta con un sistema dinámico de temas gestionado por `ThemeContext`:
1. **6 Paletas Cromáticas Canónicas:**
   - **`Cyber Neon` (Predeterminada):** Cyan (`#06B6D4`), acento fucsia neón (`#D946EF`) sobre fondo Zinc 950 (`#09090B`).
   - **`JetBrains Dark`:** Naranja JetBrains (`#F97316`) sobre Obsidian (`#1E1F22`).
   - **`Amber Terminal`:** Ámbar fósforo (`#F59E0B`) sobre Pitch Black OLED (`#050505`).
   - **`Modern SaaS`:** Índigo (`#4F46E5`) sobre Slate 950 (`#020617`).
   - **`Calma Orgánica`:** Petróleo (`#0F766E`) y ámbar cálido sobre Stone 950.
   - **`Minimal Swiss`:** Azul cobalto (`#2563EB`) y neutralidad pura.
2. **5 Familias Tipográficas:**
   - `Plus Jakarta Sans` (por defecto), `Geist`, `Inter`, `Space Grotesk` y `JetBrains Mono`.
3. **Micro-interacciones Canónicas:**
   - `.btn-bounce` (`cubic-bezier(0.34, 1.56, 0.64, 1)`): física elástica al interactuar con botones.
   - `.dropdown-menu-smooth`: animaciones suaves de entrada.
   - Modo Oscuro nativo con persistencia en `localStorage`.

---

## 📁 Estructura del Código Fuente (`/frontend`)

- **`src/context/ThemeContext.tsx`**: Gestor de estado de apariencia y persistencia.
- **`src/services/api.ts`**: Cliente tipado para interactuar con los endpoints de FastAPI.
- **`src/components/layout/`**:
  - `Sidebar.tsx`: Navegación principal con iconos Lucide normalizados.
  - `Header.tsx`: Indicador de salud del backend y switch de Modo Oscuro.
- **`src/views/`**:
  - `ServicesView.tsx`: Explorador y ejecutor de servicios (Port scan con Nmap, CIDR scan, health).
  - `LLMView.tsx`: Chat con CyberSentinel IA, historial y subida/ingestión de documentos en ChromaDB.
  - `CodeAnalysisView.tsx`: Análisis estático de código fuente (SAST) y generación de PDF.
  - `DocsView.tsx`: Renderizador Markdown de la carpeta `/Docs`.
  - `ConfigView.tsx`: Panel interactivo para cambiar tema, fuentes y editar archivos `.ini`.
  - `StatusView.tsx`: Monitor en tiempo real de infraestructura y workers.
  - `IframeView.tsx`: Embebedor con carga diferida de OpenSearch Dashboards y Tiny RSS.

---

## 🚀 Ejecución en Desarrollo

```bash
cd frontend
npm install
npm run dev
```
La aplicación se levantará en `http://localhost:5173`, con proxy configurado hacia `http://localhost:8000`.
