const form = document.getElementById("form-archivo");
const inputArchivo = document.getElementById("archivo-zip");
const btnPredecir = document.getElementById("btn-predecir");
const errorEl = document.getElementById("error-archivo");
const resultadosEl = document.getElementById("resultados");
const resumenCiclos = document.getElementById("resumen-ciclos");
const contenedorCiclos = document.getElementById("contenedor-ciclos");
const estadoModelo = document.getElementById("estado-modelo");
const zonaCarga = document.getElementById("zona-carga");
const nombreArchivo = document.getElementById("nombre-archivo");

async function consultarEstado() {
  try {
    const resp = await fetch("/api/estado");
    const datos = await resp.json();
    if (datos.modelo_disponible) {
      estadoModelo.textContent = "Modelo cargado";
      estadoModelo.className = "estado-modelo ok";
    } else {
      estadoModelo.textContent =
        "Sin modelo en el servidor: coloque los artefactos en web/modelo/";
      estadoModelo.className = "estado-modelo aviso";
    }
  } catch {
    estadoModelo.textContent = "No se pudo consultar el servidor";
    estadoModelo.className = "estado-modelo aviso";
  }
}

function mostrarError(mensaje) {
  errorEl.textContent = mensaje;
  errorEl.hidden = false;
}

function limpiarError() {
  errorEl.hidden = true;
  errorEl.textContent = "";
}

function mostrarNombreArchivo(archivo) {
  if (!archivo) {
    nombreArchivo.hidden = true;
    nombreArchivo.textContent = "";
    return;
  }
  nombreArchivo.textContent =
    archivo.name + " · " + (archivo.size / (1024 * 1024)).toFixed(2) + " MB";
  nombreArchivo.hidden = false;
}

function crearBarra(probabilidad) {
  const cont = document.createElement("div");
  cont.className = "barra-prob";
  const relleno = document.createElement("div");
  relleno.className = "barra-relleno";
  relleno.style.width = (probabilidad * 100).toFixed(1) + "%";
  const texto = document.createElement("span");
  texto.textContent = (probabilidad * 100).toFixed(1) + " %";
  cont.appendChild(relleno);
  cont.appendChild(texto);
  return cont;
}

function crearTarjeta(titulo, dato, etiquetasClase) {
  const tarjeta = document.createElement("div");
  tarjeta.className = "tarjeta-resultado";
  const h3 = document.createElement("h3");
  h3.textContent = titulo;
  const p = document.createElement("p");
  p.className = "prediccion";
  p.textContent = dato.etiqueta;
  tarjeta.appendChild(h3);
  tarjeta.appendChild(p);
  const lista = document.createElement("div");
  lista.className = "lista-probs";
  dato.probabilidades.forEach((prob, i) => {
    const fila = document.createElement("div");
    fila.className = "fila-prob";
    const nombre = document.createElement("span");
    nombre.textContent = etiquetasClase[i];
    fila.appendChild(nombre);
    fila.appendChild(crearBarra(prob));
    lista.appendChild(fila);
  });
  tarjeta.appendChild(lista);
  return tarjeta;
}

const ETIQUETAS = {
  cooler: ["3 %", "20 %", "100 %"],
  valvula: ["73 %", "80 %", "90 %", "100 %"],
  bomba: ["0 fugas", "1 fuga", "2 fugas"],
};

const ICONS = {
  layers: `<svg class="icono-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>`,
  alertTriangle: `<svg class="icono-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`,
  alertCircle: `<svg class="icono-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`,
  checkCircle: `<svg class="icono-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/></svg>`,

  bannerDanger: `<svg class="icono-svg lg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`,
  bannerWarning: `<svg class="icono-svg lg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`,
  bannerOk: `<svg class="icono-svg lg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/></svg>`,

  bot: `<svg class="icono-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/></svg>`,
  target: `<svg class="icono-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>`,
  fileText: `<svg class="icono-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/></svg>`,
  brain: `<svg class="icono-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 1.98-3A2.5 2.5 0 0 1 9.5 2Z"/><path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-1.98-3A2.5 2.5 0 0 0 14.5 2Z"/></svg>`,
  thumbsUp: `<svg class="icono-svg-solid" viewBox="0 0 512 512" fill="currentColor"><path d="M313.4 32.9c26 5.2 45.5 27.9 45.5 54.4V144h80.4c36.7 0 64.9 33.2 57.6 69.1l-36.4 178.6C454.7 421.1 428.8 448 398 448H160c-17.7 0-32-14.3-32-32V192c0-8.5 3.4-16.6 9.4-22.6l125.7-125.7c14.2-14.2 34.6-21.4 54.3-17.5zM48 192h48c8.8 0 16 7.2 16 16v192c0 8.8-7.2 16-16 16H48c-8.8 0-16-7.2-16-16V208c0-8.8 7.2-16 16-16z"/></svg>`,
  thumbsDown: `<svg class="icono-svg-solid" viewBox="0 0 512 512" fill="currentColor"><path d="M313.4 479.1c26-5.2 45.5-27.9 45.5-54.4V368h80.4c36.7 0 64.9-33.2 57.6-69.1l-36.4-178.6C454.7 90.9 428.8 64 398 64H160c-17.7 0-32 14.3-32 32v224c0 8.5 3.4 16.6 9.4 22.6l125.7 125.7c14.2 14.2 34.6 21.4 54.3 17.5zM48 320h48c8.8 0 16-7.2 16-16V112c0-8.8-7.2-16-16-16H48c-8.8 0-16 7.2-16 16v192c0 8.8 7.2 16 16 16z"/></svg>`,
  star: `<svg class="icono-svg star" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="1.5"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>`,
  check: `<svg class="icono-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>`,
  sparkles: `<svg class="icono-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3L12 3Z"/><path d="M5 3v4"/><path d="M19 17v4"/><path d="M3 5h4"/><path d="M17 19h4"/></svg>`,
  sliders: `<svg class="icono-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="4" y1="21" x2="4" y2="14"/><line x1="4" y1="10" x2="4" y2="3"/><line x1="12" y1="21" x2="12" y2="12"/><line x1="12" y1="8" x2="12" y2="3"/><line x1="20" y1="21" x2="20" y2="16"/><line x1="20" y1="12" x2="20" y2="3"/><line x1="1" y1="14" x2="7" y2="14"/><line x1="9" y1="8" x2="15" y2="8"/><line x1="17" y1="16" x2="23" y2="16"/></svg>`,
  xCircle: `<svg class="icono-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>`
};

function formatearMarkdown(texto) {
  if (!texto) return "";
  let seguro = texto
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  seguro = seguro.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
  seguro = seguro.replace(/__(.*?)__/g, "<strong>$1</strong>");
  seguro = seguro.replace(/\*(.*?)\*/g, "<em>$1</em>");

  const lineas = seguro.split("\n");
  let html = "";
  let enSublista = false;
  let enPaso = false;

  for (let rawLinea of lineas) {
    let linea = rawLinea.trim();
    if (!linea) {
      if (enSublista) {
        html += "</ul>";
        enSublista = false;
      }
      continue;
    }

    if (linea.startsWith("---")) {
      if (enSublista) { html += "</ul>"; enSublista = false; }
      if (enPaso) { html += "</div>"; enPaso = false; }
      html += '<hr class="rec-hr" style="border:none;border-top:1px solid #e2e8f0;margin:12px 0;">';
      continue;
    }

    if (linea.startsWith("### ") || linea.startsWith("#### ")) {
      if (enSublista) { html += "</ul>"; enSublista = false; }
      if (enPaso) { html += "</div>"; enPaso = false; }
      const tit = linea.replace(/^#{3,4}\s+/, "");
      html += `<h4 class="rec-seccion-header" style="margin:14px 0 8px;color:#0f172a;font-size:0.95rem;font-weight:700;">${tit}</h4>`;
      continue;
    }

    let partesInline = [];
    if (linea.includes(" - ")) {
      partesInline = linea.split(/\s+-\s+/);
      linea = partesInline[0].trim();
    }

    const matchNum = linea.match(/^(\d+)\.\s*(.*)$/);
    const matchBullet = linea.match(/^[-*•]\s*(.*)$/);

    if (matchNum) {
      if (enSublista) {
        html += "</ul>";
        enSublista = false;
      }
      if (enPaso) {
        html += "</div>";
      }
      enPaso = true;
      html += `
        <div class="rec-paso">
          <div class="rec-paso-header">
            <span class="rec-badge-num">${matchNum[1]}</span>
            <div class="rec-paso-texto">${matchNum[2]}</div>
          </div>
      `;
    } else if (matchBullet) {
      if (!enSublista) {
        html += '<ul class="rec-sublista">';
        enSublista = true;
      }
      html += `<li>${matchBullet[1]}</li>`;
    } else {
      if (enSublista) {
        html += "</ul>";
        enSublista = false;
      }
      if (enPaso) {
        html += "</div>";
        enPaso = false;
      }
      html += `<p class="rec-parrafo">${linea}</p>`;
    }

    if (partesInline.length > 1) {
      if (!enSublista) {
        html += '<ul class="rec-sublista">';
        enSublista = true;
      }
      for (let i = 1; i < partesInline.length; i++) {
        html += `<li>${partesInline[i].trim()}</li>`;
      }
    }
  }

  if (enSublista) {
    html += "</ul>";
  }
  if (enPaso) {
    html += "</div>";
  }

  return html;
}

function renderizarResultados(datos) {
  contenedorCiclos.innerHTML = "";

  let totalCriticos = 0;
  let totalPreventivos = 0;
  let totalNormales = 0;

  datos.predicciones.forEach((pred) => {
    if (pred.falla) {
      if (pred.falla.alerta === "peligro") {
        totalCriticos++;
      } else if (pred.falla.alerta === "aviso") {
        totalPreventivos++;
      } else {
        totalNormales++;
      }
    }
  });

  resumenCiclos.innerHTML = `
    <div style="margin-bottom: 10px; color: #475569; font-size: 0.9rem;">
      <strong>Archivo:</strong> ${datos.archivo} · <strong>${datos.n_ciclos}</strong> ciclo(s) analizados · 
      ${datos.n_features} características por ciclo.
    </div>
    <div class="resumen-badges">
      <span class="badge-resumen total">
        ${ICONS.layers}
        <span>Total: <strong>${datos.n_ciclos}</strong> ciclo(s)</span>
      </span>
      <span class="badge-resumen peligro">
        ${ICONS.alertTriangle}
        <span>Riesgo Alto: <strong>${totalCriticos}</strong></span>
      </span>
      <span class="badge-resumen aviso">
        ${ICONS.alertCircle}
        <span>Preventivo: <strong>${totalPreventivos}</strong></span>
      </span>
      <span class="badge-resumen ok">
        ${ICONS.checkCircle}
        <span>Normal: <strong>${totalNormales}</strong></span>
      </span>
    </div>
  `;

  datos.predicciones.forEach((pred) => {
    const bloque = document.createElement("section");
    bloque.className = "bloque-ciclo";
    const h3 = document.createElement("h3");
    h3.textContent = "Ciclo " + pred.ciclo + " · " + datos.archivo;
    bloque.appendChild(h3);

    if (pred.falla) {
      const banner = document.createElement("div");
      const tipoAlerta = pred.falla.alerta || (pred.falla.va_a_fallar ? "peligro" : "ok");
      banner.className = "banner-falla alerta-" + tipoAlerta;

      const icono = tipoAlerta === "peligro" ? ICONS.bannerDanger : (tipoAlerta === "aviso" ? ICONS.bannerWarning : ICONS.bannerOk);
      banner.innerHTML = `
        <div class="falla-icono-wrapper ${tipoAlerta}">
          ${icono}
        </div>
        <div class="falla-info">
          <div class="falla-titulo-row">
            <span class="falla-titulo">${pred.falla.estado}</span>
            <span class="badge-falla-pct">${pred.falla.probabilidad_pct}% de riesgo</span>
          </div>
          <span class="falla-sub">${pred.falla.diagnostico || "Evaluación de condición del sistema hidráulico según la red neuronal."}</span>
        </div>
      `;
      bloque.appendChild(banner);
    }

    const rejilla = document.createElement("div");
    rejilla.className = "rejilla";
    rejilla.appendChild(crearTarjeta("Enfriador (cooler)", pred.cooler, ETIQUETAS.cooler));
    rejilla.appendChild(crearTarjeta("Válvula", pred.valvula, ETIQUETAS.valvula));
    rejilla.appendChild(crearTarjeta("Bomba", pred.bomba, ETIQUETAS.bomba));
    const tarjetaEf = document.createElement("div");
    tarjetaEf.className = "tarjeta-resultado";
    const hEf = document.createElement("h3");
    hEf.textContent = "Eficiencia hidráulica";
    const pEf = document.createElement("p");
    pEf.className = "prediccion grande";
    pEf.textContent = pred.eficiencia_pct.toFixed(2) + " %";
    const pNota = document.createElement("p");
    pNota.className = "nota";
    pNota.textContent = "Media por ciclo del sensor SE.";
    tarjetaEf.appendChild(hEf);
    tarjetaEf.appendChild(pEf);
    tarjetaEf.appendChild(pNota);
    rejilla.appendChild(tarjetaEf);
    bloque.appendChild(rejilla);

    if (pred.recomendacion_llm) {
      const rec = pred.recomendacion_llm;
      const recBox = document.createElement("div");
      recBox.className = "tarjeta-llm";
      recBox.innerHTML = `
        <div class="header-llm">
          <div class="titulo-llm">
            <div class="llm-icono-wrapper" title="Generado por Pipeline Autoregresivo de IA">
              ${ICONS.sparkles}
            </div>
            <div class="titulo-llm-texto">
              <div class="ai-pill-tag">
                <span class="ai-dot-pulse"></span>
                <span>Asistente Autónomo · IA Generativa</span>
              </div>
              <strong>Recomendación Técnica Especializada (Qwen-2.5 Instruct)</strong>
            </div>
          </div>
        </div>
        <div class="cuerpo-llm">${formatearMarkdown(rec.texto)}</div>

        <div class="panel-rlhf" id="feedback-ciclo-${pred.ciclo}">
          <div class="rlhf-header">
            <div class="rlhf-titulo">
              ${ICONS.brain}
              <div>
                <strong>Dictamen Técnico Operativo (Feedback RLHF · Contextual Q-Learning)</strong>
                <p class="rlhf-sub">Valida la viabilidad en planta para recalibrar en tiempo real la política óptima de Bellman:</p>
              </div>
            </div>
          </div>

          <div class="cuadricula-dictamenes">
            <button type="button" class="btn-dictamen opt-optima" onclick="enviarFeedback('${pred.estado_rl}', '${pred.accion_rl}', 1.0, ${pred.ciclo}, 'Acción Óptima')">
              <div class="dictamen-top">
                <span class="dictamen-icono">${ICONS.checkCircle}</span>
                <span class="dictamen-tag badge-r-pos">+1.00 Óptima</span>
              </div>
              <strong class="dictamen-nombre">Aprobada en Planta</strong>
              <span class="dictamen-desc">Plan seguro bajo LOTO, certero y priorizado</span>
            </button>

            <button type="button" class="btn-dictamen opt-ajuste" onclick="enviarFeedback('${pred.estado_rl}', '${pred.accion_rl}', 0.4, ${pred.ciclo}, 'Ajuste Operativo')">
              <div class="dictamen-top">
                <span class="dictamen-icono">${ICONS.sliders}</span>
                <span class="dictamen-tag badge-r-mod">+0.40 Ajustable</span>
              </div>
              <strong class="dictamen-nombre">Ajuste Menor</strong>
              <span class="dictamen-desc">Diagnóstico certero; requiere calibrar tiempos</span>
            </button>

            <button type="button" class="btn-dictamen opt-suboptima" onclick="enviarFeedback('${pred.estado_rl}', '${pred.accion_rl}', -0.5, ${pred.ciclo}, 'Subóptima')">
              <div class="dictamen-top">
                <span class="dictamen-icono">${ICONS.alertTriangle}</span>
                <span class="dictamen-tag badge-r-pen">-0.50 Subóptima</span>
              </div>
              <strong class="dictamen-nombre">Desproporcionada</strong>
              <span class="dictamen-desc">Intervención excesiva o tardía para el fallo</span>
            </button>

            <button type="button" class="btn-dictamen opt-riesgo" onclick="enviarFeedback('${pred.estado_rl}', '${pred.accion_rl}', -1.8, ${pred.ciclo}, 'Riesgo Crítico (Penalización Asimétrica)')">
              <div class="dictamen-top">
                <span class="dictamen-icono">${ICONS.xCircle}</span>
                <span class="dictamen-tag badge-r-neg">-1.80 Riesgo Asimétrico</span>
              </div>
              <strong class="dictamen-nombre">Riesgo Operativo</strong>
              <span class="dictamen-desc">Penalización severa por riesgo crítico o inviabilidad</span>
            </button>
          </div>

          <div class="msg-feedback" id="msg-fb-${pred.ciclo}" hidden></div>
        </div>
      `;
      bloque.appendChild(recBox);
    }

    contenedorCiclos.appendChild(bloque);
  });
  resultadosEl.hidden = false;
}

["dragenter", "dragover"].forEach((evento) => {
  zonaCarga.addEventListener(evento, (e) => {
    e.preventDefault();
    zonaCarga.classList.add("resaltada");
  });
});

["dragleave", "drop"].forEach((evento) => {
  zonaCarga.addEventListener(evento, (e) => {
    e.preventDefault();
    zonaCarga.classList.remove("resaltada");
  });
});

zonaCarga.addEventListener("drop", (evento) => {
  const archivo = evento.dataTransfer.files[0];
  if (!archivo) {
    return;
  }
  inputArchivo.files = evento.dataTransfer.files;
  limpiarError();
  mostrarNombreArchivo(archivo);
});

inputArchivo.addEventListener("change", () => {
  limpiarError();
  mostrarNombreArchivo(inputArchivo.files[0]);
});

form.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  limpiarError();
  resultadosEl.hidden = true;
  const archivo = inputArchivo.files[0];
  if (!archivo) {
    mostrarError("Selecciona un archivo ZIP de sensores.");
    return;
  }
  btnPredecir.disabled = true;
  btnPredecir.textContent = "Procesando...";
  const datos = new FormData();
  datos.append("archivo", archivo);
  try {
    const resp = await fetch("/api/predecir", { method: "POST", body: datos });
    const cuerpo = await resp.json();
    if (!resp.ok) {
      mostrarError(cuerpo.detail || "No se pudo procesar el archivo.");
      return;
    }
    renderizarResultados(cuerpo);
  } catch {
    mostrarError("Error de conexión con el servidor.");
  } finally {
    btnPredecir.disabled = false;
    btnPredecir.textContent = "Predecir estado";
  }
});

window.enviarFeedback = async function (estado, accion, calificacion, ciclo, dictamen) {
  const cont = document.getElementById("feedback-ciclo-" + ciclo);
  const msg = document.getElementById("msg-fb-" + ciclo);
  try {
    const resp = await fetch("/api/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ estado, accion, calificacion, ciclo, dictamen }),
    });
    const res = await resp.json();
    if (resp.ok && res.registro) {
      cont.querySelectorAll(".btn-dictamen").forEach((b) => (b.disabled = true));
      const r = res.registro;
      const signoR = r.recompensa >= 0 ? "+" : "";
      const signoTD = r.td_error >= 0 ? "+" : "";
      msg.innerHTML = `
        <div class="telemetria-rl-box">
          <div class="telemetria-head">
            ${ICONS.check}
            <strong>Dictamen Registrado en el Agente de Aprendizaje por Refuerzo</strong>
            <span class="badge-dictamen-tag">${dictamen || r.dictamen}</span>
          </div>
          <div class="telemetria-grid">
            <div><span>Estado del Sistema</span><code>${r.estado}</code></div>
            <div><span>Estrategia Evaluada</span><code>${r.accion}</code></div>
            <div><span>Recompensa (R)</span><strong>${signoR}${r.recompensa.toFixed(2)}</strong></div>
            <div><span>TD-Error (δ)</span><strong>${signoTD}${r.td_error}</strong></div>
            <div><span>Q Anterior</span><code>${r.q_anterior}</code></div>
            <div><span>Q Nuevo (Bellman)</span><strong class="q-destacado">${r.q_nuevo}</strong></div>
          </div>
          <div class="telemetria-footer">
            <span>${ICONS.check} Actualización de Bellman completada (α = ${r.alpha || 0.25}) · Persistido en <code>rl_q_table.json</code> · Matriz Q actualizada en tiempo real</span>
          </div>
        </div>
      `;
      msg.hidden = false;
      cargarTablaQ();
    }
  } catch (e) {
    msg.textContent = "Error al conectar con el agente RL para registrar el feedback.";
    msg.className = "msg-feedback error";
    msg.hidden = false;
  }
};

window.cargarTablaQ = async function () {
  const contenedor = document.getElementById("contenedor-tabla-q");
  if (!contenedor) return;
  try {
    const resp = await fetch("/api/rl/estado");
    const datos = await resp.json();
    const qTable = datos.q_table;
    const acciones = Object.keys(datos.acciones);

    let html = `<table class="tabla-q"><thead><tr><th>Estado (Diagnóstico de Falla)</th>`;
    acciones.forEach((a) => {
      html += `<th>${datos.acciones[a].nombre}</th>`;
    });
    html += `</tr></thead><tbody>`;

    Object.keys(qTable).forEach((estado) => {
      html += `<tr><td><strong>${estado}</strong></td>`;
      const valores = qTable[estado];
      const maxVal = Math.max(...Object.values(valores));
      acciones.forEach((a) => {
        const val = valores[a];
        const esMejor = Math.abs(val - maxVal) < 1e-4;
        html += `<td class="${esMejor ? "mejor-accion" : ""}">${val.toFixed(4)}${esMejor ? " " + ICONS.star : ""}</td>`;
      });
      html += `</tr>`;
    });
    html += `</tbody></table>`;
    contenedor.innerHTML = html;
  } catch (e) {
    contenedor.innerHTML = "<p>No se pudo cargar la tabla Q.</p>";
  }
};

consultarEstado();
cargarTablaQ();
