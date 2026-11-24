// Page de jeu multijoueur sur téléphone (8.18) : tout tient sur un écran, sans défiler, de 2 à 8 joueurs.
// Adversaires (mini-grilles) en haut, ma grille au milieu, clavier du jeu en bas ; « Agrandir » grossit grille et clavier.
const puppeteer = require("puppeteer-core");
const sleep = ms => new Promise(r => setTimeout(r, ms));
const BASE = "http://127.0.0.1:9000", SITE = process.env.SMOUT_SITE || "http://127.0.0.1:8000/";
const res = []; const ok = (n, c, i = "") => { res.push(!!c); console.log((c ? "OK    " : "ÉCHEC ") + n + (i && !c ? "  — " + i : "")); };
const NOMS = ["BOB", "CHLOE", "DAVID", "EMMA", "FELIX", "GABY", "HUGO"];
async function faux(code, n) {
  const out = [];
  for (let i = 0; i < n; i++) {
    const r = await (await fetch(BASE + "/signup", { method: "POST", body: "{}" })).json();
    const put = () => fetch(`${BASE}/v7/lobbies/${code}/players/${r.localId}.json?auth=${r.idToken}`, { method: "PATCH", body: JSON.stringify({ name: NOMS[i], score: 0, last_seen: { ".sv": "timestamp" } }) });
    await put(); out.push(put);
  }
  const t = setInterval(() => out.forEach(f => f().catch(() => {})), 4000);
  return () => clearInterval(t);
}
(async () => {
  const b = await puppeteer.launch({ executablePath: process.env.CHROME || "/usr/bin/google-chrome", headless: "new", args: ["--no-sandbox"] });
  const err = [];
  for (const [n, L, H] of [[2, 390, 844], [4, 390, 844], [8, 390, 844], [8, 360, 780]]) {
    const ctx = await b.createBrowserContext(); const p = await ctx.newPage();
    await p.setViewport({ width: L, height: H, isMobile: true, hasTouch: true });
    p.on("pageerror", e => err.push(`${n}: ${e.message}`)); p.on("dialog", d => d.accept());
    await p.setRequestInterception(true);
    p.on("request", async r => { const u = r.url(); let c = null;
      if (u.includes("firebasedatabase.app")) c = BASE + "/" + u.split(".app/")[1]; else if (u.includes("securetoken")) c = BASE + "/token"; else if (u.includes("identitytoolkit")) c = BASE + "/signup";
      if (!c) return r.continue();
      if (r.method() === "OPTIONS") return r.respond({ status: 204, headers: { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "*", "Access-Control-Allow-Headers": "*" } });
      const x = await fetch(c, { method: r.method(), body: r.postData(), headers: { "Content-Type": "application/json" } }); r.respond({ status: x.status, headers: { "Access-Control-Allow-Origin": "*" }, contentType: "application/json", body: await x.text() }); });
    await p.evaluateOnNewDocument(() => { if (!sessionStorage.getItem("i")) { localStorage.setItem("smout_config", JSON.stringify({ pseudo: "ALICE" })); sessionStorage.setItem("i", "1"); } });
    await p.goto(SITE, { waitUntil: "networkidle0" });
    await p.evaluate(() => multiAccueil()); await sleep(500);
    await p.evaluate(() => document.querySelector("button.a-creer").click()); await sleep(400);
    await p.evaluate(() => [...document.querySelectorAll("button")].find(x => x.textContent === "Créer le salon").click()); await sleep(1500);
    const stop = await faux(await p.evaluate(() => M.lobby), n - 1);
    await p.waitForFunction(m => M.nbJoueurs >= m, { timeout: 15000 }, n); await sleep(500);
    await p.evaluate(() => document.querySelector(".salon-partie button.lancer").click());
    await p.waitForFunction(() => document.querySelector(".clavier"), { timeout: 20000 }); await sleep(1500);
    const m = await p.evaluate(() => {
      const r = s => document.querySelector(s).getBoundingClientRect(), moi = r(".jeu-tel .grille:not(.mini)"), adv = r(".adv-tel"), kb = r(".clavier");
      return { defile: document.documentElement.scrollHeight - innerHeight, H: innerHeight, advHaut: adv.bottom <= moi.top + 1, kbBas: kb.top >= moi.bottom - 1 && kb.bottom <= innerHeight + 1,
               nAdv: document.querySelectorAll(".adv-tel .adv").length, t: parseFloat(document.querySelector(".jeu-tel .grille:not(.mini) .tuile").style.getPropertyValue("--t")), kh: r(".touche").height };
    });
    const nom = `${n} joueurs (${L}×${H})`;
    ok(`${nom} : ${n - 1} adversaire(s) en haut, au-dessus de ma grille`, m.nAdv === n - 1 && m.advHaut, JSON.stringify(m));
    ok(`${nom} : clavier en bas, entièrement visible`, m.kbBas, JSON.stringify(m));
    ok(`${nom} : tout tient sur l'écran (pas de défilement)`, m.defile <= 1, JSON.stringify(m));
    ok(`${nom} : ma grille reste lisible (cases ≥ 24 px)`, m.t >= 24, String(m.t));
    if (n === 2) {
      await p.evaluate(() => document.querySelector('button.icone[aria-label="Agrandir"]').click()); await sleep(300);
      const z = await p.evaluate(() => ({ t: parseFloat(document.querySelector(".jeu-tel .grille:not(.mini) .tuile").style.getPropertyValue("--t")), kh: document.querySelector(".touche").getBoundingClientRect().height }));
      ok("« Agrandir » : la grille ET le clavier grossissent", z.t > m.t && z.kh > m.kh + 2, `${JSON.stringify(m)} → ${JSON.stringify(z)}`);
    }
    stop(); await ctx.close();
  }
  ok("aucune erreur JavaScript", !err.length, err.join(" | "));
  console.log(`${res.filter(Boolean).length}/${res.length} conformes`); await b.close(); process.exit(res.every(Boolean) ? 0 : 1);
})().catch(e => { console.log("EXCEPTION", e); process.exit(1); });
