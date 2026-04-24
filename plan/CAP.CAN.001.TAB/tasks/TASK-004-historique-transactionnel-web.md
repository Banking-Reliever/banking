---
task_id: TASK-004
capability_id: CAP.CAN.001.TAB
capability_name: Tableau de Bord Bénéficiaire
epic: Épic 3 — Tableau de bord web — historique transactionnel
status: todo
priority: medium
depends_on: [TASK-003]
---

# TASK-004 — Stub BSP.004.AUT et historique transactionnel web

## Contexte
La vue situation courante (TASK-003) expose l'état présent du bénéficiaire. Cette tâche y ajoute la dimension historique : l'accès à l'historique complet des transactions (autorisées et refusées) avec filtres et tri. Les refus doivent afficher leur motif — une exigence de la règle de dignité (ADR-BCM-FUNC-0009 : tout refus est accompagné d'une explication motivée). Les événements transactionnels viennent de CAP.BSP.004.AUT, une capacité distincte des trois déjà stub-ées en TASK-002 : un stub dédié à BSP.004.AUT est donc nécessaire.

## Référence capacité
- Capacité : Tableau de Bord Bénéficiaire (CAP.CAN.001.TAB)
- Zone : CANAL
- ADR gouvernants : ADR-BCM-FUNC-0009, ADR-BCM-URBA-0009

## Ce qu'il faut produire

### Extension du stub — événements BSP.004.AUT
Étendre le mécanisme de stub de TASK-002 pour publier sur le point de souscription de CAP.CAN.001.TAB les événements transactionnels :
- `Transaction.Autorisée` — avec catégorie, montant, marchand, horodatage, bénéficiaire
- `Transaction.Refusée` — avec catégorie, montant tenté, motif de refus (règle du palier appliquée), horodatage, bénéficiaire

Le stub génère un historique simulé suffisant pour tester les filtres et le tri.

### Extension du read model — historique transactionnel
Étendre le read model de TASK-002 pour stocker les transactions par bénéficiaire (autorisées et refusées), incluant le motif de refus pour les transactions refusées.

### Vue historique transactionnel (interface web)
L'interface web expose, depuis la vue principale de TASK-003, un accès à l'historique transactionnel :
- Affichage de toutes les transactions du bénéficiaire (autorisées et refusées)
- **Filtres disponibles** : période (date début / date fin), catégorie de dépense, statut (autorisée / refusée)
- **Tri disponible** : par date (croissant/décroissant), par montant (croissant/décroissant)
- Chaque transaction refusée affiche le motif de refus de manière intelligible (pas un code technique)
- `TableauDeBord.Consulté` est produit à chaque accès à la vue historique

## Événements métier à produire
- `TableauDeBord.Consulté` — émis à chaque accès à la vue historique (enrichi du contexte : canal=web, vue=historique)

## Objets métier impliqués
- **Bénéficiaire** — sujet de l'historique
- **Transaction** — chaque acte d'achat autorisé ou refusé, avec son contexte (catégorie, montant, motif si refus)
- **Enveloppe** — catégorie de dépense permettant de filtrer les transactions

## Souscriptions événementielles requises
- `Transaction.Autorisée` (de CAP.BSP.004.AUT) — abonnement ressource : alimente l'historique dans le read model
- `Transaction.Refusée` (de CAP.BSP.004.AUT) — abonnement métier : fait partie du cycle de vie visible du bénéficiaire ; le motif de refus est une donnée métier à afficher

## Définition de Done
- [ ] Le stub produit `Transaction.Autorisée` et `Transaction.Refusée` conformément au contrat BSP.004.AUT
- [ ] Le read model stocke l'historique transactionnel par bénéficiaire avec les motifs de refus
- [ ] La vue web affiche les transactions avec filtre sur période, catégorie et statut
- [ ] Le tri par date et par montant fonctionne dans les deux sens
- [ ] Les transactions refusées affichent leur motif de refus en langage intelligible (pas un code)
- [ ] `TableauDeBord.Consulté` est émis à chaque accès à la vue historique
- [ ] L'historique fonctionne avec le bénéficiaire de test alimenté par le stub
- [ ] validate_repo.py passe sans erreur
- [ ] validate_events.py passe sans erreur

## Critères d'acceptation (métier)
Un bénéficiaire de test peut filtrer ses transactions par catégorie et période, trier par montant décroissant, et lire le motif de chaque refus en clair. Aucune transaction refusée n'est affichée sans explication.

## Dépendances
- **TASK-003** : la vue situation courante et le read model de base doivent exister avant d'ajouter l'historique
- **CAP.BSP.004.AUT** : source de `Transaction.Autorisée` et `Transaction.Refusée` — stub obligatoire pour le développement isolé

## Questions ouvertes
- Quelle est la durée de rétention de l'historique transactionnel affiché (30 jours ? durée du dispositif complet ?)
- Le motif de refus est-il une énumération fixe (dictée par les paliers de CAP.REF.001.PAL) ou un texte libre produit par BSP.004.AUT ?
