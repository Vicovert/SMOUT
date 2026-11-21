// Accueil (cartes côte à côte, couleurs) et clavier sur téléphone : touches larges, saisie immédiate, bascule vers le clavier du téléphone.
const puppeteer = require("puppeteer-core");
const sleep = ms => new Promise(r => setTimeout(r, ms));
const res = []; const ok = (n, c, i = "") => { res.push(!!c); console.log((c ? "OK    " : "ÉCHEC ") + n + (i ? "  — " + i : "")); };
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
    const k = await p.evaluate(() => { const t = [...document.querySelectorAll(".rang")[0].children].map(x => x.getBoundingClientRect()); const cl = document.querySelector(".clavier").getBoundingClientRect(); return { l: t[0].width, h: t[0].height, rempli: cl.width, w: window.innerWidth, natif: !!document.querySelector(".bascule-clavier") }; });
    if (mobile) { ok("téléphone clavier : touches larges (≥ 30 px) et hautes (≥ 50 px)", k.l >= 30 && k.h >= 50, `${k.l.toFixed(0)}×${k.h.toFixed(0)}`); ok("téléphone clavier : occupe presque toute la largeur", k.rempli >= k.w - 12); }
    ok(`${nom} : bouton « clavier du téléphone » ${mobile ? "présent" : "absent sur ordinateur"}`, k.natif === mobile);
    // appui immédiat sur une touche (pointerdown)
    await p.evaluate(() => { const t = [...document.querySelectorAll(".touche")].find(x => x.textContent === "E"); t.dispatchEvent(new PointerEvent("pointerdown", { bubbles: true, cancelable: true })); });
    ok(`${nom} : appui sur une touche = lettre saisie`, await p.evaluate(() => document.querySelectorAll(".grille .tuile")[1].textContent === "E"));
    if (mobile) {
      await p.evaluate(() => document.querySelector(".bascule-clavier").click()); await sleep(300);
      ok("téléphone : clavier du jeu masqué, zone de saisie affichée", await p.evaluate(() => getComputedStyle(document.querySelector(".clavier .rangs")).display === "none" && getComputedStyle(document.querySelector(".zone-natif")).display !== "none"));
      const s = await p.evaluate(() => { const c = document.querySelector(".champ-natif"), S = "​", set = v => { c.value = v; c.dispatchEvent(new Event("input")); }; set(S + "a"); set(S + "ab"); set(S + "abé"); set(S + "ab"); return [...document.querySelectorAll(".grille .tuile")].slice(1, 6).map(t => t.textContent).join(""); });
      ok("téléphone : saisie native (lettres, accent ramené à la lettre, effacer)", s === "EAB", s);
      ok("téléphone : préférence mémorisée", await p.evaluate(() => JSON.parse(localStorage.getItem("smout_config")).clavier_natif === true));
    }
    await p.close();
  }
  ok("aucune erreur JavaScript", !err.length, err.join(" | "));
  console.log(`${res.filter(Boolean).length}/${res.length} conformes`); await b.close(); process.exit(res.every(Boolean) ? 0 : 1);
})().catch(e => { console.log("EXCEPTION", e); process.exit(1); });
