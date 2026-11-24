# Leçons apprises
- 24/11/2026 : CI découpé en 8 jobs courts (base-pc, base-web, 6 tranches de parties) : ~4 min au lieu de 10-25 ; un cache npm exige package-lock.json (ignoré par git) : ne pas l'activer.
- 24/11/2026 : avant de pousser, chercher dans tests/ les textes et boutons modifiés (robots web et PC) : sinon CI rouge à coup sûr.
- 24/11/2026 : Firebase Auth avec protection contre l'énumération des e-mails : rattacher un joueur anonyme par accounts:signUp + idToken (accounts:update est refusé).
- Pages : si la source GitHub Pages repasse en « Deploy from a branch », chaque push sur une branche de travail republie le dépôt brut (site cassé) : Victor remet « GitHub Actions » (Settings → Pages), puis relancer pages.yml sur main (pages.yml refait un 2e essai tout seul depuis la 9.0 ; relancer si les deux échouent).

Une ligne par leçon, la plus récente en haut. Ajoutées à la clôture d'un fil (voir `claude/PASSATION.md`). Une leçon qui devient une règle durable passe dans `CLAUDE.md`.

- 22/11/2026 — Un merge par l'interface GitHub d'une branche déjà squashée (PR #2 `travail-8.10`) relance build et site pour rien : supprimer les branches de travail après le squash-merge.
- 22/11/2026 — Un push sur `main` déclenche build + release avec le titre du commit comme tag : une modification de documentation seule ne doit pas déclencher de release (d'où le `paths-ignore` des workflows).
- 22/11/2026 — Dans les fils cloud, `gh` n'est pas utilisable (sauf recherche) : vérifier une release avec l'outil GitHub `get_release_by_tag`.
