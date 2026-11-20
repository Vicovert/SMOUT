// Vérifie la mise en page des écrans multijoueur (accueil, salon) sur ordinateur et téléphone, avec le faux serveur.
const puppeteer = require("puppeteer-core");
const sleep = ms => new Promise(r => setTimeout(r, ms));
const res = []; const ok = (n, c, i = "") => { res.push(!!c); console.log((c ? "OK    " : "ÉCHEC ") + n + (i ? "  — " + i : "")); };
(async () => {
  const b = await puppeteer.launch({ executablePath: process.env.CHROME || "/usr/bin/google-chrome", headless: "new", args: ["--no-sandbox"] });
  const err = [];
  for (const [l, hh] of [[1280, 860], [360, 740]]) {
    const p = await b.newPage(); await p.setViewport({ width: l, height: hh, isMobile: l < 600, hasTouch: l < 600 });
    p.on("pageerror", e => err.push(e.message)); p.on("dialog", d => d.dismiss());
    await p.setRequestInterception(true);
    p.on("request", async r => { const u = r.url(); let c = null;
      if (u.includes("firebasedatabase.app")) c = "http://127.0.0.1:9000/" + u.split(".app/")[1]; else if (u.includes("securetoken")) c = "http://127.0.0.1:9000/token"; else if (u.includes("identitytoolkit")) c = "http://127.0.0.1:9000/signup";
      if (!c) return r.continue();
      if (r.method() === "OPTIONS") return r.respond({ status: 204, headers: { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "*", "Access-Control-Allow-Headers": "*" } });
      const x = await fetch(c, { method: r.method(), body: r.postData(), headers: { "Content-Type": "application/json" } }); r.respond({ status: x.status, headers: { "Access-Control-Allow-Origin": "*" }, contentType: "application/json", body: await x.text() }); });
    await p.evaluateOnNewDocument(() => { if (!sessionStorage.getItem("i")) { localStorage.setItem("smout_config", JSON.stringify({ pseudo: "ALICE", partie_en_cours: { code: "4821", mdp: "", t: Date.now() / 1000, score: 2 } })); sessionStorage.setItem("i", "1"); } });
    await p.goto(process.env.SMOUT_SITE || "http://127.0.0.1:8000/", { waitUntil: "networkidle0" });
    await p.evaluate(() => multiAccueil()); await sleep(1500);
    const deb = () => p.evaluate(() => { const w = document.documentElement.clientWidth; return [...document.querySelectorAll("body *")].filter(e => { const r = e.getBoundingClientRect(); return r.width > 0 && (r.right > w + 1 || r.left < -1); }).slice(0, 3).map(e => e.className); });
    ok(`${l}px accueil multi : reprise + créer / rejoindre`, await p.evaluate(() => document.body.innerText.includes("Partie interrompue · salon 4821") && document.body.innerText.includes("Créer un salon") && document.body.innerText.includes("Rejoindre un salon") && !document.body.innerText.includes("Partie rapide")));
    ok(`${l}px accueil multi : rien ne dépasse`, !(await deb()).length, (await deb()).join(" "));
    await p.screenshot({ path: `/tmp/wm_accueil_${l}.png` });
    await p.evaluate(() => document.querySelector("button.a-rejoindre").click()); await sleep(1200);
    ok(`${l}px page Rejoindre : code + liste`, await p.evaluate(() => !!document.querySelector('input[placeholder="CODE"]') && /salons publics/i.test(document.body.innerText)));
    ok(`${l}px page Rejoindre : rien ne dépasse`, !(await deb()).length, (await deb()).join(" "));
    await p.screenshot({ path: `/tmp/wm_rejoindre_${l}.png` });
    await p.evaluate(() => multiAccueil()); await sleep(800);
    await p.evaluate(() => document.querySelector("button.a-creer").click()); await sleep(600);
    ok(`${l}px création : cadenas sur Privé, couleurs différentes`, await p.evaluate(() => { const c = [...document.querySelectorAll(".choix")]; const pri = c.find(x => x.textContent.includes("Privé")), pub = c.find(x => x.textContent.includes("Public")); return !!pri.querySelector(".ico svg") && !pub.querySelector(".ico") && getComputedStyle(pri).getPropertyValue("--mc") !== getComputedStyle(pub).getPropertyValue("--mc") && !document.body.innerText.includes("Protéger") && !document.body.innerText.includes("jamais enregistré"); }));
    await p.screenshot({ path: `/tmp/wm_creation_${l}.png` });
    await p.evaluate(() => [...document.querySelectorAll("button")].find(x => x.textContent === "Créer le salon").click()); await sleep(2500);
    ok(`${l}px salon créé`, await p.evaluate(() => !!M.lobby && M.estHote));
    ok(`${l}px salon : curseurs (manches, temps, essais, lettres) et plus de pastilles de lettres`, await p.evaluate(() => document.querySelectorAll(".salon-partie input[type=range]").length === 5 && !document.querySelector(".salon-partie .chips")));
    ok(`${l}px salon : un curseur modifie le réglage`, await p.evaluate(() => { const i = document.querySelector(".salon-partie .curseur input"); i.value = 5; i.dispatchEvent(new Event("input")); return document.querySelector(".salon-partie .curseur .val").textContent === "5"; }));
    ok(`${l}px salon : 9 modes dont Mot piégé`, await p.evaluate(() => document.querySelectorAll(".choix").length >= 9 && document.body.innerText.includes("Mot piégé")));
    ok(`${l}px salon : rien ne dépasse`, !(await deb()).length, (await deb()).join(" "));
    await p.screenshot({ path: `/tmp/wm_salon_${l}.png`, fullPage: true });
    await p.evaluate(() => M.quitter()); await sleep(800); await p.close();
  }
  ok("aucune erreur JavaScript", !err.length, err.join(" | "));
  console.log(`${res.filter(Boolean).length}/${res.length} conformes`); await b.close(); process.exit(res.every(Boolean) ? 0 : 1);
})().catch(e => { console.log("EXCEPTION", e); process.exit(1); });
