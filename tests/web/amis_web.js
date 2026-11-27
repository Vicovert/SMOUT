// 9.2 (web, faux serveur) : amis. Code ami, demande (bandeau partout) et acceptation, statut en ligne / dans un salon,
// invitation dans un salon protégé (sans taper le code, mot de passe demandé), invitation pendant une partie (spectateur direct).
const puppeteer = require("puppeteer-core");
const sleep = ms => new Promise(r => setTimeout(r, ms));
const BASE = "http://127.0.0.1:9000", SITE = process.env.SMOUT_SITE || "http://127.0.0.1:8000/";
const res = []; const ok = (n, c, i = "") => { res.push(!!c); console.log((c ? "OK    " : "ÉCHEC ") + n + (i && !c ? "  — " + i : "")); };
const db = async () => (await (await fetch(BASE + "/__admin.json")).json()) || {};
(async () => {
  const b = await puppeteer.launch({ executablePath: process.env.CHROME || "/usr/bin/google-chrome", headless: "new", args: ["--no-sandbox"] });
  const err = [], t0 = Date.now();
  async function joueur(nom) {
    const p = await (await b.createBrowserContext()).newPage(); await p.setViewport({ width: 1280, height: 860 });
    p.on("pageerror", e => err.push(nom + ": " + e.message)); p.on("dialog", d => { err.push(nom + ": fenêtre native"); d.accept(); });
    await p.setRequestInterception(true);
    p.on("request", async r => { const u = r.url(); let c = null;
      if (u.includes("firebasedatabase.app")) c = BASE + "/" + u.split(".app/")[1]; else if (u.includes("securetoken")) c = BASE + "/token"; else if (u.includes("identitytoolkit")) c = BASE + "/signup?op=" + u.split("accounts:")[1].split("?")[0];
      if (!c) return r.continue();
      if (r.method() === "OPTIONS") return r.respond({ status: 204, headers: { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "*", "Access-Control-Allow-Headers": "*" } });
      const x = await fetch(c, { method: r.method(), body: r.postData(), headers: { "Content-Type": r.headers()["content-type"] || "application/json" } });
      r.respond({ status: x.status, headers: { "Access-Control-Allow-Origin": "*" }, contentType: "application/json", body: await x.text() }); });
    await p.evaluateOnNewDocument(n => { if (!sessionStorage.getItem("i")) { localStorage.setItem("smout_config", JSON.stringify({ pseudo: n })); sessionStorage.setItem("i", "1"); } }, nom);
    await p.goto(SITE, { waitUntil: "networkidle0" });
    await p.evaluate(async m => { await FB.jeton(); await Compte.creer(m, "secret1"); await Amis.tic(); }, `${nom.toLowerCase()}${t0}@test.fr`);
    return p;
  }
  const ev = (p, f, ...a) => p.evaluate(f, ...a);
  const attendre = async (p, f, t = 15000, ...a) => { const fin = Date.now() + t; while (Date.now() < fin) { try { if (await ev(p, f, ...a)) return true; } catch (e) {} await sleep(300); } return false; };
  const clic = (p, sel) => ev(p, s => { const e = document.querySelector(s); if (e) e.click(); return !!e; }, sel);
  const A = await joueur("ALICE"), B = await joueur("BOB"), C = await joueur("CHLOE");
  await ev(A, () => ecranAmis()); await sleep(800);
  const codeA = await ev(A, () => Amis.code);
  ok("écran Amis : mon code ami (6 caractères)", /^[A-Z2-9]{6}$/.test(codeA || "") && (await ev(A, () => document.querySelector(".code-ami .c").textContent)) === codeA, codeA);
  ok("plus de texte sous le code (9.14)", await ev(A, () => !document.body.innerText.includes("Donne-le pour ajouter des amis.")));
  // B et C ajoutent A
  for (const p of [B, C]) { await ev(p, () => ecranAmis()); await sleep(500); await p.type(".ecran-amis input", codeA); await ev(p, () => [...document.querySelectorAll("button")].find(x => x.textContent === "Ajouter").click()); }
  ok("demande envoyée", await attendre(B, () => document.body.innerText.includes("Demande envoyée")));
  await ev(A, () => accueil()); await ev(A, () => Amis.tic());
  ok("bandeau partout : « veut être ton ami » (sur l'accueil)", await attendre(A, () => /veut être ton ami/.test(document.querySelector(".bandeau-inv")?.textContent || "")));
  ok("pastille sur le bouton Amis de l'accueil : 2", await attendre(A, () => document.querySelector(".bouton-amis .badge")?.textContent === "2"));
  await clic(A, ".bandeau-inv .inv-oui"); await sleep(1000);
  for (let i = 0; i < 2; i++) { await ev(A, () => [...document.querySelectorAll(".ti-ami button")].find(x => x.textContent === "Accepter")?.click()); await sleep(900); }
  const dA = await db(), uA = await ev(A, () => FB.uid), uB = await ev(B, () => FB.uid), uC = await ev(C, () => FB.uid);
  ok("acceptées : amis des deux côtés", dA.v7.amis[uA][uB] && dA.v7.amis[uB][uA] && dA.v7.amis[uA][uC] && dA.v7.amis[uC][uA]);
  ok("liste : Bob et Chloe « En ligne »", await attendre(A, () => [...document.querySelectorAll(".ti-ami")].filter(x => /En ligne/.test(x.textContent)).length === 2, 12000));
  // A crée un salon protégé et invite B
  await ev(A, () => multiAccueil()); await sleep(400); await ev(A, () => document.querySelector("button.a-creer").click()); await sleep(400);
  await ev(A, () => { [...document.querySelectorAll(".case")].find(x => x.textContent.includes("Mot de passe")).click(); document.querySelector("input[placeholder='Mot de passe']").value = "chat"; [...document.querySelectorAll("button")].find(x => x.textContent === "Créer le salon").click(); }); await sleep(1500);
  const code = await ev(A, () => M.lobby);
  await ev(A, () => Amis.tic());
  ok("salon : bouton « Inviter des amis »", await ev(A, () => !!document.querySelector(".btn-inviter-amis:not(.cache)")));
  await clic(A, ".btn-inviter-amis"); await sleep(800);
  ok("panneau : les amis avec « Inviter »", await attendre(A, () => document.querySelectorAll(".tiroir-inviter:not(.cache) .btn-inviter").length === 2));
  await ev(A, () => [...document.querySelectorAll(".tiroir-inviter .ami")].find(x => x.textContent.includes("Bob")).querySelector(".btn-inviter").click());
  ok("invité ✓", await attendre(A, () => !!document.querySelector(".tiroir-inviter .invite-ok")));
  await ev(B, () => accueil()); await ev(B, () => Amis.tic());
  ok("Bob : bandeau « t'invite dans son salon »", await attendre(B, () => /t'invite dans son salon/.test(document.querySelector(".bandeau-inv")?.textContent || "")));
  await clic(B, ".bandeau-inv .inv-oui"); await sleep(700);
  ok("salon protégé : mot de passe demandé (pas le code)", await attendre(B, () => /Salon protégé/.test(document.querySelector(".voile:not(.cache)")?.textContent || "")));
  await ev(B, () => { document.querySelector(".voile:not(.cache) input").value = "chat"; document.querySelector(".voile:not(.cache) .dlg-oui").click(); });
  ok("Bob rejoint le salon par l'invitation", await attendre(B, c => M.lobby === c && !M.spectateur, 10000, code) && !!(await db()).v7.lobbies[code].players[uB]);
  await ev(C, () => Amis.tic());
  ok("statut de l'ami : « Dans un salon »", await (async () => { await ev(C, () => ecranAmis()); return attendre(C, c => document.body.innerText.includes("Dans un salon · " + c), 45000, code); })());
  // partie en cours : A invite C → spectateur direct
  await attendre(A, () => !document.querySelector(".salon-partie button.lancer")?.disabled, 8000);
  await clic(A, ".salon-partie button.lancer");
  await attendre(A, () => !!document.querySelector(".clavier"), 15000);
  await ev(A, () => document.querySelector('.entete button.icone[aria-label="Inviter des amis"]').click()); await sleep(800);
  await ev(A, () => [...document.querySelectorAll(".tiroir-inviter .ami")].find(x => x.textContent.includes("Chloe")).querySelector(".btn-inviter").click()); await sleep(500);
  await ev(C, () => accueil()); await ev(C, () => Amis.tic());
  await attendre(C, () => !!document.querySelector(".bandeau-inv .inv-oui"), 8000); await clic(C, ".bandeau-inv .inv-oui"); await sleep(700);
  await ev(C, () => { const i = document.querySelector(".voile:not(.cache) input"); if (i) { i.value = "chat"; document.querySelector(".voile:not(.cache) .dlg-oui").click(); } });
  ok("partie en cours : l'invitée entre directement en spectatrice", await attendre(C, () => M.spectateur && !!document.querySelector(".vue-spect"), 12000));
  ok("pas de bandeau en pleine partie", !(await ev(A, () => !!document.querySelector(".bandeau-inv"))));
  ok("aucune fenêtre native ni erreur JavaScript", !err.length, err.join(" | "));
  console.log(`${res.filter(Boolean).length}/${res.length} conformes`); await b.close(); process.exit(res.every(Boolean) ? 0 : 1);
})().catch(e => { console.log("EXCEPTION", e); process.exit(1); });
