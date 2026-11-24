// Compte SMOUT côté web (objet Compte de smout.js) sur le faux serveur : création par l'interface (rattachement du joueur anonyme),
// erreurs, connexion sur un 2e appareil, synchronisation dans les deux sens (envoi automatique, relecture au chargement), déconnexion.
// Laisse le compte COMPTE_CROISE (mot de passe « croise1 ») pour le test PC (connexion d'un compte créé sur le web).
const puppeteer = require("puppeteer-core");
const sleep = ms => new Promise(r => setTimeout(r, ms));
const BASE = "http://127.0.0.1:9000", SITE = process.env.SMOUT_SITE || "http://127.0.0.1:8000/";
const MAIL = process.env.COMPTE_CROISE || "croise@test.fr";
const res = []; const ok = (n, c, i = "") => { res.push(!!c); console.log((c ? "OK    " : "ÉCHEC ") + n + (i ? "  — " + i : "")); };
const db = async () => (await (await fetch(BASE + "/__admin.json")).json()) || {};
(async () => {
  const b = await puppeteer.launch({ executablePath: process.env.CHROME || "/usr/bin/google-chrome", headless: "new", args: ["--no-sandbox"] });
  const err = [];
  async function appareil(nom, config) {  // un nouvel appareil = un nouveau contexte de navigateur (stockage vide)
    const p = await (await b.createBrowserContext()).newPage(); await p.setViewport({ width: 390, height: 844, isMobile: true, hasTouch: true });
    p.on("pageerror", e => err.push(nom + ": " + e.message)); p.on("dialog", d => d.accept());
    await p.setRequestInterception(true);
    p.on("request", async r => { const u = r.url(); let c = null;
      if (u.includes("firebasedatabase.app")) c = BASE + "/" + u.split(".app/")[1]; else if (u.includes("securetoken")) c = BASE + "/token"; else if (u.includes("identitytoolkit")) c = BASE + "/signup";
      if (!c) return r.continue();
      if (r.method() === "OPTIONS") return r.respond({ status: 204, headers: { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "*", "Access-Control-Allow-Headers": "*" } });
      const x = await fetch(c, { method: r.method(), body: r.postData(), headers: { "Content-Type": r.headers()["content-type"] || "application/json" } });
      r.respond({ status: x.status, headers: { "Access-Control-Allow-Origin": "*" }, contentType: "application/json", body: await x.text() }); });
    await p.evaluateOnNewDocument(c => { if (!sessionStorage.getItem("i")) { localStorage.setItem("smout_config", JSON.stringify(c)); sessionStorage.setItem("i", "1"); } }, config);
    await p.goto(SITE, { waitUntil: "networkidle0" }); return p;
  }
  const ev = (p, f, ...a) => p.evaluate(f, ...a);
  const clic = (p, t) => ev(p, t => { const e = [...document.querySelectorAll("button")].find(x => x.textContent.trim() === t && x.offsetParent); if (e) e.click(); return !!e; }, t);
  const saisir = async (p, mail, mdp) => { await ev(p, (m, w) => { const [a, c] = document.querySelectorAll('.voile:not(.cache) input[type=email], .voile:not(.cache) input[type=password]'); a.value = m; c.value = w; }, mail, mdp); };
  const message = p => ev(p, () => [...document.querySelectorAll(".voile:not(.cache) div.gras")].map(x => x.textContent).filter(Boolean).pop() || "");

  // appareil A : avancement local, puis création du compte par l'interface (pseudo → Compte)
  const a = await appareil("A", { pseudo: "ALICE", mdj_serie: 3, theme: "AURORE", stats: { solo: { parties: 5, victoires: 4 } } });
  await ev(a, () => FB.jeton()); const uidA = await ev(a, () => FB.uid);
  await ev(a, () => changerPseudo()); await sleep(200);
  ok("pseudo : section Compte avec « Se connecter ou créer un compte »", await clic(a, "Se connecter ou créer un compte")); await sleep(200);
  await saisir(a, MAIL, "abc"); await clic(a, "Créer le compte"); await sleep(500);
  ok("mot de passe trop court refusé", (await message(a)).includes("trop court"), await message(a));
  await saisir(a, MAIL, "croise1"); await clic(a, "Créer le compte"); await sleep(1200);
  const cA = await ev(a, () => lireConfig());
  ok("compte créé, joueur anonyme rattaché (même identifiant)", cA.compte_email === MAIL && (await ev(a, () => FB.uid)) === uidA, JSON.stringify(cA).slice(0, 160));
  const enr = JSON.parse((((await db()).v7.comptes || {})[uidA] || {}).donnees || "{}");
  ok("avancement envoyé au compte", enr.pseudo === "ALICE" && enr.stats && enr.stats.solo.parties === 5, JSON.stringify(enr).slice(0, 160));
  await ev(a, () => changerPseudo()); await sleep(200);
  ok("pseudo : « Connecté : adresse » et « Se déconnecter »", await ev(a, m => document.body.innerText.includes("Connecté : " + m), MAIL) && await ev(a, () => [...document.querySelectorAll("button")].some(x => x.textContent === "Se déconnecter")));
  await ev(a, () => document.querySelector(".voile:not(.cache) button.btn.discret")?.click());

  // appareil B : erreurs, puis connexion
  const bb = await appareil("B", { pseudo: "BOBBY", mdj_serie: 0 });
  await ev(bb, () => ouvrirCompte()); await sleep(200);
  await saisir(bb, MAIL, "faux123"); await clic(bb, "Se connecter"); await sleep(600);
  ok("mauvais mot de passe refusé", (await message(bb)).includes("incorrect"), await message(bb));
  await saisir(bb, MAIL, "autre12"); await clic(bb, "Créer le compte"); await sleep(600);
  ok("adresse déjà utilisée refusée à la création", (await message(bb)).includes("déjà un compte"), await message(bb));
  await ev(bb, () => { [...document.querySelectorAll(".voile:not(.cache) button.lien")].find(x => x.textContent.includes("oublié")).click(); }); await sleep(500);
  ok("mot de passe oublié : e-mail envoyé", (await message(bb)).includes("a été envoyé"), await message(bb));
  await saisir(bb, MAIL, "croise1"); await clic(bb, "Se connecter"); await sleep(1500);
  const cB = await ev(bb, () => lireConfig());
  ok("connexion sur un 2e appareil : même joueur", (await ev(bb, () => FB.uid)) === uidA);
  ok("l'avancement du compte remplace celui de l'appareil", cB.pseudo === "ALICE" && cB.mdj_serie === 3 && cB.theme === "AURORE", JSON.stringify(cB).slice(0, 160));
  ok("l'accueil affiche le pseudo du compte", (await ev(bb, () => document.body.innerText)).includes("A") && (await ev(bb, () => pseudo())) === "ALICE");

  // changement sur B → compte → relu par A au chargement
  await ev(bb, () => majConfig({ mdj_serie: 9 })); await sleep(3500);
  const enr2 = JSON.parse((((await db()).v7.comptes || {})[uidA] || {}).donnees || "{}");
  ok("un changement est envoyé automatiquement au compte", enr2.mdj_serie === 9, String(enr2.mdj_serie));
  await a.reload({ waitUntil: "networkidle0" }); await sleep(1500);
  ok("au chargement, l'autre appareil relit l'avancement plus récent", (await ev(a, () => lireConfig().mdj_serie)) === 9);
  ok("on reste connecté après rechargement", (await ev(a, () => lireConfig().compte_email)) === MAIL);

  // déconnexion sur B (le compte reste pour le test PC)
  await ev(bb, () => Compte.deconnecter()); await ev(bb, () => FB.jeton());
  const cB2 = await ev(bb, () => lireConfig());
  ok("déconnexion : compte oublié, avancement local gardé, nouveau joueur anonyme", !cB2.compte_email && cB2.pseudo === "ALICE" && (await ev(bb, () => FB.uid)) !== uidA);
  ok("aucune erreur JavaScript", !err.length, err.join(" | "));
  console.log(`${res.filter(Boolean).length}/${res.length} conformes`); await b.close(); process.exit(res.every(Boolean) ? 0 : 1);
})().catch(e => { console.log("EXCEPTION", e); process.exit(1); });
