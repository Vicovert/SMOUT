// Vérifie que le jeu s'installe (manifest) et fonctionne hors ligne après une première visite.
const puppeteer = require("puppeteer-core");
const sleep = ms => new Promise(r => setTimeout(r, ms));
const res = []; const ok = (n, c, i = "") => { res.push(!!c); console.log((c ? "OK    " : "ÉCHEC ") + n + (i ? "  — " + i : "")); };
(async () => {
  const b = await puppeteer.launch({ executablePath: process.env.CHROME || "/usr/bin/google-chrome", headless: "new", args: ["--no-sandbox"] });
  const p = await b.newPage(); const err = []; p.on("pageerror", e => err.push(e.message)); p.on("dialog", d => d.dismiss());
  await p.goto((process.env.SMOUT_SITE || "http://127.0.0.1:8000/"), { waitUntil: "networkidle0" });
  const man = await p.evaluate(async () => (await fetch(document.querySelector('link[rel="manifest"]').href)).json());
  ok("manifest valide (nom, icônes 192/512, standalone)", man.name === "SMOUT" && man.display === "standalone" && man.icons.some(i => i.sizes === "512x512"));
  ok("service worker actif", await p.evaluate(async () => { const r = await navigator.serviceWorker.ready; return !!r.active; }));
  await sleep(1500);
  const enCache = await p.evaluate(async () => { const k = await caches.keys(); const c = await caches.open(k[0]); return (await c.keys()).length; });
  ok("fichiers mis en cache", enCache >= 15, String(enCache));
  await p.setOfflineMode(true);
  await p.reload({ waitUntil: "load" }); await sleep(800);
  ok("hors ligne : l'accueil s'affiche", await p.evaluate(() => document.querySelectorAll(".carte-menu").length === 3));
  await p.evaluate(() => solo("libre")); await sleep(500);
  ok("hors ligne : partie solo jouable", await p.evaluate(() => !!document.querySelector(".clavier") && MOTS.liste.length > 20000));
  await p.evaluate(() => solo("mdj")); await sleep(400);
  ok("hors ligne : mot du jour", await p.evaluate(() => document.body.innerText.includes("Mot du jour")));
  await p.evaluate(() => multiAccueil()); await sleep(2500);
  ok("hors ligne : le multijoueur ne plante pas", await p.evaluate(() => document.body.innerText.includes("Multijoueur")), (await p.evaluate(() => document.body.innerText)).slice(0, 120).replace(/\n/g, " "));
  ok("aucune erreur JavaScript", !err.length, err.join(" | "));
  console.log(`${res.filter(Boolean).length}/${res.length} conformes`); await b.close(); process.exit(res.every(Boolean) ? 0 : 1);
})().catch(e => { console.log("EXCEPTION", e); process.exit(1); });
