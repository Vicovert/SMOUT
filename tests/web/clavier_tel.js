// Accueil (cartes côte à côte, couleurs) et clavier sur téléphone : touches larges, saisie immédiate, clavier du jeu seulement (8.18),
// pas de zoom de la page au double appui, le réglage « taille » agrandit aussi le clavier.
const puppeteer = require("puppeteer-core");
const sleep = ms => new Promise(r => setTimeout(r, ms));
const res = []; const ok = (n, c, i = "") => { res.push(!!c); console.log((c ? "OK    " : "ÉCHEC ") + n + (i && !c ? "  — " + i : "")); };
(async () => {
  const b = await puppeteer.launch({ executablePath: process.env.CHROME || "/usr/bin/google-chrome", headless: "new", args: ["--no-sandbox"] });
  const err = [];
  for (const [nom, l, hh, mobile] of [["téléphone", 375, 740, true], ["ordinateur", 1280, 860, false]]) {
    const p = await b.newPage(); await p.setViewport({ width: l, height: hh, isMobile: mobile, hasTouch: mobile });
    p.on("pageerror", e => err.push(e.message));
    await p.goto(process.env.SMOUT_SITE || "http://127.0.0.1:8000/", { waitUntil: "networkidle0" }); await sleep(500);
    const r = await p.evaluate(() => { const c = s => document.querySelector(s).getBoundingClientRect(), so = c(".carte-menu.solo"), mu = c(".carte-menu.multi"), md = c(".carte-menu.mdj");
      const fond = s => getComputedStyle(document.querySelector(s)).backgroundColor;
      return { cote: Math.abs(so.top - mu.top) < 2 && so.right <= mu.left + 1, dessous: md.top > so.bottom, couleurs: new Set([fond(".carte-menu.solo"), fond(".carte-menu.multi"), fond(".carte-menu.mdj")]).size === 3 }; });
    ok(`${nom} accueil : Solo et Multijoueur côte à côte`, r.cote); ok(`${nom} accueil : Mot du jour à part, dessous`, r.dessous); ok(`${nom} accueil : 3 couleurs différentes`, r.couleurs);
    await p.evaluate(() => solo("libre")); await sleep(2000);
    const k = await p.evaluate(() => { const t = [...document.querySelectorAll(".rang")[0].children].map(x => x.getBoundingClientRect()); const cl = document.querySelector(".clavier").getBoundingClientRect(); return { l: t[0].width, h: t[0].height, rempli: cl.width, w: window.innerWidth, natif: !!document.querySelector(".bascule-clavier, .champ-natif, .zone-natif, input") }; });
    if (mobile) { ok("téléphone clavier : touches larges (≥ 30 px) et hautes (≥ 50 px)", k.l >= 30 && k.h >= 50, `${k.l.toFixed(0)}×${k.h.toFixed(0)}`); ok("téléphone clavier : occupe presque toute la largeur", k.rempli >= k.w - 12); }
    ok(`${nom} : clavier du jeu seulement (aucun champ qui ouvrirait le clavier du téléphone)`, !k.natif);
    // appui immédiat sur une touche (pointerdown)
    await p.evaluate(() => { const t = [...document.querySelectorAll(".touche")].find(x => x.textContent === "E"); t.dispatchEvent(new PointerEvent("pointerdown", { bubbles: true, cancelable: true })); });
    ok(`${nom} : appui sur une touche = lettre saisie`, await p.evaluate(() => document.querySelectorAll(".grille .tuile")[1].textContent === "E"));
    // le réglage « taille » (+) agrandit la grille ET le clavier
    const mes = () => p.evaluate(() => { const t = [...document.querySelectorAll(".touche")].find(x => x.textContent === "A").getBoundingClientRect(); return { h: t.height, w: document.querySelector(".clavier").getBoundingClientRect().width, f: parseFloat(getComputedStyle(document.querySelector(".touche")).fontSize) }; });
    const z0 = await mes(); await p.evaluate(() => document.querySelector('button.icone[aria-label="Réduire"]').click()); await sleep(200); const z1 = await mes();
    ok(`${nom} : réduire la taille réduit aussi le clavier`, z1.h < z0.h - 2 && z1.f < z0.f && z1.w <= z0.w, `${JSON.stringify(z0)} → ${JSON.stringify(z1)}`);
    await p.evaluate(() => document.querySelector('button.icone[aria-label="Agrandir"]').click()); await sleep(200);
    ok(`${nom} : agrandir la ramène`, Math.abs((await mes()).h - z0.h) < 1.5);
    if (mobile) {
      const v = await p.evaluate(() => ({ meta: document.querySelector('meta[name=viewport]').content, ta: getComputedStyle(document.body).touchAction, ta2: getComputedStyle(document.documentElement).touchAction }));
      ok("téléphone : pas de zoom au double appui (viewport non zoomable, touch-action: manipulation)", /user-scalable=no/.test(v.meta) && /maximum-scale=1/.test(v.meta) && v.ta === "manipulation" && v.ta2 === "manipulation", JSON.stringify(v));
      const d = await p.evaluate(() => { const e = new MouseEvent("dblclick", { bubbles: true, cancelable: true }); document.body.dispatchEvent(e); return e.defaultPrevented; });
      ok("téléphone : double appui neutralisé", d);
    }
    await p.close();
  }
  ok("aucune erreur JavaScript", !err.length, err.join(" | "));
  console.log(`${res.filter(Boolean).length}/${res.length} conformes`); await b.close(); process.exit(res.every(Boolean) ? 0 : 1);
})().catch(e => { console.log("EXCEPTION", e); process.exit(1); });
