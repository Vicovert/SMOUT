/* SMOUT — version web (même jeu que la version PC : mêmes règles, thèmes, listes de mots et serveur multijoueur). */
"use strict";
const D = window.SMOUT_DONNEES;
const VERSION_APP = D.version;
const FIREBASE_URL = "https://smout-multi-default-rtdb.europe-west1.firebasedatabase.app/";
const FIREBASE_API_KEY = "AIzaSyCUliQiMhKmHZzxrMK6k35Gt0z7zBfZP3g";
const RACINE = "v7";
const VERSION_JEU = "8.10";
const DELAI_ABANDON_MS = 1800000;  // salon sans signe de vie depuis 30 min : supprimable par n'importe qui (pas de déconnexion pour simple inactivité)
const ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
const THEMES = Object.assign({}, D.themes);
const MODES = [
  ["CLASSIQUE", "Classique", "1 point par mot trouvé"],
  ["BLAST", "Blast", "Les rapides marquent"],
  ["PRECISION", "Précision", "Peu d'essais, + de pts"],
  ["MYSTERE", "Mystère", "1re lettre cachée"],
  ["RUSH", "Rush", "Max de mots avant la fin"],
  ["ELIMINATION", "Élimination", "Le dernier est éliminé"],
  ["CHAINE", "Chaîne", "Les mots s'enchaînent"],
  ["COOP", "Coopératif", "Une grille pour tous"],
  ["PIEGE", "Mot piégé", "Choisis le mot d'un autre"],
];
const RUSHS = ["RUSH", "CHAINE"];
// chaque mode a sa couleur (identique à COULEURS_MODES de page_multi.py) et une règle en une phrase
const COULEURS_MODES = { CLASSIQUE: "#F5B83D", BLAST: "#FF6B6B", PRECISION: "#4CC9F0", MYSTERE: "#A78BFA", RUSH: "#FF8FC7", ELIMINATION: "#FF9F43", CHAINE: "#2DD4BF", COOP: "#7ED957", PIEGE: "#5B7CFA" };
const REGLES_MODES = {
  CLASSIQUE: "Chacun cherche le mot : 1 point par mot trouvé.", BLAST: "Les plus rapides marquent le plus de points à chaque manche.",
  PRECISION: "Moins tu utilises d'essais, plus tu marques.", MYSTERE: "Même la première lettre est cachée.",
  RUSH: "Un maximum de mots avant la fin du temps.", ELIMINATION: "Qui ne trouve pas, ou le plus lent, est éliminé. Le dernier gagne.",
  CHAINE: "Chaque mot commence par la dernière lettre du précédent.", COOP: "Une seule grille pour l'équipe, essais partagés.",
  PIEGE: "Choisis en secret le mot qu'un autre joueur devra deviner. 1 point si tu trouves le tien." };  // modes « un maximum de mots avant la fin du temps »
const NOM_MODE = Object.fromEntries(MODES.map(m => [m[0], m[1]]));
const COULEURS_AVATAR = ["#F5B83D", "#8FB3FF", "#7ED6A8", "#F2A1C5", "#C4A7FF", "#FFB38A"];

/* ------------------------------------------------------------------ couleurs (identique à design.py) */
const hexRgb = h => { h = h.replace("#", ""); return [0, 2, 4].map(i => parseInt(h.substr(i, 2), 16)); };
const rgbHex = c => "#" + c.map(v => Math.max(0, Math.min(255, Math.round(v))).toString(16).padStart(2, "0")).join("");
function melanger(a, b, t) { try { const x = hexRgb(a), y = hexRgb(b); return rgbHex(x.map((v, i) => v + (y[i] - v) * t)); } catch (e) { return a; } }
function luminance(h) { const [r, g, b] = hexRgb(h); return (0.299 * r + 0.587 * g + 0.114 * b) / 255; }
const contraste = (h, clair = "#ffffff", fonce = "#16130a") => luminance(h) > 0.6 ? fonce : clair;
function rgbToHls(r, g, b) {
  const mx = Math.max(r, g, b), mn = Math.min(r, g, b), l = (mn + mx) / 2;
  if (mn === mx) return [0, l, 0];
  const s = l <= 0.5 ? (mx - mn) / (mx + mn) : (mx - mn) / (2 - mx - mn);
  const rc = (mx - r) / (mx - mn), gc = (mx - g) / (mx - mn), bc = (mx - b) / (mx - mn);
  let h = r === mx ? bc - gc : g === mx ? 2 + rc - bc : 4 + gc - rc;
  h = ((h / 6) % 1 + 1) % 1; return [h, l, s];
}
function hlsToRgb(h, l, s) {
  if (s === 0) return [l, l, l];
  const m2 = l <= 0.5 ? l * (1 + s) : l + s - l * s, m1 = 2 * l - m2;
  const v = hue => { hue = ((hue % 1) + 1) % 1; if (hue < 1 / 6) return m1 + (m2 - m1) * hue * 6; if (hue < 0.5) return m2; if (hue < 2 / 3) return m1 + (m2 - m1) * (2 / 3 - hue) * 6; return m1; };
  return [v(h + 1 / 3), v(h), v(h - 1 / 3)];
}
function eclaircir(h, f) {
  const [r, g, b] = hexRgb(h).map(v => v / 255); let [hh, l, s] = rgbToHls(r, g, b);
  l = Math.max(0, Math.min(1, f < 1 ? l * f : l + (1 - l) * (f - 1)));
  return rgbHex(hlsToRgb(hh, l, s).map(v => v * 255));
}
function calculerPalette(t) {
  const fond = t.bg; let texte = t.txt1 || "#EAF0FF";
  if (Math.abs(luminance(texte) - luminance(fond)) < 0.35) texte = luminance(fond) < 0.5 ? "#EAF0FF" : "#1b1a22";
  const sombre = luminance(fond) < 0.5;
  const p = { fond, texte, panneau: t.panel || melanger(fond, texte, 0.06), tuile: t.tuile || melanger(fond, texte, 0.12),
    vide: t.vide || melanger(fond, texte, 0.035), bordure: t.bordure || melanger(fond, texte, 0.24),
    bien: t.accent1, mal: t.accent2, absent: t.muted || melanger(fond, texte, 0.06), accent: t.btn1 || t.accent2 };
  const t2 = t.txt3;
  p.texte2 = t2 && Math.abs(luminance(t2) - luminance(fond)) > 0.25 ? t2 : melanger(texte, fond, 0.35);
  if (Math.abs(luminance(p.absent) - luminance(fond)) > 0.35) p.absent = melanger(fond, texte, 0.07);
  p.texte_absent = melanger(p.absent, texte, 0.38);
  p.sur_accent = contraste(p.accent); p.sur_bien = contraste(p.bien); p.sur_mal = contraste(p.mal);
  p.danger = sombre ? "#F28B8B" : "#B42318"; p.succes = sombre ? "#4ADE80" : "#15803D";
  p.ombre_bien = eclaircir(p.bien, 0.72); p.ombre_mal = eclaircir(p.mal, 0.72);
  p.survol = melanger(p.panneau, texte, 0.06); p.sombre = sombre;
  return p;
}
let P = {};
const PALETTE_DALTONIEN = ["#F5793A", "#85C0F9"];  // orange = bien placée, bleu = mal placée (identique à design.py)
function appliquerTheme(nom) {
  let t = THEMES[nom]; if (lireConfig().daltonien) t = Object.assign({}, t, { accent1: PALETTE_DALTONIEN[0], accent2: PALETTE_DALTONIEN[1] });
  P = calculerPalette(t);
  const r = document.documentElement.style;
  for (const [k, v] of Object.entries(P)) if (typeof v === "string") r.setProperty("--" + k.replace(/_/g, "-"), v);
  document.querySelector('meta[name="theme-color"]')?.setAttribute("content", P.fond);
}
const nomTheme = n => D.noms_themes[n] || (n === n.toUpperCase() ? n.charAt(0) + n.slice(1).toLowerCase() : n);
const espacer = t => t.toUpperCase();
const nombre = n => Math.trunc(n).toString().replace(/\B(?=(\d{3})+(?!\d))/g, " ");
const mmss = v => `${String(Math.floor(v / 60)).padStart(2, "0")}:${String(Math.floor(v % 60)).padStart(2, "0")}`;
const capitaliser = s => s ? s.charAt(0).toUpperCase() + s.slice(1).toLowerCase() : s;

/* ------------------------------------------------------------------ configuration (équivalent de config.json) */
const CLE_CONFIG = "smout_config";
const lireConfig = () => { try { return JSON.parse(localStorage.getItem(CLE_CONFIG)) || {}; } catch (e) { return {}; } };
function majConfig(v) { const c = Object.assign(lireConfig(), v); try { localStorage.setItem(CLE_CONFIG, JSON.stringify(c)); } catch (e) {} return c; }
const aujourdhui = () => { const d = new Date(); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`; };
const hier = () => { const d = new Date(); d.setDate(d.getDate() - 1); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`; };
function serieMotDuJour() {
  const c = lireConfig(); const joue = c.last_mdj === aujourdhui();
  let serie = c.mdj_serie || 0;
  if (!c.mdj_dernier_gagne || ![aujourdhui(), hier()].includes(c.mdj_dernier_gagne)) serie = 0;
  return [serie, joue];
}
function enregistrerResultatMdj(victoire) {
  const c = lireConfig();
  if (victoire) majConfig({ mdj_serie: c.mdj_dernier_gagne === hier() ? (c.mdj_serie || 0) + 1 : 1, mdj_dernier_gagne: aujourdhui() });
  else majConfig({ mdj_serie: 0 });
}
function configSolo() {
  const c = lireConfig();
  return { nb_essais: c.nb_essais ?? 6, nb_lettres_min: c.nb_lettres_min ?? 6, nb_lettres_max: c.nb_lettres_max ?? 10, last_mdj: c.last_mdj || "", difficile: !!c.difficile };
}

/* ------------------------------------------------------------------ mots */
const MOTS = { liste: [], banque: new Set(), multiListe: [], multiBanque: new Set(), pret: null };
MOTS.pret = (async () => {
  const lire = async f => (await (await fetch("fichiers/" + f)).text()).split(/\r?\n/).map(l => l.trim().toUpperCase()).filter(Boolean);
  const [liste, banque] = await Promise.all([lire("mots_trouver.txt"), lire("banque_mots.txt")]);
  MOTS.liste = liste; MOTS.banque = new Set(banque.length ? banque : liste);
  MOTS.multiListe = liste.filter(m => m.length >= 4);
  MOTS.multiBanque = new Set([...MOTS.multiListe, ...banque.filter(m => m.length >= 4)]);
})();
async function sha256hex(t) {
  const b = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(t));
  return [...new Uint8Array(b)].map(x => x.toString(16).padStart(2, "0")).join("");
}
/* Identique à design.mot_graine : même mot sur PC et sur le web */
async function motGraine(listeTriee, graine, index = 0) {
  const h = (await sha256hex(`${graine}:${index}`)).slice(0, 12);
  return listeTriee[parseInt(h, 16) % listeTriee.length];
}
const trier = l => [...l].sort((a, b) => a < b ? -1 : a > b ? 1 : 0);
/* Mode Chaîne : chaque mot commence par la dernière lettre du précédent (identique à design.mots_chaine) */
async function motsChaine(listeTriee, graine, n = 100) {
  const initiales = new Set(listeTriee.map(m => m[0]));
  let jouables = listeTriee.filter(m => initiales.has(m[m.length - 1])); if (!jouables.length) jouables = listeTriee;
  const parLettre = {}; for (const m of jouables) (parLettre[m[0]] ||= []).push(m);
  const mots = [await motGraine(jouables, graine, 0)];
  for (let i = 1; i < n; i++) mots.push(await motGraine(parLettre[mots[i - 1][mots[i - 1].length - 1]] || jouables, graine, i));
  return mots;
}
/* Élimination (identique à calcul_elimination de page_multi.py) */
function calculElimination(d, manche) {
  const p = d.players || {}, s = d.settings || {}, deja = new Set(s.elimines || []);
  const vivants = Object.keys(p).filter(x => !deja.has(x)).sort();
  const rw = d.round_wins || {}, r = (!Array.isArray(rw) && rw[`r${manche}`]) || {};
  const trouves = Object.fromEntries(Object.entries(r).filter(([pid, t]) => vivants.includes(pid) && typeof t === "number"));
  const nb = Object.keys(trouves).length; let elim;
  if (!nb || vivants.length <= 1) elim = [];
  else if (nb < vivants.length) elim = vivants.filter(x => !(x in trouves));
  else elim = [Object.keys(trouves).sort((a, b) => trouves[b] - trouves[a] || (a < b ? 1 : -1))[0]];
  return [elim, vivants.filter(x => !elim.includes(x))];
}
/* Coopératif : propositions de tous les joueurs dans l'ordre d'arrivée sur le serveur (identique à fusion_coop) */
function fusionCoop(md, essais) {
  const tout = [];
  for (const [pid, lignes] of Object.entries(md || {})) {
    const items = Array.isArray(lignes) ? lignes.map((v, i) => [i, v]) : Object.entries(lignes || {});
    for (const [k, v] of items) if (v && typeof v === "object" && v.c) tout.push([typeof v.t === "number" ? v.t : 9e15, pid, Number(k), v]);
  }
  tout.sort((a, b) => a[0] - b[0] || (a[1] < b[1] ? -1 : a[1] > b[1] ? 1 : 0) || a[2] - b[2]);
  return tout.slice(0, essais);
}

/* Mot piégé (identique aux fonctions piege_* de page_multi.py) */
const PIEGE_FIN_INFINIE = 32503680000000;  // fin du choix (ms, an 3000) tant que l'hôte ne l'a pas fixée : on choisit sans limite de temps
// {cible: choisisseur} pour la manche : ordre circulaire tiré au lancement, décalage différent à chaque manche
function piegePaires(ordre, joueurs, manche) {
  ordre = ordre || []; joueurs = [...joueurs];
  const part = ordre.filter(u => joueurs.includes(u)).concat(joueurs.filter(u => !ordre.includes(u)).sort());
  const n = part.length; if (n < 2) return {};
  const d = 1 + (Number(manche) - 1) % (n - 1), r = {};
  for (let i = 0; i < n; i++) r[part[i]] = part[((i - d) % n + n) % n];
  return r;
}
// réglages d'une manche (écrits par l'hôte) : paires, identifiant de manche, fin du choix (infinie : l'hôte la fixe quand tous ont choisi, ou en forçant)
function piegeReglages(ordre, joueurs, manche, graine, debut) {
  return { piege_ordre: [...ordre], piege_de: piegePaires(ordre, joueurs, manche), piege_id: `p${graine}`, piege_fin_choix: PIEGE_FIN_INFINIE };
}
// [points du devineur, points du choisisseur] : k = essai gagnant (1…), 0 si le mot n'est pas trouvé
function piegePointsPaire(essaisMax, k) { return [k > 0 ? 1 : 0, 0]; }  // 1 point à celui qui trouve son mot, 0 sinon ; le choisisseur ne marque rien
// total d'un joueur sur toutes les manches, recalculé à partir du récapitulatif
function piegePoints(recap, uid, essaisMax) {
  let total = 0;
  for (const r of Object.values(recap || {})) {
    if (!r || typeof r !== "object") continue;
    for (const [cible, x] of Object.entries(r)) {
      if (!x || typeof x !== "object") continue;
      const [dev, cho] = piegePointsPaire(Number(essaisMax), Number(x.essais) || 0);
      if (cible === uid) total += dev;
      if (x.de === uid && !x.auto) total += cho;
    }
  }
  return total;
}
// lignes « Alice → Bob : MOT · trouvé en 3 » d'une manche
function piegeLignesRecap(recapManche, deMap, noms) {
  recapManche = recapManche || {};
  if (!deMap) deMap = Object.fromEntries(Object.entries(recapManche).filter(([, x]) => x && typeof x === "object").map(([c, x]) => [c, x.de]));
  const nom = u => noms[u] || "?";
  return Object.entries(deMap).sort((a, b) => { const x = noms[a[1]] || "", y = noms[b[1]] || ""; return x < y ? -1 : x > y ? 1 : 0; }).map(([cible, cho]) => {
    const x = recapManche[cible], a = capitaliser(nom(cho)), b = capitaliser(nom(cible));
    if (!x || typeof x !== "object") return `${a} → ${b} : paire annulée`;
    const k = Number(x.essais) || 0;
    return `${a} → ${b} : ${x.mot ?? "?"} · ${k ? `trouvé en ${k}` : "pas trouvé"}` + (x.auto ? " (mot au hasard)" : "");
  });
}

/* ------------------------------------------------------------------ DOM */
function h(tag, attrs, ...enfants) {
  const [nom, ...classes] = tag.split(".");
  const e = document.createElement(nom || "div");
  if (classes.length) e.className = classes.join(" ");
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === undefined || v === null || v === false) continue;
    if (k.startsWith("on")) e.addEventListener(k.slice(2), v);
    else if (k === "style" && typeof v === "object") { for (const [sk, sv] of Object.entries(v)) { if (sv === null || sv === undefined) continue; if (sk.startsWith("--")) e.style.setProperty(sk, sv); else e.style[sk] = sv; } }
    else if (k === "class") e.className += " " + v;
    else if (k === "html") e.innerHTML = v;
    else e.setAttribute(k, v === true ? "" : v);
  }
  for (const c of enfants.flat()) if (c !== null && c !== undefined && c !== false) e.append(c.nodeType ? c : document.createTextNode(c));
  return e;
}
const APP = () => document.getElementById("app");
let nettoyageEcran = [];
let enAccueil = false, enJeu = false;  // enAccueil : le retour du téléphone y quitte la page ; enJeu : partie en cours (le retour demande confirmation)
function ecran(...enfants) {
  enAccueil = false; enJeu = false;
  nettoyageEcran.forEach(f => { try { f(); } catch (e) {} }); nettoyageEcran = [];
  document.onkeydown = null;
  const a = APP(); a.innerHTML = ""; const p = h("div.page", {}, ...enfants); a.append(p); window.scrollTo(0, 0); return p;
}
const SVG = {
  retour: '<path d="M14 6l-6 6 6 6"/>',
  aide: '<circle cx="12" cy="12" r="10"/><path d="M9.5 9a2.5 2.5 0 1 1 3.5 2.3c-.7.3-1 .8-1 1.5v.7"/><circle cx="12" cy="17.2" r=".6" fill="currentColor"/>',
  palette: '<circle cx="12" cy="12" r="10"/><circle cx="7.5" cy="10.5" r="1.4" fill="currentColor"/><circle cx="12" cy="7" r="1.4" fill="currentColor"/><circle cx="16.5" cy="10.5" r="1.4" fill="currentColor"/><circle cx="15" cy="16" r="2.2"/>',
  reglages: '<circle cx="12" cy="12" r="3.5"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M4.9 19.1L7 17M17 7l2.1-2.1"/>',
  copier: '<rect x="9" y="9" width="12" height="12" rx="3"/><path d="M5 15V5a2 2 0 0 1 2-2h8"/>',
  rafraichir: '<path d="M20 12a8 8 0 1 1-2.3-5.7"/><path d="M20 4v5h-5"/>',
  plus: '<path d="M12 5v14M5 12h14"/>', moins: '<path d="M5 12h14"/>',
  chevron: '<path d="M9 6l6 6-6 6"/>', check: '<path d="M5 12l5 5 9-10"/>',
  couronne: '<path d="M3 18h18l-2-10-5 5-2-7-2 7-5-5z"/>',
  stats: '<path d="M6 20v-7M12 20V6M18 20v-10"/>',
  crayon: '<path d="M4 20h4L19 9l-4-4L4 16z M14 6l4 4"/>',
  cadenas: '<rect x="5" y="11" width="14" height="10" rx="2.5" fill="currentColor"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>',
};
const svg = (nom, taille) => `<svg viewBox="0 0 24 24"${taille ? ` style="width:${taille}px;height:${taille}px"` : ""}>${SVG[nom]}</svg>`;
const icone = (nom, onclick, cadre = false, titre = "") => h("button.icone" + (cadre ? ".cadre" : ""), { onclick, html: svg(nom), "aria-label": titre || nom, title: titre });
function bouton(texte, onclick, opts = {}) {
  const b = h("button.btn" + (opts.variante ? "." + opts.variante : "") + (opts.grand ? ".grand" : ""), { onclick: e => { if (!b.disabled) onclick(e); }, style: { width: opts.largeur ? opts.largeur + "px" : null, height: opts.hauteur ? opts.hauteur + "px" : null, maxWidth: "100%" } }, texte);
  return b;
}
function tuile(taille, mini = false) {
  const t = h("div.tuile" + (mini ? ".mini" : ""), { style: { "--t": taille + "px" } });
  t.etat = ""; t.lettre = "";
  t.maj = (lettre, etat, curseur = false) => {
    if (lettre !== undefined && lettre !== t.lettre) { t.lettre = lettre; t.textContent = mini && taille < 14 ? "" : lettre; }
    if (etat !== undefined) { t.etat = etat; }
    const cls = "tuile" + (mini ? " mini" : "") + (t.etat ? " " + t.etat : (t.lettre ? " saisie" : "")) + (curseur ? " curseur" : "");
    if (t.className !== cls) t.className = cls;
  };
  t.taille = n => t.style.setProperty("--t", n + "px");
  return t;
}
function grille(lignes, colonnes, taille, mini = false) {
  const g = h("div.grille" + (mini ? ".mini" : ""), { style: { gridTemplateColumns: `repeat(${colonnes}, auto)` } });
  const cases = [];
  for (let r = 0; r < lignes; r++) { const l = []; for (let c = 0; c < colonnes; c++) { const t = tuile(taille, mini); g.append(t); l.push(t); } cases.push(l); }
  g.cases = cases; return g;
}
function logo(taille = 88, ecart = 14) {
  const etats = ["mal", "mal", "mal", "bien", "mal"];  // comme MOTUS : U bien placé, le reste mal placé
  return h("div.logo", { style: { gap: ecart + "px" } }, [..."SMOUT"].map((ch, i) => { const t = tuile(taille); t.maj(ch, etats[i]); t.style.boxShadow = "none"; return t; }));
}
function avatar(nom, taille = 44, index = 0, onclick = null) {
  return h("div.avatar", { onclick, style: { width: taille + "px", height: taille + "px", background: COULEURS_AVATAR[index % 6], cursor: onclick ? "pointer" : null, fontSize: Math.round(taille * 0.42) + "px" } }, (nom || "?").charAt(0).toUpperCase());
}
function stat(titre, valeur, couleur, taille = 44) {
  // taille réduite sur les petits écrans (sinon la ligne Temps / Score / Essai déborde sur téléphone)
  const v = h("span.v", { style: { color: couleur || null, fontSize: `min(${taille}px, ${(taille / 5.2).toFixed(2)}vw)` } }, valeur);
  const s = h("span.s", { style: { fontSize: `min(${Math.round(taille * 0.55)}px, ${(taille * 0.55 / 5.2).toFixed(2)}vw)` } });
  const e = h("div.stat", {}, h("div.caps", {}, titre), h("div", {}, v, s));
  e.set = (val, coul, suff) => { v.textContent = val; if (coul) v.style.color = coul; if (suff !== undefined) s.textContent = suff; };
  return e;
}
function chips(valeurs, valeur, onchange) {
  const e = h("div.chips"); e.valeur = valeur; e.actif = true;
  const bs = valeurs.map(v => h("button.chip", { onclick: () => { if (!e.actif || v === e.valeur) return; e.set(v); onchange && onchange(v); } }, String(v)));
  e.append(...bs);
  e.set = v => { e.valeur = v; bs.forEach((b, i) => b.classList.toggle("sel", valeurs[i] === v)); };
  e.activer = s => { e.actif = s; bs.forEach(b => b.disabled = !s); };
  e.set(valeur); return e;
}
function stepper(mini, maxi, valeur, pas, onchange, fmt = String) {
  const e = h("div.stepper"); e.valeur = valeur; e.actif = true;
  const v = h("span.v");
  const m = icone("moins", () => chg(-1), true), p = icone("plus", () => chg(1), true);
  function chg(s) { if (!e.actif) return; const n = Math.max(mini, Math.min(maxi, e.valeur + s * pas)); if (n !== e.valeur) { e.set(n); onchange && onchange(n); } }
  e.set = n => { e.valeur = n; v.textContent = fmt(n); };
  e.activer = s => { e.actif = s; m.disabled = !s; p.disabled = !s; v.style.color = s ? "" : "var(--texte2)"; };
  e.append(m, v, p); e.set(valeur); return e;
}
function curseur(mini, maxi, valeur, pas, onchange, fmt = String) {
  const inp = h("input", { type: "range", min: mini, max: maxi, step: pas, value: valeur }), v = h("span.val");
  const e = h("div.curseur", {}, inp, v); e.valeur = valeur; e.actif = true;
  const aff = () => { v.textContent = fmt(e.valeur); inp.style.setProperty("--p", `${(e.valeur - mini) / (maxi - mini) * 100}%`); };
  inp.addEventListener("input", () => { e.valeur = +inp.value; aff(); onchange && onchange(e.valeur); });
  e.set = n => { e.valeur = n; inp.value = n; aff(); };
  e.activer = s => { e.actif = s; inp.disabled = !s; };
  aff(); return e;
}
/* plage à deux poignées (ex. nombre de lettres) : une poignée qui dépasse l'autre la pousse */
function plage(mini, maxi, [a, b], onchange) {
  const mk = x => h("input", { type: "range", min: mini, max: maxi, step: 1, value: x }), lo = mk(a), hi = mk(b), v = h("span.val");
  const rempli = h("div.rempli"), e = h("div.curseur.plage", {}, h("div.duo", {}, h("div.piste", {}, rempli), lo, hi), v); e.actif = true;
  const aff = () => { v.textContent = e.vmin === e.vmax ? String(e.vmin) : `${e.vmin} à ${e.vmax}`; rempli.style.setProperty("--pa", `${(e.vmin - mini) / (maxi - mini) * 100}%`); rempli.style.setProperty("--pb", `${(e.vmax - mini) / (maxi - mini) * 100}%`); };
  lo.addEventListener("input", () => { e.vmin = +lo.value; if (e.vmin > e.vmax) { e.vmax = e.vmin; hi.value = e.vmax; } aff(); onchange && onchange(); });
  hi.addEventListener("input", () => { e.vmax = +hi.value; if (e.vmax < e.vmin) { e.vmin = e.vmax; lo.value = e.vmin; } aff(); onchange && onchange(); });
  e.set = (x, y) => { e.vmin = x; e.vmax = y; lo.value = x; hi.value = y; aff(); };
  e.activer = s => { e.actif = s; lo.disabled = hi.disabled = !s; };
  e.set(a, b); return e;
}
function choix(titre, desc, onclick, largeur, couleur, ico) {
  const b = h("button.choix" + (couleur ? ".mode" : ""), { onclick: () => !b.disabled && onclick(), style: { width: largeur ? largeur + "px" : null, "--mc": couleur || null } }, h("div.t", {}, titre), h("div.d", {}, desc), ico ? h("span.ico", { html: svg(ico, 24) }) : null);
  b.sel = s => b.classList.toggle("sel", s); return b;
}
function caseACocher(texte, valeur, onchange) {
  const e = h("div.case" + (valeur ? ".on" : ""), { onclick: () => { e.valeur = !e.valeur; e.classList.toggle("on", e.valeur); onchange && onchange(e.valeur); } }, h("div.b", { html: svg("check") }), texte);
  e.valeur = valeur; return e;
}
function clavier(onLettre, onEffacer, onValider, hauteurTouche = 50) {
  const e = h("div.clavier", { style: { "--kh": hauteurTouche + "px" } });
  const touches = {}, rangs = h("div.rangs");
  const tactile = window.matchMedia("(pointer: coarse)").matches || window.innerWidth <= 760;
  // appui immédiat (pas d'attente du « click » ni de zoom au double appui) ; le « click » reste actif pour le clavier physique (detail = 0)
  const touche = (cls, contenu, action, etiquette) => {
    const t = h("button" + cls, { "aria-label": etiquette || contenu, type: "button" }, contenu);
    t.onpointerdown = ev => { ev.preventDefault(); action(); try { navigator.vibrate && navigator.vibrate(6); } catch (x) {} };
    t.onclick = ev => { if (ev.detail === 0) action(); };
    return t;
  };
  ["AZERTYUIOP", "QSDFGHJKLM", "WXCVBN"].forEach((rang, i) => {
    const r = h("div.rang");
    if (i === 2) r.append(touche(".touche.large", "⌫", onEffacer, "Effacer"));
    for (const ch of rang) { const t = touche(".touche", ch, () => onLettre(ch)); touches[ch] = t; r.append(t); }
    if (i === 2) r.append(touche(".touche.large.valider", "↵", onValider, "Valider"));
    rangs.append(r);
  });
  e.append(rangs);
  e.setCouleur = (ch, etat) => { const t = touches[ch]; if (t) t.className = "touche" + (etat ? " " + etat : ""); };
  // Clavier du téléphone : un champ invisible reçoit la saisie du clavier natif (lettres, effacer, entrée), comme le clavier physique sur ordinateur
  if (tactile) {
    const SENT = "​", champ = h("input.champ-natif", { type: "text", autocapitalize: "characters", autocorrect: "off", autocomplete: "off", spellcheck: "false", enterkeyhint: "enter", "aria-label": "Clavier du téléphone" });
    champ.value = SENT; let prec = SENT;
    const zone = h("button.zone-natif", { type: "button", onclick: () => champ.focus() }, "Touche ici pour écrire avec le clavier du téléphone");
    const bascule = h("button.lien.bascule-clavier", { type: "button" });
    champ.addEventListener("input", () => {
      const v = champ.value;
      if (v.length < prec.length) for (let i = 0; i < prec.length - v.length; i++) onEffacer();
      else if (v.startsWith(prec)) for (const c of v.slice(prec.length).normalize("NFD").replace(/[̀-ͯ]/g, "").toUpperCase()) if (ALPHABET.includes(c)) onLettre(c);
      prec = v;
      if (!champ.isComposing && v.length > 24) { champ.value = SENT; prec = SENT; }
    });
    champ.addEventListener("compositionend", () => { champ.value = SENT; prec = SENT; });
    champ.addEventListener("keydown", ev => { ev.stopPropagation(); if (ev.key === "Enter") { ev.preventDefault(); onValider(); } });  // la saisie passe par « input » seulement
    const maj = natif => { e.classList.toggle("natif", natif); bascule.textContent = natif ? "⌨ Clavier du jeu" : "⌨ Clavier du téléphone"; };
    const regler = natif => { majConfig({ clavier_natif: natif }); maj(natif); if (natif) { champ.value = SENT; prec = SENT; champ.focus(); } else champ.blur(); };
    bascule.onclick = () => regler(!e.classList.contains("natif"));
    maj(!!lireConfig().clavier_natif);
    e.append(zone, champ, bascule);
  }
  return e;
}
function superposition(contenu, largeur = 520) {
  const v = h("div.voile.cache", {}, h("div.panneau", { style: { width: largeur + "px" } }, contenu));
  v.montrer = () => v.classList.remove("cache"); v.cacher = () => v.classList.add("cache");
  document.body.append(v); nettoyageEcran.push(() => v.remove()); return v;
}
function entete(titre, onRetour, droite) {
  return h("div.entete", {}, onRetour ? icone("retour", onRetour, false, "Retour") : h("div", { style: { width: "40px" } }), h("div.milieu", {}, titre), droite || h("div", { style: { width: "40px" } }));
}
function fenetreAide() {
  const ex = etat => { const t = tuile(38); t.maj("A", etat); return t; };
  let o;
  o = superposition(h("div.col", {},
    h("div.titre", { style: { fontSize: "28px" } }, "Comment jouer"),
    h("div.t2", { style: { margin: "6px 0 16px", fontSize: "15px" } }, "Trouvez le mot caché. La première lettre est donnée (sauf en mode Mystère)."),
    ...[["bien", "Lettre bien placée"], ["mal", "Lettre présente mais mal placée"], ["absent", "Lettre absente du mot"]].map(([e, t]) => h("div.ligne", { style: { gap: "12px", margin: "4px 0" } }, ex(e), t)),
    h("div.t2", { style: { margin: "16px 0 18px", fontSize: "13px" } }, "Clavier : tapez les lettres, Entrée pour valider, Retour arrière pour effacer."),
    h("div", { style: { textAlign: "right" } }, bouton("Compris", () => o.cacher(), { largeur: 160 }))), 560);
  return o;
}
const hauteurFenetre = () => Math.max(560, window.innerHeight);

/* ------------------------------------------------------------------ accueil */
let themeActuel = D.theme_defaut;
function chargerTheme() {
  const c = lireConfig();
  for (let [n, t] of Object.entries(c.custom_themes || {})) { if (THEMES[n] && THEMES[n].type !== "PERSO") n += " PERSO"; THEMES[n] = Object.assign({}, THEMES[D.theme_defaut], t, { type: "PERSO" }); }  // ne jamais écraser un thème intégré ; clés manquantes : celles du thème par défaut
  themeActuel = THEMES[c.theme] ? c.theme : D.theme_defaut;
  appliquerTheme(themeActuel);
}
function changerTheme(nom, sauver = true) { themeActuel = nom; appliquerTheme(nom); if (sauver) majConfig({ theme: nom }); }
const pseudo = () => lireConfig().pseudo || "ANONYME";

function accueil() {
  const [serie, joue] = serieMotDuJour();
  const badge = (serie || joue) ? [serie ? `Série ${serie}` : "", joue ? "Joué ✓" : ""].filter(Boolean).join(" · ") : null;
  const carte = (t, s, f, b, cls = "") => h("button.carte-menu" + cls, { onclick: f }, h("div", {}, h("div.t", {}, t), h("div.s", {}, s)), b ? h("div.d", {}, b) : h("span.chevron", { html: svg("chevron", 22) }));
  ecran(
    h("div.ligne", { style: { justifyContent: "flex-end", gap: "16px", padding: "22px 28px 0" } },
      icone("palette", () => themes(), true, "Thèmes"), icone("stats", () => statistiques(), true, "Statistiques"), avatar(pseudo(), 46, 0, () => changerPseudo())),
    h("div.centre", { style: { flex: 1, justifyContent: "center", gap: "12px", padding: "16px 0" } },
      logo(Math.min(88, Math.floor((window.innerWidth - 80) / 5.8)), 14),
      h("div.t2", { style: { fontSize: "19px", margin: "0 0 22px" } }, "Trouvez le mot caché."),
      // Solo et Multijoueur côte à côte, chacun de sa couleur ; le Mot du jour, à part, dessous, d'une troisième couleur
      h("div.menu-ligne", {}, carte("Solo", "Normal, marathon, réglages", menuSolo, null, ".solo"), carte("Multijoueur", "Salons publics ou entre amis", multiAccueil, null, ".multi")),
      h("div.menu-ligne.mdj", {}, carte("Mot du jour", "Un mot, une partie par jour", () => solo("mdj"), badge, ".mdj"))),
    h("div.t2", { style: { textAlign: "center", padding: "0 0 22px", fontSize: "14px" } }, `SMOUT v${VERSION_APP} · version en ligne`));
  enAccueil = true;
}
/* page intermédiaire du solo */
function menuSolo() {
  const rec = lireStats().marathon.record;
  const carte = (t, s, f, b) => h("button.carte-menu", { onclick: f }, h("div", {}, h("div.t", {}, t), h("div.s", {}, s)), b ? h("div.d", {}, b) : h("span.chevron", { html: svg("chevron", 22) }));
  ecran(entete("", accueil),
    h("div.centre", { style: { flex: 1, justifyContent: "center", gap: "12px", padding: "0 0 40px" } },
      h("div.titre", { style: { fontSize: "46px", textAlign: "center" } }, "Solo"),
      h("div.t2", { style: { fontSize: "18px", margin: "0 0 22px", textAlign: "center" } }, "À votre rythme"),
      carte("Partie normale", "Un mot, à votre rythme", () => solo("libre")),
      carte("Marathon", "Enchaînez les mots jusqu'à l'erreur", () => solo("marathon"), rec ? `Record ${rec}` : null),
      carte("Paramètres", "Essais, longueur des mots, difficile", parametres)));
}
function changerPseudo(apres) {
  if (typeof apres !== "function") apres = accueil;  // appelée aussi comme gestionnaire de clic
  const ch = h("input.champ.mono", { maxlength: 15, style: { width: "400px", maxWidth: "80vw" }, value: lireConfig().pseudo || "" });
  ch.addEventListener("input", () => { const v = ch.value.toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 15); if (v !== ch.value) ch.value = v; });
  const ok = () => { if (ch.value) { majConfig({ pseudo: ch.value }); apres(); } else o.cacher(); };
  ch.addEventListener("keydown", e => e.key === "Enter" && ok());
  const o = superposition(h("div.col", {}, h("div.titre", { style: { fontSize: "28px" } }, "Ton pseudo"),
    h("div.t2", { style: { margin: "4px 0 16px" } }, "Il s'affiche pour les autres joueurs en multijoueur."), ch,
    h("div.ligne", { style: { justifyContent: "flex-end", gap: "10px", marginTop: "20px" } }, bouton("Annuler", () => o.cacher(), { variante: "discret", largeur: 130 }), bouton("Enregistrer", ok, { largeur: 160 }))), 460);
  o.montrer(); ch.focus();
}

/* ------------------------------------------------------------------ solo (modes : libre, mdj, marathon) */
const TITRES = { libre: "Solo", mdj: "Mot du jour", marathon: "Marathon" };
let marathon = null;
async function solo(mode = "libre") {
  if (mode === true) mode = "mdj"; if (mode === false) mode = "libre";
  await MOTS.pret;
  if (mode === "marathon" && !marathon) marathon = { mots: 0, score: 0, temps: 0 };
  if (mode !== "marathon") marathon = null;
  const conf = configSolo(); const auj = aujourdhui();
  const difficile = !!conf.difficile && mode !== "mdj";
  if (mode === "mdj" && conf.last_mdj === auj) {
    const [serie] = serieMotDuJour();
    ecran(entete("Mot du jour", accueil), h("div.centre", { style: { flex: 1, justifyContent: "center", gap: "10px" } },
      h("div.titre", { style: { fontSize: "44px", textAlign: "center" } }, "Déjà joué aujourd'hui"),
      h("div.t2", { style: { fontSize: "18px", marginBottom: "18px", textAlign: "center" } }, (serie ? `Série en cours : ${serie} jour${serie > 1 ? "s" : ""}. ` : "") + "Revenez demain pour un nouveau mot."),
      bouton("Retour à l'accueil", accueil, { largeur: 240, hauteur: 52 })));
    return;
  }
  let mot, essais;
  if (mode === "mdj") { mot = await motGraine(trier(MOTS.liste), "mdj:" + auj); essais = 7; majConfig({ last_mdj: auj }); }
  else {
    const f = MOTS.liste.filter(m => m.length >= conf.nb_lettres_min && m.length <= conf.nb_lettres_max);
    const l = f.length ? f : MOTS.liste; mot = l[Math.floor(Math.random() * l.length)]; essais = conf.nb_essais;
  }
  const S = { mot, essais, ligne: 0, tape: [mot[0]], penalite: 0, historique: [], lignes: [], fini: false, statut: {}, debut: Date.now() };
  const scoreInitial = mot.length * 100 * (13 - essais);
  const score = ec => Math.max(0, scoreInitial - ec * 2 - S.penalite);
  const kh = hauteurFenetre() >= 760 ? 50 : 40;
  const taille = Math.floor(Math.max(26, Math.min(58, (hauteurFenetre() - 300 - 3 * (kh + 8)) / essais - 8, (Math.min(window.innerWidth, 640) - 40) / mot.length - 8)));
  let aide = null;
  const sT = stat("Temps", "00:00"), sS = stat("Score", "0", "var(--mal)"), sE = stat("Essai", "1");
  sE.set("1", null, ` / ${essais}`);
  const sTot = mode === "marathon" ? stat("Total", nombre(marathon.score), "var(--bien)") : null;
  const g = grille(essais, mot.length, taille);
  const msg = h("div.msg", { style: { color: "var(--danger)", margin: "8px 0 4px", textAlign: "center" } });
  const kb = clavier(ajouter, effacer, valider, kh);
  const abandon = h("button.lien", { onclick: () => !S.fini && fin(false) }, "Abandonner");
  const titre = TITRES[mode] + (mode === "marathon" ? ` · mot ${marathon.mots + 1}` : "") + ` · ${mot.length} lettres` + (difficile ? " · difficile" : "");
  ecran(entete(titre, quitter, icone("aide", () => aide.montrer(), false, "Aide")),
    h("div.centre", { style: { gap: "0" } }, h("div.stats", { style: { marginTop: "10px" } }, sT, sS, sE, sTot), h("div", { style: { marginTop: "18px" } }, g), msg, kb, h("div", { style: { margin: "14px 0 20px" } }, abandon)));
  enJeu = true;
  aide = fenetreAide();  // après ecran() : sinon le nettoyage de l'écran la supprimerait
  const minuteur = setInterval(() => { if (S.fini) return; const ec = Math.floor((Date.now() - S.debut) / 1000); sT.set(mmss(ec)); sS.set(nombre(score(ec))); }, 1000);
  nettoyageEcran.push(() => clearInterval(minuteur));
  sS.set(nombre(score(0)));
  document.onkeydown = e => {
    if (S.fini || e.ctrlKey || e.metaKey || e.altKey || !aide.classList.contains("cache")) return;
    const c = e.key.length === 1 ? e.key.toUpperCase() : "";
    if (c && ALPHABET.includes(c)) ajouter(c); else if (e.key === "Backspace") effacer(); else if (e.key === "Enter") valider(); else return;
    e.preventDefault();
  };
  function quitter() { S.fini = true; marathon = null; if (mode === "mdj") accueil(); else menuSolo(); }
  function maj() {
    if (S.fini) return;
    g.cases[S.ligne].forEach((t, i) => t.maj(i < S.tape.length ? S.tape[i] : "", i === 0 ? "bien" : "", i === S.tape.length));
  }
  function message(t, coul, duree = 1600) { msg.textContent = t; msg.style.color = coul || "var(--danger)"; setTimeout(() => { if (!S.fini && msg.textContent === t) msg.textContent = ""; }, duree); }
  function ajouter(c) { if (S.tape.length < mot.length && !S.fini) { S.tape.push(c); maj(); } }
  function effacer() { if (S.fini) return; if (S.tape.length > 1) S.tape.pop(); maj(); }
  function valider() {
    if (S.tape.length !== mot.length || S.fini) return;
    const t = S.tape.join("");
    if (!MOTS.banque.has(t) && t !== mot) { S.penalite += 100; return message("Mot inconnu  ·  −100 points"); }
    if (difficile) { const err = verifierDifficile(S.tape, S.lignes); if (err) return message(err, null, 2200); }
    const res = evaluer(S.tape, mot);
    majStatuts(S.statut, S.tape, res); for (const ch of ALPHABET) kb.setCouleur(ch, S.statut[ch]);
    S.historique.push(res); S.lignes.push([t, res]);
    g.cases[S.ligne].forEach((c, i) => c.maj(S.tape[i], res[i], false));
    if (t === mot) fin(true);
    else if (S.ligne + 1 >= essais) fin(false);
    else { S.ligne++; S.tape = [mot[0]]; sE.set(String(S.ligne + 1)); maj(); }
  }
  function fin(victoire) {
    enJeu = false;
    S.fini = true; const ec = Math.floor((Date.now() - S.debut) / 1000);
    const sc = victoire ? score(ec) : 0, nEssais = S.ligne + 1;
    let titreFin, stats, rejouer = () => solo(mode), partage = null, note = null;
    if (mode === "marathon") {
      marathon.temps += ec;
      if (victoire) {
        marathon.mots++; marathon.score += sc; sTot.set(nombre(marathon.score));
        message(`Trouvé ! +${nombre(sc)} pts · mot suivant…`, "var(--succes)", 5000);
        setTimeout(() => { if (marathon && document.body.contains(msg)) solo("marathon"); }, 1300); return;
      }
      const m = marathon, ancien = lireStats().marathon.record, record = enregistrerMarathon(m.mots, m.score, mot);
      const r = Math.max(ancien, m.mots);
      note = record && m.mots ? "Nouveau record !" : `Record : ${r} mot${r > 1 ? "s" : ""}`;
      titreFin = "Marathon terminé"; stats = [["Mots trouvés", String(m.mots)], ["Score total", nombre(m.score), "var(--mal)"], ["Temps", mmss(m.temps)]];
      partage = `SMOUT · Marathon · ${m.mots} mot${m.mots > 1 ? "s" : ""} · ${nombre(m.score)} pts` + (difficile ? " · difficile" : "") + `\n${D.url_web}`;
      rejouer = () => { marathon = null; solo("marathon"); }; marathon = null;
    } else {
      if (mode === "mdj") { majConfig({ last_mdj: aujourdhui() }); enregistrerResultatMdj(victoire); }
      const essaisTxt = victoire ? `${nEssais} / ${essais}` : `– / ${essais}`;
      enregistrerPartie({ libre: "solo", mdj: "mdj" }[mode], victoire, nEssais, sc, mot);
      if (mode === "mdj") {
        const d = new Date(); const t = `Mot du jour ${String(d.getDate()).padStart(2, "0")}/${String(d.getMonth() + 1).padStart(2, "0")}` + (difficile ? " (difficile)" : "");
        partage = textePartage(t, S.historique, essaisTxt.replace(/ /g, ""), nombre(sc), D.url_web);
      }
      titreFin = victoire ? (mode === "mdj" ? "Bravo, mot du jour trouvé !" : "Bravo, mot trouvé !") : "Perdu…";
      stats = [["Temps", mmss(ec)], ["Score", nombre(sc), "var(--mal)"], ["Essais", essaisTxt]];
      if (mode === "mdj") rejouer = null;
    }
    const tt = Math.max(26, Math.min(56, Math.floor((Math.min(window.innerWidth, 700) - 30) / mot.length) - 8));
    const tl = h("div.ligne", { style: { gap: "8px", margin: "10px 0 20px" } }, [...mot].map(ch => { const t = tuile(tt); t.maj(ch, victoire ? "bien" : "absent"); return t; }));
    const hist = h("div.col", { style: { gap: "4px", marginBottom: "20px", alignItems: "center" } }, S.historique.slice(-8).map(l => h("div.ligne", { style: { gap: "4px" } }, l.map(e => { const t = tuile(22, true); t.maj("", e); return t; }))));
    const msgCopie = h("div.gras", { style: { color: "var(--succes)", minHeight: "22px", fontSize: "14px", marginBottom: "6px", textAlign: "center" } });
    const v = h("div.voile", {}, h("div.centre", {},
      h("div.t2", { style: { fontSize: "17px" } }, "Le mot était"), tl,
      h("div.titre", { style: { fontSize: "min(52px, 10vw)", textAlign: "center" } }, titreFin),
      note ? h("div.t2", { style: { fontSize: "17px", marginTop: "6px" } }, note) : null,
      h("div.stats", { style: { margin: "22px 0", gap: "min(68px, 7.5vw)" } }, stats.map(([a, b, c]) => stat(a, b, c, 34))),
      hist, msgCopie,
      h("div.ligne", { style: { gap: "16px", flexWrap: "wrap", justifyContent: "center" } },
        rejouer ? bouton("Rejouer", rejouer, { largeur: 210, grand: true }) : null,
        partage ? bouton("Partager le résultat", () => partager(partage, msgCopie), { largeur: 250, grand: true, variante: "secondaire" }) : null,
        bouton("Retour", mode === "mdj" ? accueil : menuSolo, { largeur: 230, grand: true, variante: "discret" }))));
    document.body.append(v); nettoyageEcran.push(() => v.remove());
  }
  maj();
}
async function partager(texte, cible) {
  try { if (navigator.share && matchMedia("(pointer: coarse)").matches) { await navigator.share({ text: texte }); return; } } catch (e) { if (e.name === "AbortError") return; }
  try { await navigator.clipboard.writeText(texte); cible.textContent = "Résultat copié ✓ — colle-le à tes amis"; }
  catch (e) { cible.style.whiteSpace = "pre-line"; cible.textContent = texte; }
}

/* ------------------------------------------------------------------ mode difficile, défis, statistiques (identiques à design.py) */
function verifierDifficile(tape, lignes) {
  for (const [motP, etats] of lignes) {
    for (let i = 0; i < etats.length; i++) if (etats[i] === "bien" && tape[i] !== motP[i]) return `Mode difficile : la ${i + 1}${i === 0 ? "re" : "e"} lettre doit être un ${motP[i]}`;
    const besoin = {};
    etats.forEach((e, i) => { if (e === "bien" || e === "mal") besoin[motP[i]] = (besoin[motP[i]] || 0) + 1; });
    for (const ch of Object.keys(besoin).sort()) { const n = besoin[ch]; if (tape.filter(x => x === ch).length < n) return `Mode difficile : le mot doit contenir ${n === 1 ? "un" : n + " ×"} ${ch}`; }
  }
  return null;
}
const EMOJI = { bien: "🟥", mal: "🟡", absent: "🟦" };
const textePartage = (titre, lignes, essais, score, lien = "") => [`SMOUT · ${titre} · ${essais} · ${score} pts`, ...lignes.map(l => l.map(e => EMOJI[e]).join("")), lien].filter(Boolean).join("\n");
const statsVides = () => ({ parties: 0, victoires: 0, repartition: {}, serie: 0, meilleure_serie: 0, meilleur_score: 0 });
function lireStats() {
  const st = lireConfig().stats || {};
  for (const k of ["solo", "mdj"]) st[k] = Object.assign(statsVides(), st[k] || {});
  st.marathon = Object.assign({ parties: 0, record: 0, record_score: 0, mots: 0 }, st.marathon || {});
  st.historique = st.historique || []; return st;
}
function enregistrerPartie(genre, victoire, essais = 0, score = 0, mot = "", detail = "") {
  const st = lireStats(), s = st[genre];
  s.parties++;
  if (victoire) { s.victoires++; s.serie++; s.repartition[essais] = (s.repartition[essais] || 0) + 1; s.meilleur_score = Math.max(s.meilleur_score, Math.trunc(score)); } else s.serie = 0;
  s.meilleure_serie = Math.max(s.meilleure_serie, s.serie);
  st.historique = [{ d: aujourdhui(), g: genre, m: mot, v: !!victoire, e: essais, s: Math.trunc(score), x: detail }, ...st.historique].slice(0, 30);
  majConfig({ stats: st }); return st;
}
function enregistrerMarathon(nb, score, dernier = "") {
  const st = lireStats(), m = st.marathon;
  m.parties++; m.mots += nb;
  const nouveau = nb > m.record || (nb === m.record && score > m.record_score);
  if (nouveau) { m.record = nb; m.record_score = Math.trunc(score); }
  st.historique = [{ d: aujourdhui(), g: "marathon", m: dernier, v: nb > 0, e: nb, s: Math.trunc(score), x: "" }, ...st.historique].slice(0, 30);
  majConfig({ stats: st }); return nouveau;
}

/* ------------------------------------------------------------------ statistiques */
function statistiques() {
  const st = lireStats();
  const carte = (nom, s) => {
    const taux = s.parties ? Math.round(100 * s.victoires / s.parties) : 0, mx = Math.max(1, ...Object.values(s.repartition));
    const barres = [1, 2, 3, 4, 5, 6, 7, 8].filter(n => n <= 7 || s.repartition[n]).map(n => { const v = s.repartition[n] || 0;
      return h("div.ligne", { style: { gap: "8px", margin: "2px 0" } }, h("span.chiffres.t2", { style: { width: "14px", fontSize: "13px" } }, String(n)),
        h("div", { style: { width: `calc(18px + ${Math.round(70 * v / mx)}%)`, background: v && v === mx ? "var(--bien)" : "var(--tuile)", color: v && v === mx ? "var(--sur-bien)" : "var(--texte)", borderRadius: "5px", fontSize: "11px", textAlign: "right", padding: "1px 6px", fontFamily: "var(--f-chiffres)" } }, String(v))); });
    return h("div.panneau", { style: { padding: "20px", flex: "1 1 280px" } }, h("div.gras", { style: { fontSize: "18px" } }, nom),
      h("div.ligne", { style: { gap: "14px", margin: "8px 0 10px" } }, stat("Parties", String(s.parties), null, 22), stat("Réussite", `${taux} %`, null, 22), stat("Série", String(s.serie), null, 22), stat("Max", String(s.meilleure_serie), null, 22)), ...barres);
  };
  const m = st.marathon;
  const hist = st.historique.slice(0, 8).map(x => { const g = { solo: "Solo", mdj: "Mot du jour", defi: "Défi", marathon: "Marathon" }[x.g] || x.g;
    const res = x.g === "marathon" ? `${x.e} mot${x.e > 1 ? "s" : ""}` : x.v ? `${x.e} essai${x.e > 1 ? "s" : ""}` : "perdu";
    return h("div.r", { style: { color: x.v ? "var(--texte)" : "var(--texte2)" } }, h("span.chiffres", {}, `${x.d.slice(8, 10)}/${x.d.slice(5, 7)}`), h("span", {}, g), h("span.chiffres", {}, x.m), h("span", {}, res), h("span.chiffres", { style: { textAlign: "right" } }, `${nombre(x.s)} pts`)); });
  ecran(entete("", accueil), h("div", { style: { padding: "0 4vw 30px" } },
    h("div.titre", { style: { fontSize: "46px", margin: "0 0 18px" } }, "Statistiques"),
    h("div.ligne", { style: { gap: "16px", flexWrap: "wrap", alignItems: "stretch" } }, carte("Solo", st.solo), carte("Mot du jour", st.mdj)),
    h("div.ligne", { style: { gap: "16px", flexWrap: "wrap", alignItems: "flex-start", marginTop: "16px" } },
      h("div.panneau", { style: { padding: "20px", flex: "1 1 280px" } }, h("div.gras", { style: { fontSize: "18px" } }, "Marathon"),
        h("div.ligne", { style: { gap: "14px", marginTop: "8px" } }, stat("Record", String(m.record), null, 22), stat("Meilleur score", nombre(m.record_score), null, 22), stat("Parties", String(m.parties), null, 22))),
      h("div.panneau", { style: { padding: "20px", flex: "2 1 400px" } }, h("div.gras", { style: { fontSize: "18px", marginBottom: "8px" } }, "Dernières parties"),
        hist.length ? h("div.historique", {}, ...hist) : h("div.t2", {}, "Aucune partie pour le moment.")))));
}

function evaluer(tape, mot) {
  const res = Array(mot.length).fill("absent"), secret = [...mot];
  for (let i = 0; i < mot.length; i++) if (tape[i] === mot[i]) { res[i] = "bien"; secret[i] = null; }
  for (let i = 0; i < mot.length; i++) if (res[i] !== "bien") { const j = secret.indexOf(tape[i]); if (j >= 0) { res[i] = "mal"; secret[j] = null; } }
  return res;
}
function majStatuts(statut, lettres, res) {
  lettres.forEach((ch, i) => {
    const cur = statut[ch];
    if (res[i] === "bien") statut[ch] = "bien";
    else if (res[i] === "mal" && cur !== "bien") statut[ch] = "mal";
    else if (res[i] === "absent" && cur !== "bien" && cur !== "mal") statut[ch] = "absent";
  });
}

/* ------------------------------------------------------------------ paramètres */
function parametres() {
  const c = configSolo(), cf = lireConfig();
  const cE = curseur(4, 8, c.nb_essais, 1, null), cL = plage(6, 10, [c.nb_lettres_min, c.nb_lettres_max]);
  const cDiff = caseACocher("Mode difficile (lettres trouvées obligatoires)", !!c.difficile), cDalt = caseACocher("Mode daltonien (orange et bleu)", !!cf.daltonien);
  const lab = t => h("div.gras", { style: { fontSize: "17px", margin: "0 0 10px" } }, t);
  ecran(entete("", menuSolo), h("div", { style: { padding: "0 6vw" } },
    h("div.titre", { style: { fontSize: "46px", margin: "0 0 6px" } }, "Paramètres"),
    h("div.t2", { style: { fontSize: "16px", marginBottom: "24px" } }, "Réglages des parties normales et du marathon (le mot du jour se joue toujours en 7 essais)."),
    h("div.panneau", { style: { padding: "30px", maxWidth: "620px" } }, lab("Nombre d'essais"), cE, h("div", { style: { height: "22px" } }), lab("Longueur des mots"), cL,
      h("div", { style: { height: "22px" } }), cDiff, h("div", { style: { height: "10px" } }), cDalt,
      h("div", { style: { height: "26px" } }), bouton("Enregistrer", () => {
        majConfig({ nb_essais: cE.valeur, nb_lettres_min: cL.vmin, nb_lettres_max: cL.vmax, difficile: cDiff.valeur, daltonien: cDalt.valeur });
        appliquerTheme(themeActuel); menuSolo(); }, { grand: true, largeur: 560 }))));
}

/* ------------------------------------------------------------------ thèmes */
function miniTheme(nom, t, choisi, actuel, onclick, onSuppr) {
  const p = calculerPalette(t);
  const etats = [["S", "bien"], ["M", "tuile"], ["O", "mal"], ["U", "vide"], ["T", "bien"]];
  const fg = e => e === "bien" ? p.sur_bien : e === "mal" ? p.sur_mal : e === "vide" ? p.texte_absent : p.texte;
  const c = h("div.carte-theme" + (choisi ? ".choisi" : ""), { onclick, style: { background: p.fond, boxShadow: p.fond === P.fond ? `inset 0 0 0 1px ${p.bordure}` : null } },
    h("div.mt", {}, etats.map(([ch, e]) => h("span", { style: { background: p[e], color: fg(e) } }, ch))),
    h("div.nm", { style: { color: p.texte } }, nomTheme(nom)),
    actuel ? h("span.ok", { html: `<svg viewBox="0 0 24 24" style="width:20px;height:20px;stroke:${p.texte};stroke-width:2.5;fill:none;stroke-linecap:round;stroke-linejoin:round">${SVG.check}</svg>` }) : null);
  if (onSuppr) c.append(h("button.x", { style: { background: p.panneau, color: p.texte }, onclick: e => { e.stopPropagation(); onSuppr(); } }, "×"));
  return c;
}
function dessinerApercu(cv, p, x0, y0, taille, ecart) {
  const ctx = cv.getContext("2d"); const lignes = [["STORE", "bmmaa"], ["SOUPE", "bmmaa"], ["SMO", "sss"]];
  for (let r = 0; r < 4; r++) for (let c = 0; c < 5; c++) {
    const [mot, et] = lignes[r] || ["", ""]; const ch = mot[c] || "", e = et[c] || "";
    const [fill, fg] = e === "b" ? [p.bien, p.sur_bien] : e === "m" ? [p.mal, p.sur_mal] : e === "a" ? [p.absent, p.texte_absent] : e === "s" ? [p.tuile, p.texte] : [p.vide, p.texte];
    const x = x0 + c * (taille + ecart), y = y0 + r * (taille + ecart);
    ctx.fillStyle = fill; ctx.beginPath(); ctx.roundRect(x, y, taille, taille, 8); ctx.fill();
    if (r === 2 && c === 3) { ctx.strokeStyle = p.mal; ctx.lineWidth = 2; ctx.beginPath(); ctx.roundRect(x + 1, y + 1, taille - 2, taille - 2, 8); ctx.stroke(); }
    if (ch) { ctx.fillStyle = fg; ctx.font = `700 ${taille * 0.5}px ${getComputedStyle(document.body).getPropertyValue("--f-chiffres")}`; ctx.textAlign = "center"; ctx.textBaseline = "middle"; ctx.fillText(ch, x + taille / 2, y + taille / 2 + 1); }
  }
}
function themes(choix) {
  const yAvant = document.querySelector(".carte-theme") ? window.scrollY : 0;  // choisir un thème ne ramène pas en haut de page
  if (typeof choix !== "string" || !THEMES[choix]) choix = themeActuel;  // appelée aussi comme gestionnaire de clic
  const t = THEMES[choix], p = calculerPalette(t);
  const cv = h("canvas", { width: 294, height: 330, style: { borderRadius: "14px", margin: "14px 0 18px" } });
  const ctx = cv.getContext("2d"); ctx.fillStyle = p.fond; ctx.beginPath(); ctx.roundRect(0, 0, 294, 330, 14); ctx.fill();
  const f = getComputedStyle(document.body);
  ctx.textAlign = "center"; ctx.fillStyle = p.texte2; ctx.font = `600 11px ${f.getPropertyValue("--f-texte")}`;
  ctx.fillText("TEMPS", 90, 32); ctx.fillText("SCORE", 204, 32);
  ctx.font = `700 28px ${f.getPropertyValue("--f-chiffres")}`; ctx.fillStyle = p.texte; ctx.fillText("01:42", 90, 66); ctx.fillStyle = p.mal; ctx.fillText("2 450", 204, 66);
  dessinerApercu(cv, p, 22, 96, 46, 7);
  const actuel = choix === themeActuel;
  const btn = bouton(actuel ? "Thème actuel ✓" : "Appliquer ce thème", () => { changerTheme(choix); themes(choix); }, { largeur: 294, hauteur: 50, variante: actuel ? "discret" : null });
  btn.disabled = actuel;
  const liste = h("div", { style: { flex: 1, minWidth: "240px" } });
  const cats = {}; for (const [n, th] of Object.entries(THEMES)) (cats[th.type || "CLASSIQUE"] ||= []).push(n);
  const nbPerso = (cats.PERSO || []).length;
  for (const cat of D.ordre_categories) {
    const noms = cats[cat] || []; if (!noms.length && cat !== "PERSO") continue;
    liste.append(h("div.caps", { style: { margin: "10px 0 8px" } }, D.categories[cat] || cat));
    const g = h("div.cartes-themes");
    noms.forEach(n => g.append(miniTheme(n, THEMES[n], n === choix, n === themeActuel, () => themes(n), cat === "PERSO" ? () => supprimerTheme(n) : null)));
    if (cat === "PERSO") g.append(h("button.carte-ajout", { onclick: () => nbPerso < 4 && createurTheme(), style: { cursor: nbPerso < 4 ? "pointer" : "default" } }, nbPerso < 4 ? "+ Créer mon thème" : "Limite de 4 thèmes perso"));
    liste.append(g);
  }
  btn.style.width = "100%";
  ecran(entete("", accueil), h("div", { style: { padding: "0 4vw 30px" } },
    h("div.titre", { style: { fontSize: "46px", margin: "0 0 22px" } }, "Thèmes"),
    h("div.ligne.themes-corps", {},
      h("div.panneau.centre.theme-apercu", {}, h("div.caps", {}, `Aperçu · ${nomTheme(choix)}`), cv, btn), liste)));
  if (yAvant) window.scrollTo(0, yAvant);
}
function supprimerTheme(n) {
  delete THEMES[n]; if (themeActuel === n) changerTheme(D.theme_defaut);
  majConfig({ custom_themes: Object.fromEntries(Object.entries(THEMES).filter(([, t]) => t.type === "PERSO")) }); themes();
}
function createurTheme() {
  const PROPS = [["bg", "Fond"], ["tuile", "Tuile"], ["accent1", "Bien placée"], ["accent2", "Mal placée"], ["muted", "Absente"], ["btn1", "Bouton principal"], ["txt1", "Texte"], ["txt3", "Texte secondaire"]];
  const cur = Object.assign({}, THEMES[themeActuel]); cur.tuile = cur.tuile || P.tuile; ["panel", "vide", "bordure"].forEach(k => delete cur[k]); cur.type = "PERSO";
  let sel = "bg";
  const cv = h("canvas", { width: 286, height: 300, style: { borderRadius: "14px", marginTop: "12px" } });
  const lignes = PROPS.map(([k, l]) => { const sw = h("div", { style: { width: "30px", height: "30px", borderRadius: "8px" } }); const lb = h("span", {}, l);
    const r = h("div.ligne", { style: { gap: "10px", padding: "4px 0", cursor: "pointer", fontSize: "15px" }, onclick: () => { sel = k; hex.value = cur[k]; picker.set(cur[k]); rafraichir(); } }, sw, lb); r.sw = sw; r.lb = lb; r.k = k; return r; });
  const hex = h("input.champ.mono", { style: { width: "240px", height: "44px", fontSize: "15px" }, maxlength: 7 });
  hex.addEventListener("input", () => { if (/^#[0-9a-fA-F]{6}$/.test(hex.value)) { cur[sel] = hex.value.toLowerCase(); picker.set(cur[sel]); rafraichir(); } });
  const nom = h("input.champ", { style: { width: "240px", height: "44px", fontSize: "15px" }, value: "MON THÈME" });
  const picker = nuancier(c => { cur[sel] = c; hex.value = c; rafraichir(); });
  function rafraichir() {
    lignes.forEach(r => { r.sw.style.background = cur[r.k] || "#000"; r.sw.style.boxShadow = `inset 0 0 0 ${r.k === sel ? 2.5 : 1}px ${r.k === sel ? P.mal : P.bordure}`; r.lb.style.color = r.k === sel ? P.texte : P.texte2; });
    const p = calculerPalette(cur), ctx = cv.getContext("2d"); ctx.clearRect(0, 0, 286, 300);
    ctx.fillStyle = p.fond; ctx.beginPath(); ctx.roundRect(0, 0, 286, 300, 14); ctx.fill(); dessinerApercu(cv, p, 18, 22, 44, 8);
    ctx.fillStyle = p.accent; ctx.beginPath(); ctx.roundRect(18, 242, 250, 42, 10); ctx.fill();
    ctx.fillStyle = p.sur_accent; ctx.font = `600 14px ${getComputedStyle(document.body).getPropertyValue("--f-texte")}`; ctx.textAlign = "center"; ctx.textBaseline = "middle"; ctx.fillText("Bouton principal", 143, 264);
  }
  ecran(entete("", () => themes()), h("div", { style: { padding: "0 4vw 30px" } },
    h("div.titre", { style: { fontSize: "46px", margin: "0 0 20px" } }, "Créer mon thème"),
    h("div.ligne", { style: { alignItems: "flex-start", gap: "24px", flexWrap: "wrap" } },
      h("div.panneau", { style: { width: "280px" } }, h("div.gras", { style: { fontSize: "17px", marginBottom: "10px" } }, "Couleurs"), lignes),
      h("div.panneau.centre", { style: { width: "330px" } }, h("div.caps", {}, "Aperçu"), cv),
      h("div.panneau", {}, picker, h("div.t2", { style: { margin: "14px 0 4px", fontSize: "13px" } }, "Code hexadécimal"), hex, h("div.t2", { style: { margin: "14px 0 4px", fontSize: "13px" } }, "Nom du thème"), nom)),
    h("div.ligne", { style: { gap: "12px", marginTop: "24px" } },
      bouton("Enregistrer", () => { const n = nom.value.trim().toUpperCase(); if (!n) return;
        if (THEMES[n] && THEMES[n].type !== "PERSO") return alert("Ce nom est déjà celui d'un thème intégré. Choisis-en un autre."); THEMES[n] = Object.assign({}, cur);
        majConfig({ custom_themes: Object.fromEntries(Object.entries(THEMES).filter(([, t]) => t.type === "PERSO")) }); changerTheme(n); themes(n); }, { largeur: 200, hauteur: 50 }),
      bouton("Annuler", () => themes(), { largeur: 160, hauteur: 50, variante: "discret" }))));
  hex.value = cur[sel]; picker.set(cur[sel]); rafraichir();
}
function nuancier(onchange) {
  const sv = h("canvas", { width: 200, height: 150, style: { cursor: "crosshair", borderRadius: "6px", display: "block" } });
  const hu = h("canvas", { width: 200, height: 20, style: { cursor: "pointer", borderRadius: "6px", display: "block", marginTop: "10px" } });
  const e = h("div", {}, sv, hu); let H = 0, S = 1, V = 1;
  const hsvHex = (hh, s, v) => { const f = n => { const k = (n + hh * 6) % 6; return v - v * s * Math.max(0, Math.min(k, 4 - k, 1)); }; return rgbHex([f(5), f(3), f(1)].map(x => x * 255)); };
  function dessiner() {
    const c = sv.getContext("2d"); c.fillStyle = hsvHex(H, 1, 1); c.fillRect(0, 0, 200, 150);
    let g = c.createLinearGradient(0, 0, 200, 0); g.addColorStop(0, "#fff"); g.addColorStop(1, "rgba(255,255,255,0)"); c.fillStyle = g; c.fillRect(0, 0, 200, 150);
    g = c.createLinearGradient(0, 0, 0, 150); g.addColorStop(0, "rgba(0,0,0,0)"); g.addColorStop(1, "#000"); c.fillStyle = g; c.fillRect(0, 0, 200, 150);
    c.strokeStyle = V > 0.5 ? "#000" : "#fff"; c.lineWidth = 2; c.beginPath(); c.arc(S * 200, (1 - V) * 150, 6, 0, 7); c.stroke();
    const k = hu.getContext("2d"); for (let x = 0; x < 200; x++) { k.fillStyle = hsvHex(x / 200, 1, 1); k.fillRect(x, 0, 1, 20); }
    k.strokeStyle = "#fff"; k.lineWidth = 2; k.strokeRect(H * 200 - 2, 1, 4, 18);
  }
  const glisser = (cible, f) => { let actif = false; const m = ev => { const r = cible.getBoundingClientRect(); f(Math.max(0, Math.min(1, (ev.clientX - r.left) / r.width)), Math.max(0, Math.min(1, (ev.clientY - r.top) / r.height))); dessiner(); onchange(hsvHex(H, S, V)); };
    cible.addEventListener("pointerdown", ev => { actif = true; cible.setPointerCapture(ev.pointerId); m(ev); }); cible.addEventListener("pointermove", ev => actif && m(ev)); cible.addEventListener("pointerup", () => actif = false); };
  glisser(sv, (x, y) => { S = x; V = 1 - y; }); glisser(hu, x => { H = x; });
  e.set = hex => { try { const [r, g, b] = hexRgb(hex).map(v => v / 255); const mx = Math.max(r, g, b), mn = Math.min(r, g, b), d = mx - mn; V = mx; S = mx ? d / mx : 0;
    H = !d ? H : mx === r ? ((g - b) / d + 6) % 6 / 6 : mx === g ? ((b - r) / d + 2) / 6 : ((r - g) / d + 4) / 6; dessiner(); } catch (e) {} };
  dessiner(); return e;
}

/* ------------------------------------------------------------------ Firebase */
const FB = {
  uid: "", jetonId: null, refresh: lireConfig().auth_refresh || null, expire: 0, offset: 0, enCours: null,  // même joueur d'une visite à l'autre (reprise de partie)
  async jeton() {
    if (this.jetonId && Date.now() / 1000 < this.expire - 120) return this.jetonId;
    if (this.enCours) return this.enCours;
    this.enCours = (async () => {
      try {
        if (this.refresh) {
          const r = await fetch(`https://securetoken.googleapis.com/v1/token?key=${FIREBASE_API_KEY}`, { method: "POST", headers: { "Content-Type": "application/x-www-form-urlencoded" }, body: `grant_type=refresh_token&refresh_token=${encodeURIComponent(this.refresh)}` });
          if (r.ok) { const d = await r.json(); this.appliquer(d.id_token, d.refresh_token, d.user_id, d.expires_in); return this.jetonId; }
        }
        const r = await fetch(`https://identitytoolkit.googleapis.com/v1/accounts:signUp?key=${FIREBASE_API_KEY}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ returnSecureToken: true }) });
        if (r.ok) { const d = await r.json(); this.appliquer(d.idToken, d.refreshToken, d.localId, d.expiresIn); }
      } catch (e) { console.error(e); }
      return this.jetonId;
    })();
    try { return await this.enCours; } finally { this.enCours = null; }
  },
  appliquer(t, r, uid, exp) { if (r && r !== this.refresh) majConfig({ auth_refresh: r }); this.jetonId = t; this.refresh = r; this.uid = uid; this.expire = Date.now() / 1000 + Number(exp); },
  async req(method, path, data, keepalive = false) {
    if (!path || path.endsWith("/") || path.includes("//")) return { ok: false };  // salon déjà quitté : rien à lire
    try {
      const t = await this.jeton(); if (!t) return { ok: false };
      const avant = Date.now();
      const r = await fetch(`${FIREBASE_URL}${RACINE}/${path}.json?auth=${t}`, { method, keepalive, headers: { "Content-Type": "application/json" }, body: data === undefined ? undefined : JSON.stringify(data) });
      let j = null; try { j = await r.json(); } catch (e) {}
      return { ok: r.ok, data: j, rtt: Date.now() - avant, avant };
    } catch (e) { return { ok: false }; }
  },
  // aligne l'horloge locale sur celle du serveur (écriture d'horodatage sur son propre chemin) : sans cela, un appareil dont l'heure est décalée
  // de plus de 30 s ne voyait plus aucun salon (ni dans la liste, ni par le code). Sans effet si les règles ne l'autorisent pas encore.
  async synchro() {
    try { const r = await this.req("PUT", `horloge/${this.uid}`, SV); if (r.ok && typeof r.data === "number") this.offset = (r.data - (r.avant + r.rtt / 2)) / 1000; } catch (e) {}
  },
  async get(path) { const r = await this.req("GET", path); return r.ok ? r.data : null; },
  async ok(method, path, data) { return (await this.req(method, path, data)).ok; },
  patch(path, data) { this.req("PATCH", path, data); }, put(path, data) { this.req("PUT", path, data); }, del(path) { this.req("DELETE", path); },
  maintenant() { return Date.now() / 1000 + this.offset; },
};
const SV = { ".sv": "timestamp" };

/* ------------------------------------------------------------------ multijoueur : état commun (équivalent de PageMulti) */
const M = {
  lobby: "", estHote: false, score: 0, reglages: { essais: 8, min: 6, max: 7, rounds: 3, round_num: 1, timer: 180, password: "", visible: true, game_mode: "CLASSIQUE" },
  nbJoueurs: 1, statut: "waiting", dernierMot: "", gen: 0, battement: null,
  pseudo() { return pseudo(); },
  vuOk: 0,
  // Lecture du salon. Si on n'y figure plus (exclu après une mise en veille, salon fermé) pendant 10 s, retour au menu multijoueur.
  async lireSalon() {
    if (!this.lobby) return null;
    const lobby = this.lobby, d = await FB.get(`lobbies/${lobby}`);
    if (lobby !== this.lobby) return null;
    if (d && d.players && d.players[FB.uid]) { this.vuOk = Date.now(); return d; }
    // retiré du salon (ancien client, longue mise en veille) : on s'y réinscrit tout seul, sans déconnexion
    if (Date.now() - (this.dernierRetour || 0) > 3000) {
      this.dernierRetour = Date.now();
      const moi = { name: this.pseudo(), score: this.score, last_seen: SV }, preuve = await preuveSalon(lobby, this.reglages.password || "");
      if (preuve) moi.preuve = preuve;
      if (await FB.ok("PUT", `lobbies/${lobby}/players/${FB.uid}`, moi)) {
        const d2 = await FB.get(`lobbies/${lobby}`);
        if (lobby === this.lobby && d2 && d2.players && d2.players[FB.uid]) { this.vuOk = Date.now(); return d2; }
      }
    }
    if (this.vuOk && Date.now() - this.vuOk > 10000) {
      this.lobby = ""; this.gen++; this.estHote = false; this.vuOk = 0;
      ecran(); setTimeout(() => { alert("Ce salon n'existe plus."); multiAccueil(); }, 0);
      return null;
    }
    return d;
  },
  async demarrerBattement() {
    if (this.battement) return;
    const tic = async () => {
      if (this.lobby) {
        const uid = FB.uid; this.memoriser();
        const r = await FB.req("PATCH", `lobbies/${this.lobby}`, { maj: SV, [`players/${uid}/last_seen`]: SV, [`players/${uid}/name`]: this.pseudo(), [`players/${uid}/score`]: this.score });
        if (r.ok && r.data && typeof r.data.maj === "number") FB.offset = (r.data.maj - (r.avant + r.rtt / 2)) / 1000;
        if (this.estHote) this.majIndex();
      }
    };
    this.battement = setInterval(tic, 5000); tic();
  },
  majIndex() {
    if (!this.lobby) return; const sc = this.reglages;
    FB.patch(`index/${this.lobby}`, { owner: FB.uid, hote: this.pseudo().slice(0, 20), nb: this.nbJoueurs, prive: !!sc.password, visible: !!sc.visible, status: this.statut, version: VERSION_JEU, maj: SV });
  },
  async supprimerSalon(code) {
    if (await FB.ok("DELETE", `lobbies/${code}`)) { await FB.ok("DELETE", `secrets/${code}`); await FB.ok("DELETE", `pieges/${code}`); await FB.ok("DELETE", `index/${code}`); return true; }
    return false;
  },
  // garde le salon en mémoire : si la page se ferme ou plante, « Reprendre » permet d'y revenir
  memoriser() { if (this.lobby) majConfig({ partie_en_cours: { code: this.lobby, mdp: this.reglages.password || "", t: Date.now() / 1000, score: this.score } }); },
  oublier() { majConfig({ partie_en_cours: null }); },
  // hôte : tout le monde retourne au salon (partie annulée, scores remis à zéro) ; les clients le voient au prochain rafraîchissement
  async ramenerAuSalon() {
    const dd = await this.lireSalon(); if (!dd) return;
    this.score = 0; const pp = dd.players || {}; for (const pid in pp) { pp[pid].score = 0; pp[pid].rush_index = 0; }
    const ss = dd.settings || {}; ss.rush_seed = 1000 + Math.floor(Math.random() * 999000); this.statut = "waiting";
    FB.put(`lobbies/${this.lobby}`, { status: "waiting", maj: SV, players: pp, settings: ss, match_data: null, fini_states: null, round_wins: null, rush_recap: null, piege_pret: null, piege_essais: null, piege_verdicts: null, piege_recap: null });
  },
  async quitter(keepalive = false) {
    if (!this.lobby) return; const code = this.lobby; this.lobby = ""; this.gen++; if (!keepalive) this.oublier();  // départ volontaire
    const d = await FB.get(`lobbies/${code}`);
    if (!d) return;
    const joueurs = d.players || {};
    if ((d.settings || {}).host_id === FB.uid && Object.keys(joueurs).length > 1) {
      const nouvel = Object.keys(joueurs).filter(p => p !== FB.uid).sort()[0];
      await FB.ok("PATCH", `lobbies/${code}/settings`, { host_id: nouvel }); await FB.ok("PATCH", `index/${code}`, { owner: nouvel });
    }
    if (joueurs[FB.uid]) { await FB.req("DELETE", `lobbies/${code}/players/${FB.uid}`, undefined, keepalive); delete joueurs[FB.uid]; }
    if (!Object.keys(joueurs).length) await this.supprimerSalon(code);
  },
};
window.addEventListener("pagehide", () => { if (M.lobby && FB.jetonId) fetch(`${FIREBASE_URL}${RACINE}/lobbies/${M.lobby}/players/${FB.uid}.json?auth=${FB.jetonId}`, { method: "DELETE", keepalive: true }); });
const preuveSalon = async (code, mdp) => mdp ? (await sha256hex(`${code}:${mdp}`)).slice(0, 32) : null;
const enCodes = res => res.map(e => e === "bien" ? "B" : e === "mal" ? "M" : "A");
const deCode = c => c === "B" ? "bien" : c === "M" ? "mal" : "absent";
function barreHaut(onRetour, droite = "") {
  const d = h("div.droite", {}, droite);
  const e = h("div.barre-haut", {}, icone("retour", onRetour, true, "Retour"), h("div.titre", { style: { fontSize: "24px" } }, "SMOUT"), d); e.droite = d; return e;
}

/* ---------- Multijoueur : créer ou rejoindre */
const pseudoDefini = () => pseudo() && pseudo() !== "ANONYME";
const pseudoOk = retour => { if (pseudoDefini()) return true; changerPseudo(retour); return false; };
async function rejoindre(c, motDePasse, silencieux = false, score = null) {
  const joueur = { name: pseudo(), score: score || 0, last_seen: SV }; const preuve = await preuveSalon(c, motDePasse);
  if (preuve) joueur.preuve = preuve;
  if (!(await FB.ok("PUT", `lobbies/${c}/players/${FB.uid}`, joueur))) { if (!silencieux) alert("Salon introuvable"); return false; }
  const d = await FB.get(`lobbies/${c}`) || {};
  if (Object.keys(d.players || {}).length > 4) { await FB.ok("DELETE", `lobbies/${c}/players/${FB.uid}`); alert("Ce salon est déjà complet (maximum 4 joueurs)."); return true; }
  M.estHote = false; M.lobby = c; M.score = score || 0; M.reprise = score !== null; M.vuOk = Date.now();
  Object.assign(M.reglages, { password: motDePasse, visible: (d.settings || {}).visible !== false });
  M.demarrerBattement(); salon();
  return true;
}
async function multiAccueil() {
  M.gen++;
  const puce = h("button.puce-pseudo", { onclick: () => changerPseudo(multiAccueil), title: "Changer de pseudo" },
    pseudoDefini() ? avatar(pseudo(), 30, 0) : null, h("span", {}, pseudoDefini() ? capitaliser(pseudo()) : "Choisir un pseudo"), h("span.crayon", { html: svg("crayon", 16) }));
  const zoneReprise = h("div");
  function afficherReprise() {
    zoneReprise.innerHTML = ""; const pe = lireConfig().partie_en_cours;
    if (!pe || Date.now() / 1000 - (pe.t || 0) > 900) return;
    zoneReprise.append(h("div.panneau.ligne", { style: { marginBottom: "18px", padding: "14px 18px", gap: "10px", flexWrap: "wrap", boxShadow: "inset 0 0 0 1.5px var(--mal)" } },
      h("div.gras", { style: { fontSize: "16px", flex: 1, minWidth: "190px" } }, `Partie interrompue · salon ${pe.code}`),
      bouton("Reprendre", () => reprendre(pe), { largeur: 150, hauteur: 44 }), bouton("Ignorer", () => { M.oublier(); afficherReprise(); }, { variante: "discret", largeur: 110, hauteur: 44 })));
  }
  async function reprendre(pe) {
    if (!(await FB.jeton())) return alert("Connexion au serveur impossible.");
    if (!(await rejoindre(pe.code, pe.mdp || "", true, Number(pe.score) || 0))) { M.oublier(); afficherReprise(); alert("Cette partie est terminée ou le salon n'existe plus."); }
  }
  const tuileAction = (cls, t, st, f) => h("button.action." + cls, { onclick: f }, h("div.t", {}, t), h("div.s", {}, st));
  ecran(h("div.entete", {}, icone("retour", accueil, false, "Retour"), h("div.milieu", { style: { color: "var(--texte)", fontWeight: 600, fontSize: "18px" } }, "Multijoueur"), puce),
    h("div.centre", { style: { flex: 1, justifyContent: "center", paddingBottom: "60px" } }, h("div", { style: { width: "min(800px, 94vw)" } },
      zoneReprise,
      h("div.actions", {},
        tuileAction("a-creer", "Créer un salon", "Choisis le mode et invite tes amis", () => pseudoOk(multiAccueil) && creerSalon()),
        tuileAction("a-rejoindre", "Rejoindre un salon", "Avec un code ou depuis la liste", () => pseudoOk(multiAccueil) && rejoindreSalon())))));
  afficherReprise();
}

/* ---------- rejoindre un salon : code ou liste des salons publics */
async function rejoindreSalon() {
  M.gen++;
  const code = h("input.champ.mono", { placeholder: "CODE", inputmode: "numeric", style: { flex: 1, minWidth: "0", height: "52px", fontSize: "22px" }, maxlength: 4 });
  code.addEventListener("input", () => { code.value = code.value.replace(/\D/g, "").slice(0, 4); });
  code.addEventListener("keydown", e => e.key === "Enter" && code.value && tenterRejoindre(code.value));
  const liste = h("div", { style: { width: "100%" } });
  // mot de passe
  const mdp = h("input.champ", { type: "password", style: { width: "400px", maxWidth: "80vw" } });
  const erreurMdp = h("div.gras", { style: { color: "var(--danger)", minHeight: "22px", marginTop: "8px", fontSize: "14px" } });
  let codeCible = "";
  const contenuMdp = (h("div.col", {}, h("div.titre", { style: { fontSize: "28px" } }, "Salon protégé"), h("div.t2", { style: { margin: "4px 0 14px" } }, "Entre le mot de passe donné par l'hôte."), mdp, erreurMdp,
    h("div.ligne", { style: { justifyContent: "flex-end", gap: "10px", marginTop: "12px" } }, bouton("Annuler", () => vueMdp.cacher(), { variante: "discret", largeur: 130 }), bouton("Rejoindre", verifierMdp, { largeur: 150 }))));
  let vueMdp = null;
  mdp.addEventListener("keydown", e => e.key === "Enter" && verifierMdp());
  async function verifierMdp() { if (!(await rejoindre(codeCible, mdp.value.trim(), true))) erreurMdp.textContent = "Mot de passe incorrect"; }
  ecran(h("div.entete", {}, icone("retour", multiAccueil, false, "Retour")),
    h("div.centre", {}, h("div", { style: { width: "min(748px, 94vw)" } },
      h("div.titre", { style: { fontSize: "min(46px, 10vw)", margin: "6px 0 20px" } }, "Rejoindre un salon"),
      h("div.ligne.rejoindre", { style: { marginTop: "0" } }, h("span.gras", {}, "Code du salon"), code,
        bouton("Rejoindre", () => code.value && tenterRejoindre(code.value), { variante: "tuile-b", largeur: 130, hauteur: 52 })),
      h("div.ligne", { style: { margin: "30px 0 10px" } }, h("div.caps", {}, "Salons publics"), h("div", { style: { marginLeft: "auto" } }, icone("rafraichir", charger, false, "Actualiser"))),
      liste)));
  vueMdp = superposition(contenuMdp, 460);  // après ecran()
  async function charger() {
    liste.innerHTML = ""; liste.append(h("div.t2", { style: { padding: "10px 0", fontSize: "15px" } }, "Chargement…"));
    await MOTS.pret;
    if (!(await FB.jeton())) { liste.innerHTML = ""; liste.append(h("div.t2", { style: { padding: "10px 0", fontSize: "16px" } }, "Pas de connexion au serveur : le multijoueur a besoin d'internet. Le solo, le marathon et le mot du jour restent jouables.")); return; }
    await FB.synchro();
    const data = await FB.get("index") || {};
    liste.innerHTML = ""; let n = 0, autres = 0;
    for (const [c, v] of Object.entries(data).sort()) {
      if (!v || typeof v !== "object") continue;
      const age = FB.maintenant() * 1000 - (v.maj || 0);
      if (age > DELAI_ABANDON_MS + 10000) { M.supprimerSalon(c); continue; }  // salon abandonné : n'importe quel joueur le supprime
      if (v.visible && v.status === "waiting" && v.version !== VERSION_JEU && age < 30000) autres++;
      if (v.visible && v.status === "waiting" && v.version === VERSION_JEU && age < 30000) {
        liste.append(h("button.carte-salon", { onclick: () => tenterRejoindre(c) }, h("div", {}, h("div.t", {}, `Salon de ${capitaliser(v.hote || "ANONYME")}`), h("div.s", {}, `Code ${c}` + (v.prive ? "  ·  mot de passe" : ""))), h("div.d", {}, `${v.nb || 1}/4`)));
        n++;
      }
    }
    if (!n) liste.append(h("div.t2", { style: { padding: "10px 0", fontSize: "16px" } }, "Aucun salon public pour le moment. Crée le tien !"));
    if (autres) liste.append(h("div.t2", { style: { padding: "6px 0", fontSize: "14px", color: "var(--danger)" } }, `${autres} salon${autres > 1 ? "s" : ""} d'une autre version du jeu (la tienne : ${VERSION_JEU}). Recharge la page (Ctrl+F5) ou mets SMOUT à jour.`));
  }
  async function tenterRejoindre(c) {
    if (!(await FB.jeton())) return alert("Connexion au serveur impossible.");
    await FB.synchro();
    const idx = await FB.get(`index/${c}`);
    if (!idx || FB.maintenant() * 1000 - (idx.maj || 0) > 30000) return alert("Salon introuvable");
    if (idx.version !== VERSION_JEU) return alert(`Ce salon utilise une autre version du jeu (${idx.version || "?"}). Mets SMOUT à jour.`);
    if ((idx.nb || 0) >= 4) return alert("Ce salon est déjà complet (maximum 4 joueurs).");
    codeCible = c;
    if (idx.prive) { mdp.value = ""; erreurMdp.textContent = ""; vueMdp.montrer(); mdp.focus(); } else rejoindre(c, "");
  }
  FB.jeton().then(charger);
}

/* ---------- création */
function creerSalon() {
  let pub = true;
  const cPub = choix("Public", "Visible dans la liste des salons", () => setVis(true), 306, "var(--succes)"), cPri = choix("Privé", "Seulement avec le code", () => setVis(false), 306, "var(--mal)", "cadenas");
  const setVis = v => { pub = v; cPub.sel(v); cPri.sel(!v); };
  const champ = h("input.champ.cache", { placeholder: "Mot de passe", style: { width: "100%", marginTop: "10px" } });
  const caseMdp = caseACocher("Mot de passe", false, v => { champ.classList.toggle("cache", !v); if (v) champ.focus(); else champ.value = ""; });
  ecran(h("div.entete", {}, icone("retour", multiAccueil, false, "Retour")), h("div.centre", {}, h("div", { style: { width: "min(700px, 94vw)" } },
    h("div.titre", { style: { fontSize: "min(46px, 10vw)", margin: "14px 0 24px" } }, "Créer un salon"),
    h("div.panneau", { style: { padding: "30px" } }, h("div.gras", { style: { fontSize: "18px", marginBottom: "12px" } }, "Visibilité"),
      h("div.ligne", { style: { gap: "12px", flexWrap: "wrap" } }, cPub, cPri), h("div", { style: { height: "26px" } }), caseMdp, champ,
      h("div", { style: { marginTop: "24px" } }, bouton("Créer le salon", valider, { grand: true, largeur: 632 }))))));
  setVis(true);
  async function valider() {
    Object.assign(M.reglages, { password: caseMdp.valeur ? champ.value.trim() : "", visible: pub, game_mode: "CLASSIQUE", rounds: 3, essais: 8, min: 6, max: 7, timer: 180 });
    if (!(await FB.jeton())) return alert("Connexion au serveur impossible.");
    const sc = M.reglages, uid = FB.uid;
    for (let i = 0; i < 10; i++) {
      const code = String(1000 + Math.floor(Math.random() * 9000));
      const idx = await FB.get(`index/${code}`);
      if (idx && FB.maintenant() * 1000 - (idx.maj || 0) < 30000) continue;
      if (!(await FB.ok("DELETE", `lobbies/${code}`))) continue;  // refusé si le salon existe et est actif
      const preuve = await preuveSalon(code, sc.password);
      if (!(preuve ? await FB.ok("PUT", `secrets/${code}`, preuve) : await FB.ok("DELETE", `secrets/${code}`))) continue;
      const hote = { name: pseudo(), score: 0, last_seen: SV }; if (preuve) hote.preuve = preuve;
      if (await FB.ok("PUT", `lobbies/${code}`, { status: "waiting", maj: SV, settings: { game_mode: sc.game_mode, rounds: 3, essais: 8, min: 6, max: 7, timer: 180, host_id: uid, visible: sc.visible, version: VERSION_JEU }, players: { [uid]: hote } })) {
        M.lobby = code; M.estHote = true; M.score = 0; M.vuOk = Date.now(); M.nbJoueurs = 1; M.statut = "waiting"; M.majIndex(); M.demarrerBattement(); salon(); return;
      }
    }
    alert("Impossible de créer le salon. Vérifie ta connexion internet.");
  }
}

/* ---------- salon */
function salon() {
  const gen = ++M.gen; let modeActif = M.reglages.game_mode || "CLASSIQUE";
  const barre = barreHaut(() => { M.quitter(); multiAccueil(); });
  const titre = h("div.titre", { style: { fontSize: "34px" } }, "Salon"), statut = h("div.t2", { style: { fontSize: "15px", marginTop: "2px" } });
  const lblCode = h("div.caps", {}, "Code du salon");
  const boite = h("div.code-boite", {}, h("div", {}, lblCode, h("div.chiffres", { style: { fontSize: "40px", color: "var(--mal)" } }, M.lobby)),
    icone("copier", () => { navigator.clipboard?.writeText(M.lobby); lblCode.textContent = "Code copié ✓"; setTimeout(() => lblCode.textContent = "Code du salon", 1500); }, true, "Copier le code"));
  const slots = [0, 1, 2, 3].map(() => h("div.joueur"));
  const cartes = {};
  const gm = h("div.grille-modes", {}, MODES.map(([m, n]) => { const c = cartes[m] = choix(n, "", () => setMode(m)); c.classList.add("mode"); c.style.setProperty("--mc", COULEURS_MODES[m]); return c; }));
  // bandeau du mode choisi : nom, règle, résumé des réglages (lisible aussi par les joueurs qui ne sont pas l'hôte)
  const bNom = h("div.n"), bRegle = h("div.r"), bResume = h("div.resume");
  const bandeau = h("div.bandeau-mode", {}, h("div.caps", {}, "Mode de jeu"), bNom, bRegle);
  // réglages choisis par l'hôte, en lecture seule (les mêmes lignes que l'hôte, sans les curseurs)
  const vInv = {}, lInv = {}, ligneInv = (cle, t) => { vInv[cle] = h("div.gras", { style: { fontSize: "17px" } }); lInv[cle] = h("div.t2.gras", {}, t); return h("div.reglage", {}, lInv[cle], vInv[cle]); };
  const zoneInvite = h("div.reglages", { style: { marginTop: "14px" } }, ligneInv("rounds", "Manches"), ligneInv("timer", "Temps par manche"), ligneInv("essais", "Essais"), ligneInv("lettres", "Lettres"), ligneInv("choix", "Choix du mot"));
  const R0 = M.reglages;  // réglages en cours (conservés après « Rejouer dans ce salon »)
  const cRounds = curseur(1, 10, R0.rounds ?? 3, 1, sync), sEssais = curseur(4, 10, R0.essais ?? 8, 1, sync), sTemps = curseur(15, 600, R0.timer ?? 180, 15, sync, mmss);
  const cLettres = plage(6, 10, [R0.min ?? 6, R0.max ?? 7], sync);
  const lancer = bouton("Lancer la partie", lancerPartie, { grand: true, largeur: 9999 }); lancer.style.width = "100%"; lancer.disabled = true;
  const reglage = (t, w) => h("div.reglage", {}, h("div.t2.gras", {}, t), w);
  const regle = h("div.regle"), rTemps = h("div.t2.gras"), rManches = reglage("Manches", cRounds);
  const zoneHote = h("div", {}, gm, regle, h("div.reglages", {}, rManches, h("div.reglage", {}, rTemps, sTemps), reglage("Essais", sEssais), reglage("Lettres", cLettres)));
  const noteInvite = h("div.t2", { style: { fontSize: "14px", marginTop: "14px" } }, "L'hôte choisit le mode et les réglages.");
  const panneauPartie = h("div.panneau.salon-partie", { style: { flex: 1, minWidth: "min(300px, 100%)", padding: "22px" } }, bandeau, zoneInvite, zoneHote, noteInvite, h("div", { style: { marginTop: "20px" } }, lancer));
  ecran(barre, h("div", { style: { padding: "18px 4vw 30px" } },
    h("div.ligne.salon-tete", {}, h("div", { style: { minWidth: "0" } }, titre, statut), h("div", { style: { marginLeft: "auto" } }, boite)),
    h("div.ligne", { style: { marginTop: "20px", gap: "20px", alignItems: "flex-start", flexWrap: "wrap" } },
      h("div.panneau", { style: { width: "320px", maxWidth: "100%" } }, h("div.gras", { style: { fontSize: "18px", marginBottom: "4px" } }, "Joueurs"), slots),
      panneauPartie)));
  majModes();
  function majModes() {
    for (const [m, c] of Object.entries(cartes)) c.sel(m === modeActif);
    const coul = COULEURS_MODES[modeActif] || COULEURS_MODES.CLASSIQUE;
    panneauPartie.style.setProperty("--mc", coul);
    bNom.textContent = NOM_MODE[modeActif] || modeActif; bRegle.textContent = regle.textContent = REGLES_MODES[modeActif] || "";
    const v = valeurs(), rush = RUSHS.includes(modeActif);
    rManches.classList.toggle("cache", rush); rTemps.textContent = rush ? "Temps de jeu" : modeActif === "PIEGE" ? "Temps pour deviner" : "Temps par manche";
    const lt = v.min === v.max ? `${v.min} lettres` : v.max === v.min + 1 ? `${v.min} ou ${v.max} lettres` : `de ${v.min} à ${v.max} lettres`;
    vInv.rounds.textContent = `${v.rounds}${modeActif === "ELIMINATION" ? " max" : ""}`; vInv.timer.textContent = mmss(v.timer); vInv.essais.textContent = String(v.essais); vInv.lettres.textContent = lt; vInv.choix.textContent = "sans limite de temps";
    lInv.timer.textContent = rush ? "Temps de jeu" : modeActif === "PIEGE" ? "Temps pour deviner" : "Temps par manche";
    vInv.rounds.parentNode.classList.toggle("cache", rush); vInv.choix.parentNode.classList.toggle("cache", modeActif !== "PIEGE");
    bResume.innerHTML = "";
    bResume.append(...[rush ? `${mmss(v.timer)} de jeu` : `${v.rounds} manche${v.rounds > 1 ? "s" : ""}${modeActif === "ELIMINATION" ? " max" : ""}`, modeActif === "PIEGE" ? "choix du mot sans limite" : null, rush ? null : `${mmss(v.timer)} ${modeActif === "PIEGE" ? "pour deviner" : "par manche"}`,
      rush ? null : `${v.essais} essais`, v.min === v.max ? `${v.min} lettres` : `${v.min} à ${v.max} lettres`].filter(Boolean).map(x => h("span", {}, x)));
    if (M.estHote) lancer.textContent = M.nbJoueurs > 1 ? `Lancer · ${NOM_MODE[modeActif]}` : "Il faut au moins 2 joueurs";
  }
  function valeurs() { return { rounds: cRounds.valeur, essais: sEssais.valeur, min: cLettres.vmin, max: cLettres.vmax, timer: sTemps.valeur }; }
  function sync() {
    if (!M.estHote || gen !== M.gen) return;
    FB.patch(`lobbies/${M.lobby}/settings`, Object.assign({ game_mode: modeActif, host_id: FB.uid, visible: M.reglages.visible, version: VERSION_JEU }, valeurs()));
  }
  function setMode(m) {
    if (!M.estHote || modeActif === m) return;
    modeActif = m; M.reglages.game_mode = m;
    sEssais.set(8); cLettres.set(6, 7);
    const [t, r] = { MYSTERE: [180, 3], RUSH: [120, 1], BLAST: [60, 3], PRECISION: [180, 3], CLASSIQUE: [180, 3], ELIMINATION: [90, 10], CHAINE: [150, 1], COOP: [180, 3], PIEGE: [180, 3] }[m];
    sTemps.set(t); cRounds.set(r); majModes(); sync();
  }
  [cLettres, cRounds, sEssais, sTemps].forEach(w => { const s0 = w.set; w.set = (...a) => { s0(...a); majModes(); }; });  // le bandeau suit les réglages
  function dessinerJoueur(slot, i, nom, hote, deco, moi) {
    slot.className = "joueur" + (nom ? " plein" : ""); slot.innerHTML = ""; slot.style.setProperty("--jc", COULEURS_AVATAR[i % 6]);
    if (!nom) { slot.append(h("div.avatar", { style: { width: "36px", height: "36px", background: "var(--vide)" } }), h("span.n", { style: { color: "var(--texte-absent)" } }, "Place libre")); return; }
    slot.append(...[avatar(nom, 36, i), h("span.n", {}, capitaliser(nom) + (moi ? " (vous)" : "")),
      deco ? h("span.r", { style: { color: "var(--danger)", fontWeight: 400 } }, "Déconnecté") : hote ? h("span.r.ligne", { style: { color: "var(--mal)", gap: "6px" }, html: `<svg viewBox="0 0 24 24" style="width:18px;height:18px;stroke:currentColor;fill:none;stroke-width:1.8;stroke-linejoin:round">${SVG.couronne}</svg>Hôte` }) : null].filter(Boolean));
  }
  async function boucle() {
    while (gen === M.gen && M.lobby) {
      const d = await M.lireSalon();
      if (gen !== M.gen) return;
      if (d) {
        const s = d.settings || {}, p = d.players || {};
        const serverNow = Math.max(0, ...Object.values(p).map(x => x.last_seen || 0));
        if (!Object.keys(p).length) { M.quitter(); multiAccueil(); return; }
        // un joueur inactif reste dans le salon (affiché « Déconnecté ») : pas d'exclusion pour inactivité
        let actifsL = Object.keys(p).filter(pid => !serverNow || serverNow - (p[pid].last_seen || 0) <= 25000); if (!actifsL.length) actifsL = Object.keys(p);
        let hid = s.host_id;
        if (!actifsL.includes(hid)) { hid = actifsL.sort()[0]; if (hid === FB.uid) FB.patch(`lobbies/${M.lobby}/settings`, { host_id: hid }); }  // hôte parti ou inactif : relais
        M.estHote = s.host_id === FB.uid; M.nbJoueurs = Object.keys(p).length; M.statut = d.status || "waiting";
        const hn = (p[hid] || {}).name;
        titre.textContent = hn ? `Salon de ${capitaliser(hn)}` : "Salon";
        barre.droite.textContent = M.estHote ? "Vous êtes l'hôte" : "L'hôte règle la partie";
        if (!M.estHote) {  // l'hôte garde ses propres réglages (la base peut avoir un temps de retard)
          modeActif = s.game_mode || "CLASSIQUE"; M.reglages.game_mode = modeActif;
          cRounds.set(s.rounds ?? 3); sEssais.set(s.essais ?? 8); cLettres.set(s.min ?? 6, s.max ?? 7); sTemps.set(s.timer ?? 180);
        }
        majModes();
        if (d.status === "playing") { Object.assign(M.reglages, s); M.reglages.round_num = s.current_round || 1; partie(); return; }
        const pids = Object.keys(p);
        slots.forEach((sl, i) => { const pid = pids[i]; if (pid) dessinerJoueur(sl, i, p[pid].name, pid === hid, serverNow > 0 && (serverNow - (p[pid].last_seen || 0)) / 1000 > 12, pid === FB.uid); else dessinerJoueur(sl, i); });
        const n = pids.length;
        statut.textContent = `En attente des joueurs · ${n} sur 4` + (M.reglages.visible ? "" : "  ·  salon privé");
        [cRounds, sEssais, cLettres, sTemps].forEach(w => w.activer(M.estHote)); Object.values(cartes).forEach(c => c.disabled = !M.estHote);
        zoneHote.classList.toggle("cache", !M.estHote); noteInvite.classList.toggle("cache", M.estHote); bandeau.classList.toggle("cache", M.estHote); zoneInvite.classList.toggle("cache", M.estHote);
        if (M.estHote) { lancer.className = "btn grand lancer"; lancer.disabled = n < 2; majModes(); }
        else { lancer.className = "btn grand discret"; lancer.textContent = "En attente du lancement par l'hôte…"; lancer.disabled = true; }
      }
      await new Promise(r => setTimeout(r, 800));
    }
  }
  async function lancerPartie() {
    const v = valeurs(), sc = M.reglages;
    let joueurs = [FB.uid];
    if (modeActif === "PIEGE") { const dd = await M.lireSalon(); if (gen !== M.gen) return; if (dd && Object.keys(dd.players || {}).length) { const pl = dd.players, mx = Math.max(0, ...Object.values(pl).map(v => v.last_seen || 0)); joueurs = Object.keys(pl).filter(pid => mx - (pl[pid].last_seen || 0) <= 25000); if (!joueurs.length) joueurs = [FB.uid]; } }
    const ns = { game_mode: modeActif, rush_seed: 1000 + Math.floor(Math.random() * 999000), version: VERSION_JEU, rounds: v.rounds, current_round: 1, essais: v.essais, min: v.min, max: v.max,
      timer: v.timer, host_id: FB.uid, visible: sc.visible !== false, start_time: FB.maintenant() };
    if (modeActif === "PIEGE") {  // ordre circulaire tiré au hasard, puis paires « qui choisit pour qui » de la 1re manche
      const ordre = [...joueurs]; for (let i = ordre.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [ordre[i], ordre[j]] = [ordre[j], ordre[i]]; }
      Object.assign(ns, piegeReglages(ordre, joueurs, 1, ns.rush_seed, ns.start_time));
    }
    Object.assign(M.reglages, ns); M.statut = "playing"; M.majIndex();
    FB.patch(`lobbies/${M.lobby}`, { status: "playing", settings: ns, match_data: null, fini_states: null, round_wins: null, rush_recap: null, piege_pret: null, piege_essais: null, piege_verdicts: null, piege_recap: null });
  }
  boucle();
}

/* ---------- partie */
async function partie() {
  const gen = ++M.gen;
  await MOTS.pret;
  const dm = await M.lireSalon();
  if (gen !== M.gen) return;
  if (dm && dm.settings) Object.assign(M.reglages, dm.settings);
  const conf = M.reglages, mode = conf.game_mode || "CLASSIQUE", piege = mode === "PIEGE";
  const fl = trier(MOTS.multiListe.filter(m => m.length >= (conf.min || 6) && m.length <= (conf.max || 10)));
  const fList = fl.length ? fl : trier(MOTS.multiListe);
  const graine = conf.rush_seed || 12345;
  const motsRush = piege ? ["?".repeat(conf.max || 7)] : mode === "CHAINE" ? await motsChaine(fList, graine) : await Promise.all(Array.from({ length: 100 }, (_, i) => motGraine(fList, graine, i)));
  if (gen !== M.gen) return;
  const G = { mot: motsRush[0], rush: 0, ligne: 0, fini: false, statut: {}, round: Number(conf.round_num || 1), debut: conf.start_time || FB.maintenant(), reste: conf.timer || 180, minuteur: true, scoresBlast: M._scoresBlast || new Set() };
  M.dernierMot = piege ? "" : G.mot;
  G.tape = mode === "MYSTERE" ? [] : [G.mot[0]];
  const reprise = M.reprise; M.reprise = false;
  if (G.round === 1 && !reprise) { M.score = 0; G.scoresBlast = new Set(); FB.patch(`lobbies/${M.lobby}/players/${FB.uid}`, { score: 0 }); }
  M._scoresBlast = G.scoresBlast;
  if (RUSHS.includes(mode)) FB.patch(`lobbies/${M.lobby}/players/${FB.uid}`, { rush_index: 0 });
  G.elimine = mode === "ELIMINATION" && (conf.elimines || []).includes(FB.uid);
  if (mode === "ELIMINATION" && G.round > 1 && !G.elimine) { M.score = G.round - 1; FB.patch(`lobbies/${M.lobby}/players/${FB.uid}`, { score: M.score }); }  // 1 point par manche survécue
  G.coopN = 0; G.coopAttente = []; G.coopMd = {}; G.coopSig = "";
  if (piege) {  // Mot piégé : chacun choisit le mot de sa cible, puis devine celui qu'on lui a choisi
    G.piegeDe = Object.assign({}, conf.piege_de || {}); G.piegeId = conf.piege_id || ""; G.piegeFin = Number(conf.piege_fin_choix || PIEGE_FIN_INFINIE) / 1000;
    G.piegeCible = Object.keys(G.piegeDe).find(t => G.piegeDe[t] === FB.uid) || null;
    G.mots = {}; G.lectures = {}; G.envoyes = new Set(); G.recaps = new Set(); G.secours = new Set(); G.essaisTxt = {}; G.pretEnvoye = {};
    G.monMot = ""; G.choix = []; G.choixEnvoi = false; G.attenteVerdict = null; G.motReel = ""; G.premiere = ""; G.piegeN = 0; G.attenteRecap = null; G.casesChoix = [];
    G.phase = G.piegeCible && FB.uid in G.piegeDe ? "choix" : "spectateur"; G.etatPiege = null;
  }

  const kh = hauteurFenetre() >= 760 ? 50 : 40;
  const tailleMoi = () => Math.floor(Math.max(24, Math.min(70, Math.min(58, (hauteurFenetre() - 250 - 3 * (kh + 8)) / (conf.essais || 6) - 8, (Math.min(window.innerWidth - (window.innerWidth > 900 ? 330 : 0), 640) - 30) / Math.max(G.mot.length, 5) - 8) * (lireConfig().user_zoom || 1))));
  const info = h("div.milieu"), sM = stat("Manche", "1"), sT = stat("Temps", "00:00"), sS = stat("Score", nombre(M.score), "var(--mal)");
  sM.set(String(G.round), null, ` / ${conf.rounds || 1}`);
  const zoneMoi = h("div", { style: { marginTop: "16px" } }); let gMoi = grille(conf.essais || 6, G.mot.length, tailleMoi()); zoneMoi.append(gMoi);
  const msg = h("div.msg", { style: { margin: "10px 0 6px", fontSize: "15px" } });
  const lienDef = h("button.lien.cache", { onclick: () => window.open(`https://www.google.com/search?q=D%C3%A9finition+du+mot+${G.mot}`, "_blank") }, "Définition ↗");
  const suivant = bouton("Manche suivante", clicSuivant, { largeur: 300, hauteur: 52 }); suivant.classList.add("cache");
  const kb = clavier(ajouter, effacer, valider, kh);
  // l'hôte peut ramener tout le monde au salon en cours de partie (avec confirmation)
  const btnSalon = h("button.lien.cache", { onclick: () => { if (M.estHote && confirm("Ramener tous les joueurs au salon ?\nLa partie en cours sera annulée.")) M.ramenerAuSalon(); } }, "Retour au salon");
  const advZone = h("div.col", { style: { gap: "26px", padding: "20px 40px 0 10px", minWidth: "260px" } });
  const adv = {};
  const opp = Object.entries((dm || {}).players || {}).filter(([pid]) => pid !== FB.uid);
  const tAdv = Math.floor(Math.max(8, Math.min({ 1: 30, 2: 24 }[opp.length] || 18, ((hauteurFenetre() - 160) / Math.max(1, opp.length) - 30) / (conf.essais || 6) - 3)));  // adaptée au nombre de joueurs
  function construireAdv(pid, nom, longueur) {
    const g = grille(conf.essais || 6, longueur, tAdv, true);
    if (!adv[pid]) { const nm = h("div.gras", { style: { fontSize: "17px" } }, nom), sc = h("div.chiffres", { style: { fontSize: "22px", color: "var(--mal)" } }, "0"), et = h("div.t2", { style: { fontSize: "14px" } }), mm = h("div.gras", { style: { fontSize: "14px", color: "var(--mal)", marginTop: "4px" } });
      const bloc = h("div.ligne", { style: { alignItems: "flex-start", gap: "16px" } }, h("div"), h("div", {}, nm, sc, et, mm)); advZone.append(bloc); adv[pid] = { bloc, nm, sc, et, mm }; }
    adv[pid].bloc.firstChild.replaceWith(g); adv[pid].g = g; adv[pid].longueur = longueur;
  }
  opp.forEach(([pid, p]) => construireAdv(pid, capitaliser(p.name), G.mot.length));
  const zm = h("span.t2", { style: { fontSize: "13px", minWidth: "44px", textAlign: "center" } }, `${Math.round((lireConfig().user_zoom || 1) * 100)} %`);
  const zoom = d => { const z = Math.round(Math.max(0.6, Math.min(1.6, (lireConfig().user_zoom || 1) + d)) * 100) / 100; majConfig({ user_zoom: z }); zm.textContent = `${Math.round(z * 100)} %`; gMoi.cases.flat().forEach(t => t.taille(tailleMoi())); G.casesChoix?.forEach?.(t => t.taille(tailleMoi())); };
  ecran(h("div.entete", {}, icone("retour", quitterJeu, false, "Quitter"), info, h("div.ligne", {}, btnSalon, icone("moins", () => zoom(-0.1), false, "Réduire"), zm, icone("plus", () => zoom(0.1), false, "Agrandir"))),
    h("div.ligne", { style: { alignItems: "flex-start", flexWrap: "wrap", justifyContent: "center" } },
      h("div.centre", { style: { flex: 1, minWidth: "320px" } }, h("div.stats", { style: { marginTop: "4px", gap: "min(68px, 7.5vw)" } }, sM, sT, sS), zoneMoi, h("div.ligne", { style: { gap: "8px", margin: "8px 0 4px" } }, msg, lienDef), suivant, h("div", { style: { margin: "4px 0 16px" } }, kb)),
      advZone));
  enJeu = true;
  info.textContent = `${NOM_MODE[mode] || mode} · ${G.mot.length} lettres`;
  document.onkeydown = e => {
    if (G.fini || e.ctrlKey || e.metaKey || e.altKey) return;
    const c = e.key.length === 1 ? e.key.toUpperCase() : "";
    if (c && ALPHABET.includes(c)) ajouter(c); else if (e.key === "Backspace") effacer(); else if (e.key === "Enter") valider(); else return;
    e.preventDefault();
  };
  function quitterJeu() { M.quitter(); accueil(); }
  const maxTape = () => mode === "MYSTERE" ? G.mot.length - 1 : G.mot.length;
  function maj() {
    if (G.fini) return;
    if (piege && G.phase !== "devine") { if (G.phase === "choix") piegeRendreChoix(); return; }
    const l = gMoi.cases[G.ligne];
    if (mode === "MYSTERE") {
      l[0].maj("?", "", false); l[0].classList.add("saisie");
      for (let i = 1; i < l.length; i++) l[i].maj(G.tape[i - 1] || "", "", i === G.tape.length + 1);
    } else l.forEach((t, i) => t.maj(i < G.tape.length ? G.tape[i] : "", i === 0 ? "bien" : "", i === G.tape.length));
  }
  function ajouter(c) {
    if (G.fini) return;
    if (piege && G.phase !== "devine") { if (G.phase === "choix" && !G.choixEnvoi && G.choix.length < (conf.max || 7)) { G.choix.push(c); piegeRendreChoix(); } return; }
    if (piege && G.attenteVerdict !== null) return;
    if (G.tape.length < maxTape()) G.tape.push(c); maj();
  }
  function effacer() {
    if (G.fini) return;
    if (piege && G.phase !== "devine") { if (G.phase === "choix" && !G.choixEnvoi && G.choix.length) { G.choix.pop(); piegeRendreChoix(); } return; }
    if (piege && G.attenteVerdict !== null) return;
    if (G.tape.length > (mode === "MYSTERE" ? 0 : 1)) G.tape.pop(); maj();
  }
  function messageTemp(t, coul, duree = 1200) { msg.textContent = t; msg.style.color = coul; setTimeout(() => { if (!G.fini && msg.textContent === t) msg.textContent = ""; }, duree); }
  const pj = `lobbies/${M.lobby}/players/${FB.uid}`;
  function valider() {
    if (G.fini) return;
    if (piege) { if (G.phase === "choix") validerChoix(); else if (G.phase === "devine") validerPiege(); return; }
    if (G.tape.length !== maxTape()) return;
    const essais = conf.essais || 6;
    if (mode === "MYSTERE") {
      const suf = G.tape.join(""), cible = G.mot.slice(1);
      const ok = suf === cible || [...ALPHABET].some(ch => MOTS.multiBanque.has(ch + suf));
      if (!ok) return messageTemp("Mot inconnu", "var(--danger)");
      const res = Array(cible.length).fill("absent"), secret = [...G.mot];
      for (let i = 0; i < cible.length; i++) if (G.tape[i] === cible[i]) { res[i] = "bien"; secret[i + 1] = null; }
      for (let i = 0; i < cible.length; i++) if (res[i] !== "bien") { const j = secret.indexOf(G.tape[i]); if (j >= 0) { res[i] = "mal"; secret[j] = null; } }
      majStatuts(G.statut, G.tape, res); for (const ch of ALPHABET) kb.setCouleur(ch, G.statut[ch]);
      res.forEach((e, i) => gMoi.cases[G.ligne][i + 1].maj(G.tape[i], e, false));
      gMoi.cases[G.ligne].forEach(t => t.classList.remove("curseur"));
      FB.put(`lobbies/${M.lobby}/match_data/${FB.uid}/${G.ligne}`, { c: enCodes(["absent", ...res]), l: ["?", ...G.tape] });
      if (res.every(e => e === "bien")) { gMoi.cases[G.ligne][0].maj(G.mot[0], "bien"); finirRound(true); }
      else if (G.ligne >= essais - 1) finirRound(false);
      else { G.ligne++; G.tape = []; maj(); }
      return;
    }
    const t = G.tape.join("");
    if (!MOTS.multiBanque.has(t) && t !== G.mot) return messageTemp("Mot inconnu", "var(--danger)");
    if (mode === "COOP") return validerCoop();
    const res = evaluer(G.tape, G.mot);
    majStatuts(G.statut, G.tape, res); for (const ch of ALPHABET) kb.setCouleur(ch, G.statut[ch]);
    gMoi.cases[G.ligne].forEach((c, i) => c.maj(G.tape[i], res[i], false));
    const payload = { c: enCodes(res), l: G.tape };
    if (RUSHS.includes(mode)) payload.w_idx = G.rush;
    if (!(RUSHS.includes(mode) && t === G.mot)) FB.put(`lobbies/${M.lobby}/match_data/${FB.uid}/${G.ligne}`, payload);
    if (t === G.mot) {
      if (RUSHS.includes(mode)) { M.score++; FB.patch(pj, { score: M.score, rush_index: G.rush + 1 }); sS.set(nombre(M.score)); motSuivantRush(); messageTemp("+1 point · mot suivant !", "var(--succes)"); }
      else finirRound(true);
    } else if (G.ligne >= essais - 1) {
      if (RUSHS.includes(mode)) {
        const c = gMoi.cases;
        for (let r = 0; r < essais - 1; r++) c[r].forEach((x, i) => x.maj(c[r + 1][i].lettre, c[r + 1][i].etat));
        c[essais - 1].forEach(x => x.maj("", ""));
        G.ligne = essais - 1; G.tape = [G.mot[0]]; maj();
      } else finirRound(false);
    } else { G.ligne++; G.tape = [G.mot[0]]; maj(); }
  }
  /* coopératif : une grille commune remplie par tous les joueurs */
  function validerCoop() {
    const k = G.coopN++, res = evaluer(G.tape, G.mot);
    const v = { c: enCodes(res), l: [...G.tape], t: SV };
    FB.put(`lobbies/${M.lobby}/match_data/${FB.uid}/${k}`, v);
    G.coopAttente.push([FB.uid, k, Object.assign({}, v, { t: null })]);  // affiché tout de suite, en attendant le serveur
    G.tape = [G.mot[0]]; rendreCoop();
  }
  function rendreCoop() {
    const essais = conf.essais || 6, serveur = fusionCoop(G.coopMd, essais);
    const connus = new Set(serveur.map(([, pid, k]) => pid + "/" + k));
    G.coopAttente = G.coopAttente.filter(([pid, k]) => !connus.has(pid + "/" + k));
    const lignes = [...serveur, ...G.coopAttente.map(([pid, k, v]) => [9e15, pid, k, v])].slice(0, essais);
    const sig = lignes.map(([, pid, k]) => pid + "/" + k).join(",");
    if (sig !== G.coopSig) {
      G.coopSig = sig; G.statut = {};
      gMoi.cases.forEach((row, r) => {
        if (r < lignes.length) { const v = lignes[r][3]; row.forEach((t, c) => t.maj((v.l || [])[c] || "", deCode((v.c || [])[c] || "A"), false));
          majStatuts(G.statut, v.l || [], (v.c || []).map(x => ({ B: "bien", M: "mal" })[x] || "absent")); }
        else if (!(G.fini && r === G.ligne)) row.forEach(t => t.maj("", "", false));
      });
      for (const ch of ALPHABET) kb.setCouleur(ch, G.statut[ch]);
    }
    if (G.fini) return;
    G.ligne = Math.min(lignes.length, essais - 1);
    if (lignes.some(([, , , v]) => (v.c || ["A"]).every(x => x === "B"))) finirRound(true);
    else if (lignes.length >= essais) finirRound(false);
    else maj();
  }
  /* ---- Mot piégé : le mot n'est jamais lisible par celui qui le devine (règles Firebase) ; ses essais sont évalués par son
     choisisseur ou, s'il est parti, par le premier autre joueur présent, qui révèle aussi le mot en fin de paire. */
  let nomsPiege = Object.fromEntries(Object.entries((dm || {}).players || {}).map(([pid, v]) => [pid, v.name || "?"]));
  const piegeNoms = d => { if (d && d.players) nomsPiege = Object.fromEntries(Object.entries(d.players).map(([pid, v]) => [pid, v.name || "?"])); return nomsPiege; };
  const piegeFinConnue = () => G.piegeFin < 3e10;  // la fin du choix est fixée (tous ont choisi, ou l'hôte a forcé)
  const piegeTexteLongueur = (mi, ma) => mi === ma ? `${mi} lettres` : ma === mi + 1 ? `${mi} ou ${ma} lettres` : `de ${mi} à ${ma} lettres`;
  function piegeVider() { zoneMoi.innerHTML = ""; gMoi = { cases: [] }; G.casesChoix = []; G.etiqMonMot = null; }
  function piegeDemarrer(d) {
    d = d || {}; piegeNoms(d);
    if (G.phase === "spectateur") {
      piegeVider(); G.fini = true; kb.remove(); FB.put(`lobbies/${M.lobby}/fini_states/${FB.uid}`, true);
      msg.textContent = "Tu regardes cette manche"; msg.style.color = "var(--texte2)"; return;
    }
    const pret = d.piege_pret || {};
    if (pret[G.piegeCible]) G.phase = "attente";  // reprise : le mot de notre cible est déjà choisi
    if (G.phase === "attente" && pret[FB.uid] && typeof pret[FB.uid] === "object" && piegeFinConnue()) piegeDevine(pret[FB.uid], d);
    else if (G.phase === "attente") piegeConstruireAttente();
    else piegeConstruireChoix(d);
  }
  function piegeConstruireChoix(d) {
    piegeVider();
    const mi = conf.min || 6, ma = conf.max || 7, nom = capitaliser(piegeNoms(d)[G.piegeCible] || "?");
    info.textContent = `${NOM_MODE.PIEGE} · choisis le mot de ${nom}`;
    const rg = h("div.ligne", { style: { gap: "8px", justifyContent: "center", margin: "12px 0 4px", flexWrap: "wrap" } });
    G.casesChoix = Array.from({ length: ma }, () => { const t = tuile(tailleMoi()); rg.append(t); return t; });
    zoneMoi.append(h("div.centre", {}, h("div.gras", { style: { fontSize: "19px" } }, `Choisis le mot que ${nom} devra deviner`),
      h("div.t2", { style: { fontSize: "14px", marginTop: "2px" } }, piegeTexteLongueur(mi, ma) + (ma > mi ? " (cases en pointillé facultatives)" : "") + " · un mot du dictionnaire · gardé secret · pas de limite de temps"), rg));
    G.ligne = 0; piegeRendreChoix(); piegeZoneHote();
  }
  function piegeRendreChoix() {
    const mi = conf.min || 6;  // toutes les cases sont affichées ; celles au-delà du minimum sont facultatives (pointillés)
    G.casesChoix.forEach((t, i) => { t.classList.toggle("facultative", i >= mi && !G.choix[i]); t.maj(G.choix[i] || "", "", i === G.choix.length && !G.choixEnvoi); if (i >= mi && !G.choix[i]) t.classList.add("facultative"); });
  }
  // avancement du choix des mots, et pour l'hôte le bouton qui force le démarrage (mot au hasard pour ceux qui n'ont pas choisi)
  function piegeZoneHote() {
    G.etatPiege = h("div.t2", { style: { fontSize: "14px", marginTop: "14px", textAlign: "center" } });
    G.zoneForcer = h("div.centre.cache", { style: { marginTop: "10px" } }, bouton("Forcer le démarrage", () => piegeForcer(), { variante: "discret", largeur: 240 }));
    zoneMoi.append(G.etatPiege, G.zoneForcer);
    piegeMajEtat();
  }
  function piegeMajEtat(d) {
    if (!G.etatPiege || !G.etatPiege.isConnected) return;
    const pret = (d || M._dernierSalon || {}).piege_pret || {};
    G.etatPiege.textContent = `${Object.keys(G.piegeDe).filter(t => t in pret).length} sur ${Object.keys(G.piegeDe).length} mots choisis` + (piegeFinConnue() ? " · c'est parti !" : "");
    G.zoneForcer.classList.toggle("cache", !(M.estHote && !piegeFinConnue()));  // seul l'hôte peut forcer le démarrage
  }
  // affiche le mot qu'on a choisi pour sa cible (jamais ceux choisis par ou pour les autres)
  function piegeMajMonMot(d) {
    if (!G.monMot && G.piegeCible && (((d || M._dernierSalon || {}).piege_pret) || {})[G.piegeCible]) {
      const sec = G.mots[G.piegeCible] || piegeMot(G.piegeCible);  // reprise : relu en arrière-plan (autorisé : on est son choisisseur)
      if (sec && sec.de === FB.uid) G.monMot = sec.mot;
    }
    const a = adv[G.piegeCible];  // affiché sous la mini-grille du joueur concerné
    if (G.monMot && a && a.mm.textContent !== `Ton mot : ${G.monMot}`) a.mm.textContent = `Ton mot : ${G.monMot}`;
  }
  // hôte : fixe la fin du choix à maintenant ; chacun passe à la devinette, ceux qui n'ont rien choisi ont un mot au hasard
  function piegePoserFin() {
    const ms = Math.floor(FB.maintenant() * 1000); G.piegeFin = ms / 1000; conf.piege_fin_choix = ms;
    FB.patch(`lobbies/${M.lobby}/settings`, { piege_fin_choix: ms });
  }
  // hôte : démarre la devinette tout de suite ; ceux qui n'ont pas encore choisi reçoivent un mot au hasard
  function piegeForcer() {
    if (!M.estHote || piegeFinConnue()) return;
    piegePoserFin(); piegeMajEtat();
  }
  function piegeConstruireAttente(texte = "Mot envoyé ✓") {
    piegeVider();
    zoneMoi.append(h("div.centre", { style: { padding: "30px 0 0" } }, h("div.titre", { style: { fontSize: "26px", marginBottom: "6px" } }, texte),
      h("div.t2", { style: { fontSize: "15px" } }, "En attente des autres joueurs…")));
    piegeMajMonMot(); piegeZoneHote();
  }
  function piegeMotHasard() {
    const mi = conf.min || 6, ma = conf.max || 7, l = MOTS.multiListe.filter(m => m.length >= mi && m.length <= ma && /^[A-Z]+$/.test(m));
    const src = l.length ? l : MOTS.multiListe; return src[Math.floor(Math.random() * src.length)];
  }
  function validerChoix() {
    if (G.choixEnvoi) return;
    const mi = conf.min || 6, ma = conf.max || 7, mot = G.choix.join("");
    if (mot.length < mi || mot.length > ma) return messageTemp(`Le mot doit faire ${piegeTexteLongueur(mi, ma)}`, "var(--danger)", 1800);
    if (!MOTS.multiBanque.has(mot)) return messageTemp("Mot inconnu", "var(--danger)");
    piegeEnvoyer(G.piegeCible, mot, FB.uid, false);
  }
  // enregistre le mot secret de « cible » puis annonce sa longueur et sa 1re lettre (comme dans les autres modes)
  async function piegeEnvoyer(cible, mot, de, auto) {
    const moiChoix = cible === G.piegeCible && de === FB.uid;
    if (moiChoix) { G.choixEnvoi = true; piegeRendreChoix(); }
    const ok = await FB.ok("PUT", `pieges/${M.lobby}/${G.piegeId}/${cible}`, { mot, de, auto });
    if (ok) await FB.ok("PUT", `lobbies/${M.lobby}/piege_pret/${cible}`, { n: mot.length, p: mot[0] });
    if (gen !== M.gen) return;
    if (ok) G.mots[cible] = { mot, de, auto };
    else if (!moiChoix) G.secours.delete(cible);  // mot de secours refusé (horloge) : on réessaiera
    if (ok && cible === G.piegeCible && de === FB.uid) G.monMot = mot;
    if (!moiChoix || G.phase !== "choix") return;
    if (ok || FB.maintenant() > G.piegeFin) {  // refusé après la fin du décompte : un mot au hasard a déjà été attribué
      G.phase = "attente"; piegeConstruireAttente(auto || !ok ? "Mot tiré au hasard" : "Mot envoyé ✓");
    } else { G.choixEnvoi = false; piegeRendreChoix(); messageTemp("Envoi impossible, réessaie", "var(--danger)", 1800); }
  }
  function piegeDevine(inf, d) {
    const n = Number(inf.n) || 0, prem = String(inf.p || "?").slice(0, 1);
    piegeVider(); G.phase = "devine"; G.piegeN = n; G.premiere = prem; G.mot = prem + "?".repeat(Math.max(0, n - 1));
    G.ligne = 0; G.tape = [prem]; G.attenteVerdict = null; G.statut = {};
    gMoi = grille(conf.essais || 6, n, tailleMoi()); zoneMoi.append(gMoi);
    info.textContent = `${NOM_MODE.PIEGE} · mot choisi par ${capitaliser(piegeNoms(d)[G.piegeDe[FB.uid]] || "?")} · ${n} lettres`;
    const essais = (d.piege_essais || {})[FB.uid] || {};
    for (let k = 0; k < (conf.essais || 6); k++) {  // reprise : on rejoue les essais déjà envoyés
      const t = essais[`e${k}`]; if (typeof t !== "string") break;
      G.essaisTxt[k] = t; G.ligne = k; G.tape = [...t]; G.attenteVerdict = k;
      if (!piegeAppliquerVerdict(d) || G.fini) break;
    }
    for (const ch of ALPHABET) kb.setCouleur(ch, G.statut[ch]);
    maj(); piegeMajMonMot(d);
    if (G.attenteVerdict !== null) { gMoi.cases[G.attenteVerdict].forEach(t => t.classList.remove("curseur")); msg.textContent = "Vérification…"; msg.style.color = "var(--texte2)"; }
  }
  function validerPiege() {
    if (G.attenteVerdict !== null || G.tape.length !== G.piegeN) return;
    const t = G.tape.join("");
    if (!MOTS.multiBanque.has(t)) return messageTemp("Mot inconnu", "var(--danger)");
    const k = G.ligne; G.essaisTxt[k] = t; G.attenteVerdict = k;
    FB.put(`lobbies/${M.lobby}/piege_essais/${FB.uid}/e${k}`, t);
    gMoi.cases[k].forEach(c => c.classList.remove("curseur"));
    msg.textContent = "Vérification…"; msg.style.color = "var(--texte2)";
  }
  // applique le verdict (couleurs) de l'essai en attente, s'il est arrivé ; renvoie true s'il a été appliqué
  function piegeAppliquerVerdict(d) {
    const k = G.attenteVerdict; if (k === null) return false;
    const v = (((d.piege_verdicts || {})[FB.uid]) || {})[`e${k}`], t = [...(G.essaisTxt[k] || "")];
    if (typeof v !== "string" || v.length !== G.piegeN || t.length !== G.piegeN) return false;
    const res = [...v].map(c => ({ B: "bien", M: "mal" })[c] || "absent");
    G.attenteVerdict = null;
    majStatuts(G.statut, t, res); for (const ch of ALPHABET) kb.setCouleur(ch, G.statut[ch]);
    res.forEach((e, i) => gMoi.cases[k][i].maj(t[i], e, false));
    gMoi.cases[k].forEach(c => c.classList.remove("curseur"));
    FB.put(`lobbies/${M.lobby}/match_data/${FB.uid}/${k}`, { c: [...v], l: t });
    if (msg.textContent === "Vérification…") msg.textContent = "";
    if (res.every(e => e === "bien")) { G.motReel = G.mot = M.dernierMot = t.join(""); finirRound(true); }
    else if (k >= (conf.essais || 6) - 1) finirRound(false);
    else { G.ligne = k + 1; G.tape = [G.premiere]; maj(); }
    return true;
  }
  // mot secret de « cible » (pour l'évaluer) : en cache, sinon lu en arrière-plan (refusé par la base si c'est le nôtre)
  function piegeMot(cible) {
    if (G.mots[cible]) return G.mots[cible];
    if (Date.now() - (G.lectures[cible] || 0) > 1500) {
      G.lectures[cible] = Date.now();
      FB.get(`pieges/${M.lobby}/${G.piegeId}/${cible}`).then(x => { if (gen === M.gen && x && typeof x.mot === "string") G.mots[cible] = x; });
    }
    return null;
  }
  // qui évalue les essais de « cible » : son choisisseur s'il est là, sinon le premier autre participant présent
  function piegeEvaluateur(cible, actifs) {
    const c = G.piegeDe[cible]; if (actifs.includes(c)) return c;
    return actifs.filter(u => u !== cible && u in G.piegeDe).sort()[0] || null;
  }
  function piegeTick(d, s, p, actifs, fs) {
    const essaisMax = Number(s.essais || 8), maintenant = FB.maintenant(), pret = d.piege_pret || {};
    const recapR = ((d.piege_recap || {})[`r${G.round}`]) || {};
    const fin = Number(s.piege_fin_choix || PIEGE_FIN_INFINIE) / 1000;  // fixée par l'hôte (tous ont choisi, ou démarrage forcé)
    if (fin !== G.piegeFin) G.piegeFin = fin;
    // 0. hôte : tous les mots (des joueurs présents) sont choisis → la devinette commence
    if (M.estHote && !piegeFinConnue()) {
      const attendus = Object.entries(G.piegeDe).filter(([t, c]) => actifs.includes(t) && actifs.includes(c)).map(([t]) => t);
      if (attendus.length && attendus.every(t => t in pret)) piegePoserFin();
    }
    piegeMajEtat(d); piegeMajMonMot(d);
    // 1. notre choix : mot au hasard si l'hôte a forcé le démarrage
    if (G.phase === "choix" && !G.choixEnvoi && piegeFinConnue() && maintenant > G.piegeFin) {
      if (pret[G.piegeCible]) { G.phase = "attente"; piegeConstruireAttente("Mot tiré au hasard"); }
      else piegeEnvoyer(G.piegeCible, piegeMotHasard(), FB.uid, true);
    }
    // 2. notre mot est prêt, la fin du choix est fixée : place à la devinette
    if (G.phase === "attente" && pret[FB.uid] && typeof pret[FB.uid] === "object" && piegeFinConnue()) piegeDevine(pret[FB.uid], d);
    // 3. verdict de notre dernier essai
    if (G.phase === "devine" && G.attenteVerdict !== null && !G.fini) piegeAppliquerVerdict(d);
    // 4. mot au hasard pour un choisisseur parti avant d'avoir choisi
    if (piegeFinConnue() && maintenant > G.piegeFin + 5) {
      for (const [t, c] of Object.entries(G.piegeDe)) {
        if (t in pret || !actifs.includes(t) || G.secours.has(t)) continue;
        if (piegeEvaluateur(t, actifs.filter(u => u !== c)) === FB.uid) { G.secours.add(t); piegeEnvoyer(t, piegeMotHasard(), c, true); }
      }
    }
    // 5. évaluation des essais des cibles dont on a la charge, puis révélation du mot en fin de paire
    const tousEssais = d.piege_essais || {}, tousVerdicts = d.piege_verdicts || {};
    const num = k => /^\d+$/.test(String(k).slice(1)) ? Number(String(k).slice(1)) : 99;
    for (const [t, c] of Object.entries(G.piegeDe)) {
      if (t === FB.uid || !(t in p) || t in recapR || G.recaps.has(t)) continue;
      if (piegeEvaluateur(t, actifs) !== FB.uid) continue;
      const sec = piegeMot(t); if (!sec) continue;
      const mot = sec.mot;
      if (!(t in pret) && Date.now() / 1000 - (G.pretEnvoye[t] || 0) > 3) {  // annonce perdue : on la renvoie
        G.pretEnvoye[t] = Date.now() / 1000; FB.put(`lobbies/${M.lobby}/piege_pret/${t}`, { n: mot.length, p: mot[0] });
      }
      const et = tousEssais[t] && typeof tousEssais[t] === "object" ? tousEssais[t] : {};
      const vt = tousVerdicts[t] && typeof tousVerdicts[t] === "object" ? Object.assign({}, tousVerdicts[t]) : {};
      for (const k of Object.keys(et).sort((a, b) => num(a) - num(b))) {
        const g = et[k];
        if (k in vt || G.envoyes.has(`${t}|${k}`) || typeof g !== "string" || g.length !== mot.length) continue;
        const v = enCodes(evaluer([...g], mot)).join("");
        FB.put(`lobbies/${M.lobby}/piege_verdicts/${t}/${k}`, v); G.envoyes.add(`${t}|${k}`); vt[k] = v;
      }
      const cle = Object.keys(vt).sort((a, b) => num(a) - num(b)).find(k => vt[k].length && [...vt[k]].every(x => x === "B"));
      const gagne = cle === undefined ? 0 : num(cle) + 1;
      if (gagne || Object.keys(vt).length >= essaisMax || fs[t] || G.reste <= 0) {
        G.recaps.add(t);
        FB.put(`lobbies/${M.lobby}/piege_recap/r${G.round}/${t}`, { de: c, mot, essais: gagne, auto: !!sec.auto });
      }
    }
    // 6. notre mot révélé et notre score (recalculé à partir du récapitulatif de toutes les manches)
    const mien = recapR[FB.uid];
    if (mien && typeof mien === "object" && typeof mien.mot === "string" && !G.motReel) G.motReel = G.mot = M.dernierMot = mien.mot;
    const total = piegePoints(d.piege_recap, FB.uid, essaisMax);
    if (total !== M.score) { M.score = total; sS.set(nombre(total)); FB.patch(pj, { score: total }); }
  }
  // la manche ne se clôt qu'une fois chaque mot révélé (8 s de délai au plus, si un évaluateur manque)
  function piegeRecapsComplets(d, actifs) {
    const recapR = ((d.piege_recap || {})[`r${G.round}`]) || {};
    const attendus = Object.keys(G.piegeDe).filter(t => actifs.includes(t) && piegeEvaluateur(t, actifs) && !(t in recapR));
    if (!attendus.length) return true;
    if (G.attenteRecap === null) G.attenteRecap = Date.now();
    return Date.now() - G.attenteRecap > 8000;
  }
  // état d'un adversaire pendant une manche de Mot piégé
  function piegeEtatAdv(pid, d, nbEssais) {
    const pret = d.piege_pret || {};
    if (!(pid in G.piegeDe)) return "Spectateur";
    const saCible = Object.keys(G.piegeDe).find(t => G.piegeDe[t] === pid);
    if (saCible && !(saCible in pret)) return "Choisit un mot…";
    if (!(pid in pret)) return "Attend son mot…";
    return `Essai ${Math.min(nbEssais + 1, conf.essais || 6)}`;
  }
  function motSuivantRush() {
    G.rush++; G.mot = motsRush[G.rush] || fList[Math.floor(Math.random() * fList.length)]; M.dernierMot = G.mot;
    G.ligne = 0; G.tape = [G.mot[0]]; G.statut = {};
    FB.del(`lobbies/${M.lobby}/match_data/${FB.uid}`); FB.put(`lobbies/${M.lobby}/match_data/${FB.uid}`, {});
    FB.patch(pj, { rush_index: G.rush, score: M.score });
    const ng = grille(conf.essais || 6, G.mot.length, tailleMoi()); gMoi.replaceWith(ng); gMoi = ng;
    for (const ch of ALPHABET) kb.setCouleur(ch, null);
    info.textContent = `${NOM_MODE[mode]} · mot n° ${G.rush + 1} · ${G.mot.length} lettres`; maj();
  }
  function finirRound(vic) {
    G.fini = true; (gMoi.cases[Math.min(G.ligne, gMoi.cases.length - 1)] || []).forEach(t => t.classList.remove("curseur"));
    if (vic) {
      if (mode === "CLASSIQUE" || mode === "MYSTERE" || mode === "COOP") { M.score++; FB.patch(pj, { score: M.score }); }
      else if (mode === "PRECISION") { const base = Math.max(1, (conf.essais || 6) - G.ligne); M.score += G.ligne === 0 ? base * 2 : base; FB.patch(pj, { score: M.score }); }
      else if (mode === "BLAST" || mode === "ELIMINATION") FB.put(`lobbies/${M.lobby}/round_wins/r${G.round}/${FB.uid}`, SV);
    }
    sS.set(nombre(M.score));
    FB.put(`lobbies/${M.lobby}/fini_states/${FB.uid}`, true);
    msg.textContent = vic ? "Bien joué !" : "Manche terminée"; msg.style.color = vic ? "var(--succes)" : "var(--texte2)";
    lienDef.classList.remove("cache");
  }
  async function clicSuivant() {
    suivant.classList.add("cache");
    const d = await M.lireSalon(); if (!d) return;
    const s = d.settings;
    if (RUSHS.includes(mode)) {
      const maxIdx = Math.max(0, G.rush, ...Object.values(d.players || {}).map(p => p.rush_index || 0));
      FB.patch(`lobbies/${M.lobby}/rush_recap`, { [`r${G.round}`]: motsRush.slice(0, maxIdx + 1) });
    }
    const fin = { status: "finished" };
    if (mode === "ELIMINATION") {
      const [elim, vivants] = calculElimination(d, Number(s.current_round));
      s.elimines = [...(s.elimines || []), ...elim];
      // scores finaux écrits avec la fin de partie : 1 point par manche survécue (les survivants ont survécu à toutes)
      fin["settings/elimines"] = s.elimines; for (const v of vivants) fin[`players/${v}/score`] = Number(s.current_round);
      if (vivants.length <= 1) { M.statut = "finished"; FB.patch(`lobbies/${M.lobby}`, fin); return; }
    }
    let actifsP = [];
    if (piege && Number(s.current_round) < Number(s.rounds)) {
      const pl = d.players || {}, maxMs = Math.max(0, ...Object.values(pl).map(v => v.last_seen || 0));
      actifsP = Object.keys(pl).filter(pid => maxMs - (pl[pid].last_seen || 0) <= 15000);
      if (actifsP.length < 2) { M.statut = "finished"; FB.patch(`lobbies/${M.lobby}`, fin); return; }  // plus assez de joueurs pour former des paires
    }
    if (Number(s.current_round) < Number(s.rounds)) {
      Object.assign(s, { rush_seed: 1000 + Math.floor(Math.random() * 999000), current_round: Number(s.current_round) + 1, start_time: FB.maintenant() });
      const maj = { settings: s, status: "playing", match_data: null, fini_states: null };
      if (piege) { Object.assign(s, piegeReglages(s.piege_ordre || [], actifsP, s.current_round, s.rush_seed, s.start_time)); Object.assign(maj, { piege_pret: null, piege_essais: null, piege_verdicts: null }); }
      Object.assign(M.reglages, s);
      FB.patch(`lobbies/${M.lobby}`, maj);
    } else { M.statut = "finished"; FB.patch(`lobbies/${M.lobby}`, fin); }
  }
  function pointsBlast(d) {
    const rw = d.round_wins || {}; let r = {};
    if (Array.isArray(rw)) r = rw[G.round] || {}; else r = rw[`r${G.round}`] || rw[String(G.round)] || {};
    return Object.entries(r).sort((a, b) => (typeof a[1] === "number" ? a[1] : 0) - (typeof b[1] === "number" ? b[1] : 0));
  }
  function traiter(d) {
    if (d.status === "waiting") { G.minuteur = false; salon(); return false; }
    if (d.status === "finished") {
      const sf = d.settings || {};
      if (sf.game_mode === "ELIMINATION" && !(sf.elimines || []).includes(FB.uid)) { M.score = Number(sf.current_round || 1); FB.patch(pj, { score: M.score }); }  // a survécu jusqu'au bout
      G.minuteur = false; resultats(); return false;
    }
    const s = d.settings || {}, p = d.players || {};
    const serverNow = Math.max(0, ...Object.values(p).map(x => x.last_seen || 0));
    // nouvelle manche, ou nouvelle partie lancée après la manche en cours (une lecture en retard est ignorée)
    if (Number(s.current_round || 1) > G.round || (s.rush_seed && s.rush_seed !== conf.rush_seed && Number(s.start_time || 0) > G.debut + 0.5)) {
      Object.assign(M.reglages, s); M.reglages.round_num = Number(s.current_round || 1); partie(); return false;
    }
    let hid = s.host_id;
    let actifs = Object.keys(p).filter(pid => serverNow === 0 || (serverNow - (p[pid].last_seen || 0)) / 1000 <= 15);
    if (!actifs.length) actifs = Object.keys(p);
    if (actifs.length && !actifs.includes(hid)) { const nh = [...actifs].sort()[0]; if (nh === FB.uid) FB.patch(`lobbies/${M.lobby}/settings`, { host_id: nh }); hid = nh; }
    M.estHote = s.host_id === FB.uid; M.nbJoueurs = Object.keys(p).length; M._dernierSalon = d;
    btnSalon.classList.toggle("cache", !M.estHote);
    sM.set(String(s.current_round || 1), null, ` / ${s.rounds || 1}`);
    const moi = p[FB.uid] || {}; sS.set(nombre(Math.max(M.score, typeof moi.score === "number" ? moi.score : 0)));
    if (RUSHS.includes(mode)) info.textContent = `${NOM_MODE[mode]} · mot n° ${G.rush + 1} · ${G.mot.length} lettres`;
    const fs = d.fini_states || {}, md = d.match_data || {};
    if (mode === "COOP") { G.coopMd = md; rendreCoop(); }
    const fc = actifs.filter(pid => fs[pid]).length;
    if (piege) piegeTick(d, s, p, actifs, fs);
    let roundFini = fc >= actifs.length || G.reste <= 0;
    if (piege && roundFini && !piegeRecapsComplets(d, actifs)) roundFini = false;
    if (roundFini) G.minuteur = false;
    for (const [pid, a] of Object.entries(adv)) {
      const pd = p[pid] || {}; const deco = !(p[pid] && (serverNow === 0 || (serverNow - (pd.last_seen || 0)) / 1000 <= 12));
      a.nm.textContent = capitaliser(pd.name || a.nm.textContent) + (pid === hid ? " ♛" : "");
      a.sc.textContent = nombre(typeof pd.score === "number" ? pd.score : 0);
      const advIdx = pd.rush_index ?? pd.score ?? 0;
      if (piege) { const nAdv = (((d.piege_pret || {})[pid]) || {}).n; if (typeof nAdv === "number" && a.longueur !== nAdv) construireAdv(pid, a.nm.textContent, nAdv); }
      if (RUSHS.includes(mode) && advIdx < motsRush.length && a.longueur !== motsRush[advIdx].length) construireAdv(pid, a.nm.textContent, motsRush[advIdx].length);
      let lignes = md[pid] || {}; lignes = Array.isArray(lignes) ? lignes.map((v, i) => [i, v]) : Object.entries(lignes).filter(([k]) => /^\d+$/.test(k)).map(([k, v]) => [Number(k), v]);
      lignes = lignes.filter(([, v]) => v && (!RUSHS.includes(mode) || v.w_idx === advIdx));
      const trouve = lignes.some(([, v]) => { const c = (v.c || []).slice(mode === "MYSTERE" ? 1 : 0); return c.length > 0 && c.every(x => x === "B"); });  // Mystère : la case 0 (lettre cachée) est toujours "A"
      let etat, coul = "var(--texte2)";
      if (deco) { etat = "Déconnecté"; coul = "var(--danger)"; }
      else if (mode === "ELIMINATION" && (s.elimines || []).includes(pid)) etat = "Éliminé";
      else if (mode === "COOP") etat = `${lignes.length} proposition${lignes.length > 1 ? "s" : ""}`;
      else if (piege && !fs[pid]) etat = piegeEtatAdv(pid, d, lignes.length);
      else if (RUSHS.includes(mode)) etat = `Mot n° ${advIdx + 1}` + (advIdx < G.rush ? ` · ${motsRush[advIdx]}` : "");
      else if (fs[pid]) { etat = trouve ? `Trouvé en ${lignes.length}` : "Pas trouvé"; if (trouve) coul = "var(--succes)"; }
      else etat = `Essai ${Math.min(lignes.length + 1, conf.essais || 6)}`;
      a.et.textContent = etat; a.et.style.color = coul;
      const voir = RUSHS.includes(mode) ? advIdx < G.rush : (G.fini || mode === "COOP");
      const cible = a.g.cases.map(r => r.map(() => ["", ""]));
      for (const [i, v] of lignes) { if (i >= cible.length) continue; (v.c || []).forEach((c, j) => { if (j < cible[i].length) cible[i][j] = [voir ? ((v.l || [])[j] || "") : "", deCode(c)]; }); }
      a.g.cases.forEach((r, i) => r.forEach((t, j) => t.maj(cible[i][j][0], cible[i][j][1])));
    }
    if (mode === "BLAST" && !G.scoresBlast.has(G.round)) {
      const sw = pointsBlast(d);
      if (sw.length) { const rang = sw.findIndex(([pid]) => pid === FB.uid); if (rang >= 0 && rang < 4) { M.score += [4, 3, 2, 1][rang]; FB.patch(pj, { score: M.score }); G.scoresBlast.add(G.round); } }
      else if (roundFini) G.scoresBlast.add(G.round);
    }
    if (G.fini) {
      lienDef.classList.remove("cache");
      if (roundFini) {
        let t = `Le mot était ${G.mot}`;
        if (piege) t = piegeLignesRecap(((d.piege_recap || {})[`r${G.round}`]) || {}, G.piegeDe, piegeNoms(d)).join("\n");
        if (mode === "BLAST") { const parts = pointsBlast(d).slice(0, 4).map(([pid], r) => `${capitaliser((p[pid] || {}).name || "Joueur")} +${[4, 3, 2, 1][r]}`); if (parts.length) t += "\n" + parts.join("   ·   "); }
        let derniere = Number(s.current_round) >= Number(s.rounds);
        if (mode === "ELIMINATION") {
          const [elim, vivants] = calculElimination(d, Number(s.current_round || 1));
          t += elim.length ? `\nÉliminé${elim.length > 1 ? "s" : ""} : ${elim.map(x => capitaliser((p[x] || {}).name || "?")).join(", ")}` : "\nPersonne n'est éliminé";
          derniere = derniere || vivants.length <= 1;
        }
        msg.textContent = t; msg.style.color = "var(--mal)";
        if (M.estHote && suivant.classList.contains("cache")) { suivant.textContent = derniere ? "Voir les résultats" : "Manche suivante"; suivant.classList.remove("cache"); }
      } else { msg.textContent = (G.elimine ? "Tu es éliminé : tu regardes la fin de la partie\n" : "") + `En attente des autres joueurs (${fc}/${actifs.length})`; msg.style.color = "var(--texte2)"; }
    }
    return true;
  }
  if (piege) piegeDemarrer(dm);
  (async () => {
    while (gen === M.gen) {
      const d = await M.lireSalon();
      if (gen !== M.gen) return;
      if (d && !traiter(d)) return;
      await new Promise(r => setTimeout(r, piege ? 350 : 800));  // Mot piégé : le verdict d'un essai passe par un autre joueur, on rafraîchit plus vite
    }
  })();
  const minuteur = setInterval(() => {
    if (gen !== M.gen || !G.minuteur) return;
    if (piege) {  // le temps ne court qu'une fois le choix des mots terminé
      G.reste = piegeFinConnue() ? Math.max(0, Math.floor((conf.timer || 180) - (FB.maintenant() - G.piegeFin))) : (conf.timer || 180);
      if (!piegeFinConnue()) { sT.set("--:--", "var(--texte)"); return; }
    } else G.reste = Math.max(0, Math.floor((conf.timer || 180) - (FB.maintenant() - G.debut)));
    sT.set(mmss(G.reste), G.reste > 30 ? "var(--texte)" : "var(--danger)");
    if (G.reste <= 0) { if (!G.fini) finirRound(false); G.minuteur = false; }
  }, 500);
  nettoyageEcran.push(() => clearInterval(minuteur));
  maj();
  if (G.elimine) {  // spectateur jusqu'à la fin de la partie
    G.fini = true; kb.remove(); gMoi.cases[0].forEach(t => t.classList.remove("curseur"));
    FB.put(`lobbies/${M.lobby}/fini_states/${FB.uid}`, true);
    msg.textContent = "Tu es éliminé : tu regardes la fin de la partie"; msg.style.color = "var(--texte2)";
  }
}

/* ---------- résultats */
async function resultats() {
  const gen = ++M.gen;
  const d = await M.lireSalon();
  if (!d || gen !== M.gen) return;
  const p = d.players || {}; if (!Object.keys(p).length) return;
  const s = d.settings || {}, mode = s.game_mode || "CLASSIQUE";
  const hote = (p[s.host_id] || {}).name;
  const classement = Object.entries(p).sort((a, b) => (b[1].score || 0) - (a[1].score || 0));
  const top = classement[0][1].score || 0, gagnants = classement.filter(([, v]) => (v.score || 0) === top).map(([, v]) => capitaliser(v.name));
  const rang = {}; let r = 0; classement.forEach(([pid, v], i) => { if (i > 0 && (v.score || 0) < (classement[i - 1][1].score || 0)) r = i; rang[pid] = r; });
  const ordre = classement.length >= 3 ? [1, 0, 2] : classement.length === 2 ? [1, 0] : [0];
  const hauteurs = [150, 110, 84];  // indexées par le rang : ex aequo = même marche
  const podium = h("div.podium", {}, ordre.map(k => { const [pid, v] = classement[k]; const premier = rang[pid] === 0;
    return h("div.centre", {}, premier ? h("div", { style: { color: "var(--mal)" }, html: `<svg viewBox="0 0 24 24" style="width:30px;height:30px;stroke:currentColor;fill:none;stroke-width:1.6;stroke-linejoin:round">${SVG.couronne}</svg>` }) : null,
      h("div.gras", { style: { fontSize: "17px", margin: "6px 0 12px" } }, capitaliser(v.name)),
      h("div.marche", { style: { height: hauteurs[rang[pid]] + "px", background: premier ? "var(--mal)" : "var(--tuile)", color: premier ? "var(--sur-mal)" : "var(--texte)" } }, h("div.rang", {}, String(rang[pid] + 1)), h("div.gras", { style: { fontSize: "16px" } }, `${nombre(v.score || 0)} pt${(v.score || 0) > 1 ? "s" : ""}`))); }));
  const tab = h("div.tableau", {}, h("div.r.h", {}, h("span", { style: { width: "62px" } }, "#"), h("span", {}, "Joueur"), h("span.p", {}, "Points")),
    classement.map(([pid, v]) => h("div.r" + (pid === FB.uid ? ".moi" : ""), {}, h("span", { style: { width: "62px" } }, String(rang[pid] + 1)), h("span", {}, capitaliser(v.name) + (pid === FB.uid ? " (vous)" : "")), h("span.p", {}, nombre(v.score || 0)))));
  const recap = h("div.t2", { style: { textAlign: "center", fontSize: "14px", whiteSpace: "pre-line" } });
  const majRecap = dd => {
    if ((dd.settings || {}).game_mode === "PIEGE") {  // qui a choisi quoi pour qui, manche par manche
      const rec = dd.piege_recap || {}, noms = Object.fromEntries(Object.entries(dd.players || {}).map(([pid, v]) => [pid, v.name || "?"]));
      const l = []; for (const k of Object.keys(rec).sort((a, b) => (parseInt(a.slice(1)) || 0) - (parseInt(b.slice(1)) || 0))) l.push(`Manche ${k.slice(1)}`, ...piegeLignesRecap(rec[k], null, noms));
      recap.textContent = l.join("\n"); return;
    }
    const rc = dd.rush_recap; if (!RUSHS.includes((dd.settings || {}).game_mode) || !rc) return;
    const l = Array.isArray(rc) ? rc.map((w, i) => w && Array.isArray(w) ? `Manche ${i} : ${w.join(", ")}` : null).filter(Boolean)
      : Object.keys(rc).sort((a, b) => parseInt(a.replace("r", "")) - parseInt(b.replace("r", ""))).filter(k => Array.isArray(rc[k]) && rc[k].length).map(k => `Manche ${k.replace("r", "")} : ${rc[k].join(", ")}`);
    recap.textContent = l.join("\n"); };
  majRecap(d);
  const mot = mode === "PIEGE" ? "" : M.dernierMot;
  ecran(barreHaut(() => { M.quitter(); accueil(); }, (hote ? `Salon de ${capitaliser(hote)} · ` : "") + `${NOM_MODE[mode] || mode} · Partie terminée`),
    h("div.centre", { style: { padding: "18px 0 30px", gap: "0" } },
      mot ? h("div.t2", { style: { fontSize: "17px" } }, "Le dernier mot était") : null,
      mot ? h("div.ligne", { style: { gap: "8px", margin: "8px 0 12px" } }, [...mot].map(ch => { const t = tuile(46); t.maj(ch, "bien"); return t; })) : null,
      h("div.titre", { style: { fontSize: "46px", margin: "0 0 14px", textAlign: "center" } }, gagnants.length === 1 ? `${gagnants[0]} remporte la partie` : "Égalité : " + gagnants.join(" et ")),
      podium, h("div", { style: { height: "18px" } }), tab, h("div", { style: { height: "14px" } }), recap,
      h("div.ligne", { style: { gap: "16px", marginTop: "10px", flexWrap: "wrap", justifyContent: "center" } },
        M.estHote ? bouton("Rejouer dans ce salon", rejouer, { largeur: 280, grand: true }) : (() => { const b = bouton("En attente de l'hôte…", () => {}, { largeur: 280, grand: true, variante: "discret" }); b.disabled = true; return b; })(),
        bouton("Retour à l'accueil", () => { M.quitter(); accueil(); }, { largeur: 240, grand: true, variante: "discret" }))));
  function rejouer() { return M.ramenerAuSalon(); }
  while (gen === M.gen) {
    await new Promise(r => setTimeout(r, 1000));
    if (gen !== M.gen) return;
    const dd = await M.lireSalon();
    if (gen !== M.gen) return;
    if (dd && dd.status === "waiting") { M.score = 0; salon(); return; }
    if (dd && (dd.settings || {}).game_mode === "PIEGE") {  // dernier mot révélé après la fin : récapitulatif et score à jour
      majRecap(dd);
      const total = piegePoints(dd.piege_recap, FB.uid, Number((dd.settings || {}).essais || 8));
      if (total !== M.score) { M.score = total; FB.patch(`lobbies/${M.lobby}/players/${FB.uid}`, { score: total }); }
    } else if (dd && !recap.textContent) majRecap(dd);
  }
}

/* ------------------------------------------------------------------ retour du téléphone
   Le bouton « retour » du téléphone (ou Alt+←) revient à l'écran précédent comme la flèche de l'écran, au lieu de fermer la page.
   Une entrée d'historique est ajoutée dès la première interaction (les navigateurs ignorent celles ajoutées sans geste de l'utilisateur) et après chaque retour. */
{
  const armer = () => { if (!history.state || history.state.smout !== 1) history.pushState({ smout: 1 }, ""); };
  addEventListener("pointerdown", armer, { once: true, capture: true });
  addEventListener("keydown", armer, { once: true, capture: true });
  addEventListener("popstate", () => {
    if (history.state && history.state.smout === 1) return;  // avance : rien à faire
    const ouvert = [...document.querySelectorAll(".voile:not(.cache)")].pop();
    if (enAccueil && !ouvert) { history.back(); return; }  // sur l'accueil : le retour quitte vraiment la page
    armer();
    if (ouvert) { ouvert.classList.add("cache"); return; }  // une fenêtre ouverte : on la ferme d'abord
    const b = document.querySelector('button.icone[aria-label="Retour"], button.icone[aria-label="Quitter"]');
    if (enJeu && !confirm("Quitter la partie en cours ?")) return;
    if (b) b.click(); else accueil();
  });
}

/* ------------------------------------------------------------------ démarrage */
chargerTheme();
{
  accueil();
}
