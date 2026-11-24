// 9.3 (web, faux serveur) : frappe en direct dans tous les modes, visible seulement une fois SA manche finie (pas de triche) ;
// sur téléphone, manche finie → ma grille et le clavier s'effacent, les grilles des autres s'agrandissent (lettres lisibles).
const puppeteer = require("puppeteer-core");
const sleep = ms => new Promise(r => setTimeout(r, ms));
const BASE = "http://127.0.0.1:9000", SITE = process.env.SMOUT_SITE || "http://127.0.0.1:8000/";
const res = []; const ok = (n, c, i = "") => { res.push(!!c); console.log((c ? "OK    " : "ÉCHEC ") + n + (i && !c ? "  — " + i : "")); };
(async () => {
  const b = await puppeteer.launch({ executablePath: process.env.CHROME || "/usr/bin/google-chrome", headless: "new", args: ["--no-sandbox"] });
  const err = [];
  async function joueur(nom, L, H) {
    const p = await (await b.createBrowserContext()).newPage(); await p.setViewport({ width: L, height: H, isMobile: L < 600, hasTouch: L < 600 });
    p.on("pageerror", e => err.push(nom + ": " + e.message));
    await p.setRequestInterception(true);
    p.on("request", async r => { const u = r.url(); let c = null;
      if (u.includes("firebasedatabase.app")) c = BASE + "/" + u.split(".app/")[1]; else if (u.includes("securetoken")) c = BASE + "/token"; else if (u.includes("identitytoolkit")) c = BASE + "/signup";
      if (!c) return r.continue();
      if (r.method() === "OPTIONS") return r.respond({ status: 204, headers: { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "*", "Access-Control-Allow-Headers": "*" } });
      const x = await fetch(c, { method: r.method(), body: r.postData(), headers: { "Content-Type": "application/json" } });
      r.respond({ status: x.status, headers: { "Access-Control-Allow-Origin": "*" }, contentType: "application/json", body: await x.text() }); });
    await p.evaluateOnNewDocument(n => { if (!sessionStorage.getItem("i")) { localStorage.setItem("smout_config", JSON.stringify({ pseudo: n })); sessionStorage.setItem("i", "1"); } }, nom);
    await p.goto(SITE, { waitUntil: "networkidle0" }); await p.evaluate(() => FB.jeton()); return p;
  }
  const ev = (p, f, ...a) => p.evaluate(f, ...a);
  const attendre = async (p, f, t = 15000, ...a) => { const fin = Date.now() + t; while (Date.now() < fin) { try { if (await ev(p, f, ...a)) return true; } catch (e) {} await sleep(250); } return false; };
  const taper = (p, t) => ev(p, t => { for (const ch of t) document.dispatchEvent(new KeyboardEvent("keydown", { key: ch })); }, t);
  const A = await joueur("ALICE", 390, 844), B = await joueur("BOB", 1280, 860);
  await ev(A, () => multiAccueil()); await sleep(400); await ev(A, () => document.querySelector("button.a-creer").click()); await sleep(400);
  await ev(A, () => [...document.querySelectorAll("button")].find(x => x.textContent === "Créer le salon").click()); await sleep(1500);
  const code = await ev(A, () => M.lobby);
  await ev(B, () => multiAccueil()); await sleep(400); await ev(B, () => document.querySelector("button.a-rejoindre").click()); await sleep(600);
  await B.type('input[placeholder="CODE"]', code); await B.keyboard.press("Enter"); await sleep(1800);
  await attendre(A, () => !document.querySelector(".salon-partie button.lancer")?.disabled, 8000);
  await ev(A, () => document.querySelector(".salon-partie button.lancer").click());
  await attendre(A, () => !!document.querySelector(".clavier") && M.G, 15000); await attendre(B, () => !!document.querySelector(".clavier") && M.G, 15000); await sleep(1000);
  const mot = await ev(A, () => M.G.mot);
  const lettresBobChezAlice = () => ev(A, () => [...document.querySelectorAll(".adv-tel .grille .tuile")].map(t => t.textContent).join(""));
  await taper(B, "ZZ"); await sleep(1500);
  ok("avant d'avoir fini : la frappe de Bob n'est pas visible (pas de triche)", !/Z/.test(await lettresBobChezAlice()), await lettresBobChezAlice());
  await taper(A, mot.slice(1) + "\r".replace("\r", "")); await ev(A, () => document.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter" })));
  ok("Alice a trouvé son mot", await attendre(A, () => M.G.fini, 8000));
  ok("téléphone, manche finie : ma grille et le clavier s'effacent", await attendre(A, () => { const c = document.querySelector(".clavier"); return !c || !c.offsetParent; }, 5000));
  ok("téléphone : les grilles des autres s'agrandissent (cases ≥ 14 px, lettres affichées)", await ev(A, () => parseFloat(document.querySelector(".adv-tel .grille .tuile").style.getPropertyValue("--t")) >= 14));
  await taper(B, "AB"); await sleep(2500);
  ok("après avoir fini : on voit ce que Bob tape en direct", await attendre(A, () => /ZZAB|ZAB|AB/.test([...document.querySelectorAll(".adv-tel .grille .tuile")].map(t => t.textContent).join("")), 8000), await lettresBobChezAlice());
  ok("aucune erreur JavaScript", !err.length, err.join(" | "));
  console.log(`${res.filter(Boolean).length}/${res.length} conformes`); await b.close(); process.exit(res.every(Boolean) ? 0 : 1);
})().catch(e => { console.log("EXCEPTION", e); process.exit(1); });
