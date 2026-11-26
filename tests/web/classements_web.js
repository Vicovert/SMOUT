// 9.4 (web, faux serveur) : classements (mot du jour sur l'accueil, marathon dans le menu Solo et en partie), fiche joueur,
// et lettres lisibles DANS les mini-grilles (dès 9 px).
const puppeteer = require("puppeteer-core");
const sleep = ms => new Promise(r => setTimeout(r, ms));
const BASE = "http://127.0.0.1:9000", SITE = process.env.SMOUT_SITE || "http://127.0.0.1:8000/";
const res = []; const ok = (n, c, i = "") => { res.push(!!c); console.log((c ? "OK    " : "ÉCHEC ") + n + (i && !c ? "  — " + i : "")); };
const db = async () => (await (await fetch(BASE + "/__admin.json")).json()) || {};
(async () => {
  const b = await puppeteer.launch({ executablePath: process.env.CHROME || "/usr/bin/google-chrome", headless: "new", args: ["--no-sandbox"] });
  const err = [], t0 = Date.now();
  const autres = [];
  for (const [n, m, r, moy, tr] of [["ZEBULON", 900 % 401, 58, 4, 98], ["YANN", 30, 44, 5, 30], ["WALTER", 7, 10, 2.5, 9]]) {  // joueurs déjà classés (Walter : autant de mots trouvés qu'Alice, meilleure moyenne)
    const u = (await (await fetch(BASE + "/signup", { method: "POST", body: "{}" })).json()).localId; autres.push(u);
    await fetch(`${BASE}/v7/classements/mdj/${u}.json?auth=tok-${u}`, { method: "PUT", body: JSON.stringify({ pseudo: n, meilleure: m, actuelle: 1, moyenne: moy, trouves: tr, maj: { ".sv": "timestamp" } }) });
    await fetch(`${BASE}/v7/classements/marathon/${u}.json?auth=tok-${u}`, { method: "PUT", body: JSON.stringify({ pseudo: n, record: r, score: r * 1000, maj: { ".sv": "timestamp" } }) });
    await fetch(`${BASE}/v7/profils/${u}.json?auth=tok-${u}`, { method: "PUT", body: JSON.stringify({ pseudo: n, code: "", vu: { ".sv": "timestamp" }, salon: "", cree: Date.UTC(2026, 9, 3) }) });
  }
  const p = await (await b.createBrowserContext()).newPage(); await p.setViewport({ width: 390, height: 844, isMobile: true, hasTouch: true });
  p.on("pageerror", e => err.push(e.message));
  await p.setRequestInterception(true);
  p.on("request", async r => { const u = r.url(); let c = null;
    if (u.includes("firebasedatabase.app")) c = BASE + "/" + u.split(".app/")[1]; else if (u.includes("securetoken")) c = BASE + "/token"; else if (u.includes("identitytoolkit")) c = BASE + "/signup?op=" + u.split("accounts:")[1].split("?")[0];
    if (!c) return r.continue();
    if (r.method() === "OPTIONS") return r.respond({ status: 204, headers: { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "*", "Access-Control-Allow-Headers": "*" } });
    const x = await fetch(c, { method: r.method(), body: r.postData(), headers: { "Content-Type": r.headers()["content-type"] || "application/json" } });
    r.respond({ status: x.status, headers: { "Access-Control-Allow-Origin": "*" }, contentType: "application/json", body: await x.text() }); });
  await p.evaluateOnNewDocument(() => { if (!sessionStorage.getItem("i")) { const d = new Date(), auj = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
    localStorage.setItem("smout_config", JSON.stringify({ pseudo: "ALICE", last_mdj: auj, stats: { historique: [{ d: auj, g: "mdj", m: "MAISON", v: true, e: 3, s: 0 }],  mdj: { parties: 9, victoires: 9, repartition: { 3: 4, 4: 5 }, serie: 0, meilleure_serie: 7, meilleur_score: 0 }, marathon: { parties: 3, record: 12, record_score: 0, mots: 30, meilleur_points: 12345, meilleur_detail: { mots: 12, essais: 6, lmin: 6, lmax: 10, difficile: false } } } })); sessionStorage.setItem("i", "1"); } });
  await p.goto(SITE, { waitUntil: "networkidle0" });
  const ev = (f, ...a) => p.evaluate(f, ...a);
  const attendre = async (f, t = 12000, ...a) => { const fin = Date.now() + t; while (Date.now() < fin) { try { if (await ev(f, ...a)) return true; } catch (e) {} await sleep(250); } return false; };
  ok("sans compte : classement affiché, invitation à créer un compte", await attendre(() => document.querySelectorAll(".classement-mdj .cl-l").length >= 2 && /Crée un compte/.test(document.querySelector(".classement-mdj").textContent)));
  await ev(async m => { await FB.jeton(); await Compte.creer(m, "secret1"); }, `alice${t0}@test.fr`); await ev(() => accueil());
  ok("avec compte : ma ligne apparaît (9 mots trouvés)", await attendre(() => [...document.querySelectorAll(".classement-mdj .cl-l.moi")].some(x => /Alice/.test(x.textContent) && x.querySelector(".cl-tr")?.textContent === "9")));
  const uid = await ev(() => FB.uid), d = (await db()).v7.classements;
  ok("envoyé à la base : mot du jour (avec le résultat du jour) et marathon", d.mdj[uid].meilleure === 7 && d.mdj[uid].essais === 3 && d.mdj[uid].moyenne === 3.56 && d.mdj[uid].trouves === 9 && d.marathon[uid].record === 12 && d.marathon[uid].score === 12345 && d.marathon[uid].mots === 12 && d.marathon[uid].essais === 6, JSON.stringify([d.mdj[uid], d.marathon[uid]]));
  ok("classement trié (le plus de mots du jour trouvés en premier, 9.11)", await ev(() => { const v = [...document.querySelectorAll(".classement-mdj .cl-l .cl-tr")].map(x => +x.textContent); return v.length >= 2 && v.every((x, i) => !i || v[i - 1] >= x); }));
  ok("autant de mots trouvés : la meilleure moyenne passe devant (Walter 2,5 avant Alice 3,6)", await ev(() => { const n = [...document.querySelectorAll(".classement-mdj .cl-l .n")].map(x => x.textContent); return n.indexOf("Walter") >= 0 && n.indexOf("Walter") < n.indexOf("Alice"); }));
  ok("colonne « moy. essais » : 3,6 en jaune pour moi (vert jusqu'à 3,5), 2,5 en vert pour Walter", await ev(() => { const c = document.querySelector(".classement-mdj"); return /moy\. essais/.test(c.textContent) && c.querySelector(".cl-l.moi .cl-cm .p-moyen")?.textContent === "3,6" && [...c.querySelectorAll(".cl-cm .p-ok")].some(x => x.textContent === "2,5"); }));
  ok("colonnes trouvés / moy. essais / série, « Aujourd'hui » sous le pseudo (3 essais pour moi, pas joué pour les autres)", await ev(() => { const c = document.querySelector(".classement-mdj"); return /trouvés/.test(c.textContent) && c.querySelector(".cl-l.moi .det")?.textContent === "Aujourd'hui : 3 essais" && c.querySelector(".cl-l.moi .cl-tr")?.textContent === "9" && [...c.querySelectorAll(".det")].some(x => x.textContent === "Aujourd'hui : pas joué") && !/série en cours/.test(c.textContent); }));
  await ev(() => menuSolo());
  ok("menu Solo : classement du marathon", await attendre(() => document.querySelectorAll(".classement-marathon .cl-l").length >= 3));
  ok("marathon : mots et réglages de ma meilleure partie (9.10)", await ev(() => { const l = document.querySelector(".classement-marathon .cl-l.moi"); return !!l && l.querySelector(".cl-mots")?.textContent === "12" && /6 essais · 6–10 lettres/.test(l.textContent); }));
  await ev(() => solo("marathon"));
  ok("marathon en cours : ma place en direct", await attendre(() => /Classement : \d+/.test(document.querySelector(".cl-direct")?.textContent || "")));
  await ev(() => menuSolo()); await attendre(() => !!document.querySelector(".classement-marathon .cl-l"));
  await ev(() => [...document.querySelectorAll(".classement-marathon .cl-l")].find(x => /Zebulon/.test(x.textContent)).click());
  ok("fiche joueur : ancienneté, meilleure série, record, « Ajouter en ami »", await attendre(() => { const f = document.querySelector(".fiche-joueur:not(.cache)"); return f && /Joueur depuis octobre 2026/.test(f.textContent) && /58/.test(f.textContent) && /Ajouter en ami/.test(f.textContent); }));
  await ev(() => [...document.querySelectorAll(".fiche-joueur button")].find(x => x.textContent === "Ajouter en ami").click()); await sleep(600);
  ok("fiche : demande d'ami envoyée", !!((await db()).v7.amis_demandes[autres[0]] || {})[uid]);
  ok("mini-grilles : lettres affichées dès 9 px (police plus grande)", await ev(() => { const t = tuile(10, true); t.maj("A", "bien"); document.body.append(t); const r = t.textContent === "A" && parseFloat(getComputedStyle(t).fontSize) >= 7; t.remove(); return r; }));
  ok("aucune erreur JavaScript", !err.length, err.join(" | "));
  console.log(`${res.filter(Boolean).length}/${res.length} conformes`); await b.close(); process.exit(res.every(Boolean) ? 0 : 1);
})().catch(e => { console.log("EXCEPTION", e); process.exit(1); });
