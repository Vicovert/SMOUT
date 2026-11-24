// Salon et partie (web, faux serveur) : « Donner l'hôte », pause en pleine partie puis « Reprendre », départ définitif de l'hôte
// avec relais au PREMIER ARRIVÉ (et non au plus petit identifiant : C a l'identifiant le plus petit mais arrive en dernier).
const puppeteer = require("puppeteer-core");
const sleep = ms => new Promise(r => setTimeout(r, ms));
const BASE = "http://127.0.0.1:9000", SITE = process.env.SMOUT_SITE || "http://127.0.0.1:8000/";
const res = []; const ok = (n, c, i = "") => { res.push(!!c); console.log((c ? "OK    " : "ÉCHEC ") + n + (i && !c ? "  — " + i : "")); };
const db = async () => (await (await fetch(BASE + "/__admin.json")).json()) || {};
(async () => {
  const b = await puppeteer.launch({ executablePath: process.env.CHROME || "/usr/bin/google-chrome", headless: "new", args: ["--no-sandbox"] });
  const err = [];
  async function joueur(nom) {
    const p = await (await b.createBrowserContext()).newPage(); await p.setViewport({ width: 1280, height: 860 });
    p.on("pageerror", e => err.push(nom + ": " + e.message)); p.on("dialog", d => d.accept());
    await p.setRequestInterception(true);
    p.on("request", async r => { const u = r.url(); let c = null;
      if (u.includes("firebasedatabase.app")) c = BASE + "/" + u.split(".app/")[1]; else if (u.includes("securetoken")) c = BASE + "/token"; else if (u.includes("identitytoolkit")) c = BASE + "/signup";
      if (!c) return r.continue();
      if (r.method() === "OPTIONS") return r.respond({ status: 204, headers: { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "*", "Access-Control-Allow-Headers": "*" } });
      const x = await fetch(c, { method: r.method(), body: r.postData(), headers: { "Content-Type": r.headers()["content-type"] || "application/json" } });
      r.respond({ status: x.status, headers: { "Access-Control-Allow-Origin": "*" }, contentType: "application/json", body: await x.text() }); });
    await p.evaluateOnNewDocument(n => { if (!sessionStorage.getItem("i")) { localStorage.setItem("smout_config", JSON.stringify({ pseudo: n })); sessionStorage.setItem("i", "1"); } }, nom);
    await p.goto(SITE, { waitUntil: "networkidle0" }); await p.evaluate(() => FB.jeton()); return p;
  }
  const ev = (p, f, ...a) => p.evaluate(f, ...a);
  const attendre = async (p, f, t = 15000, ...a) => { const fin = Date.now() + t; while (Date.now() < fin) { try { if (await ev(p, f, ...a)) return true; } catch (e) {} await sleep(250); } return false; };
  const clic = (p, t) => ev(p, t => { const e = [...document.querySelectorAll("button")].find(x => x.textContent.trim() === t && x.offsetParent); if (e) e.click(); return !!e; }, t);
  const salon = async () => (await db()).v7.lobbies[code];

  const C = await joueur("CHLOE"), A = await joueur("ALICE"), B = await joueur("BOB");  // identifiants : C < A < B
  const [uA, uB, uC] = [await ev(A, () => FB.uid), await ev(B, () => FB.uid), await ev(C, () => FB.uid)];
  ok("identifiants : C a le plus petit", uC < uA && uC < uB, [uA, uB, uC].join());
  await ev(A, () => multiAccueil()); await sleep(400); await ev(A, () => document.querySelector("button.a-creer").click()); await sleep(400);
  await clic(A, "Créer le salon"); await sleep(1500);
  var code = await ev(A, () => M.lobby);
  for (const p of [B, C]) {  // B arrive avant C
    await ev(p, () => multiAccueil()); await sleep(400); await ev(p, () => document.querySelector("button.a-rejoindre").click()); await sleep(600);
    await p.type('input[placeholder="CODE"]', code); await p.keyboard.press("Enter"); await sleep(1800);
  }
  ok("3 joueurs dans le salon", Object.keys((await salon()).players).length === 3);
  ok("heure d'arrivée enregistrée pour chacun", Object.values((await salon()).players).every(x => typeof x.arrivee === "number"));
  ok("l'hôte voit « Donner l'hôte » sur la ligne des deux autres joueurs", await attendre(A, () => document.querySelectorAll("button.donner-hote").length === 2));
  ok("les autres joueurs ne voient pas « Donner l'hôte »", (await ev(B, () => document.querySelectorAll("button.donner-hote").length)) === 0);

  // A donne l'hôte à B
  await ev(A, () => { const l = [...document.querySelectorAll(".joueur")].find(x => x.textContent.includes("Bob")); l.querySelector("button.donner-hote").click(); });
  ok("« Donner l'hôte » : B devient l'hôte", await attendre(B, () => M.estHote && document.body.innerText.includes("Vous êtes l'hôte")) && (await salon()).settings.host_id === uB);
  ok("l'ancien hôte n'a plus la main", await attendre(A, () => !M.estHote && document.body.innerText.includes("L'hôte règle la partie")));

  // B lance la partie ; C se met en pause puis reprend
  await attendre(B, () => !document.querySelector(".salon-partie button.lancer")?.disabled, 8000);
  await ev(B, () => document.querySelector(".salon-partie button.lancer").click());
  ok("partie lancée par le nouvel hôte", await attendre(C, () => !!document.querySelector(".clavier"), 15000));
  await ev(C, () => document.querySelector('button.icone[aria-label="Quitter"]').click()); await sleep(300);
  ok("retour en partie : fenêtre « Quitter la partie ? » (Continuer / Quitter / Mettre en pause)", await ev(C, () => ["Continuer", "Quitter la partie", "Mettre en pause"].every(t => [...document.querySelectorAll(".voile:not(.cache) button")].some(x => x.textContent === t))));
  await clic(C, "Mettre en pause"); await sleep(800);
  ok("en pause : C garde sa place dans le salon", !!(await salon()).players[uC]);
  ok("en pause : « Reprendre » proposé sur l'accueil du multijoueur", await attendre(C, c => document.body.innerText.includes("Partie interrompue · salon " + c), 5000, code));
  await clic(C, "Reprendre");
  ok("« Reprendre » ramène dans la partie en cours", await attendre(C, () => !!document.querySelector(".clavier") && M.lobby, 15000));

  // B (hôte) quitte définitivement : le relais va au premier arrivé (A), pas au plus petit identifiant (C)
  await ev(B, () => document.querySelector('button.icone[aria-label="Quitter"]').click()); await sleep(300);
  await clic(B, "Quitter la partie"); await sleep(2500);
  const s2 = await salon();
  ok("départ définitif : B n'est plus dans le salon", !s2.players[uB]);
  ok("relais au premier arrivé (A), et non au plus petit identifiant (C)", s2.settings.host_id === uA, s2.settings.host_id);
  ok("aucune erreur JavaScript", !err.length, err.join(" | "));
  console.log(`${res.filter(Boolean).length}/${res.length} conformes`); await b.close(); process.exit(res.every(Boolean) ? 0 : 1);
})().catch(e => { console.log("EXCEPTION", e); process.exit(1); });
