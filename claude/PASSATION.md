# Clôture d'un fil et passation

À appliquer quand un fil devient trop long : réponses plus lentes, contexte déjà résumé au moins une fois, beaucoup de fichiers relus, ou tâche qui change de sujet. Mieux vaut clore tôt qu'un fil qui consomme du quota pour se relire.

Claude ne voit pas précisément la taille de son contexte : il s'appuie sur ces signes et le dit honnêtement.

## Procédure
1. **Finir l'étape en cours** jusqu'à un état propre : rien de cassé, travail commité et poussé sur la branche du fil (ou noté comme non commencé).
2. **Leçons apprises** : ajouter en haut de `claude/lecons.md` ce qui aurait fait gagner du temps (piège rencontré, commande utile, fausse piste). Une ligne par leçon, datée. Si une leçon est une règle durable, l'ajouter aussi à `CLAUDE.md`.
3. **ETAT.md** : mettre à jour « En cours », « À faire par Victor » et « Prochaines pistes ».
4. **Note de passation** : créer `claude/passations/AAAA-MM-JJ-sujet.md` avec le modèle ci-dessous, commiter et pousser.
5. **Prévenir** : un message court à Victor (ce qui est fait, ce qui reste, lien vers la note), puis demander au coordinateur d'ouvrir un nouveau fil qui commence par lire la note.
6. Résoudre le fil.

## Modèle de note
```markdown
# Passation — <sujet> (<date>)
Fil d'origine : <titre du fil>
Branche : <branche> — dernier commit : <hash court>
Modèle et effort conseillés pour la suite : <ex. Sonnet, effort moyen>

## Objectif
<ce que Victor a demandé, avec ses mots>

## Fait
- …

## Reste à faire (dans l'ordre)
1. …

## Décisions prises et pourquoi
- …

## À ne pas refaire
- <fausses pistes, tests déjà passés, fichiers déjà vérifiés>

## Fichiers clés
- `chemin` : rôle
```
