// Captures de la page de jeu pour chaque mode avec 1 à 8 joueurs (navigateur sans écran, faux serveur).
// node captures_jeu.js <dossier> [largeur] [hauteur] [modes séparés par des virgules] [nombres de joueurs séparés par des virgules]
const puppeteer = require("puppeteer-core");
const sleep = ms => new Promise(r => setTimeout(r, ms));
const [dossier, L = "1280", H = "860", MODES = "CLASSIQUE,BLAST,PRECISION,MYSTERE,RUSH,ELIMINATION,CHAINE,COOP,PIEGE", NS = "1,2,3,4,5,6,7,8"] = process.argv.slice(2);
const THEMES_TEST = [
  { f: "#F4F1EA", v: "#E4E0D6", t: "#D8D3C6", b: "#2E8B57", m: "#E0A82E", a: "#BDB8AA", x: "#1B1A22", y: "#8A857A", s: "#FFFFFF", u: "#1B1A22" },
  { f: "#0D0221", v: "#1A0B3B", t: "#2B1259", b: "#FF2E88", m: "#00E5FF", a: "#2B1259", x: "#F5F0FF", y: "#8C7BB5", s: "#0D0221", u: "#0D0221" },
  { f: "#0F2A1D", v: "#153826", t: "#1E4D35", b: "#F2C94C", m: "#EB5757", a: "#1E4D35", x: "#E8F5EC", y: "#6FA283", s: "#0F2A1D", u: "#0F2A1D" },
  { f: "#2A0F0F", v: "#3A1818", t: "#512424", b: "#FF9F1C", m: "#2EC4B6", a: "#512424", x: "#FFF1E6", y: "#B27C6A", s: "#2A0F0F", u: "#2A0F0F" }];
const NOMS = ["BOB", "CHLOE", "DAVID", "EMMA", "FELIX", "GABY", "HUGO"];
const BASE = "http://127.0.0.1:9000";
async function faux(code, n) {  // n joueurs factices inscrits dans le salon (jetons du faux serveur)
  const out = [];
  for (let i = 0; i < n; i++) {
    const r = await (await fetch(BASE + "/signup", { method: "POST", body: "{}" })).json();
    const put = () => fetch(`${BASE}/v7/lobbies/${code}/players/${r.localId}.json?auth=${r.idToken}`, { method: "PATCH", body: JSON.stringify({ name: NOMS[i], score: 0, last_seen: { ".sv": "timestamp" } }) });
    await put(); out.push({ uid: r.localId, put });
    if (process.env.VIVANT) {  // joueurs « vivants » : chacun a SON thème, une ligne déjà jouée et une frappe en cours
      const th = THEMES_TEST[i % THEMES_TEST.length], H = `${BASE}/v7/lobbies/${code}`, A = `?auth=${r.idToken}`;
      await fetch(`${H}/players/${r.localId}.json${A}`, { method: "PATCH", body: JSON.stringify({ theme: th, frappe: "AB" + "CDE".slice(0, i % 3) }) });
      out[i].apres = () => fetch(`${H}/match_data/${r.localId}/0.json${A}`, { method: "PUT", body: JSON.stringify({ c: ["B", "A", "M", "A", "M", "A"], l: ["A", "R", "T", "I", "S", "T"] }) });
    }
  }
  const t = setInterval(() => out.forEach(o => o.put().catch(() => {})), 4000);
  return { out, stop: () => clearInterval(t), retirer: async i => fetch(`${BASE}/v7/lobbies/${code}/players/${out[i].uid}.json?auth=tok-${out[i].uid}`, { method: "DELETE" }) };
}
(async () => {
  const b = await puppeteer.launch({ executablePath: process.env.CHROME || "/usr/bin/google-chrome", headless: "new", args: ["--no-sandbox"] });
  const err = [];
  for (const mode of MODES.split(",")) for (const n of NS.split(",").map(Number)) {
    const ctx = await b.createBrowserContext(); const p = await ctx.newPage();
    await p.setViewport({ width: +L, height: +H, isMobile: +L < 600, hasTouch: +L < 600 });
    p.on("pageerror", e => err.push(`${mode}/${n}: ${e.message}`)); p.on("dialog", d => d.accept());
    await p.setRequestInterception(true);
    p.on("request", async r => { const u = r.url(); let c = null;
      if (u.includes("firebasedatabase.app")) c = BASE + "/" + u.split(".app/")[1]; else if (u.includes("securetoken")) c = BASE + "/token"; else if (u.includes("identitytoolkit")) c = BASE + "/signup";
      if (!c) return r.continue();
      if (r.method() === "OPTIONS") return r.respond({ status: 204, headers: { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "*", "Access-Control-Allow-Headers": "*" } });
      const x = await fetch(c, { method: r.method(), body: r.postData(), headers: { "Content-Type": "application/json" } }); r.respond({ status: x.status, headers: { "Access-Control-Allow-Origin": "*" }, contentType: "application/json", body: await x.text() }); });
    await p.evaluateOnNewDocument(() => { if (!sessionStorage.getItem("i")) { localStorage.setItem("smout_config", JSON.stringify({ pseudo: "ALICE" })); sessionStorage.setItem("i", "1"); } });
    try {
      await p.goto(process.env.SMOUT_SITE || "http://127.0.0.1:8000/", { waitUntil: "networkidle0" });
      await p.evaluate(() => multiAccueil()); await sleep(600);
      await p.evaluate(() => document.querySelector("button.a-creer").click()); await sleep(400);
      await p.evaluate(() => [...document.querySelectorAll("button")].find(x => x.textContent === "Créer le salon").click()); await sleep(1500);
      const code = await p.evaluate(() => M.lobby);
      const f = await faux(code, Math.max(1, n - 1));
      await p.waitForFunction(m => M.nbJoueurs >= m, { timeout: 15000 }, Math.max(2, n)); await sleep(500);
      await p.evaluate(m => [...document.querySelectorAll(".choix.mode")].find(x => x.textContent.includes(m)).click(), ({ CLASSIQUE: "Classique", BLAST: "Blast", PRECISION: "Précision", MYSTERE: "Mystère", RUSH: "Rush", ELIMINATION: "Élimination", CHAINE: "Chaîne", COOP: "Coopératif", PIEGE: "Mot piégé" })[mode]);
      await sleep(1200);
      await p.evaluate(() => document.querySelector(".salon-partie button.lancer").click());
      await p.waitForFunction(() => document.querySelector(".clavier") || /Choisis/.test(document.body.innerText), { timeout: 20000 }); await sleep(1500);
      for (const o of f.out) if (o.apres) await o.apres(); await sleep(1500);  // lignes déjà jouées (écrites après le lancement : il remet match_data à zéro)
      if (n === 1) { await f.retirer(0); await sleep(2500); }  // seul : le joueur factice est parti
      await p.screenshot({ path: `${dossier}/web_${L}_${mode}_${n}.png`, fullPage: +L < 600 });  // téléphone : page entière (les adversaires sont sous le clavier)
      const deb = await p.evaluate(() => { const r = []; const W = document.documentElement.clientWidth; document.querySelectorAll("body *").forEach(e => { const b = e.getBoundingClientRect(); if (b.width && b.right > W + 1 && getComputedStyle(e).position !== "fixed") r.push(e.className); }); return r.slice(0, 3); });
      if (deb.length) err.push(`${mode}/${n}: dépasse à droite ${deb.join(",")}`);
      f.stop();
    } catch (e) { err.push(`${mode}/${n}: ${e.message.split("\n")[0]}`); try { await p.screenshot({ path: `${dossier}/web_${L}_${mode}_${n}_ERREUR.png` }); } catch (_) {} }
    await ctx.close();
  }
  console.log("problèmes:", err.length ? "\n" + err.join("\n") : "aucun");
  await b.close();
})().catch(e => { console.log("EXCEPTION", e); process.exit(1); });
