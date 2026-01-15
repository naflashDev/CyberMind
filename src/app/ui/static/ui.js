document.addEventListener('DOMContentLoaded', function () {
  // Sidebar / view switching
  const sidebar = document.getElementById("sidebar");
  const btnToggle = document.getElementById("btn-toggle");

  const buttons = document.querySelectorAll(".nav-button");
  const views = {
    fastapi: document.getElementById("view-fastapi"),
    datos: document.getElementById("view-datos"),
    tiny: document.getElementById("view-tiny"),
    llm: document.getElementById("view-llm"),
    status: document.getElementById("view-status"),
  };

  function activateView(viewName) {
    buttons.forEach(btn => btn.classList.remove("active"));
    const activeBtn = document.querySelector(`.nav-button[data-view="${viewName}"]`);
    if (activeBtn) activeBtn.classList.add("active");
    Object.values(views).forEach(v => v.classList.remove("active"));
    if (views[viewName]) views[viewName].classList.add("active");
  }

  buttons.forEach(btn => {
    btn.addEventListener("click", () => {
      const view = btn.dataset.view;
      activateView(view);
    });
  });

  if (btnToggle) btnToggle.addEventListener("click", () => {
    const hidden = sidebar.classList.toggle("hidden");
    btnToggle.innerHTML = hidden ? "☰" : "«";
  });

  activateView("fastapi");

  // FastAPI operations panel
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
          opBtn.textContent = op.title;
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
            const icon = header.querySelector('.toggle-icon'); if (icon) icon.textContent = '▾';
            // highlight the new scan_range op if present
            const btn = sec.querySelector('.op-btn');
            const rangeBtn = sec.querySelector('button.op-btn[data-op-id="network-scan-range"]');
            if (!rangeBtn) {
              // fallback: find by title text
              const all = sec.querySelectorAll('button.op-btn');
              all.forEach(b => { if (b.textContent && b.textContent.toLowerCase().includes('rango')) { b.style.boxShadow = '0 0 0 2px rgba(37,99,235,0.15)'; b.style.border = '1px solid #2563eb'; } });
            } else {
              rangeBtn.style.boxShadow = '0 0 0 2px rgba(37,99,235,0.15)'; rangeBtn.style.border = '1px solid #2563eb';
            }
          }
        });
      } catch (e) { console.log('renderControllers post-process error', e); }
    }

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

    function escapeHtml(unsafe) { return String(unsafe).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/\"/g, "&quot;").replace(/'/g, "&#039;"); }

    function showToast(msg, ms = 1800) {
      try { const t = document.createElement('div'); t.className = 'toast'; t.textContent = msg; document.body.appendChild(t); void t.offsetWidth; t.classList.add('show'); setTimeout(() => { t.classList.remove('show'); setTimeout(() => t.remove(), 200); }, ms); } catch (e) { console.log('toast', e); }
    }

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

    function renderRawJson(obj) { const jsonText = escapeHtml(JSON.stringify(obj, null, 2)); const header = `<div style="display:flex;justify-content:space-between;align-items:center;gap:8px;"><div class=\"response-meta\">JSON crudo</div><div><button class=\"panel-toggle\">▾</button> <button class=\"copy-json-btn\" type=\"button\">Copiar JSON</button></div></div>`; return `<div class="panel"><div class="panel-head">${header}</div><div class="panel-body"><div class="raw-box"><pre>${jsonText}</pre></div></div></div>`; }

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
          const t = text || ''; const maybeMd = window.marked && (t.trim().startsWith('#') || t.includes('\n\n') || t.includes('```'));
          if (maybeMd) { try { if (opResult) opResult.innerHTML = `<div class="response-box">${window.marked.parse(t)}</div>`; } catch (me) { if (opResult) opResult.innerHTML = `<pre>${escapeHtml(t)}</pre>`; } }
          else { if (opResult) opResult.innerHTML = `<pre>${escapeHtml(t)}</pre>`; }
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

  // LLM client
  (function () {
    const messagesEl = document.getElementById("llm-messages");
    const promptEl = document.getElementById("llm-prompt");
    const sendBtn = document.getElementById("llm-send-btn");
    const LLM_API_BASE = window.__CYBERMIND_API_BASE__ || "http://127.0.0.1:8000";
    if (!messagesEl || !promptEl || !sendBtn) return;
    function appendMessage(text, role) {
      const wrapper = document.createElement("div"); const span = document.createElement("span");
      if (role === "user") { wrapper.className = "user-message"; span.textContent = text; }
      else { wrapper.className = "bot-message"; const html = window.marked ? window.marked.parse(text) : text; span.innerHTML = html; }
      wrapper.appendChild(span); messagesEl.appendChild(wrapper); messagesEl.scrollTop = messagesEl.scrollHeight;
    }
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
