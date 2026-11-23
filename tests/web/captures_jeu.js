// Captures de la page de jeu pour chaque mode avec 1 à 8 joueurs (navigateur sans écran, faux serveur).
// node captures_jeu.js <dossier> [largeur] [hauteur] [modes séparés par des virgules] [nombres de joueurs séparés par des virgules]
const puppeteer = require("puppeteer-core");
const sleep = ms => new Promise(r => setTimeout(r, ms));
const [dossier, L = "1280", H = "860", MODES = "CLASSIQUE,BLAST,PRECISION,MYSTERE,RUSH,ELIMINATION,CHAINE,COOP,PIEGE", NS = "1,2,3,4,5,6,7,8"] = process.argv.slice(2);
const NOMS = ["BOB", "CHLOE", "DAVID", "EMMA", "FELIX", "GABY", "HUGO"];
const BASE = "http://127.0.0.1:9000";
async function faux(code, n) {  // n joueurs factices inscrits dans le salon (jetons du faux serveur)
  const out = [];
  for (let i = 0; i < n; i++) {
    const r = await (await fetch(BASE + "/signup", { method: "POST", body: "{}" })).json();
    const put = () => fetch(`${BASE}/v7/lobbies/${code}/players/${r.localId}.json?auth=${r.idToken}`, { method: "PATCH", body: JSON.stringify({ name: NOMS[i], score: 0, last_seen: { ".sv": "timestamp" } }) });
    await put(); out.push({ uid: r.localId, put });
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
