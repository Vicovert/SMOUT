// Robot joueur web (vraie page SMOUT dans Chrome sans écran) sur le faux serveur à règles. node robot_web.js '<json scénario>'
const puppeteer = require("puppeteer-core");
const fs = require("fs");
const S = JSON.parse(process.argv[2]);
const R = { nom: S.nom, support: "WEB", mots: [], evenements: [], erreurs: [] };
const log = (...a) => { console.log(`[WEB ${S.nom}]`, ...a); R.evenements.push(a.join(" ")); };
const sleep = ms => new Promise(r => setTimeout(r, ms));
const db = async () => (await (await fetch("http://127.0.0.1:9000/__admin.json")).json()) || {};
let b, p;
async function fin(ok) {
  R.ok = ok && !R.erreurs.length;
  try { const d = await db(); const lb = d.v7.lobbies[R.code]; R.scores_base = Object.fromEntries(Object.values(lb.players).map(x => [x.name, x.score]));
    if (lb.piege_recap) { R.recap_piege = lb.piege_recap; R.uids = Object.fromEntries(Object.entries(lb.players).map(([u, v]) => [u, v.name])); } } catch (e) {}
  fs.writeFileSync(S.sortie, JSON.stringify(R, null, 1)); log("fin", R.ok ? "OK" : "ÉCHEC");
  try { await p.evaluate(() => M.quitter()); await sleep(1500); await b.close(); } catch (e) {}
  process.exit(0);
}
const ev = (f, ...a) => p.evaluate(f, ...a);
async function attendre(f, t = 60000, ...a) { const end = Date.now() + t; while (Date.now() < end) { try { if (await ev(f, ...a)) return true; } catch (e) {} await sleep(200); } return false; }
async function clicTexte(sel, txt) { return ev((s, t) => { const e = [...document.querySelectorAll(s)].find(x => x.textContent.includes(t) && !x.closest(".cache")); if (!e) return false; e.click(); return true; }, sel, txt); }
// Mot piégé : choisit le mot de sa cible (S.choix : valide | invalide | rien), puis devine le sien (S.jeu : gagne | perd)
async function jeuPiege(manche) {
  const [mi, ma] = await ev(() => [M.reglages.min || 6, M.reglages.max || 7]);
  const txt = () => ev(() => document.body.innerText), msg = () => ev(() => document.querySelector(".msg")?.textContent || "");
  const enChoix = () => ev(() => document.body.innerText.includes("Choisis le mot que")), enDevine = () => ev(() => (document.querySelector(".milieu")?.textContent || "").includes("mot choisi par"));
  if (!(await attendre(() => /Choisis le mot que|Mot envoyé|Temps écoulé|mot choisi par|Tu regardes/.test(document.body.innerText), 30000))) { log("ÉCHEC pas de phase de choix"); return fin(false); }
  let choix = S.choix || "valide"; if (!(await enChoix())) { choix = "deja"; log(`manche ${manche} : mot de sa cible déjà choisi (reprise)`); }
  const effacer = async n => { for (let i = 0; i < n; i++) await p.keyboard.press("Backspace"); };
  if (choix === "invalide") {  // trop court, puis inconnu : refusés avec un message, sans rien envoyer
    for (const essai of ["ab", "z".repeat(mi)]) {
      await p.keyboard.type(essai, { delay: 15 }); await p.keyboard.press("Enter"); await sleep(400);
      const m = await msg(); (R.refus_choix ||= []).push(m); log("mot", essai, "refusé :", m);
      if (!(await enChoix())) { log("ÉCHEC mot invalide accepté"); return fin(false); }
      await effacer(essai.length);
    }
  }
  if (choix === "valide" || choix === "invalide") {
    const mot = await ev((mi, ma) => { const l = MOTS.multiListe.filter(m => m.length >= mi && m.length <= ma && /^[A-Z]+$/.test(m)); return l[Math.floor(Math.random() * l.length)]; }, mi, ma);
    await p.keyboard.type(mot.toLowerCase(), { delay: 15 }); await p.keyboard.press("Enter");
    if (!(await attendre(() => !document.body.innerText.includes("Choisis le mot que"), 20000))) { log("ÉCHEC envoi du mot choisi"); return fin(false); }
    (R.choisis ||= []).push(mot); log(`manche ${manche} : mot choisi pour sa cible`, mot);
  } else if (choix === "rien") log(`manche ${manche} : ne choisit rien (mot au hasard à la fin du décompte)`);
  if (S.planter_apres_choix === manche) { log("PLANTAGE simulé après le choix"); R.config = await ev(() => localStorage.getItem("smout_config")); fs.writeFileSync(S.sortie, JSON.stringify(Object.assign(R, { ok: true, plante: true }))); b.process().kill("SIGKILL"); process.exit(0); }
  if (!(await attendre(() => (document.querySelector(".milieu")?.textContent || "").includes("mot choisi par") || /Manche terminée|Bien joué|Tu regardes/.test(document.body.innerText), 90000))) { log("ÉCHEC pas de mot à deviner"); return fin(false); }
  if (!(await enDevine())) return;
  const uid = await ev(() => FB.uid), pid = await ev(() => M.reglages.piege_id), code = R.code;
  const secret = (await db()).v7.pieges[code][pid][uid].mot;  // le robot « triche » via l'admin du faux serveur
  R.mots.push(secret);
  const essais = await ev(() => M.reglages.essais || 6);
  const coups = (S.jeu || "gagne") === "gagne" ? [secret]
    : await ev((m, n) => [...MOTS.multiBanque].filter(x => x.length === m.length && x[0] === m[0] && x !== m).sort().slice(0, n), secret, essais);
  let trouve = false, nb = 0;
  for (let k = 0; k < coups.length; k++) {
    await p.keyboard.type(coups[k].slice(1).toLowerCase(), { delay: 15 }); await p.keyboard.press("Enter");
    let verdict = "";
    for (let i = 0; i < 750 && !verdict; i++) { verdict = ((((await db()).v7.lobbies[code].piege_verdicts || {})[uid] || {})[`e${k}`]) || ""; if (!verdict) await sleep(200); }
    if (!verdict) { log("ÉCHEC pas de verdict pour", coups[k]); return fin(false); }
    nb = k + 1; if (/^B+$/.test(verdict)) trouve = true;
    await sleep(900);
    if (await ev(() => /Manche terminée|Bien joué/.test(document.body.innerText))) break;
  }
  (R.devinettes ||= []).push([secret, trouve ? nb : 0]);
  log(`manche ${manche} : mot`, secret, trouve ? "trouvé en" : "pas trouvé ·", nb);
}
(async () => {
  b = await puppeteer.launch({ executablePath: process.env.CHROME || "/usr/bin/google-chrome", headless: "new", args: ["--no-sandbox"] });
  p = await b.newPage(); await p.setViewport({ width: S.largeur || 1200, height: S.hauteur || 860 });
  p.on("pageerror", e => { R.erreurs.push(e.message); log("ERREUR PAGE", e.message); });
  p.on("console", m => { if (m.type() === "error" && !/401|Failed to load resource/.test(m.text())) { R.erreurs.push(m.text()); log("console", m.text()); } });
  p.on("dialog", async d => { R.evenements.push("alerte: " + d.message()); log("alerte", d.message()); await d.dismiss(); });
  await p.setRequestInterception(true);
  p.on("request", async r => {
    const u = r.url(); let c = null;
    if (u.includes("firebasedatabase.app")) c = "http://127.0.0.1:9000/" + u.split(".app/")[1];
    else if (u.includes("securetoken")) c = "http://127.0.0.1:9000/token";
    else if (u.includes("identitytoolkit")) c = "http://127.0.0.1:9000/signup";
    if (!c) return r.continue();
    if (r.method() === "OPTIONS") return r.respond({ status: 204, headers: { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "*", "Access-Control-Allow-Headers": "*" } });
    try { const res = await fetch(c, { method: r.method(), body: r.postData(), headers: { "Content-Type": "application/json" } });
      r.respond({ status: res.status, headers: { "Access-Control-Allow-Origin": "*" }, contentType: "application/json", body: await res.text() }); } catch (e) { try { r.abort(); } catch (e2) {} }
  });
  let confInit = { pseudo: S.nom };
  if (S.config_depuis) {  // reprise : configuration (identité, partie en cours) laissée par un robot qui a planté
    for (let i = 0; i < 600 && !(fs.existsSync(S.config_depuis) && JSON.parse(fs.readFileSync(S.config_depuis)).config); i++) await sleep(500);
    const prec = fs.existsSync(S.config_depuis) ? JSON.parse(fs.readFileSync(S.config_depuis)) : {};
    if (!prec.config) { log("ÉCHEC pas de configuration à reprendre"); R.erreurs.push("pas de configuration"); fs.writeFileSync(S.sortie, JSON.stringify(R)); process.exit(0); }
    confInit = JSON.parse(prec.config); await sleep((S.attente_reprise || 0) * 1000);
  }
  await p.evaluateOnNewDocument(c => { if (!sessionStorage.getItem("i")) { localStorage.setItem("smout_config", c); sessionStorage.setItem("i", "1"); } }, JSON.stringify(confInit));
  await p.goto((process.env.SMOUT_SITE || "http://127.0.0.1:8000/"), { waitUntil: "networkidle0" });
  await clicTexte(".carte-menu", "Multijoueur"); await sleep(1200);
  if (S.role === "reprise") {
    if (!(await attendre(() => [...document.querySelectorAll("button")].some(b => b.textContent === "Reprendre"), 15000))) { log("ÉCHEC pas de proposition de reprise"); return fin(false); }
    await clicTexte("button", "Reprendre");
    if (!(await attendre(() => M.lobby !== "", 15000))) { log("ÉCHEC reprise"); return fin(false); }
    R.code = await ev(() => M.lobby); log("partie reprise", R.code, "score", await ev(() => M.score));
  } else if (S.role === "host") {
    await clicTexte("button", "Créer un salon"); await sleep(400);
    if (S.prive) await clicTexte(".choix", "Privé");
    if (S.mdp) { await ev(() => document.querySelector(".case").click()); await p.type('input[placeholder="Mot de passe"]', S.mdp); }
    await clicTexte("button", "Créer le salon");
    if (!(await attendre(() => M.lobby !== "", 20000))) { log("ÉCHEC création"); return fin(false); }
    R.code = await ev(() => M.lobby); log("salon créé", R.code);
  } else {
    const trouver = async () => { const idx = ((await db()).v7 || {}).index || {}; const c = Object.entries(idx).filter(([k, v]) => v.status === "waiting" && v.hote === S.hote).sort((a, b) => b[1].maj - a[1].maj); return c.length ? c[0][0] : null; };
    await clicTexte("button", "Rejoindre un salon"); await sleep(500);
    let code = null; for (let i = 0; i < 300 && !(code = await trouver()); i++) await sleep(300);
    if (!code) { log("ÉCHEC salon introuvable"); return fin(false); }
    await p.type('input[placeholder="CODE"]', code); await p.keyboard.press("Enter"); await sleep(1500);
    if (S.mdp || S.mdp_faux) {
      if (!(await attendre(() => !document.querySelector(".voile").classList.contains("cache"), 8000))) { log("ÉCHEC pas de demande de mot de passe"); return fin(false); }
      if (S.mdp_faux) {
        await attendre(() => document.activeElement && document.activeElement.type === "password", 8000) || await p.click('input[type="password"]');
        await p.type('input[type="password"]', S.mdp_faux); await p.keyboard.press("Enter");
        await attendre(() => document.body.textContent.includes("Mot de passe incorrect") || M.lobby !== "", 8000);  // la machine peut être chargée
        const refus = await ev(() => document.body.textContent.includes("Mot de passe incorrect") && M.lobby === "");
        R.mdp_faux_refuse = refus; log(refus ? "mauvais mot de passe refusé" : "BUG: mauvais mot de passe accepté");
        if (!refus) return fin(false);
        await ev(() => { document.querySelector('input[type="password"]').value = ""; });
      }
      await attendre(() => document.activeElement && document.activeElement.type === "password", 8000) || await p.click('input[type="password"]');
      await p.type('input[type="password"]', S.mdp || ""); await p.keyboard.press("Enter");
    }
    if (!(await attendre(() => M.lobby !== "", 15000))) { log("ÉCHEC rejoindre"); return fin(!!S.attendu_refus); }
    R.code = await ev(() => M.lobby); log("a rejoint", R.code);
  }
  for (let partie = 1; partie <= (S.parties || 1); partie++) {
    if (S.role === "host") {
      if (!(await attendre(n => M.nbJoueurs >= n && document.querySelector(".joueur"), 120000, S.nb || 2))) { log("ÉCHEC joueurs manquants"); return fin(false); }
      if (partie === 1) {
        if (S.mode !== "CLASSIQUE") await clicTexte(".choix", ({ BLAST: "Blast", PRECISION: "Précision", MYSTERE: "Mystère", RUSH: "Rush", ELIMINATION: "Élimination", CHAINE: "Chaîne", COOP: "Coopératif", PIEGE: "Mot piégé" })[S.mode]);
        await sleep(300);
        const regler = (i, v) => ev((i, v) => { const x = document.querySelectorAll(".salon-partie input[type=range]")[i]; x.value = v; x.dispatchEvent(new Event("input")); }, i, v);
        await regler(0, S.manches || 1);
        if (S.timer) await regler(1, S.timer);
        if (S.essais) await regler(2, S.essais);
      }
      await sleep(1500);
      if (!(await clicTexte("button.lancer", "Lancer"))) { log("ÉCHEC lancer"); return fin(false); }
      log("partie lancée", partie);
    }
    let debut = 1;
    if (S.role === "reprise") { await attendre(() => document.querySelector(".clavier") && document.querySelector(".stat .v"), 90000); debut = await ev(() => +document.querySelector(".stat .v").textContent || 1); log("reprend à la manche", debut); }
    for (let manche = debut; manche <= (S.manches || 1); manche++) {
      if (manche > 1 && await ev(() => !!document.querySelector(".podium"))) { log("partie terminée avant la manche", manche); break; }
      if (!(await attendre(m => (document.querySelector(".clavier") || document.body.innerText.includes("Tu es éliminé")) && document.querySelector(".stat .v")?.textContent === String(m) && (M.reglages.game_mode === "PIEGE" || M.dernierMot), 90000, manche))) { log("ÉCHEC manche pas commencée", manche, JSON.stringify(await ev(() => ({ t: document.body.innerText.slice(0, 200), clavier: !!document.querySelector(".clavier"), v: document.querySelector(".stat .v")?.textContent, mot: M.dernierMot })))); return fin(false); }
      if (await ev(() => document.body.innerText.includes("Tu es éliminé"))) { log(`manche ${manche} : éliminé, spectateur`); R.elimine = manche; await attendre(m => document.querySelector(".podium") || +document.querySelector(".stat .v").textContent > m, 300000, manche); continue; }
      await sleep(1200);
      const mot = S.mode === "PIEGE" ? "" : await ev(() => M.dernierMot); if (mot) R.mots.push(mot);
      if (S.capture_jeu && manche === 1) { await p.keyboard.type("ab"); await sleep(200); await p.screenshot({ path: S.capture_jeu }); await p.keyboard.press("Backspace"); await p.keyboard.press("Backspace");
        R.deborde = await ev(() => { const w = document.documentElement.clientWidth; return [...document.querySelectorAll("body *")].filter(e => { const r = e.getBoundingClientRect(); return r.width > 0 && (r.right > w + 1 || r.left < -1); }).slice(0, 4).map(e => e.className); }); log("débordements", JSON.stringify(R.deborde)); } log(`partie ${partie} manche ${manche} mot ${mot}`);
      if (S.planter_manche === manche) { log("PLANTAGE simulé"); R.config = await ev(() => localStorage.getItem("smout_config")); fs.writeFileSync(S.sortie, JSON.stringify(Object.assign(R, { ok: true, plante: true }))); b.process().kill("SIGKILL"); process.exit(0); }
      const jeu = S.jeu || "gagne";
      if (S.mode === "PIEGE") await jeuPiege(manche);
      else if (jeu === "gagne") { await p.keyboard.type(mot.slice(1).toLowerCase(), { delay: 15 }); await p.keyboard.press("Enter"); }
      else if (jeu === "perd") {
        const faux = await ev((m, mys) => [...MOTS.multiBanque].filter(x => x.length === m.length && x !== m && (mys || x[0] === m[0])).sort().slice(0, 12), mot, S.mode === "MYSTERE");
        const essais = await ev(() => M.reglages.essais || 6);
        for (let k = 0; k < essais; k++) { await p.keyboard.type(faux[k].slice(1).toLowerCase(), { delay: 5 }); await p.keyboard.press("Enter"); await sleep(250); }
      } else if (jeu === "rush") {
        let n = 0;
        while (true) {
          const reste = await ev(() => { const v = document.querySelectorAll(".stat .v")[1].textContent.split(":"); return +v[0] * 60 + +v[1]; });
          if (reste <= 2) break;
          const m = await ev(() => M.dernierMot); await p.keyboard.type(m.slice(1).toLowerCase(), { delay: 5 }); await p.keyboard.press("Enter"); n++; await sleep(600);
        }
        (R.rush_trouves ||= []).push(n); log("rush trouvés", n);
      }
      await sleep(1000);
      await ev(() => { window.__clic = false; });
      const ok = await attendre(m => { if (document.querySelector(".podium") || (document.querySelector(".stat .v") && +document.querySelector(".stat .v").textContent > m)) return true;
        const b = [...document.querySelectorAll(".btn")].find(x => !x.classList.contains("cache") && /Manche suivante|Voir les résultats/.test(x.textContent));
        if (b && M.estHote && !window.__clic) { window.__clic = true; b.click(); } return false; }, 300000, manche);
      if (!ok) { log("ÉCHEC manche suivante / résultats"); return fin(false); }
    }
    if (!(await attendre(() => document.querySelector(".podium"), 90000))) { log("ÉCHEC pas de résultats"); return fin(false); }
    await sleep(2500);
    const d = await db(); const res = Object.fromEntries(Object.values(d.v7.lobbies[R.code].players).map(x => [x.name, x.score]));
    (R.resultats ||= []).push(res); log("résultats", JSON.stringify(res));
    R.texte_podium = await ev(() => document.querySelector(".titre").textContent + " | " + [...document.querySelectorAll(".tableau .r:not(.h)")].map(r => r.textContent).join(" ; "));
    if (S.capture) await p.screenshot({ path: S.capture });
    if (partie < (S.parties || 1)) {
      if (await ev(() => M.estHote)) await clicTexte("button", "Rejouer dans ce salon");
      if (!(await attendre(() => document.querySelector(".joueur"), 60000))) { log("ÉCHEC retour au salon"); return fin(false); }
      log("retour au salon");
    }
  }
  await sleep((S.rester ?? 6) * 1000);
  await fin(true);
})().catch(e => { R.erreurs.push(String(e)); log("EXCEPTION", e.message); fin(false); });
