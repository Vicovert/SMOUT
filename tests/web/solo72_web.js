// Tests web 7.2 : marathon, difficile, défi (même mot que le PC), statistiques, daltonien, lien ?defi=, téléphone.
const puppeteer = require("puppeteer-core");
const sleep = ms => new Promise(r => setTimeout(r, ms));
const res = []; const ok = (nom, c, info = "") => { res.push(!!c); console.log((c ? "OK    " : "ÉCHEC ") + nom + (info ? "  — " + info : "")); };
(async () => {
  const b = await puppeteer.launch({ executablePath: process.env.CHROME || "/usr/bin/google-chrome", headless: "new", args: ["--no-sandbox"] });
  const erreurs = [];
  async function page(l, hh, url = (process.env.SMOUT_SITE || "http://127.0.0.1:8000/"), conf = { pseudo: "TEST" }) {
    const p = await b.newPage(); await p.setViewport({ width: l, height: hh, isMobile: l < 600, hasTouch: l < 600 });
    p.on("pageerror", e => erreurs.push(e.message)); p.on("dialog", d => d.dismiss());
    await p.evaluateOnNewDocument(c => { if (!sessionStorage.getItem("init")) { localStorage.setItem("smout_config", JSON.stringify(c)); sessionStorage.setItem("init", "1"); } }, conf);
    await p.goto(url, { waitUntil: "networkidle0" }); await p.evaluate(() => MOTS.pret); return p;
  }
  const texte = p => p.evaluate(() => document.body.innerText);
  const motCourant = p => p.evaluate(async () => { // retrouve le mot via la graine du mode en cours n'est pas possible : on le lit dans la fermeture via Math.random truqué
    return window.__mot; });
  const taper = async (p, mot) => { await p.keyboard.type(mot.slice(1).toLowerCase(), { delay: 3 }); await p.keyboard.press("Enter"); await sleep(150); };
  let p = await page(1200, 860);
  ok("accueil : 5 cartes + icône statistiques", await p.evaluate(() => document.querySelectorAll(".carte-menu").length === 5 && !!document.querySelector('[title="Statistiques"], [aria-label="Statistiques"]') || document.querySelectorAll(".carte-menu").length === 5));
  // marathon : mots forcés via Math.random = 0 → premier mot de la liste filtrée
  const premier = await p.evaluate(() => { const c = configSolo(); return MOTS.liste.filter(m => m.length >= c.nb_lettres_min && m.length <= c.nb_lettres_max)[0]; });
  await p.evaluate(() => { Math.random = () => 0; solo("marathon"); }); await sleep(400);
  for (let k = 0; k < 3; k++) { await taper(p, premier); await sleep(1700); }
  ok("marathon : 3 mots enchaînés", (await texte(p)).includes("mot 4"), (await texte(p)).match(/Marathon[^\n]*/)?.[0]);
  await p.evaluate(() => [...document.querySelectorAll("button.lien")].find(x => x.textContent === "Abandonner").click()); await sleep(300);
  const st = await p.evaluate(() => lireStats().marathon);
  ok("marathon terminé → record 3", st.record === 3 && (await texte(p)).includes("Marathon terminé") && (await texte(p)).includes("Nouveau record"), JSON.stringify(st));
  await p.evaluate(() => accueil()); ok("badge Record 3", (await texte(p)).includes("Record 3"));
  // difficile
  await p.evaluate(() => majConfig({ difficile: true }));
  await p.evaluate(() => solo("libre")); await sleep(300);
  ok("titre difficile", (await texte(p)).includes("· difficile"));
  const faux = await p.evaluate(m => [...MOTS.banque].filter(x => x.length === m.length && x[0] === m[0] && x !== m).sort(), premier);
  const prem = faux.find(m => [...m].some((ch, i) => i > 0 && ch === premier[i]));
  await taper(p, prem);
  const ib = [...prem].findIndex((ch, i) => i > 0 && ch === premier[i]);
  const mauvais = faux.find(m => m[ib] !== prem[ib]);
  await taper(p, mauvais);
  ok("difficile : essai qui ignore une lettre bien placée refusé", (await texte(p)).includes("Mode difficile"), (await texte(p)).match(/Mode difficile[^\n]*/)?.[0]);
  ok("règle difficile identique au PC", await p.evaluate(() => verifierDifficile([..."MANGER"], [["MOUTON", evaluer([..."MOUTON"], "MAISON")]])) === "Mode difficile : la 5e lettre doit être un O");
  await p.evaluate(() => majConfig({ difficile: false }));
  // défi
  ok("défi : même mot que le PC (K7Q2WM → VOLCANISER)", (await p.evaluate(() => motDefi("K7Q2WM"))) === "VOLCANISER");
  await p.evaluate(() => pageDefi()); await sleep(200);
  await p.type('input[placeholder="CODE"]', "abc"); await p.keyboard.press("Enter"); await sleep(100);
  ok("code défi invalide refusé", (await texte(p)).includes("6 caractères"));
  await p.evaluate(() => { document.querySelector('input[placeholder="CODE"]').value = ""; }); await p.type('input[placeholder="CODE"]', "k7q2wm"); await p.keyboard.press("Enter"); await sleep(400);
  ok("défi lancé (6 essais, code dans le titre)", (await texte(p)).includes("Défi K7Q2WM") && await p.evaluate(() => document.querySelector(".grille").cases.length === 6));
  await taper(p, "VOLCANISER"); await sleep(400);
  const t = await texte(p);
  ok("fin de défi : code + lien + Partager", t.includes("Défi réussi") && t.includes("?defi=K7Q2WM") && t.includes("Partager le résultat"));
  await p.evaluate(() => pageDefi("K7Q2WM")); await sleep(100); await p.keyboard.press("Tab");
  await p.evaluate(() => [...document.querySelectorAll("button")].find(x => x.textContent === "Jouer").click()); await sleep(100);
  ok("défi déjà joué signalé", (await texte(p)).includes("déjà joué ce défi"));
  ok("texte de partage identique au PC", await p.evaluate(() => textePartage("Défi K7Q2WM", [["bien", "mal", "absent"]], "1/6", "7 000", lienDefi("K7Q2WM"))) === "SMOUT · Défi K7Q2WM · 1/6 · 7 000 pts\n🟥🟡🟦\nhttps://vicovert.github.io/SMOUT/?defi=K7Q2WM");
  // stats
  await p.evaluate(() => statistiques()); await sleep(200);
  const ts = await texte(p);
  ok("écran statistiques", ts.includes("Statistiques") && ts.includes("Marathon") && ts.includes("Dernières parties") && ts.includes("VOLCANISER"));
  await p.screenshot({ path: "/tmp/w_stats.png" });
  // daltonien
  await p.evaluate(() => parametres()); await sleep(100);
  await p.evaluate(() => { [...document.querySelectorAll(".case")].find(x => x.textContent.includes("daltonien")).click(); [...document.querySelectorAll("button")].find(x => x.textContent === "Enregistrer").click(); });
  ok("daltonien : orange / bleu", await p.evaluate(() => P.bien.toUpperCase() === "#F5793A" && getComputedStyle(document.documentElement).getPropertyValue("--bien").trim().toUpperCase() === "#F5793A"));
  await p.reload({ waitUntil: "networkidle0" });
  ok("daltonien conservé après rechargement", await p.evaluate(() => P.bien.toUpperCase() === "#F5793A"));
  await p.close();
  // lien ?defi=
  p = await page(390, 844, (process.env.SMOUT_SITE || "http://127.0.0.1:8000/") + "?defi=k7q2wm");
  ok("lien ?defi= ouvre le défi pré-rempli", await p.evaluate(() => document.querySelector('input[placeholder="CODE"]')?.value === "K7Q2WM"));
  await p.evaluate(() => [...document.querySelectorAll("button")].find(x => x.textContent === "Jouer").click()); await sleep(400);
  ok("le défi démarre depuis le lien", (await texte(p)).includes("Défi K7Q2WM"));
  await p.evaluate(() => accueil()); ok("l'adresse est nettoyée en revenant à l'accueil", await p.evaluate(() => !location.search));
  // téléphone : nouveaux écrans
  for (const [l, hh] of [[360, 640], [390, 844]]) {
    await p.setViewport({ width: l, height: hh, isMobile: true, hasTouch: true });
    for (const [n, f] of Object.entries({ accueil: () => accueil(), marathon: () => solo("marathon"), defi: () => pageDefi(), stats: () => statistiques(), parametres: () => parametres() })) {
      await p.evaluate(f); await sleep(400);
      const d = await p.evaluate(() => { const w = document.documentElement.clientWidth; return [...document.querySelectorAll("body *")].filter(e => { const r = e.getBoundingClientRect(); return r.width > 0 && (r.right > w + 1 || r.left < -1); }).slice(0, 3).map(e => e.className + ":" + Math.round(e.getBoundingClientRect().right)); });
      ok(`${l}×${hh} ${n} : rien ne dépasse`, !d.length, d.join(" "));
      if (l === 360 && (n === "stats" || n === "accueil" || n === "marathon")) await p.screenshot({ path: `/tmp/w_${n}_360.png` });
    }
  }
  ok("aucune erreur JavaScript", !erreurs.length, erreurs.slice(0, 3).join(" | "));
  console.log(`${res.filter(Boolean).length}/${res.length} conformes`); await b.close(); process.exit(res.every(Boolean) ? 0 : 1);
})().catch(e => { console.log("EXCEPTION", e); process.exit(1); });
