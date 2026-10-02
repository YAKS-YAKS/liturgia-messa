"use strict";
/* Lumen — lecteur de textes du Magistère + panneau IA (clé de l'utilisateur, stockée localement). */

const $ = s => document.querySelector(s);
const esc = s => String(s == null ? "" : s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const store = {
  get(k, d) { try { const v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } },
  set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* stockage indisponible */ } },
};
const nrm = s => String(s).split("").map(c => c.normalize("NFD")[0].toLowerCase()).join("");
const toast = m => { const t = $("#toast"); t.textContent = m; t.hidden = false; clearTimeout(toast.t); toast.t = setTimeout(() => t.hidden = true, 2800); };

/* ---------- corpus ---------- */
let INDEX = null;           // liste des documents
const DOCS = {};            // id -> document complet
let ALL = null;             // paragraphes à plat, pour la recherche

async function loadIndex() {
  if (INDEX) return INDEX;
  try {
    const r = await fetch("data/documents/index.json");
    INDEX = r.ok ? await r.json() : [];
  } catch (e) { INDEX = []; }
  return INDEX;
}
async function loadDoc(id) {
  if (!DOCS[id]) {
    const r = await fetch("data/documents/" + encodeURIComponent(id) + ".json");
    if (!r.ok) throw new Error("Document introuvable : " + id);
    DOCS[id] = await r.json();
  }
  return DOCS[id];
}
const paraText = p => typeof p === "string" ? p : (p && (p.texte || p.text)) || "";

function flatten(doc) {
  const out = [];
  (doc.introduction || []).forEach((t, i) => out.push({ doc: doc.id, ref: "Introduction", text: paraText(t), key: `i-${i}` }));
  (doc.chapitres || []).forEach((c, ci) => (c.sections || []).forEach((s, si) =>
    (s.paragraphes || []).forEach((p, pi) => out.push({
      doc: doc.id, key: `p-${ci}-${si}-${pi}`, text: paraText(p),
      ref: `${s.numero != null && s.numero !== "" ? "n° " + s.numero : "§"}${s.titre ? " — " + s.titre : ""}`,
    }))));
  return out;
}
async function loadAll() {
  if (ALL) return ALL;
  const idx = await loadIndex();
  const docs = await Promise.all(idx.map(d => loadDoc(d.id).catch(() => null)));
  ALL = docs.filter(Boolean).flatMap(flatten).map(e => Object.assign(e, { n: nrm(e.text) }));
  return ALL;
}

/* ---------- routage ---------- */
window.addEventListener("hashchange", route);
$("#home").onclick = () => { location.hash = "#/"; };
$("#q").addEventListener("keydown", e => { if (e.key === "Enter" && e.target.value.trim()) location.hash = "#/s/" + encodeURIComponent(e.target.value.trim()); });

function route() {
  closeIA();
  const [, kind, a, b] = location.hash.split("/").map(decodeURIComponent);
  if (kind === "d" && a) return viewDoc(a, b);
  if (kind === "s" && a) return viewSearch(a);
  viewHome();
}

/* ---------- accueil ---------- */
let motFiltre = null;
async function viewHome() {
  const idx = await loadIndex();
  const m = $("#main");
  if (!idx.length) {
    m.innerHTML = `<h1>Lumen</h1><div class="empty"><p><b>Aucun texte chargé.</b></p>
      <p>Place le corpus dans <code>lumen/data/documents/</code> : un fichier <code>index.json</code> et un fichier <code>&lt;id&gt;.json</code> par document (format produit par <code>scripts/construire_vatican2.py</code>), puis recharge cette page.</p>
      <p class="muted">Les réglages de l'IA restent accessibles via « ⚙︎ IA ».</p></div>`;
    return;
  }
  const mots = [...new Set(idx.flatMap(d => d.mots_cles || []))].sort((x, y) => x.localeCompare(y, "fr"));
  const cats = [...new Set(idx.map(d => d.categorie || "Autres"))];
  let h = `<h1>Lumen</h1><p class="muted">Textes du Magistère, avec analyse, commentaire et réflexion assistés par IA. Sélectionne un mot ou un passage pour l'interroger.</p>`;
  h += `<div class="chips" id="kw">${mots.map(w => `<button class="chip" aria-pressed="${w === motFiltre}" data-w="${esc(w)}">${esc(w)}</button>`).join("")}</div>`;
  for (const c of cats) {
    const l = idx.filter(d => (d.categorie || "Autres") === c && (!motFiltre || (d.mots_cles || []).includes(motFiltre)));
    if (!l.length) continue;
    h += `<div class="cat">${esc(c)}</div>` + l.map(d => `<button class="card" data-id="${esc(d.id)}"><b>${esc(d.titre)}</b>
      <div class="muted">${esc(d.sous_titre || "")}${d.date ? " · " + esc(d.date) : ""}</div>
      ${d.resume ? `<div class="muted">${esc(d.resume)}</div>` : ""}</button>`).join("");
  }
  h += `<p class="muted">Écrits franciscains : voir <a href="../sources-franciscaines/">Sources franciscaines</a>.</p>`;
  m.innerHTML = h;
  m.querySelectorAll(".card").forEach(b => b.onclick = () => { location.hash = "#/d/" + encodeURIComponent(b.dataset.id); });
  m.querySelectorAll(".chip").forEach(b => b.onclick = () => { motFiltre = motFiltre === b.dataset.w ? null : b.dataset.w; viewHome(); });
  window.scrollTo(0, 0);
}

/* ---------- lecteur ---------- */
let CUR = null; // document affiché
async function viewDoc(id, anchor) {
  const m = $("#main");
  m.innerHTML = `<p class="muted">Chargement…</p>`;
  let d;
  try { d = await loadDoc(id); } catch (e) { m.innerHTML = `<div class="empty">${esc(e.message)}</div>`; return; }
  CUR = d;
  const meta = (await loadIndex()).find(x => x.id === id) || {};
  let h = `<h1>${esc(d.titre)}</h1><p class="muted">${esc(d.sous_titre || "")}${d.date ? " · " + esc(d.date) : ""}${d.promulgateur ? " · " + esc(d.promulgateur) : ""}</p>`;
  if (d.source) h += `<p class="muted">Source : ${esc(d.source)}</p>`;
  if (d.licence_note) h += `<p class="muted">${esc(d.licence_note)}</p>`;
  const chs = d.chapitres || [];
  if (chs.length > 1) h += `<details><summary>Plan</summary><ol>${chs.map((c, i) =>
    `<li><a href="#" data-go="c-${i}">${esc(c.titre || "Chapitre " + (c.numero || i + 1))}</a></li>`).join("")}</ol></details>`;
  h += `<div class="doc">`;
  if ((d.introduction || []).length) h += (d.introduction).map((t, i) => para(paraText(t), "", `i-${i}`)).join("");
  chs.forEach((c, ci) => {
    if (c.titre || c.numero) h += `<h2 id="c-${ci}">${c.numero ? "Chapitre " + esc(c.numero) + " — " : ""}${esc(c.titre || "")}</h2>`;
    else h += `<span id="c-${ci}"></span>`;
    (c.sections || []).forEach((s, si) => {
      const lab = (s.numero != null && s.numero !== "" ? s.numero + ". " : "") + (s.titre || "");
      if (s.sous_titre) h += `<p class="sub">${esc(s.sous_titre)}</p>`;
      h += `<div class="sec-h"><h3 id="s-${s.numero != null ? esc(s.numero) : ci + "-" + si}">${esc(lab)}</h3>
        <button class="ask" data-sec="${ci}-${si}" title="Interroger toute la section" aria-label="Interroger la section">✦</button></div>`;
      (s.paragraphes || []).forEach((p, pi) => { h += para(paraText(p), s.numero, `p-${ci}-${si}-${pi}`, pi === 0); });
    });
  });
  (d.annexes || []).forEach(a => {
    const titre = typeof a === "string" ? "" : (a.titre || "Annexe");
    const txt = typeof a === "string" ? [a] : (a.paragraphes || a.texte || []);
    h += `<h2>${esc(titre)}</h2>` + (Array.isArray(txt) ? txt : [txt]).map(t => para(paraText(t), "", "")).join("");
  });
  h += `</div>`;
  if ((d.notes || []).length) h += `<div class="notes"><b>Notes</b><ol>${d.notes.map(n => `<li>${esc(n)}</li>`).join("")}</ol></div>`;
  if (meta.mots_cles && meta.mots_cles.length) h += `<p class="muted">Mots-clés : ${meta.mots_cles.map(esc).join(", ")}</p>`;
  m.innerHTML = h;
  m.querySelectorAll("[data-go]").forEach(a => a.onclick = e => { e.preventDefault(); document.getElementById(a.dataset.go).scrollIntoView(); });
  m.querySelectorAll(".p .ask").forEach(b => b.onclick = () => askParagraph(b.closest(".p")));
  m.querySelectorAll(".sec-h .ask").forEach(b => b.onclick = () => askSection(b.dataset.sec));
  const t = anchor && document.getElementById(anchor);
  if (t) { t.scrollIntoView(); t.closest(".p") && t.closest(".p").classList.add("flash"); } else window.scrollTo(0, 0);
}
function para(text, num, key, first) {
  if (!text) return "";
  return `<p class="p" id="${esc(key)}" data-sec-num="${esc(num || "")}">${first && num ? `<span class="n">${esc(num)}</span>` : ""}${esc(text)}<button class="ask" title="Interroger ce passage" aria-label="Interroger ce passage">✦</button></p>`;
}
function sectionOf(el) {
  // titres du chapitre et de la section qui précèdent un élément du lecteur
  let h2 = null, h3 = null;
  for (let n = el; n && !(h2 && h3); n = n.previousElementSibling) {
    if (!h3 && n.classList.contains("sec-h")) h3 = n.querySelector("h3");
    if (!h2 && n.tagName === "H2") h2 = n;
  }
  return [h2, h3].filter(Boolean).map(x => x.textContent.trim()).join(" › ");
}
function askParagraph(p) {
  const c = p.cloneNode(true);
  c.querySelectorAll(".n,.ask").forEach(x => x.remove());
  openIA({ quote: c.textContent.trim(), where: sectionOf(p), kind: "passage" });
}
function askSection(key) {
  const [ci, si] = key.split("-").map(Number);
  const s = CUR.chapitres[ci].sections[si];
  const txt = (s.paragraphes || []).map(paraText).join("\n\n");
  openIA({ quote: txt, where: (CUR.chapitres[ci].titre || "") + " › " + (s.numero ? s.numero + ". " : "") + (s.titre || ""), kind: "section" });
}

/* sélection libre : mot, expression ou passage */
let selBtn = null;
document.addEventListener("selectionchange", () => {
  if (selBtn) { selBtn.remove(); selBtn = null; }
  const sel = getSelection();
  if (!sel || sel.isCollapsed || !sel.toString().trim()) return;
  const node = sel.anchorNode && (sel.anchorNode.nodeType === 1 ? sel.anchorNode : sel.anchorNode.parentElement);
  if (!node || !node.closest(".doc")) return;
  const r = sel.getRangeAt(0).getBoundingClientRect();
  selBtn = document.createElement("button");
  selBtn.className = "sel-btn"; selBtn.textContent = "✦ Interroger";
  selBtn.style.left = Math.max(8, Math.min(innerWidth - 130, r.left)) + "px";
  selBtn.style.top = Math.max(60, r.top - 44) + "px";
  const txt = sel.toString().trim(), where = sectionOf(node.closest(".p") || node);
  selBtn.onmousedown = selBtn.ontouchstart = e => e.preventDefault();
  selBtn.onclick = () => { openIA({ quote: txt, where, kind: txt.split(/\s+/).length <= 4 ? "mot" : "passage" }); getSelection().removeAllRanges(); };
  document.body.appendChild(selBtn);
});

/* ---------- recherche ---------- */
async function viewSearch(q) {
  $("#q").value = q;
  const m = $("#main");
  m.innerHTML = `<p class="muted">Recherche…</p>`;
  const all = await loadAll();
  const terms = nrm(q).split(/\s+/).filter(Boolean);
  const hits = [];
  for (const e of all) {
    if (!terms.every(t => e.n.includes(t))) continue;
    hits.push({ e, s: terms.reduce((a, t) => a + e.n.split(t).length - 1, 0) });
  }
  hits.sort((a, b) => b.s - a.s);
  const titre = id => (INDEX.find(d => d.id === id) || {}).titre || id;
  let h = `<h1>« ${esc(q)} »</h1><p class="muted">${hits.length} passage${hits.length > 1 ? "s" : ""}${hits.length > 80 ? " (80 premiers affichés)" : ""}</p>`;
  if (!all.length) h += `<div class="empty">Aucun corpus chargé.</div>`;
  h += hits.slice(0, 80).map(({ e }) => {
    const i = Math.max(0, e.n.indexOf(terms[0]) - 80);
    let snip = e.text.slice(i, i + 320);
    let out = esc(snip);
    if (e.n.length === e.text.length) {
      const sn = e.n.slice(i, i + 320), marks = [];
      terms.forEach(t => { let k = -1; while ((k = sn.indexOf(t, k + 1)) >= 0) marks.push([k, k + t.length]); });
      marks.sort((a, b) => a[0] - b[0]);
      let pos = 0; out = "";
      for (const [a, b] of marks) { if (a < pos) continue; out += esc(snip.slice(pos, a)) + "<mark>" + esc(snip.slice(a, b)) + "</mark>"; pos = b; }
      out += esc(snip.slice(pos));
    }
    return `<div class="hit" data-d="${esc(e.doc)}" data-k="${esc(e.key)}"><small>${esc(titre(e.doc))} · ${esc(e.ref)}</small>${i ? "… " : ""}${out}${e.text.length > i + 320 ? " …" : ""}</div>`;
  }).join("");
  m.innerHTML = h;
  m.querySelectorAll(".hit").forEach(x => x.onclick = () => { location.hash = `#/d/${encodeURIComponent(x.dataset.d)}/${encodeURIComponent(x.dataset.k)}`; });
  window.scrollTo(0, 0);
}

/* ---------- IA ---------- */
const PROV = {
  anthropic: { label: "Anthropic", model: "claude-sonnet-5-5" },
  deepseek: { label: "DeepSeek", model: "deepseek-chat", url: "https://api.deepseek.com" },
  openai: { label: "OpenAI-compatible", model: "", url: "" },
};
const MODES = {
  analyse: { label: "Analyse", brief: "Analyse le texte : ce qu'il affirme exactement, sa structure logique, ses termes clés (sens précis, sources bibliques ou patristiques SI le texte les cite), le degré d'autorité du document et la portée doctrinale de ce passage (affirmation dogmatique, enseignement, exhortation, orientation pastorale). Reste près de la lettre." },
  commentaire: { label: "Commentaire", brief: "Commente le passage : contexte historique et rédactionnel du concile, enjeux débattus à l'époque, liens avec d'autres passages du même document ou d'autres documents du Magistère, lecture dans la Tradition, et réception ou controverses d'interprétation connues." },
  reflexion: { label: "Réflexion", brief: "Propose une réflexion critique et personnelle : forces, tensions internes, ambiguïtés, objections sérieuses (y compris celles de traditions ou de courants opposés), questions que le texte laisse ouvertes, et ce qu'il demande concrètement à un chrétien — avec un éclairage franciscain si c'est pertinent et non forcé." },
};
const SYSTEM = `Tu es un théologien catholique rigoureux qui répond en français. Règles impératives :
1. Sincérité avant tout : aucune complaisance, aucune flatterie, aucune langue de bois. Si un passage est ambigu, contesté, daté ou fragile, dis-le franchement. Si une objection est forte, présente-la dans sa meilleure version.
2. Véracité : distingue toujours (a) ce que le texte fourni dit, (b) ce que tu en déduis, (c) ce qui relève de l'opinion théologique ou de débats d'interprétation. N'invente jamais de citation, de numéro de paragraphe, de date ni de référence. Si tu n'es pas certain d'un fait extérieur au texte fourni, écris « à vérifier » ou dis que tu ne sais pas.
3. Ne cite le texte que d'après l'extrait fourni ; marque clairement les citations entre guillemets.
4. Fidélité : respecte la lettre du texte et le genre du document ; ne lui fais pas dire plus ou moins que ce qu'il dit.
5. Réponse structurée, dense, sans remplissage : paragraphes courts et listes à puces si utile. Pas de préambule ni de conclusion de politesse.`;

let ctx = null, mode = "analyse";
function openIA(c) {
  ctx = c;
  $("#ia-title").textContent = { mot: "Mot ou expression", passage: "Passage", section: "Section" }[c.kind] || "Passage";
  $("#ia-quote").textContent = c.quote.length > 600 ? c.quote.slice(0, 600) + "…" : c.quote;
  $("#ia-q").value = ""; $("#ia-out").innerHTML = "";
  renderModes(); $("#ia").hidden = false;
}
function closeIA() { $("#ia").hidden = true; }
$("#ia-close").onclick = closeIA;
function renderModes() {
  $("#ia-modes").innerHTML = Object.entries(MODES).map(([k, v]) => `<button data-m="${k}" aria-pressed="${k === mode}">${v.label}</button>`).join("");
  $("#ia-modes").querySelectorAll("button").forEach(b => b.onclick = () => { mode = b.dataset.m; renderModes(); });
}
function md(t) {
  const lines = esc(t).split("\n"); let out = "", ul = false;
  for (const l of lines) {
    const li = l.match(/^\s*[-*•]\s+(.*)/);
    if (li && !ul) { out += "<ul>"; ul = true; } else if (!li && ul) { out += "</ul>"; ul = false; }
    const f = s => s.replace(/\*\*(.+?)\*\*/g, "<b>$1</b>").replace(/(^|[^*])\*([^*\n]+)\*/g, "$1<i>$2</i>");
    out += li ? `<li>${f(li[1])}</li>` : l.trim() ? `<p>${f(l.replace(/^#+\s*/, "<b>") + (/^#+\s*/.test(l) ? "</b>" : ""))}</p>` : "";
  }
  return out + (ul ? "</ul>" : "");
}
async function callAI(user) {
  const s = store.get("lumen-ia", {});
  if (!s.key) throw new Error("Aucune clé API : ouvre « ⚙︎ IA » pour la saisir.");
  const p = s.prov || "anthropic", model = s.model || PROV[p].model;
  if (!model) throw new Error("Modèle non renseigné dans les réglages.");
  if (p === "anthropic") {
    const r = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: { "content-type": "application/json", "x-api-key": s.key, "anthropic-version": "2023-06-01", "anthropic-dangerous-direct-browser-access": "true" },
      body: JSON.stringify({ model, max_tokens: 2500, system: SYSTEM, messages: [{ role: "user", content: user }] }),
    });
    const j = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error((j.error && j.error.message) || "Erreur " + r.status);
    return (j.content || []).map(b => b.text || "").join("");
  }
  const base = (s.url || PROV[p].url || "").replace(/\/+$/, "");
  if (!base) throw new Error("URL de base manquante dans les réglages.");
  const r = await fetch(base + "/chat/completions", {
    method: "POST",
    headers: { "content-type": "application/json", authorization: "Bearer " + s.key },
    body: JSON.stringify({ model, max_tokens: 2500, messages: [{ role: "system", content: SYSTEM }, { role: "user", content: user }] }),
  });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error((j.error && j.error.message) || "Erreur " + r.status);
  return j.choices && j.choices[0] && j.choices[0].message.content || "";
}
$("#ia-go").onclick = async () => {
  if (!ctx) return;
  const out = $("#ia-out"), btn = $("#ia-go"), extra = $("#ia-q").value.trim();
  const user = `Document : ${CUR ? CUR.titre : ""}${CUR && CUR.sous_titre ? " (" + CUR.sous_titre + ")" : ""}
Emplacement : ${ctx.where || "—"}
Type de cible : ${{ mot: "mot ou expression", passage: "passage", section: "section entière" }[ctx.kind]}

Extrait :
"""
${ctx.quote.slice(0, 6000)}
"""

Consigne — ${MODES[mode].label} : ${MODES[mode].brief}${extra ? "\nQuestion ou angle demandé par le lecteur : " + extra : ""}`;
  btn.disabled = true; out.innerHTML = `<p class="muted">Réflexion en cours…</p>`;
  try {
    const t = await callAI(user);
    out.innerHTML = md(t) + `<p class="warn">Généré par IA : peut contenir des erreurs. Vérifie les références et confronte toujours au texte officiel.</p>`;
  } catch (e) {
    out.innerHTML = `<p class="warn">${esc(e.message || e)}</p>`;
  } finally { btn.disabled = false; }
};

/* ---------- réglages ---------- */
const dlg = $("#set");
function syncSet() {
  const p = $("#s-prov").value;
  $("#s-url-l").style.display = p === "anthropic" ? "none" : "";
  $("#s-model").placeholder = PROV[p].model || "nom du modèle";
  $("#s-url").placeholder = PROV[p].url || "https://…/v1";
}
$("#s-prov").onchange = syncSet;
$("#open-set").onclick = () => {
  const s = store.get("lumen-ia", {});
  $("#s-prov").value = s.prov || "anthropic"; $("#s-key").value = s.key || "";
  $("#s-model").value = s.model || ""; $("#s-url").value = s.url || "";
  syncSet(); dlg.showModal();
};
$("#s-save").onclick = () => {
  store.set("lumen-ia", { prov: $("#s-prov").value, key: $("#s-key").value.trim(), model: $("#s-model").value.trim(), url: $("#s-url").value.trim() });
  toast("Réglages enregistrés");
};

if ("serviceWorker" in navigator && location.protocol !== "file:") navigator.serviceWorker.register("sw.js").catch(() => {});
route();
