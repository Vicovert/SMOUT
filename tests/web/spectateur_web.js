// 9.1 (web, faux serveur) : spectateurs et demandes pour regarder une partie en cours.
// Salon plein → spectateur puis « Prendre la place » ; « Passer spectateur » ; vue spectateur en partie (rien d'écrit) ;
// demande refusée, annulée puis acceptée par l'hôte (cloche + panneau latéral) ; fenêtres du jeu (plus de confirm/alert).
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
    p.on("pageerror", e => err.push(nom + ": " + e.message)); p.on("dialog", d => { err.push(nom + ": fenêtre native « " + d.message() + " »"); d.accept(); });
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
  const oui = p => ev(p, () => { const x = document.querySelector(".voile:not(.cache) .dlg-oui"); if (x) x.click(); return !!x; });
  const entrer = async (p, code) => { await ev(p, () => multiAccueil()); await sleep(400); await ev(p, () => document.querySelector("button.a-rejoindre").click()); await sleep(600);
    await p.type('input[placeholder="CODE"]', code); await p.keyboard.press("Enter"); };
  // joueurs factices (REST) qui restent actifs
  const faux = []; let code;
  const ajouterFaux = async n => { for (let i = 0; i < n; i++) { const r = await (await fetch(BASE + "/signup", { method: "POST", body: "{}" })).json();
    const put = () => fetch(`${BASE}/v7/lobbies/${code}/players/${r.localId}.json?auth=${r.idToken}`, { method: "PATCH", body: JSON.stringify({ name: "F" + faux.length, score: 0, last_seen: { ".sv": "timestamp" }, arrivee: { ".sv": "timestamp" } }) });
    await put(); faux.push({ uid: r.localId, tok: r.idToken, put, actif: true }); } };
  const battre = setInterval(() => faux.forEach(f => f.actif && f.put().catch(() => {})), 4000);

  const A = await joueur("ALICE"), B = await joueur("BOB"), C = await joueur("CHLOE");
  const uB = await ev(B, () => FB.uid), uC = await ev(C, () => FB.uid);
  await ev(A, () => multiAccueil()); await sleep(400); await ev(A, () => document.querySelector("button.a-creer").click()); await sleep(400);
  await ev(A, () => [...document.querySelectorAll("button")].find(x => x.textContent === "Créer le salon").click()); await sleep(1500);
  code = await ev(A, () => M.lobby);
  await entrer(B, code); await sleep(1800);
  await ajouterFaux(6);  // 8 joueurs : le salon est plein
  await attendre(A, () => M.nbJoueurs >= 8, 10000); await sleep(5500);  // l'index annonce nb = 8
  await entrer(C, code);
  ok("salon plein : on entre comme spectateur", await attendre(C, () => M.spectateur && !!document.querySelector(".salon-joueurs"), 10000));
  ok("l'hôte voit « 1 spectateur »", await attendre(A, () => /1 spectateur/.test(document.querySelector(".nb-spect")?.textContent || "")));
  ok("plein : pas de « Prendre la place »", !(await ev(C, () => !!document.querySelector(".action-place"))));
  faux[5].actif = false; await fetch(`${BASE}/v7/lobbies/${code}/players/${faux[5].uid}.json?auth=${faux[5].tok}`, { method: "DELETE" });
  ok("une place se libère : « Prendre la place » pour le spectateur", await attendre(C, () => [...document.querySelectorAll(".action-place")].some(x => x.textContent === "Prendre la place")));
  await ev(C, () => [...document.querySelectorAll(".action-place")].find(x => x.textContent === "Prendre la place").click());
  ok("« Prendre la place » : le spectateur devient joueur", await attendre(C, () => !M.spectateur, 8000) && !!(await db()).v7.lobbies[code].players[uC] && !((await db()).v7.lobbies[code].spectateurs || {})[uC]);
  // B passe spectateur
  ok("« Passer spectateur » sur sa propre ligne (pas pour l'hôte)", await attendre(B, () => [...document.querySelectorAll(".action-place")].some(x => x.textContent === "Passer spectateur")) && !(await ev(A, () => [...document.querySelectorAll(".action-place")].some(x => x.textContent === "Passer spectateur"))));
  await ev(B, () => [...document.querySelectorAll(".action-place")].find(x => x.textContent === "Passer spectateur").click());
  ok("« Passer spectateur » : B regarde, sa place est libre", await attendre(B, () => M.spectateur, 8000) && !(await db()).v7.lobbies[code].players[uB] && !!(await db()).v7.lobbies[code].spectateurs[uB]);
  // partie : B la regarde
  await attendre(A, () => !document.querySelector(".salon-partie button.lancer")?.disabled, 8000);
  await ev(A, () => document.querySelector(".salon-partie button.lancer").click());
  ok("partie : le spectateur a la vue spectateur (pas de clavier, grilles de tous les joueurs)", await attendre(B, () => !!document.querySelector(".vue-spect") && !document.querySelector(".clavier")?.isConnected, 15000)
    && (await ev(B, () => document.querySelectorAll(".vue-spect .grille").length)) === Object.keys((await db()).v7.lobbies[code].players).length);
  ok("partie : le code du salon est affiché pour les joueurs", await attendre(C, c => [...document.querySelectorAll(".stat")].some(x => x.textContent.includes("Salon") && x.textContent.includes(c)), 8000, code));
  ok("spectateur : aucune écriture dans la partie", (await ev(B, c => FB.ok("PUT", `lobbies/${c}/match_data/${FB.uid}/0`, { c: ["B"], l: ["A"] }), code)) === false && !((await db()).v7.lobbies[code].match_data || {})[uB]);
  // D demande à regarder : refusée, puis E annule, puis D acceptée
  const D = await joueur("DAVID"), E = await joueur("EMMA"), uD = await ev(D, () => FB.uid);
  await entrer(D, code);
  ok("partie en cours : fenêtre « En attente de l'hôte »", await attendre(D, () => !!document.querySelector(".attente-hote:not(.cache)"), 8000));
  ok("l'hôte : cloche en couleur avec « 1 »", await attendre(A, () => document.querySelector(".cloche.active .badge")?.textContent === "1", 8000));
  await ev(A, () => document.querySelector(".cloche").click()); await sleep(300);
  ok("panneau latéral des demandes, sans voile (le jeu reste utilisable)", await ev(A, () => !!document.querySelector(".tiroir:not(.cache) .demande") && !document.querySelector(".voile:not(.cache)") && !!document.querySelector(".clavier")));
  await ev(A, () => document.querySelector(".tiroir .dem-non").click());
  ok("demande refusée : le demandeur est prévenu", await attendre(D, () => document.body.innerText.includes("Demande refusée"), 8000));
  await oui(D);
  await entrer(E, code); await attendre(A, () => document.querySelector(".cloche .badge")?.textContent === "1", 8000);
  await ev(E, () => document.querySelector(".quitter-attente").click()); await sleep(300); await oui(E);
  ok("demande annulée : elle disparaît chez l'hôte", await attendre(A, () => document.querySelector(".cloche .badge")?.classList.contains("cache"), 8000));
  await entrer(D, code); await attendre(A, () => !!document.querySelector(".tiroir .dem-oui"), 8000);
  await ev(A, () => document.querySelector(".tiroir .dem-oui").click());
  ok("demande acceptée : le demandeur regarde la partie en spectateur", await attendre(D, () => M.spectateur && !!document.querySelector(".vue-spect"), 12000) && !!(await db()).v7.lobbies[code].spectateurs[uD]);
  ok("aucune fenêtre native ni erreur JavaScript", !err.length, err.join(" | "));
  clearInterval(battre);
  console.log(`${res.filter(Boolean).length}/${res.length} conformes`); await b.close(); process.exit(res.every(Boolean) ? 0 : 1);
})().catch(e => { console.log("EXCEPTION", e); process.exit(1); });
