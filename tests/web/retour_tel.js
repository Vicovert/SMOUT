// Bouton « retour » du téléphone : revient à l'écran précédent au lieu de fermer la page ; sur l'accueil, il quitte vraiment.
const puppeteer = require("puppeteer-core");
const sleep = ms => new Promise(r => setTimeout(r, ms));
const res = []; const ok = (n, c, i = "") => { res.push(!!c); console.log((c ? "OK    " : "ÉCHEC ") + n + (i ? "  — " + i : "")); };
(async () => {
  const b = await puppeteer.launch({ executablePath: process.env.CHROME || "/usr/bin/google-chrome", headless: "new", args: ["--no-sandbox"] });
  const p = await b.newPage(); await p.setViewport({ width: 375, height: 740, isMobile: true, hasTouch: true });
  const err = []; p.on("pageerror", e => err.push(e.message)); let confirme = null; p.on("dialog", async d => { if (d.type() === "confirm") { confirme = d.message(); await (reponse ? d.accept() : d.dismiss()); } else await d.dismiss(); });
  let reponse = false;
  const URL = process.env.SMOUT_SITE || "http://127.0.0.1:8000/";
  await p.goto(URL, { waitUntil: "networkidle0" }); await sleep(500);
  const texte = () => p.evaluate(() => document.body.innerText);
  const retour = async () => { await p.evaluate(() => history.back()); await sleep(700); };
  await p.touchscreen.tap(8, 8); await sleep(200);  // premier geste : l'entrée d'historique est ajoutée
  await p.tap(".carte-menu.solo"); await sleep(600);
  ok("menu Solo ouvert", (await texte()).includes("Partie normale"));
  await retour();
  ok("retour téléphone : du menu Solo à l'accueil (page toujours là)", p.url().startsWith(URL) && (await texte()).includes("Trouvez le mot caché"), p.url());
  await p.tap(".carte-menu.solo"); await sleep(500); await p.evaluate(() => solo("libre")); await sleep(1800);
  ok("partie solo lancée", await p.evaluate(() => !!document.querySelector(".clavier")));
  // 9.1 : la confirmation est une fenêtre du jeu (plus de confirm du navigateur)
  await retour(); await sleep(300);
  confirme = await p.evaluate(() => document.querySelector(".voile:not(.cache) .dialogue .titre")?.textContent || null);
  await p.evaluate(() => document.querySelector(".voile:not(.cache) .dlg-non")?.click()); await sleep(300);
  ok("retour en partie : demande confirmation, annulée = on reste en jeu", confirme && confirme.includes("Quitter") && await p.evaluate(() => !!document.querySelector(".clavier")), String(confirme));
  await retour(); await sleep(300); await p.evaluate(() => document.querySelector(".voile:not(.cache) .dlg-oui")?.click()); await sleep(600);
  ok("retour en partie, confirmé : retour au menu Solo (écran précédent)", (await texte()).includes("Partie normale"));
  await retour();
  ok("retour depuis le menu Solo : à l'accueil", (await texte()).includes("Trouvez le mot caché"));
  await p.tap(".icone[aria-label='Thèmes']"); await sleep(600);
  await retour();
  ok("retour depuis les thèmes : à l'accueil", (await texte()).includes("Trouvez le mot caché") && p.url().startsWith(URL));
  await retour(); await sleep(400);
  ok("retour sur l'accueil : quitte la page", !p.url().startsWith(URL), p.url());
  ok("aucune erreur JavaScript", !err.length, err.join(" | "));
  console.log(`${res.filter(Boolean).length}/${res.length} conformes`); await b.close(); process.exit(res.every(Boolean) ? 0 : 1);
})().catch(e => { console.log("EXCEPTION", e); process.exit(1); });
