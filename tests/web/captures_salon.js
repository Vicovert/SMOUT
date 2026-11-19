// Captures de l'écran Multijoueur et du salon (hôte et invité), ordinateur et téléphone.
const puppeteer = require("puppeteer-core");
const sleep = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  const b = await puppeteer.launch({ executablePath: process.env.CHROME || "/usr/bin/google-chrome", headless: "new", args: ["--no-sandbox"] });
  const err = [];
  async function page(nom, l, hh) {
    const p = await (await b.createBrowserContext()).newPage(); await p.setViewport({ width: l, height: hh, isMobile: l < 600, hasTouch: l < 600 });
    p.on("pageerror", e => err.push(nom + ": " + e.message)); p.on("dialog", d => d.dismiss());
    await p.setRequestInterception(true);
    p.on("request", async r => { const u = r.url(); let c = null;
      if (u.includes("firebasedatabase.app")) c = "http://127.0.0.1:9000/" + u.split(".app/")[1]; else if (u.includes("securetoken")) c = "http://127.0.0.1:9000/token"; else if (u.includes("identitytoolkit")) c = "http://127.0.0.1:9000/signup";
      if (!c) return r.continue();
      if (r.method() === "OPTIONS") return r.respond({ status: 204, headers: { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "*", "Access-Control-Allow-Headers": "*" } });
      const x = await fetch(c, { method: r.method(), body: r.postData(), headers: { "Content-Type": "application/json" } }); r.respond({ status: x.status, headers: { "Access-Control-Allow-Origin": "*" }, contentType: "application/json", body: await x.text() }); });
    await p.evaluateOnNewDocument(n => { if (!sessionStorage.getItem("i")) { localStorage.setItem("smout_config", JSON.stringify({ pseudo: n, partie_en_cours: n === "ALICE" ? { code: "4821", mdp: "", t: Date.now() / 1000 } : null })); sessionStorage.setItem("i", "1"); } }, nom);
    await p.goto(process.env.SMOUT_SITE || "http://127.0.0.1:8000/", { waitUntil: "networkidle0" }); return p;
  }
  const a = await page("ALICE", +(process.env.L || 390), 860);
  await a.evaluate(() => multiAccueil()); await sleep(1200); await a.screenshot({ path: "/tmp/s_multi_390.png" });
  const a2 = await page("ALICE", 1280, 860); await a2.evaluate(() => multiAccueil()); await sleep(1200); await a2.screenshot({ path: "/tmp/s_multi_1280.png" }); await a2.close();
  await a.evaluate(() => [...document.querySelectorAll("button")].find(x => x.textContent.includes("Créer un salon")).click()); await sleep(500);
  await a.evaluate(() => [...document.querySelectorAll("button")].find(x => x.textContent === "Créer le salon").click()); await sleep(1500);
  const code = await a.evaluate(() => M.lobby);
  const bo = await page("BOB", 390, 844); await bo.evaluate(() => multiAccueil()); await sleep(800);
  await bo.evaluate(() => document.querySelector("button.a-rejoindre").click()); await sleep(1200); await bo.screenshot({ path: "/tmp/s_rejoindre_390.png" });
  await bo.type('input[placeholder="CODE"]', code); await bo.keyboard.press("Enter"); await sleep(2500);
  await a.evaluate(() => [...document.querySelectorAll(".choix.mode")].find(x => x.textContent.includes("Élimination")).click()); await sleep(2000);
  await a.screenshot({ path: "/tmp/s_salon_hote_390.png", fullPage: true }); await bo.screenshot({ path: "/tmp/s_salon_invite_390.png", fullPage: true });
  await a.setViewport({ width: 1280, height: 860 }); await sleep(800); await a.screenshot({ path: "/tmp/s_salon_hote_1280.png", fullPage: true });
  console.log("erreurs:", err.length ? err.join(" | ") : "aucune");
  await b.close();
})().catch(e => { console.log("EXCEPTION", e); process.exit(1); });
