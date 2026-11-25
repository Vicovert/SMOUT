// Tests solo de la version web (Chrome sans écran) : partie gagnée/perdue, mot inconnu, mot du jour, paramètres, thèmes, pseudo, mise en page mobile.
const puppeteer = require("puppeteer-core");
const sleep = ms => new Promise(r => setTimeout(r, ms));
const res = []; const ok = (nom, c, info = "") => { res.push(!!c); console.log((c ? "OK    " : "ÉCHEC ") + nom + (info ? "  — " + info : "")); };
(async () => {
  const b = await puppeteer.launch({ executablePath: process.env.CHROME || "/usr/bin/google-chrome", headless: "new", args: ["--no-sandbox"] });
  const erreurs = [];
  async function page(l, hgt, conf = {}) {
    const p = await b.newPage(); await p.setViewport({ width: l, height: hgt, isMobile: l < 600, hasTouch: l < 600 });
    p.on("pageerror", e => erreurs.push(e.message)); p.on("console", m => m.type() === "error" && !/Failed to load|401|CORS|JSHandle@error/.test(m.text()) && erreurs.push(m.text()));
    p.on("dialog", d => d.dismiss());
    await p.evaluateOnNewDocument(c => { if (!sessionStorage.getItem("init")) { localStorage.setItem("smout_config", JSON.stringify(c)); sessionStorage.setItem("init", "1"); } }, conf);
    await p.goto((process.env.SMOUT_SITE || "http://127.0.0.1:8000/"), { waitUntil: "networkidle0" }); await p.evaluate(() => MOTS.pret); return p;
  }
  const texte = p => p.evaluate(() => document.body.innerText);
  const deborde = p => p.evaluate(() => { const w = document.documentElement.clientWidth; return [...document.querySelectorAll("body *")].filter(e => { const r = e.getBoundingClientRect(); return r.width > 0 && (r.right > w + 1 || r.left < -1) && getComputedStyle(e).position !== "fixed"; }).slice(0, 3).map(e => e.className + ":" + Math.round(e.getBoundingClientRect().right)); });
  const taper = async (p, mot) => { await p.keyboard.type(mot.slice(1).toLowerCase(), { delay: 5 }); await p.keyboard.press("Enter"); await sleep(250); };

  // ---------- solo PC (1200x860)
  let p = await page(1200, 860, { pseudo: "TEST" });
  await p.evaluate(() => { window.__r = Math.random; Math.random = () => 0; });
  const premier = await p.evaluate(() => { const c = configSolo(); return MOTS.liste.filter(m => m.length >= c.nb_lettres_min && m.length <= c.nb_lettres_max)[0]; });
  await p.evaluate(() => solo(false)); await sleep(400);
  await p.evaluate(() => { Math.random = window.__r; });
  ok("le solo s'ouvre avec le bon nombre de lettres", (await texte(p)).includes(`${premier.length} lettres`), premier);
  await p.keyboard.type("zzzzzzzzzz".slice(0, premier.length - 1)); await p.keyboard.press("Enter"); await sleep(200);
  ok("mot inconnu : message et −100", (await texte(p)).includes("Mot inconnu"));
  for (let i = 0; i < premier.length; i++) await p.keyboard.press("Backspace");
  const sc0 = await p.evaluate(() => document.querySelectorAll(".stat .v")[1].textContent);
  await taper(p, premier); await sleep(500);
  const t = await texte(p);
  ok("victoire affichée", t.includes("Bravo, mot trouvé"), sc0);
  ok("boutons Rejouer et Retour", t.includes("Rejouer") && t.includes("Retour"));
  // défaite
  await p.evaluate(() => [...document.querySelectorAll("button")].find(x => x.textContent === "Rejouer").click()); await sleep(400);
  ok("Rejouer ferme l'écran de fin", !(await p.evaluate(() => document.querySelector(".voile:not(.cache)") && document.body.innerText.includes("Bravo"))));
  const lg = await p.evaluate(() => +document.querySelector(".entete, .barre-haut, body").innerText.match(/(\d+) lettres/)[1]);
  const essais = await p.evaluate(() => configSolo().nb_essais);
  await p.evaluate(() => [...document.querySelectorAll("button.lien")].find(x => x.textContent === "Abandonner").click()); await sleep(300);
  const mot2 = await p.evaluate(() => [...document.querySelectorAll(".voile .tuile, .voile .t")].map(x => x.textContent).join("").slice(0, 20));
  ok("abandon → Perdu et mot révélé", (await texte(p)).includes("Perdu"), mot2);
  await p.evaluate(() => solo(false)); await sleep(300);
  const mot3lg = await p.evaluate(() => +document.body.innerText.match(/(\d+) lettres/)[1]);
  const premiereLettre = await p.evaluate(() => document.querySelector(".grille .tuile, .tuile").textContent);
  const faux = await p.evaluate((l, c) => [...MOTS.banque].filter(m => m.length === l && m[0] === c).sort().slice(0, 12), mot3lg, premiereLettre);
  for (let i = 0; i < essais; i++) await taper(p, faux[i]);
  await sleep(400); const t3 = await texte(p);
  ok(`défaite après ${essais} essais`, t3.includes("Perdu") || t3.includes("Bravo"), faux.slice(0, 2).join(","));
  // paramètres
  await p.evaluate(() => parametres()); await sleep(200);
  ok("paramètres : page centrée", await p.evaluate(() => { const r = document.querySelector(".page-parametres .panneau").getBoundingClientRect(); return Math.abs(r.left + r.width / 2 - innerWidth / 2) < 3; }));
  // tuiles « − valeur + » : essais 6 → 4 (deux clics sur −), lettres : le minimum monté à 10 pousse le maximum ; taille de la grille 100 → 120 %
  await p.evaluate(() => { const t = [...document.querySelectorAll(".tuile-reglage")]; const clic = (i, k, n) => { for (let j = 0; j < n; j++) t[i].querySelectorAll(".pas")[k].click(); };
    clic(0, 0, 5); clic(2, 1, 4); clic(1, 1, 2); [...document.querySelectorAll("button")].find(x => x.textContent === "Enregistrer").click(); });
  ok("taille de la grille enregistrée (120 %)", await p.evaluate(() => lireConfig().user_zoom === 1.2));
  const conf = await p.evaluate(() => configSolo());
  ok("paramètres enregistrés (4 essais, 10 lettres)", conf.nb_essais === 4 && conf.nb_lettres_min === 10 && conf.nb_lettres_max === 10, JSON.stringify(conf));
  await p.evaluate(() => solo(false)); await sleep(300);
  ok("le solo applique les paramètres", await p.evaluate(() => document.body.innerText.includes("10 lettres") && document.querySelector(".grille").cases.length === 4));
  ok("paramètres conservés après rechargement", await (async () => { await p.reload({ waitUntil: "networkidle0" }); return (await p.evaluate(() => configSolo().nb_essais)) === 4; })());
  // mot du jour
  const hierStr = await p.evaluate(() => hier());
  await p.evaluate(h => { majConfig({ mdj_serie: 4, mdj_dernier_gagne: h, last_mdj: h }); accueil(); }, hierStr);
  ok("badge série 4 sur l'accueil", (await texte(p)).includes("Série 4"));
  const mdj = await p.evaluate(async () => await motGraine(trier(MOTS.liste), "mdj:" + aujourdhui()));
  await p.evaluate(() => solo(true)); await sleep(300);
  ok("mot du jour : 7 essais", await p.evaluate(() => document.querySelector(".grille").cases.length === 7));
  await taper(p, mdj); await sleep(400);
  ok("mot du jour trouvé", (await texte(p)).includes("mot du jour trouvé"), mdj);
  ok("pas de bouton Rejouer au mot du jour", !(await p.evaluate(() => [...document.querySelectorAll(".voile button")].some(x => x.textContent === "Rejouer"))));
  ok("série passée à 5", (await p.evaluate(() => serieMotDuJour())).join() === "5,true");
  await p.evaluate(() => accueil()); ok("badge « Série 5 · Joué ✓ »", (await texte(p)).includes("Série 5 · Joué ✓"));
  await p.evaluate(() => solo(true)); await sleep(200);
  ok("mot du jour déjà joué", (await texte(p)).includes("Déjà joué aujourd'hui") && (await texte(p)).includes("5 jours"));
  // défaite au mot du jour : série remise à 0
  await p.evaluate(h => majConfig({ mdj_serie: 3, mdj_dernier_gagne: h, last_mdj: "" }), hierStr);
  await p.evaluate(() => solo(true)); await sleep(300);
  await p.evaluate(() => [...document.querySelectorAll("button.lien")].find(x => x.textContent === "Abandonner").click()); await sleep(200);
  ok("abandon au mot du jour → série 0", (await p.evaluate(() => serieMotDuJour())).join() === "0,true");
  // quitter en cours de mot du jour : la journée ne compte pas (le mot n'a pas été vu) et on reprend avec ses essais
  await p.evaluate(h => majConfig({ mdj_serie: 3, mdj_dernier_gagne: h, last_mdj: "", mdj_en_cours: null }), hierStr);
  await p.evaluate(() => solo(true)); await sleep(300);
  const essaiMdj = await p.evaluate(async () => { const m = await motGraine(trier(MOTS.liste), "mdj:" + aujourdhui()); return [...MOTS.banque].filter(x => x.length === m.length && x[0] === m[0] && x !== m).sort()[0]; });
  await taper(p, essaiMdj); await sleep(300);
  await p.evaluate(() => document.querySelector(".entete .icone, .icone").click()); await sleep(300);
  const apres = await p.evaluate(() => serieMotDuJour());
  ok("quitter le mot du jour en cours ne le compte pas comme joué", apres[1] === false, JSON.stringify(apres));
  await p.evaluate(() => solo(true)); await sleep(400);
  ok("le mot du jour reprend avec l'essai déjà fait (essai 2, ligne 1 remplie, lettres sur le clavier)", await p.evaluate(f => true) && await p.evaluate(f => { const g = document.querySelector(".grille"); return g.cases[0].map(t => t.textContent).join("") === f.toUpperCase() && /2/.test(document.querySelector(".stats").textContent) && g.cases[0].every(t => /bien|mal|absent/.test(t.className)); }, essaiMdj), essaiMdj);
  await p.evaluate(() => [...document.querySelectorAll("button.lien")].find(x => x.textContent === "Abandonner").click()); await sleep(200);
  ok("abandon : le mot est vu, la journée compte", (await p.evaluate(() => serieMotDuJour()))[1] === true && !(await p.evaluate(() => lireConfig().mdj_en_cours)));
  // thèmes
  const noms = await p.evaluate(() => Object.keys(THEMES));
  let tousOk = true;
  for (const n of noms) { const fond = await p.evaluate(n => { changerTheme(n, false); return getComputedStyle(document.body).getPropertyValue("--fond") || getComputedStyle(document.body).backgroundColor; }, n); if (!fond) tousOk = false; }
  ok(`${noms.length} thèmes s'appliquent`, tousOk && noms.length >= 10);
  await p.evaluate(() => { changerTheme("CONTRASTE ÉLEVÉ"); themes(); }); await sleep(200);
  ok("écran des thèmes", (await texte(p)).includes("Thème actuel ✓"));
  await p.reload({ waitUntil: "networkidle0" });
  ok("thème conservé après rechargement", await p.evaluate(() => themeActuel === "CONTRASTE ÉLEVÉ"));
  // créateur de thème : nom identique à un thème existant
  await p.evaluate(() => createurTheme()); await sleep(200);
  await p.evaluate(() => { const ch = [...document.querySelectorAll("input.champ")].find(x => x.value === "MON THÈME"); ch.value = "Plateau de nuit"; [...document.querySelectorAll("button")].find(x => x.textContent === "Enregistrer").click(); });
  await sleep(200);
  ok("un thème perso ne remplace pas un thème intégré", await p.evaluate(() => (THEMES["PLATEAU DE NUIT"] || {}).type !== "PERSO"));
  await p.evaluate(() => createurTheme()); await sleep(200);
  await p.evaluate(() => { const ch = [...document.querySelectorAll("input.champ")].find(x => x.value === "MON THÈME"); ch.value = "Mon bleu"; [...document.querySelectorAll("input.champ.mono")][0].value = "#123456"; [...document.querySelectorAll("input.champ.mono")][0].dispatchEvent(new Event("input")); [...document.querySelectorAll("button")].find(x => x.textContent === "Enregistrer").click(); });
  await sleep(200);
  ok("thème perso créé et appliqué", await p.evaluate(() => themeActuel === "MON BLEU" && THEMES["MON BLEU"].bg === "#123456"));
  await p.reload({ waitUntil: "networkidle0" });
  ok("thème perso conservé après rechargement", await p.evaluate(() => themeActuel === "MON BLEU" && !!THEMES["MON BLEU"]));
  await p.evaluate(() => supprimerTheme("MON BLEU")); ok("suppression du thème perso → thème par défaut", await p.evaluate(() => !THEMES["MON BLEU"] && themeActuel === D.theme_defaut));
  // pseudo
  await p.evaluate(() => accueil()); await p.evaluate(() => changerPseudo()); await sleep(100);
  await p.evaluate(() => { const c = document.querySelector(".voile:not(.cache) input"); c.value = ""; }); await p.type(".voile:not(.cache) input", "  léa-marie  2! "); await p.keyboard.press("Enter"); await sleep(100);
  ok("pseudo nettoyé (lettres avec accents, chiffres, espaces simples, en majuscules)", (await p.evaluate(() => lireConfig().pseudo)) === "LÉAMARIE 2", await p.evaluate(() => lireConfig().pseudo));
  await p.close();

  // ---------- mise en page téléphone
  for (const [l, hh] of [[360, 640], [390, 844], [768, 1024]]) {
    p = await page(l, hh, { pseudo: "TEL", nb_lettres_min: 10, nb_lettres_max: 10, nb_essais: 8 });
    const ecrans = { accueil: () => accueil(), solo10x8: () => solo(false), motDuJour: () => solo(true), parametres: () => parametres(), themes: () => themes(), createur: () => createurTheme(), multi: () => multiAccueil(), creerSalon: () => creerSalon() };
    for (const [n, f] of Object.entries(ecrans)) {
      await p.evaluate(f); await sleep(500);
      const d = await deborde(p);
      const clavierVisible = n.startsWith("solo") || n === "motDuJour" ? await p.evaluate(() => { const k = document.querySelector(".clavier"); const r = k.getBoundingClientRect(); return r.bottom <= document.documentElement.scrollHeight && r.width <= window.innerWidth; }) : true;
      ok(`${l}×${hh} ${n} : rien ne dépasse`, !d.length && clavierVisible, d.join(" "));
      if (n === "solo10x8") { await p.screenshot({ path: `/tmp/solo_${l}.png` }); const ht = await p.evaluate(() => document.documentElement.scrollHeight); ok(`${l}×${hh} solo tient dans ~1,3 écran`, ht <= hh * 1.35, `${ht}px`); }
    }
    await p.close();
  }
  ok("aucune erreur JavaScript", !erreurs.length, erreurs.slice(0, 3).join(" | "));
  console.log(`${res.filter(Boolean).length}/${res.length} conformes`);
  await b.close(); process.exit(res.every(Boolean) ? 0 : 1);
})().catch(e => { console.log("EXCEPTION", e); process.exit(1); });
