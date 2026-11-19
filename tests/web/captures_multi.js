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
    ok(`${l}px accueil multi : reprise + partie rapide`, await p.evaluate(() => document.body.innerText.includes("Partie interrompue · salon 4821") && document.body.innerText.includes("Partie rapide")));
    ok(`${l}px accueil multi : rien ne dépasse`, !(await deb()).length, (await deb()).join(" "));
    await p.screenshot({ path: `/tmp/wm_accueil_${l}.png` });
    await p.evaluate(() => document.querySelector("button.a-rapide").click()); await sleep(2500);
    ok(`${l}px partie rapide → salon créé`, await p.evaluate(() => !!M.lobby && M.estHote));
    ok(`${l}px salon : 8 modes`, await p.evaluate(() => document.querySelectorAll(".choix").length >= 8));
    ok(`${l}px salon : rien ne dépasse`, !(await deb()).length, (await deb()).join(" "));
    await p.screenshot({ path: `/tmp/wm_salon_${l}.png`, fullPage: true });
    await p.evaluate(() => M.quitter()); await sleep(800); await p.close();
  }
  ok("aucune erreur JavaScript", !err.length, err.join(" | "));
  console.log(`${res.filter(Boolean).length}/${res.length} conformes`); await b.close(); process.exit(res.every(Boolean) ? 0 : 1);
})().catch(e => { console.log("EXCEPTION", e); process.exit(1); });
