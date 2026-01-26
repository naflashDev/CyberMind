document.addEventListener('DOMContentLoaded', function () {
  // --- Sidebar / view switching ---
  // Handles sidebar toggle and view switching logic
  const sidebar = document.getElementById("sidebar");
  const btnToggle = document.getElementById("btn-toggle");

  const buttons = document.querySelectorAll(".nav-button");
  const views = {
    fastapi: document.getElementById("view-fastapi"),
    datos: document.getElementById("view-datos"),
    tiny: document.getElementById("view-tiny"),
    llm: document.getElementById("view-llm"),
    status: document.getElementById("view-status"),
    docs: document.getElementById("view-docs"),
    config: document.getElementById("view-config"),
  };

  // --- Mostrar/ocultar CyberSentinel IA según use_ollama ---
  async function updateCyberSentinelVisibility() {
    const btnLLM = document.getElementById('btn-llm');
    const viewLLM = document.getElementById('view-llm');
    try {
      const resp = await fetch('/config');
      if (!resp.ok) throw new Error('No se pudo obtener la configuración');
      const data = await resp.json();
      let useOllama = false;
      for (const file of data.files) {
        for (const p of file.params) {
          if (p.key === 'use_ollama') {
            useOllama = String(p.value).toLowerCase() === 'true';
          }
        }
      }
      if (!useOllama) {
        if (btnLLM) btnLLM.style.display = 'none';
        if (viewLLM) viewLLM.style.display = 'none';
      } else {
        if (btnLLM) btnLLM.style.display = '';
        if (viewLLM) viewLLM.style.display = '';
      }
    } catch (e) {
      // Si hay error, mostrar por defecto
      if (btnLLM) btnLLM.style.display = '';
      if (viewLLM) viewLLM.style.display = '';
    }
  }
  updateCyberSentinelVisibility();
    // --- Configuración editable de archivos .ini ---
    let configCache = null;
    const configFilesEl = document.getElementById('config-files');
    const btnSaveConfig = document.getElementById('btn-save-config');
    const btnDiscardConfig = document.getElementById('btn-discard-config');
    const configStatus = document.getElementById('config-status');

    async function loadConfigFiles() {
      configStatus.textContent = '';
      if (!configFilesEl) return;
      configFilesEl.innerHTML = '<div style="color:#9aa6b2">Cargando configuración...</div>';
      try {
        const resp = await fetch('/config');
        if (!resp.ok) throw new Error('No se pudo obtener la configuración');
        const data = await resp.json();
        configCache = JSON.parse(JSON.stringify(data.files)); // deep copy para edición
        renderConfigFiles(configCache);
      } catch (e) {
        configFilesEl.innerHTML = '<div style="color:#fca5a5">Error cargando configuración</div>';
      }
    }

    function renderConfigFiles(files) {
      configFilesEl.innerHTML = '';
      // Trabajar siempre sobre configCache
        // Diccionario de nombres amigables para parámetros de configuración
          const CONFIG_FRIENDLY_NAMES = {
            "use_ollama": "Activar IA CyberSentinel",
            "host": "Dirección del servidor",
            "ports": "Puertos a escanear",
            "concurrency": "Concurrencia de escaneo",
            "cidr": "Rango de red (CIDR)",
            "start": "IP de inicio",
            "end": "IP de fin",
            "distro_name": "Nombre distribución",
            "dockers_name": "Nombre contenedores",
            "server_ip": "IP servidor",
            "server_port": "Puerto servidor"
          };
          // Diccionario de hints explicativos para cada campo
          const CONFIG_HINTS = {
            "distro_name": "Ejemplo: Ubuntu, Debian, Windows. Indica el sistema operativo principal.",
            "dockers_name": "Lista separada por comas de los nombres de los contenedores Docker. Ejemplo: app1,db1,nginx.",
            "use_ollama": "Activa la IA CyberSentinel si está disponible en el sistema.",
            "server_ip": "Dirección IP o nombre DNS del servidor. Ejemplo: localhost, 192.168.1.10.",
            "server_port": "Puerto de conexión del servidor. Ejemplo: 9200.",
            "host": "IP o nombre del host a escanear. Ejemplo: 192.168.1.1 o example.com.",
            "ports": "Puertos separados por comas. Ejemplo: 80,443,8080.",
            "concurrency": "Número de procesos simultáneos para el escaneo. Ejemplo: 20.",
            "cidr": "Rango de red en formato CIDR. Ejemplo: 192.168.1.0/24.",
            "start": "IP de inicio del rango. Ejemplo: 192.168.1.1.",
            "end": "IP final del rango. Ejemplo: 192.168.1.254. Opcional."
          };
      configCache.forEach((fileObj, fileIdx) => {
        const fileDiv = document.createElement('div');
        fileDiv.className = 'config-file-block';
        // Nombres amigables para los bloques de archivo
        let blockName = fileObj.file;
        if (fileObj.file === "cfg_services.ini") blockName = "Configuración servicios";
        else if (fileObj.file === "cfg.ini") blockName = "Configuración general";
        fileDiv.innerHTML = `<h3 style="margin-bottom:8px;"><span style='margin-right:6px;'>🛠️</span>${blockName}</h3>`;
        fileObj.params.forEach((p, idx) => {
          const row = document.createElement('div');
          row.className = 'config-param-row';
          row.style.marginBottom = '10px';
          const label = document.createElement('label');
            label.textContent = CONFIG_FRIENDLY_NAMES[p.key] || p.key;
          label.style.fontWeight = '600';
          label.style.marginRight = '12px';
            // Añadir icono de info con tooltip si existe hint
            if (CONFIG_HINTS[p.key]) {
              const infoIcon = document.createElement('span');
              infoIcon.innerHTML = ' <span style="cursor:pointer;color:#60a5fa;font-size:16px;vertical-align:middle;" title="' + CONFIG_HINTS[p.key].replace(/"/g, '&quot;') + '">ℹ️</span>';
              infoIcon.className = 'info-icon';
              label.appendChild(infoIcon);
            }
          row.appendChild(label);
          if (p.type === 'boolean') {
            const toggle = document.createElement('button');
            toggle.className = 'config-toggle-btn';
              toggle.innerHTML = (String(p.value).toLowerCase() === 'true') ? '<span style="margin-right:6px;">✅</span>Sí' : '<span style="margin-right:6px;">❌</span>No';
            toggle.style.background = (String(p.value).toLowerCase() === 'true') ? '#10b981' : '#ef4444';
            toggle.style.color = '#fff';
            toggle.style.border = 'none';
              toggle.style.borderRadius = '0';
            toggle.style.padding = '6px 18px';
            toggle.style.cursor = 'pointer';
            toggle.onclick = () => {
              // Actualizar configCache directamente
              configCache[fileIdx].params[idx].value = (String(p.value).toLowerCase() === 'true') ? 'false' : 'true';
              renderConfigFiles(configCache);
            };
            row.appendChild(toggle);
          } else {
            const textarea = document.createElement('textarea');
            textarea.value = p.value;
            textarea.style.width = '320px';
            textarea.style.minHeight = '28px';
              textarea.style.borderRadius = '0';
            textarea.style.border = '1px solid #6b7280';
            textarea.style.padding = '6px';
            textarea.oninput = (e) => {
              configCache[fileIdx].params[idx].value = textarea.value;
            };
            row.appendChild(textarea);
          }
          fileDiv.appendChild(row);
        });
        configFilesEl.appendChild(fileDiv);
      });
    }

    if (btnSaveConfig) btnSaveConfig.onclick = async function () {
      configStatus.textContent = '';
      if (!configCache) return;
      btnSaveConfig.disabled = true;
      try {
        for (const fileObj of configCache) {
          const resp = await fetch('/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ file: fileObj.file, params: fileObj.params })
          });
          if (!resp.ok) throw new Error('Error guardando ' + fileObj.file);
        }
        configStatus.textContent = '¡Configuración guardada!';
        await loadConfigFiles();
        // Actualizar visibilidad CyberSentinel inmediatamente tras guardar
        await updateCyberSentinelVisibility();
        // Si se activa Ollama, recargar la vista CyberSentinel
        const useOllama = configCache.some(fileObj => fileObj.params.some(p => p.key === 'use_ollama' && String(p.value).toLowerCase() === 'true'));
        if (useOllama) {
          // Forzar recarga de la vista CyberSentinel si está visible
          const btnLLM = document.getElementById('btn-llm');
          const viewLLM = document.getElementById('view-llm');
          if (btnLLM && viewLLM) {
            btnLLM.style.display = '';
            viewLLM.style.display = '';
          }
        }
      } catch (e) {
        configStatus.textContent = 'Error al guardar: ' + e;
      }
      btnSaveConfig.disabled = false;
    };
     // Agregar icono al botón guardar
     if (btnSaveConfig) btnSaveConfig.innerHTML = '<span style="margin-right:6px;">💾</span>Guardar';

    if (btnDiscardConfig) btnDiscardConfig.onclick = function () {
      configStatus.textContent = 'Cambios descartados.';
      if (configCache) renderConfigFiles(configCache);
    };
     // Agregar icono al botón descartar
     if (btnDiscardConfig) btnDiscardConfig.innerHTML = '<span style="margin-right:6px;">🗑️</span>Descartar';

    // Activar vista configuración al pulsar el botón
    const btnConfig = document.getElementById('btn-config');
    if (btnConfig) {
      btnConfig.addEventListener('click', () => {
        activateView('config');
        loadConfigFiles();
      });
    }
  // --- Documentation view logic ---
  // Handles documentation sidebar and markdown rendering
  const docsListEl = document.getElementById('docs-list');
  const docsContentEl = document.getElementById('docs-content');

  // --- Documentation: sidebar and rendering ---

  let docsListCache = null;
  let currentDoc = 'README.md';

  // Mapping of friendly names for main documentation files
  const DOCS_FRIENDLY_NAMES = {
    'README.md': 'Introducción (README)',
    'Indice.md': 'Índice general',
    'home.md': 'Resumen y objetivo',
    'api_endpoints.md': 'API Endpoints',
    'llm.md': 'LLM (IA integrada)',
    'instalacion_dependencias.md': 'Instalación dependencias',
    'opensearch_install.md': 'Instalación OpenSearch',
    'tiny_rss_install.md': 'Instalación Tiny RSS',
    'task.md': 'Tareas y operaciones',
    'ChangeLog.md': 'Registro de cambios',
    // Añadir más si es necesario
  };

  /**
   * @brief Get a friendly display name for a documentation file.
   * @param filename The filename to convert.
   * @return Friendly name string.
   */
  function getFriendlyName(filename) {
    return DOCS_FRIENDLY_NAMES[filename] || filename.replace('.md', '').replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  }

  /**
   * @brief Load the documentation file list and render the sidebar.
   * @param selected The currently selected document filename.
   * @return void
   */
  async function loadDocsListAndRender(selected) {
    if (!docsListEl) return;
    docsListEl.innerHTML = '';
    // README primero
    const readmeLi = document.createElement('li');
    const readmeBtn = document.createElement('button');
    readmeBtn.textContent = getFriendlyName('README.md');
    readmeBtn.className = 'doc-btn' + (selected === 'README.md' ? ' active' : '');
    readmeBtn.onclick = () => selectDoc('README.md');
    readmeLi.appendChild(readmeBtn);
    docsListEl.appendChild(readmeLi);
    // Indice.md segundo si existe
    try {
      let files = docsListCache;
      if (!files) {
        const resp = await fetch('/docs/list');
        if (!resp.ok) throw new Error('No se pudo obtener la lista de documentos');
        files = await resp.json();
        docsListCache = files;
      }
      // Mostrar Indice.md si está
      if (files.includes('Indice.md')) {
        const indiceLi = document.createElement('li');
        const indiceBtn = document.createElement('button');
        indiceBtn.textContent = getFriendlyName('Indice.md');
        indiceBtn.className = 'doc-btn' + (selected === 'Indice.md' ? ' active' : '');
        indiceBtn.onclick = () => selectDoc('Indice.md');
        indiceLi.appendChild(indiceBtn);
        docsListEl.appendChild(indiceLi);
      }
      // El resto de archivos, excluyendo README.md e Indice.md
      files.filter(f => f !== 'README.md' && f !== 'Indice.md').forEach(f => {
        const li = document.createElement('li');
        const btn = document.createElement('button');
        btn.textContent = getFriendlyName(f);
        btn.className = 'doc-btn' + (selected === f ? ' active' : '');
        btn.onclick = () => selectDoc(f);
        li.appendChild(btn);
        docsListEl.appendChild(li);
      });
    } catch (e) {
      const li = document.createElement('li');
      li.textContent = 'Error cargando lista de documentos';
      docsListEl.appendChild(li);
    }
  }

  /**
   * @brief Select a documentation file and render its content.
   * @param filename The filename to select.
   * @return void
   */
  async function selectDoc(filename) {
    currentDoc = filename;
    await loadDocsListAndRender(filename);
    await loadDocContent(filename);
  }

  /**
   * @brief Load and render the content of a documentation file.
   * @param filename The filename to load.
   * @return void
   */
  async function loadDocContent(filename) {
    if (!docsContentEl) return;
    docsContentEl.innerHTML = '<div style="color:#9aa6b2">Cargando...</div>';
    let url = '';
    if (filename === 'README.md') url = '/docs/readme';
    else url = '/docs/file/' + encodeURIComponent(filename);
    try {
      const resp = await fetch(url);
      if (!resp.ok) throw new Error('No se pudo cargar el documento');
      const text = await resp.text();
      // Renderizar markdown y ajustar enlaces internos
      docsContentEl.innerHTML = marked.parse(text);
      fixInternalLinks();
      // Evitar desbordes horizontales
      docsContentEl.style.overflowX = 'auto';
      docsContentEl.style.wordBreak = 'break-word';
    } catch (e) {
      docsContentEl.innerHTML = '<div style="color:#fca5a5">Error cargando documento</div>';
    }
  }

  /**
   * @brief Intercept internal markdown links for SPA navigation.
   * @return void
   */
  function fixInternalLinks() {
    if (!docsContentEl) return;
    const links = docsContentEl.querySelectorAll('a[href$=".md"], a[href^="./"], a[href^="../"]');
    links.forEach(link => {
      const href = link.getAttribute('href');
      if (!href) return;
      // Normalizar nombre de archivo
      let file = href.split('/').pop().replace(/^\.?\/?/, '');
      if (file.endsWith('.md')) {
        link.onclick = (e) => {
          e.preventDefault();
          selectDoc(file);
        };
        link.style.textDecoration = 'underline';
        link.style.cursor = 'pointer';
      }
    });
  }

  // Al pulsar Documentación, mostrar README y barra lateral
  const btnDocs = document.getElementById('btn-docs');
  if (btnDocs) {
    btnDocs.addEventListener('click', () => {
      selectDoc('README.md');
    });
  }

  /**
   * @brief Activate a main view by name (show/hide sections).
   * @param viewName The view to activate.
   * @return void
   */
  function activateView(viewName) {
    // Remove 'active' class from all buttons
    buttons.forEach(btn => btn.classList.remove("active"));
    // Add 'active' class to the selected button
    const activeBtn = document.querySelector(`.nav-button[data-view="${viewName}"]`);
    if (activeBtn) activeBtn.classList.add("active");
    // Hide all views except the selected one
    Object.entries(views).forEach(([key, v]) => {
      if (key === viewName) {
        v.classList.add("active");
        v.style.display = "";
      } else {
        v.classList.remove("active");
        v.style.display = "none";
      }
    });
    // lazy-load any iframe placeholder inside the activated view
    try { ensureFrameLoaded(viewName); } catch (e) { /* ignore */ }
  }

  /**
   * @brief Create iframe element from placeholder data-src when requested.
   * @param viewName The view to check for iframe placeholder.
   * @return void
   */
  function ensureFrameLoaded(viewName) {
    const view = views[viewName];
    if (!view) return;
    const placeholder = view.querySelector('.iframe-placeholder');
    if (!placeholder) return;
    if (placeholder.dataset.loaded === '1') return;
    // if there's a button, user can click; also load automatically on first activation
    const src = placeholder.dataset.src;
    if (!src) return;
    const iframe = document.createElement('iframe');
    iframe.className = 'embed-frame';
    iframe.src = src;
    iframe.loading = 'eager';
    iframe.style.width = '100%';
    iframe.style.height = '100%';
    iframe.style.border = '0';
    // sandbox to limit exposure but allow typical UI scripts (adjust if breaks functionality)
    iframe.sandbox = 'allow-scripts allow-forms allow-same-origin';
    // replace placeholder contents
    placeholder.innerHTML = '';
    placeholder.appendChild(iframe);
    placeholder.dataset.loaded = '1';
  }

  buttons.forEach(btn => {
    btn.addEventListener("click", () => {
      const view = btn.dataset.view;
      activateView(view);
    });
  });

  // Delegate clicks on load buttons for explicit on-demand loading
  document.addEventListener('click', function (e) {
    const btn = e.target && e.target.closest && e.target.closest('.load-iframe-btn');
    if (!btn) return;
    const placeholder = btn.closest('.iframe-placeholder');
    if (!placeholder) return;
    try { ensureFrameLoaded(placeholder.closest('.view') && placeholder.closest('.view').id.replace('view-','')); } catch (err) {}
  });

  if (btnToggle) btnToggle.addEventListener("click", () => {
    const hidden = sidebar.classList.toggle("hidden");
    btnToggle.innerHTML = hidden ? "☰" : "«";
  });

  // Forzar que la vista de FastAPI esté activa al cargar
  setTimeout(() => activateView("fastapi"), 0);

  // --- FastAPI operations panel ---
  // Handles rendering and interaction for API operation controls
  (function () {
    const API_BASE = window.__CYBERMIND_API_BASE__ || "http://127.0.0.1:8000";

    const controllers = {
      "Scrapy": [
        { id: "scrape-news", title: "Scrape News", method: "GET", path: "/newsSpider/scrape-news", params: [], desc: "Extrae noticias desde las fuentes configuradas y las normaliza." },
        { id: "start-google-alerts", title: "Start Google Alerts", method: "GET", path: "/newsSpider/start-google-alerts", params: [], desc: "Inicia la recolección de alertas de Google configuradas." },
        { id: "save-feed-google-alerts", title: "Save Feed Google Alerts", method: "POST", path: "/newsSpider/save-feed-google-alerts", params: [{name: "link", type: "text", placeholder: "URL o texto del feed"}], desc: "Guarda un feed (o URL) de Google Alerts en la base de datos." },
        { id: "scrapy-google-dk-feeds", title: "Scrapy Google DK Feeds", method: "GET", path: "/newsSpider/scrapy/google-dk/feeds", params: [], desc: "Rastrea y lista feeds encontrados para Google DK (feeds)." },
        { id: "scrapy-google-dk-news", title: "Scrapy Google DK News", method: "GET", path: "/newsSpider/scrapy/google-dk/news", params: [], desc: "Rastrea artículos/noticias desde Google DK." }
      ],
      "SpaCy": [
        { id: "start-spacy", title: "Start SpaCy", method: "GET", path: "/start-spacy", params: [], desc: "Inicia o carga el pipeline de SpaCy para procesamiento de texto." }
      ],
      "Tiny": [
        { id: "search-and-insert-rss", title: "Search and Insert RSS", method: "GET", path: "/postgre-ttrss/search-and-insert-rss", params: [{name: "link", type: "text", placeholder: "consulta (opcional)"}], desc: "Busca elementos RSS por consulta e inserta los nuevos en TinyRSS/Postgres." },
        { id: "feeds", title: "List Feeds", method: "GET", path: "/postgre-ttrss/feeds", params: [], desc: "Lista los feeds almacenados en la base de datos." }
      ],
      "LLM": [
        { id: "llm-updater", title: "LLM Updater", method: "GET", path: "/llm/updater", params: [], desc: "Inicia el updater/finetune en background (llm_updater)." }
      ],
      "Network": [
        { id: "network-scan", title: "Analisis de redes (scan)", method: "POST", path: "/network/scan", params: [{name: "host", type: "text", placeholder: "IP o hostname"}, {name: "ports", type: "text", placeholder: "puertos separados por comas (opcional)"}], desc: "Escanea puertos comunes y devuelve servicios heurísticos. Asegúrate de tener permiso para escanear el host." },
        { id: "network-scan-range", title: "Analisis de redes (rango)", method: "POST", path: "/network/scan_range", params: [{name: "cidr", type: "text", placeholder: "CIDR (ej. 192.168.1.0/28)"}, {name: "start", type: "text", placeholder: "IP inicio (ej. 192.168.1.1)"}, {name: "end", type: "text", placeholder: "IP fin (opcional)"}, {name: "ports", type: "text", placeholder: "puertos separados por comas (opcional)"}, {name: "concurrency", type: "text", placeholder: "concurrency (opcional, default 20)"}], desc: "Escanea un rango de IPs y devuelve puertos abiertos/cerrados por IP. Usa con permiso." },
        { id: "network-ports", title: "List Common Ports", method: "GET", path: "/network/ports", params: [], desc: "Lista puertos comunes sugeridos para escaneo." }
      ],
      "Status": [
        { id: "system-status-op", title: "System Status", method: "GET", path: "/status", params: [], desc: "Muestra el estado de la infraestructura, UI y workers en ejecución." }
      ]
    };

    const controllersList = document.getElementById("controllers-list");
    const opTitle = document.getElementById("op-title");
    const opForm = document.getElementById("op-form");
    const opResult = document.getElementById("op-result");

    /**
     * @brief Render the list of API controllers and their operations.
     * @return void
     */
    function renderControllers() {
      if (!controllersList) return;
      controllersList.innerHTML = "";

      // Controllers to group under OSINT
      const osintNames = new Set(['Scrapy', 'SpaCy', 'Tiny', 'LLM']);

      // Create OSINT category container
      const osintCategory = document.createElement('div');
      osintCategory.className = 'controller-category';
      const osintHeader = document.createElement('button');
      osintHeader.className = 'controller-category-header';
      osintHeader.type = 'button';
      osintHeader.innerHTML = `<span>OSINT</span><span class="toggle-icon">▾</span>`;
      const osintInner = document.createElement('div');
      osintInner.className = 'controller-category-inner';
      osintHeader.addEventListener('click', () => {
        osintCategory.classList.toggle('collapsed');
        const icon = osintHeader.querySelector('.toggle-icon');
        if (icon) icon.textContent = osintCategory.classList.contains('collapsed') ? '▸' : '▾';
      });
      osintCategory.appendChild(osintHeader);
      osintCategory.appendChild(osintInner);

      // Build sections and place them appropriately
      Object.keys(controllers).forEach(name => {
        const wrapper = document.createElement("div");
        wrapper.className = "controller-section";
        const headerBtn = document.createElement("button");
        headerBtn.className = "controller-header";
        headerBtn.type = "button";
        headerBtn.innerHTML = `<span>${name}</span><span class="toggle-icon">▾</span>`;
        headerBtn.addEventListener("click", () => {
          wrapper.classList.toggle("collapsed");
          const icon = headerBtn.querySelector('.toggle-icon');
          if (icon) icon.textContent = wrapper.classList.contains('collapsed') ? '▸' : '▾';
        });
        wrapper.appendChild(headerBtn);
        const opsContainer = document.createElement("div");
        opsContainer.className = "ops-container";
        controllers[name].forEach(op => {
            const opBtn = document.createElement("button");
            opBtn.className = "op-btn";
            // Iconos representativos según el tipo de operación
            let icon = '';
            if (op.title.toLowerCase().includes('scan')) icon = '🔍';
            else if (op.title.toLowerCase().includes('save')) icon = '💾';
            else if (op.title.toLowerCase().includes('start')) icon = '▶️';
            else if (op.title.toLowerCase().includes('list')) icon = '📋';
            else if (op.title.toLowerCase().includes('updater')) icon = '♻️';
            else if (op.title.toLowerCase().includes('status')) icon = '📊';
            else if (op.title.toLowerCase().includes('feeds')) icon = '📰';
            else if (op.title.toLowerCase().includes('spacy')) icon = '🧠';
            else if (op.title.toLowerCase().includes('llm')) icon = '🤖';
            else icon = '⚙️';
            opBtn.innerHTML = `<span style='margin-right:6px;'>${icon}</span>${op.title}`;
            opBtn.type = "button";
            opBtn.dataset.opId = op.id || '';
            opBtn.addEventListener("click", () => {
              document.querySelectorAll('.op-btn').forEach(b => b.classList.remove('active'));
              opBtn.classList.add('active');
              selectOperation(name, op, opBtn);
            });
            opsContainer.appendChild(opBtn);
        });
        wrapper.appendChild(opsContainer);

        if (osintNames.has(name)) {
          osintInner.appendChild(wrapper);
        } else {
          controllersList.appendChild(wrapper);
        }
      });

      // Insert OSINT category at top if it has children
      if (osintInner.children.length) {
        controllersList.insertBefore(osintCategory, controllersList.firstChild);
      }

      // Expand the Network section by default so new ops are visible
      try {
        const sections = controllersList.querySelectorAll('.controller-section');
        sections.forEach(sec => {
          const header = sec.querySelector('.controller-header');
          if (!header) return;
          if (header.textContent && header.textContent.trim().startsWith('Network')) {
            sec.classList.remove('collapsed');
            const icon = header.querySelector('.toggle-icon');
            if (icon) icon.textContent = '▾';
            // Ya no se fuerza remarco visual en ningún botón
          }
        });
      } catch (e) { console.log('renderControllers post-process error', e); }
    }

    /**
     * @brief Select an API operation and render its form.
     * @param controllerName The controller group name.
     * @param op The operation object.
     * @param btnEl The button element clicked.
     * @return void
     */
    function selectOperation(controllerName, op, btnEl) {
      if (opTitle) opTitle.textContent = controllerName + " — " + op.title + " (" + op.method + ")";
      renderForm(op);
      const opResultEl = document.getElementById('op-result');
      if (op.path === '/status') {
        if (opResultEl) opResultEl.style.display = 'none';
      } else {
        if (opResultEl) { opResultEl.style.display = 'block'; opResultEl.textContent = 'Respuesta aquí...'; }
      }
    }

    /**
     * @brief Render the form for an API operation.
     * @param op The operation object.
     * @return void
     */
    function renderForm(op) {
      if (!opForm) return;
      opForm.innerHTML = "";
      const info = document.createElement("div");
      info.style.marginBottom = "8px";
      info.style.color = "#cbd5e1";
      const methodEl = document.createElement('strong');
      methodEl.textContent = op.method;
      info.appendChild(methodEl);
      if (op.desc) {
        const descEl = document.createElement('div');
        descEl.style.color = '#9aa6b2';
        descEl.style.fontSize = '13px';
        descEl.style.marginTop = '6px';
        descEl.textContent = op.desc;
        info.appendChild(descEl);
      }
      opForm.appendChild(info);
      const form = document.createElement("form");
      form.onsubmit = async (e) => { e.preventDefault(); await submitOperation(op, new FormData(form)); };

      if (op.path === "/status") {
        const panel = document.createElement('div');
        panel.style.display = 'flex'; panel.style.flexDirection = 'column'; panel.style.gap = '8px';
        const row = document.createElement('div'); row.style.display = 'flex'; row.style.alignItems = 'center'; row.style.gap = '8px';
        const refreshBtn = document.createElement('button'); refreshBtn.type = 'button'; refreshBtn.textContent = 'Actualizar estado'; refreshBtn.style.padding = '6px 10px'; refreshBtn.style.borderRadius = '6px'; refreshBtn.style.border = 'none'; refreshBtn.style.background = '#2563eb'; refreshBtn.style.color = '#fff'; refreshBtn.style.cursor = 'pointer';
        const startAllBtn = document.createElement('button'); startAllBtn.type = 'button'; startAllBtn.textContent = 'Start All'; startAllBtn.style.padding = '6px 10px'; startAllBtn.style.borderRadius = '6px'; startAllBtn.style.border = 'none'; startAllBtn.style.background = '#10b981'; startAllBtn.style.color = '#fff'; startAllBtn.style.cursor = 'pointer';
        const stopAllBtn = document.createElement('button'); stopAllBtn.type = 'button'; stopAllBtn.textContent = 'Stop All'; stopAllBtn.style.padding = '6px 10px'; stopAllBtn.style.borderRadius = '6px'; stopAllBtn.style.border = 'none'; stopAllBtn.style.background = '#ef4444'; stopAllBtn.style.color = '#fff'; stopAllBtn.style.cursor = 'pointer';
        row.appendChild(refreshBtn); row.appendChild(startAllBtn); row.appendChild(stopAllBtn);
        const box = document.createElement('div'); box.id = 'op-status-box'; box.style.background = '#0b1220'; box.style.color = '#e6eef8'; box.style.padding = '12px'; box.style.borderRadius = '6px'; box.style.boxSizing = 'border-box'; box.innerHTML = '<div>Cargando...</div>';
        panel.appendChild(row); panel.appendChild(box); opForm.appendChild(panel);

        async function fetchForOp() {
          try {
            const resp = await fetch((window.__CYBERMIND_API_BASE__ || API_BASE) + '/status');
            if (!resp.ok) throw new Error('HTTP ' + resp.status);
            const j = await resp.json();
            const workers = j.workers || {};
            const parts = [];
            parts.push(`<div style="margin-bottom:8px;"><strong>Infra:</strong> ${j.infra_ready ? '<span style="color:#86efac">OK</span>' : '<span style="color:#fca5a5">NO</span>'}${j.infra_error ? ` &nbsp; <em style="color:#fca5a5">${j.infra_error}</em>` : ''}</div>`);
            parts.push(`<div style="margin-bottom:8px;"><strong>UI initialized:</strong> ${j.ui_initialized ? '<span style="color:#86efac">sí</span>' : '<span style="color:#fca5a5">no</span>'}</div>`);
            parts.push('<div style="margin-bottom:6px;"><strong>Workers</strong></div>');
            parts.push('<div id="workers-control-list" style="display:flex;flex-direction:column;gap:8px;">');
            for (const [name, val] of Object.entries(workers)) {
              const status = val ? '<span style="color:#86efac">running</span>' : '<span style="color:#fca5a5">stopped</span>';
              const btnStyle = val ? 'background:#ef4444;color:#fff' : 'background:#10b981;color:#fff';
              const btnText = val ? 'Stop' : 'Activate';
              parts.push(`<div style="display:flex;align-items:center;justify-content:space-between;gap:8px;"><div style="display:flex;flex-direction:column;"><div style="font-weight:600">${name}</div><div style="font-size:12px;color:#9aa6b2">Status: ${status}</div></div><div><button data-worker-toggle="${name}" data-enabled="${val}" style="padding:8px 10px;border-radius:6px;border:none;cursor:pointer;${btnStyle}">${btnText}</button></div></div>`);
            }
            parts.push('</div>');
            document.getElementById('op-status-box').innerHTML = parts.join('');
            const toggleBtns = document.querySelectorAll('#op-status-box button[data-worker-toggle]');
            toggleBtns.forEach(btn => {
              btn.addEventListener('click', async () => {
                const name = btn.dataset.workerToggle;
                const enabled = btn.dataset.enabled === 'true' || btn.dataset.enabled === 'True';
                const newEnabled = !enabled;
                const oldText = btn.textContent; btn.disabled = true;
                try {
                  const p = await fetch((window.__CYBERMIND_API_BASE__ || API_BASE) + '/workers/' + encodeURIComponent(name), { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ enabled: newEnabled }) });
                  if (!p.ok) throw new Error('HTTP ' + p.status);
                  showToast((newEnabled ? 'Activated' : 'Stopped') + ' ' + name);
                  setTimeout(fetchForOp, 300);
                } catch (err) {
                  showToast('Error toggling worker: ' + String(err)); btn.disabled = false; btn.textContent = oldText;
                }
              });
            });
          } catch (err) {
            box.innerHTML = `<div style="color:#fca5a5">Error: ${String(err)}</div>`;
          }
        }

        refreshBtn.addEventListener('click', fetchForOp);
        async function toggleAll(enable) {
          try {
            const s = await fetch((window.__CYBERMIND_API_BASE__ || API_BASE) + '/status'); if (!s.ok) throw new Error('HTTP ' + s.status);
            const j = await s.json(); const workers = j.workers || {};
            const promises = Object.keys(workers).map(name => fetch((window.__CYBERMIND_API_BASE__ || API_BASE) + '/workers/' + encodeURIComponent(name), { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ enabled: enable }) }).then(r => ({ name, ok: r.ok, status: r.status })));
            const results = await Promise.allSettled(promises);
            const succeeded = results.filter(r => r.status === 'fulfilled' && r.value && r.value.ok).map(r => r.value.name);
            showToast((enable ? 'Started' : 'Stopped') + ' ' + succeeded.length + ' workers'); setTimeout(fetchForOp, 400);
          } catch (err) {
            showToast('Error toggling workers: ' + String(err));
          }
        }

        if (typeof startAllBtn !== 'undefined') startAllBtn.addEventListener('click', () => toggleAll(true));
        if (typeof stopAllBtn !== 'undefined') stopAllBtn.addEventListener('click', () => toggleAll(false));
        fetchForOp();
        try { window.addEventListener('status-updated', fetchForOp); } catch (e) {}
        let statusInterval = setInterval(() => { const boxEl = document.getElementById('op-status-box'); if (!boxEl) return; fetchForOp(); }, 10000);
        return;
      }

      if (op.params && op.params.length) {
        op.params.forEach(p => {
          const label = document.createElement("label"); label.style.display = "block"; label.style.marginBottom = "6px"; label.innerHTML = `<div style='font-size:13px;color:#cbd5e1;margin-bottom:4px;'>${p.name}</div>`;
          const input = document.createElement("input"); input.name = p.name; input.placeholder = p.placeholder || ""; input.style.width = "100%"; input.style.padding = "8px"; input.style.boxSizing = "border-box"; input.style.marginBottom = "6px"; label.appendChild(input); form.appendChild(label);
        });
      }

      // If this is the network scan op, add a checkbox to use nmap
      if (op.path === '/network/scan') {
        const nmLabel = document.createElement('label'); nmLabel.style.display = 'flex'; nmLabel.style.alignItems = 'center'; nmLabel.style.gap = '8px'; nmLabel.style.marginBottom = '8px';
        const nmCheckbox = document.createElement('input'); nmCheckbox.type = 'checkbox'; nmCheckbox.name = 'use_nmap'; nmCheckbox.checked = true;
        nmLabel.appendChild(nmCheckbox); const nmText = document.createElement('span'); nmText.style.color='#9aa6b2'; nmText.textContent = 'Usar nmap (recomendado)'; nmLabel.appendChild(nmText);
        form.appendChild(nmLabel);
      }

      // If this is the network scan range op, add a checkbox to use nmap
      if (op.path === '/network/scan_range') {
        const nmLabel = document.createElement('label'); nmLabel.style.display = 'flex'; nmLabel.style.alignItems = 'center'; nmLabel.style.gap = '8px'; nmLabel.style.marginBottom = '8px';
        const nmCheckbox = document.createElement('input'); nmCheckbox.type = 'checkbox'; nmCheckbox.name = 'use_nmap'; nmCheckbox.checked = true;
        nmLabel.appendChild(nmCheckbox); const nmText = document.createElement('span'); nmText.style.color='#9aa6b2'; nmText.textContent = 'Usar nmap si está disponible'; nmLabel.appendChild(nmText);
        form.appendChild(nmLabel);
      }

      const submit = document.createElement("button"); submit.textContent = "Ejecutar"; submit.type = "submit"; submit.className = "exec-btn"; submit.style.padding = "8px 12px"; submit.style.background = "#2563eb"; submit.style.color = "#fff"; submit.style.border = "none"; submit.style.borderRadius = "6px"; submit.style.cursor = "pointer";
      form.appendChild(submit); opForm.appendChild(form);
    }

    /**
     * @brief Escape HTML special characters in a string.
     * @param unsafe The string to escape.
     * @return Escaped string.
     */
    function escapeHtml(unsafe) { return String(unsafe).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/\"/g, "&quot;").replace(/'/g, "&#039;"); }

    /**
     * @brief Ensure the 'marked' markdown parser is loaded.
     * @return Promise resolving to window.marked
     */
    async function ensureMarked() {
      if (window.marked) return window.marked;
      return new Promise((resolve, reject) => {
        try {
          const s = document.createElement('script');
          s.src = 'https://cdn.jsdelivr.net/npm/marked/marked.min.js';
          s.async = true;
          s.onload = () => resolve(window.marked);
          s.onerror = () => reject(new Error('Failed loading marked'));
          document.head.appendChild(s);
        } catch (e) { reject(e); }
      });
    }

    /**
     * @brief Show a toast notification message.
     * @param msg The message to display.
     * @param ms Duration in milliseconds.
     * @return void
     */
    function showToast(msg, ms = 1800) {
      try { const t = document.createElement('div'); t.className = 'toast'; t.textContent = msg; document.body.appendChild(t); void t.offsetWidth; t.classList.add('show'); setTimeout(() => { t.classList.remove('show'); setTimeout(() => t.remove(), 200); }, ms); } catch (e) { console.log('toast', e); }
    }

    /**
     * @brief Render a friendly response panel for API results.
     * @param obj The response object.
     * @param status HTTP status code.
     * @return HTML string.
     */
    function renderResponse(obj, status) {
      function renderFriendly(value, depth = 0) {
        if (value === null) return `<span class="response-value">(nulo)</span>`;
        const t = typeof value;
        if (t === 'string' || t === 'number' || t === 'boolean') return `<span class="response-value">${escapeHtml(String(value))}</span>`;
        if (Array.isArray(value)) { if (value.length === 0) return `<span class="response-value">(vacío)</span>`; const items = value.slice(0,200).map(it => `<li>${renderFriendly(it, depth+1)}</li>`).join(''); const more = value.length>200?`<li>... ${value.length-200} más</li>`:''; return `<ul class="response-list">${items}${more}</ul>`; }
        if (t === 'object') { if (depth >= 2) return `<details><summary>Objeto (mostrar JSON)</summary><pre>${escapeHtml(JSON.stringify(value, null, 2))}</pre></details>`; const lines = Object.keys(value).map(k => { const v = value[k]; if (v === null || typeof v === 'string' || typeof v === 'number' || typeof v === 'boolean') return `<div><span class="response-key">${escapeHtml(k)}:</span> ${renderFriendly(v, depth+1)}</div>`; return `<div style="margin-top:6px;"><span class="response-key">${escapeHtml(k)}:</span> ${renderFriendly(v, depth+1)}</div>`; }).join(''); return `<div>${lines}</div>`; }
        return `<span class="response-value">${escapeHtml(String(value))}</span>`;
      }
      const panelHeader = `<div style="display:flex;justify-content:space-between;align-items:center;gap:8px;"><div class=\"response-meta\">Status: ${status || ''}</div><button class=\"panel-toggle\">▾</button></div>`;
      if (obj === null || typeof obj !== 'object') return `<div class="panel"><div class="panel-head">${panelHeader}</div><div class="panel-body">${renderFriendly(obj)}</div></div>`;
      const friendlyHtml = renderFriendly(obj,0); return `<div class="panel"><div class="panel-head">${panelHeader}</div><div class="panel-body">${friendlyHtml}</div></div>`;
    }

    /**
     * @brief Render the result of a network scan operation.
     * @param obj The scan result object.
     * @return HTML string.
     */
    function renderNetworkScanResult(obj) {
      try {
        const host = obj.host || '';
        const res = obj.results || [];
        if (!res.length) return `<div style="color:#9aa6b2">No se encontraron puertos o la respuesta está vacía.</div>`;
        const cards = res.map(r => {
          const port = r.port || '';
          const protocol = r.protocol || 'tcp';
          const identity = `${escapeHtml(host)}:${escapeHtml(String(port))}/${escapeHtml(protocol)}`;
          const methods = (r.methods && r.methods.length) ? `<div style="margin-top:6px;color:#cbd5e1"><strong>Métodos:</strong> ${r.methods.map(m=>escapeHtml(m)).join(', ')}</div>` : '';
          const product = r.product ? (escapeHtml(r.product) + (r.version ? (' v' + escapeHtml(r.version)) : '')) : '';
            let openBadge = '';
            const rstate = (r && r.state) ? String(r.state).toLowerCase().trim() : '';
            if (rstate === 'filtered') {
              openBadge = '<span style="background:#f59e0b;color:#fff;padding:4px 8px;border-radius:6px;font-weight:600">FILTERED</span>';
            } else {
              openBadge = r.open ? '<span style="background:#16a34a;color:#fff;padding:4px 8px;border-radius:6px;font-weight:600">OPEN</span>' : '';
            }
          return `<div class="port-card" style="background:#071127;padding:12px;border-radius:8px;border:1px solid #0f1724;margin-bottom:10px;display:flex;justify-content:space-between;align-items:center">
            <div>
              <div style="font-weight:700;font-size:20px">${escapeHtml(String(port))}</div>
              <div style="color:#9aa6b2;margin-top:4px">${escapeHtml(r.service || '')}</div>
              <div style="color:#9aa6b2;font-size:12px;margin-top:4px">${identity}</div>
              ${product ? `<div style="color:#9aa6b2;margin-top:6px;font-size:13px">${product}</div>` : ''}
              ${methods}
            </div>
            <div style="display:flex;flex-direction:column;align-items:flex-end;gap:6px">
              <div style="font-size:12px;color:#94a3b8">Puerto</div>
              ${openBadge}
            </div>
          </div>`;
        }).join('');
        return `<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px">${cards}</div>`;
      } catch (e) { return renderRawJson(obj); }
    }

    /**
     * @brief Render the result of a network range scan operation.
     * @param obj The scan result object.
     * @return HTML string.
     */
    function renderRangeScanResult(obj) {
      try {
        let hosts = obj.hosts || [];
        if (!hosts.length) return `<div style="color:#9aa6b2">No se obtuvieron resultados.</div>`;

        // normalize and compute open/filtered counts
        hosts = hosts.map(h => {
          const results = Array.isArray(h.results) ? h.results.slice() : [];
          // sort ports: open first, then filtered, then by port number
          results.sort((a, b) => {
            const aState = (a && a.state) ? String(a.state).toLowerCase().trim() : '';
            const bState = (b && b.state) ? String(b.state).toLowerCase().trim() : '';
            const aOpen = !!a.open;
            const bOpen = !!b.open;
            const aFiltered = aState === 'filtered';
            const bFiltered = bState === 'filtered';
            if (aOpen !== bOpen) return aOpen ? -1 : 1;
            if (aFiltered !== bFiltered) return aFiltered ? -1 : 1;
            return (Number(a.port) || 0) - (Number(b.port) || 0);
          });
          const openCount = results.filter(r => !!r.open).length;
          const filteredCount = results.filter(r => ((r && r.state) ? String(r.state).toLowerCase().trim() === 'filtered' : false)).length;
          return Object.assign({}, h, { results, openCount, filteredCount });
        });

        // sort hosts: those with any open ports first, then those with filtered ports, then by host string
        hosts.sort((a, b) => {
          if ((a.openCount > 0) !== (b.openCount > 0)) return (a.openCount > 0) ? -1 : 1;
          if ((a.filteredCount > 0) !== (b.filteredCount > 0)) return (a.filteredCount > 0) ? -1 : 1;
          return (a.host || '').localeCompare(b.host || '');
        });

        const cards = hosts.map(h => {
          if (h.error) {
            return `<div class="host-card" style="background:#071127;padding:12px;border-radius:8px;border:1px solid #0f1724;margin-bottom:10px;"><div style="font-weight:700">${escapeHtml(h.host || '')}</div><div style="color:#fca5a5;margin-top:6px">Error: ${escapeHtml(h.error)}</div></div>`;
          }
          const results = h.results || [];
          const openCount = h.openCount || 0;
          const closedCount = results.length - openCount;
          const portsHtml = results.map(r => {
            const rstate = (r && r.state) ? String(r.state).toLowerCase().trim() : '';
            let badge = '';
            if (rstate === 'filtered') {
              badge = '<span style="background:#f59e0b;color:#fff;padding:4px 6px;border-radius:6px;font-weight:600">FILTERED</span>';
            } else if (r.open) {
              badge = '<span style="background:#16a34a;color:#fff;padding:4px 6px;border-radius:6px;font-weight:600">OPEN</span>';
            } else {
              badge = '<span style="background:#ef4444;color:#fff;padding:4px 6px;border-radius:6px;font-weight:600">CLOSED</span>';
            }
            return `<div class="port-item" style="display:flex;justify-content:space-between;align-items:center;padding:6px 8px;border-radius:6px;background:#071827;margin-bottom:6px"><div><div style="font-weight:700">${escapeHtml(String(r.port))} · ${escapeHtml(r.service||'')}</div><div style="color:#9aa6b2;font-size:12px">${escapeHtml(r.protocol||'tcp')} ${r.product? '· '+escapeHtml(r.product):''}</div></div><div>${badge}</div></div>`;
          }).join('');

          // Host header: toggle, host name + summary, duration on same line
          return `<div class="host-card" data-host="${escapeHtml(h.host||'')}" style="background:#071127;padding:12px;border-radius:8px;border:1px solid #0f1724;margin-bottom:10px;">
            <div class="host-header" style="display:flex;justify-content:space-between;align-items:center">
              <div style="display:flex;align-items:center;gap:10px">
                <button class="host-toggle" aria-expanded="true" style="background:transparent;border:none;color:#cbd5e1;font-size:16px;cursor:pointer">▾</button>
                <div>
                  <div style="font-weight:700;display:flex;gap:10px;align-items:center">${escapeHtml(h.host||'')}</div>
                  <div style="color:#9aa6b2;font-size:12px;margin-top:4px">Puertos detectados: ${results.length} · Abiertos: ${openCount} · Cerrados: ${closedCount}</div>
                </div>
              </div>
              <div style="font-size:12px;color:#94a3b8" class="host-duration">${h.duration_seconds ? escapeHtml(String(h.duration_seconds))+'s' : ''}</div>
            </div>
            <div class="host-body" style="margin-top:10px">${portsHtml}</div>
          </div>`;
        }).join('');
        return `<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px">${cards}</div>`;
      } catch (e) { return renderRawJson(obj); }
    }

    /**
     * @brief Render a list of common network ports.
     * @param obj The ports list object.
     * @return HTML string.
     */
    function renderPortsList(obj) {
      try {
        const items = obj.common_ports || [];
        if (!items.length) return `<div style="color:#9aa6b2">No hay puertos comunes listados.</div>`;
        const cards = items.map(it => {
          const methods = (it.methods && it.methods.length) ? `<div style="margin-top:6px;color:#cbd5e1"><strong>Métodos:</strong> ${it.methods.map(m=>escapeHtml(m)).join(', ')}</div>` : '';
          const product = it.product ? `<div style="color:#9aa6b2;margin-top:6px;font-size:13px">${escapeHtml(it.product)}${it.version ? (' v' + escapeHtml(it.version)) : ''}</div>` : '';
          let statusBadge = '';
          if (it.state === 'filtered') {
            statusBadge = '<span style="background:#f59e0b;color:#fff;padding:4px 8px;border-radius:6px;font-weight:600">FILTERED</span>';
          } else {
            statusBadge = it.open ? '<span style="background:#16a34a;color:#fff;padding:4px 8px;border-radius:6px;font-weight:600">OPEN</span>' : '<span style="background:#ef4444;color:#fff;padding:4px 8px;border-radius:6px;font-weight:600">CLOSED</span>';
          }
          // Exact HTML structure and sizing to match the original "List Common Ports" view, with status badge
          return `<div class="port-card" style="background:#071127;padding:12px;border-radius:8px;border:1px solid #0f1724;margin-bottom:10px;display:flex;justify-content:space-between;align-items:center">
            <div>
              <div style="font-weight:700;font-size:16px">${escapeHtml(String(it.port))}</div>
              <div style="color:#9aa6b2;margin-top:4px">${escapeHtml(it.service || '')}</div>
              ${product}
              ${methods}
            </div>
            <div style="display:flex;flex-direction:column;align-items:flex-end;gap:6px">
              <div style="font-size:12px;color:#94a3b8">Puerto</div>
              ${statusBadge}
            </div>
          </div>`;
        }).join('');
        return `<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px">${cards}</div>`;
      } catch (e) { return renderRawJson(obj); }
    }

    /**
     * @brief Render raw JSON as a formatted panel.
     * @param obj The object to render.
     * @return HTML string.
     */
    function renderRawJson(obj) { const jsonText = escapeHtml(JSON.stringify(obj, null, 2)); const header = `<div style="display:flex;justify-content:space-between;align-items:center;gap:8px;"><div class=\"response-meta\">JSON crudo</div><div><button class=\"panel-toggle\">▾</button> <button class=\"copy-json-btn\" type=\"button\">Copiar JSON</button></div></div>`; return `<div class="panel"><div class="panel-head">${header}</div><div class="panel-body"><div class="raw-box"><pre>${jsonText}</pre></div></div></div>`; }

    /**
     * @brief Submit an API operation form and render the result.
     * @param op The operation object.
     * @param formData The form data to submit.
     * @return void
     */
    async function submitOperation(op, formData) {
      const url = API_BASE + op.path; if (opResult) { opResult.style.display = 'block'; opResult.innerHTML = `<div class="response-meta">Cargando...</div>`; }
      try {
        let resp;
        if (op.method === "GET") { const params = new URLSearchParams(); for (const [k, v] of formData.entries()) if (v) params.append(k, v); const final = params.toString() ? url + "?" + params.toString() : url; resp = await fetch(final); }
        else {
          const obj = {};
          for (const [k, v] of formData.entries()) {
            // skip empty string fields to avoid validation errors (422)
            if (typeof v === 'string' && v.trim() === '') continue;
            let val = v;
            if (typeof v === 'string') {
              const lv = v.toLowerCase();
              if (v === 'on' || lv === 'true') val = true;
              else if (lv === 'false') val = false;
            }
            obj[k] = val;
          }
          // parse ports field if provided as comma-separated string
          if (obj.ports && typeof obj.ports === 'string') {
            const raw = obj.ports.trim();
            if (raw === '') delete obj.ports;
            else {
              obj.ports = raw.split(',').map(s => parseInt(s.trim(), 10)).filter(n => !Number.isNaN(n));
            }
          }
          resp = await fetch(url, { method: op.method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(obj) });
        }
        const text = await resp.text();
        try {
          const j = JSON.parse(text);
          if (op.path === '/network/scan') {
            // Normalize scan results to the same structure used by renderPortsList
            try {
              const results = Array.isArray(j.results) ? j.results : [];
              const items = results.map(r => ({
                port: r.port,
                service: r.service || '',
                methods: Array.isArray(r.methods) ? r.methods : [],
                product: r.product || '',
                version: r.version || '',
                vulnerabilities: Array.isArray(r.vulnerabilities) ? r.vulnerabilities : [],
                open: !!r.open,
                state: (r && r.state) ? String(r.state).toLowerCase().trim() : '',
                host: j.host || undefined,
                protocol: r.protocol || 'tcp'
              }));
              // Orden: primero abiertos (open=true), luego por número de puerto ascendente
              items.sort((a, b) => {
                if (a.open === b.open) return (Number(a.port) || 0) - (Number(b.port) || 0);
                return a.open ? -1 : 1;
              });
              if (opResult) opResult.innerHTML = renderPortsList({ common_ports: items });
            } catch (e) {
              if (opResult) opResult.innerHTML = renderRawJson(j);
            }
          } else if (op.path === '/network/ports') {
            if (opResult) opResult.innerHTML = renderPortsList(j);
          } else if (op.path === '/network/scan_range') {
            try {
              if (opResult) {
                opResult.innerHTML = renderRangeScanResult(j);
                // attach collapse/expand handlers for host cards
                const hostToggles = opResult.querySelectorAll('.host-toggle');
                hostToggles.forEach(btn => {
                  btn.addEventListener('click', () => {
                    const hostCard = btn.closest('.host-card');
                    if (!hostCard) return;
                    const body = hostCard.querySelector('.host-body');
                    const expanded = btn.getAttribute('aria-expanded') === 'true';
                    btn.setAttribute('aria-expanded', expanded ? 'false' : 'true');
                    btn.textContent = expanded ? '▸' : '▾';
                    if (body) body.style.display = expanded ? 'none' : '';
                  });
                });
              }
            } catch (e) {
              if (opResult) opResult.innerHTML = renderRawJson(j);
            }
          } else {
            if (opResult) opResult.innerHTML = `<div class="response-two-col"><div class="left-pane">${renderResponse(j, resp.status)}</div><div class="right-pane">${renderRawJson(j)}</div></div>`;
            const copyBtn = opResult && opResult.querySelector('.right-pane .copy-json-btn');
            if (copyBtn) {
              copyBtn.addEventListener('click', async () => {
                try {
                  const textToCopy = JSON.stringify(j, null, 2);
                  if (navigator.clipboard && navigator.clipboard.writeText) {
                    await navigator.clipboard.writeText(textToCopy);
                  } else {
                    const ta = document.createElement('textarea'); ta.value = textToCopy; document.body.appendChild(ta); ta.select(); document.execCommand('copy'); document.body.removeChild(ta);
                  }
                  showToast('JSON copiado');
                } catch (e) { showToast('Error copiando JSON'); }
              });
            }
          }
          const toggles = opResult && opResult.querySelectorAll('.panel-toggle'); if (toggles) toggles.forEach(t => { t.addEventListener('click', () => { const panel = t.closest('.panel'); if (!panel) return; const body = panel.querySelector('.panel-body'); const isCollapsed = panel.classList.toggle('collapsed'); if (body) body.style.display = isCollapsed ? 'none' : ''; t.textContent = isCollapsed ? '▸' : '▾'; }); });
          try { const workerStartPaths = new Set(['/newsSpider/scrape-news','/newsSpider/start-google-alerts','/newsSpider/scrapy/google-dk/news','/newsSpider/scrapy/google-dk/feeds','/start-spacy','/postgre-ttrss/search-and-insert-rss','/llm/updater']); if (workerStartPaths.has(op.path) && resp.ok) { showToast(op.title + ' iniciada'); } } catch (e) {}
        } catch (e) {
          const t = text || '';
          const maybeMd = t && (t.trim().startsWith('#') || t.includes('\n\n') || t.includes('```'));
          if (maybeMd) {
            try {
              await ensureMarked();
              if (opResult) opResult.innerHTML = `<div class="response-box">${window.marked.parse(t)}</div>`;
            } catch (me) {
              if (opResult) opResult.innerHTML = `<pre>${escapeHtml(t)}</pre>`;
            }
          } else {
            if (opResult) opResult.innerHTML = `<pre>${escapeHtml(t)}</pre>`;
          }
        }
      } catch (err) { if (opResult) opResult.innerHTML = `<div class="response-error">Error: ${escapeHtml(String(err))}</div>`; }
      finally { try { if (typeof fetchStatus === 'function') fetchStatus(); } catch (e) {} try { window.dispatchEvent(new Event('status-updated')); } catch (e) {} }
    }

    renderControllers();

    async function fetchStatus() {
      try { const resp = await fetch((window.__CYBERMIND_API_BASE__ || API_BASE) + '/status'); if (!resp.ok) throw new Error('HTTP ' + resp.status); const j = await resp.json(); const statusJson = document.getElementById('status-json'); const statusSummary = document.getElementById('status-summary'); if (statusJson) { try { statusJson.textContent = JSON.stringify(j, null, 2); } catch (e) { statusJson.textContent = String(j); } } if (statusSummary) { const workers = j.workers || {}; const running = Object.entries(workers).filter(([k,v])=>v).map(([k])=>k).join(', ') || 'ninguno'; statusSummary.textContent = `Infra: ${j.infra_ready ? 'OK' : 'NO'} · UI init: ${j.ui_initialized ? 'sí' : 'no'} · Workers: ${running}`; } }
      catch (err) { }
    }

    const btnStatusView = document.getElementById('btn-refresh-status-view'); if (btnStatusView) btnStatusView.addEventListener('click', fetchStatus);
    fetchStatus(); setInterval(fetchStatus, 10000);
  })();

  // --- LLM client ---
  // Handles chat UI for LLM queries
  (function () {
    const messagesEl = document.getElementById("llm-messages");
    const promptEl = document.getElementById("llm-prompt");
    const sendBtn = document.getElementById("llm-send-btn");
    const LLM_API_BASE = window.__CYBERMIND_API_BASE__ || "http://127.0.0.1:8000";
    if (!messagesEl || !promptEl || !sendBtn) return;
    /**
     * @brief Append a message to the LLM chat window.
     * @param text The message text.
     * @param role 'user' or 'bot'.
     * @return void
     */
    function appendMessage(text, role) {
      const wrapper = document.createElement("div"); const span = document.createElement("span");
      if (role === "user") {
        wrapper.className = "user-message"; span.textContent = text;
      } else {
        wrapper.className = "bot-message";
        const html = window.marked ? window.marked.parse(text) : escapeHtml(text);
        span.innerHTML = html;
        if (!window.marked && text && (text.trim().startsWith('#') || text.includes('\n\n') || text.includes('```'))) {
          ensureMarked().then(() => { try { span.innerHTML = window.marked.parse(text); messagesEl.scrollTop = messagesEl.scrollHeight; } catch (e) {} });
        }
      }
      wrapper.appendChild(span); messagesEl.appendChild(wrapper); messagesEl.scrollTop = messagesEl.scrollHeight;
    }
    
    /**
     * @brief Send the user prompt to the LLM API and display the response.
     * @return void
     */
    async function sendPrompt() {
      const prompt = promptEl.value.trim(); if (!prompt) return; appendMessage("Tú: " + prompt, "user"); promptEl.value = ""; sendBtn.disabled = true;
      try { const response = await fetch(LLM_API_BASE + "/llm/query", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ prompt: prompt }) }); const data = await response.json(); appendMessage(data.response || "[Respuesta vacía]", "bot"); }
      catch (err) { appendMessage("Error llamando al LLM: " + err, "bot"); }
      finally { sendBtn.disabled = false; promptEl.focus(); }
    }
    sendBtn.addEventListener("click", sendPrompt);
    promptEl.addEventListener("keydown", function (e) { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendPrompt(); } });
  })();

});
