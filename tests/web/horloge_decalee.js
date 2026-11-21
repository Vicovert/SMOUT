// Un appareil dont l'horloge est décalée de 2 minutes voit quand même les salons (synchronisation sur l'heure du serveur),
// et un salon d'une autre version du jeu est signalé au lieu d'être caché en silence.
const puppeteer = require("puppeteer-core");
const sleep = ms => new Promise(r => setTimeout(r, ms));
const res = []; const ok = (n, c, i = "") => { res.push(!!c); console.log((c ? "OK    " : "ÉCHEC ") + n + (i ? "  — " + i : "")); };
const B = "http://127.0.0.1:9000/";
(async () => {
  const jeton = await (await fetch(B + "signup", { method: "POST", body: "{}" })).json(); const uid = jeton.idToken.slice(4);
  const VJ = require("fs").readFileSync(__dirname + "/../../web/smout.js", "utf8").match(/const VERSION_JEU = "([^"]+)"/)[1];  // version du jeu testée
  const put = (code, v) => fetch(`${B}v7/index/${code}.json?auth=${jeton.idToken}`, { method: "PUT", body: JSON.stringify({ owner: uid, hote: "HOTE", nb: 1, prive: false, visible: true, status: "waiting", version: v, maj: { ".sv": "timestamp" } }) });
  const b = await puppeteer.launch({ executablePath: process.env.CHROME || "/usr/bin/google-chrome", headless: "new", args: ["--no-sandbox"] });
  const err = [];
  for (const [nom, decal] of [["horloge juste", 0], ["horloge en avance de 2 min", 120000], ["horloge en retard de 5 min", -300000]]) {
    const p = await b.newPage(); p.on("pageerror", e => err.push(e.message));
    await p.evaluateOnNewDocument(d => { const r = Date.now; Date.now = () => r() + d; localStorage.setItem("smout_config", JSON.stringify({ pseudo: "TEST" })); }, decal);
    await p.setRequestInterception(true);
    p.on("request", async r => { const u = r.url(); let c = null;
      if (u.includes("firebasedatabase.app")) c = B + u.split(".app/")[1]; else if (u.includes("securetoken")) c = B + "token"; else if (u.includes("identitytoolkit")) c = B + "signup";
      if (!c) return r.continue();
      if (r.method() === "OPTIONS") return r.respond({ status: 204, headers: { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "*", "Access-Control-Allow-Headers": "*" } });
      const x = await fetch(c, { method: r.method(), body: r.postData(), headers: { "Content-Type": "application/json" } }); r.respond({ status: x.status, headers: { "Access-Control-Allow-Origin": "*" }, contentType: "application/json", body: await x.text() }); });
    await put("4242", VJ); await put("4343", "8.0");   // le serveur horodate lui-même (maj)
    await p.goto(process.env.SMOUT_SITE || "http://127.0.0.1:8000/", { waitUntil: "networkidle0" });
    await p.evaluate(() => { VERSION_JEU_TEST = 1; }).catch(() => {});
    await p.evaluate(() => rejoindreSalon()); await sleep(2500);
    const t = await p.evaluate(() => document.body.innerText);
    const v = await p.evaluate(() => VERSION_JEU);
    ok(`${nom} : le salon de même version est dans la liste`, t.includes("Salon de Hote") && t.includes("Code 4242"));
    ok(`${nom} : le salon d'une autre version est signalé`, /1 salon d'une autre version/.test(t), `version locale ${v}`);
    await p.close();
  }
  ok("aucune erreur JavaScript", !err.length, err.join(" | "));
  console.log(`${res.filter(Boolean).length}/${res.length} conformes`); await b.close(); process.exit(res.every(Boolean) ? 0 : 1);
})().catch(e => { console.log("EXCEPTION", e); process.exit(1); });
