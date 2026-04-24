---
id: ADR-BCM-URBA-0005
title: "Contrats d'interface guidés par la BCM (découplage logique/physique)"
status: Suspended
date: 2026-02-24
suspension_date: 2026-03-10
suspension_reason: >
  Reflète un niveau de maturité non présent encore dans l'entreprise.
  Risque d'amener plus de confusion que d'éclaircissements pour le moment.

family: URBA

decision_scope:
  level: Cross-Level
  zoning:
    - PILOTAGE
    - SERVICES_COEUR
    - SUPPORT
    - REFERENTIEL
    - ECHANGE_B2B
    - CANAL
    - DATA_ANALYTIQUE

impacted_capabilities: []
impacted_events: []
impacted_mappings:
  - SI
  - DATA

related_adr:
  - ADR-BCM-GOV-0001  # hiérarchie GOV → URBA → FUNC
  - ADR-BCM-URBA-0003
  - ADR-BCM-URBA-0004

supersedes: []

tags:
  - BCM
  - Urbanisation
  - Événements
  - API
  - Découplage
  - Legacy
  - SI Cible

stability_impact: Structural
---

# ADR-BCM-URBA-0005 — Contrats d'interface guidés par la BCM (découplage logique/physique)

## Contexte
Dans un contexte de SI legacy, plusieurs problèmes structurels émergent :
- **Couplage applicatif/fonctionnel** : les interfaces (APIs/événements) exposées suivent la structure des applications existantes (silos) plutôt que les responsabilités métier.
- **Dette technique invisible** : impossible de mesurer l'écart entre l'existant et le cible si le cible n'est pas défini.
- **Évolution applicative non dirigée** : chaque modification d'applicatif crée de nouvelles interfaces "opportunistes" sans vision d'ensemble.
- **Dépendance au legacy** : le SI est prisonnier de l'organisation physique des applications, rendant toute transformation coûteuse et risquée.

Sans référentiel fonctionnel stable, on ne peut pas :
- piloter la convergence vers un SI cible,
- mesurer et prioriser la dette technique,
- garantir la cohérence des interfaces lors d'évolutions,
- préparer le remplacement progressif d'applications legacy.

**Dans ce repository, les contrats d'interface se matérialisent principalement via des événements métier** documentés dans les fichiers `bcm/events-*.yaml`. Chaque capacité L2 doit déclarer :
- les événements qu'elle **produit** (avec `emitted_by_l2`)
- les événements qu'elle **consomme** (avec `handled_by_l2` + capacité L2 d'origine)

Cette approche événementielle favorise le découplage et l'asynchronisme, mais nécessite une gouvernance stricte pour éviter la dérive ("event spaghetti").

## Décision
- **Les contrats d'interface fonctionnels sont définis par les capacités de la BCM** :
  - Niveau **L2** : définit les **domaines fonctionnels** (périmètre, ownership, événements produits/consommés)
  - Niveau **L3** : définit les **contrats détaillés** (services métiers, événements, règles d'interface) lorsque nécessaire (cf. [ADR-BCM-URBA-0004](ADR-BCM-URBA-0004-bon-niveau-de-decision.md))

- **Les contrats d'interface se matérialisent via des événements métier** :
  - Chaque capacité **L2** déclare les **événements qu'elle produit** (avec `emitted_by_l2`)
  - Chaque capacité **L2** déclare les **événements qu'elle consomme** (avec `handled_by_l2` + origine L2 productrice)
  - Ces contrats sont documentés dans les fichiers `bcm/events-<L1>.yaml`

- **Tout applicatif doit tendre vers cette organisation** :
  - Peu importe l'état de legacy, les événements exposés/consommés doivent être **mappés** sur les capacités de la BCM
  - Toute modification d'un applicatif legacy doit **converger vers la mise en place des contrats d'événements** définis dans la BCM
  - Les écarts entre événements existants et événements cibles sont **documentés et tracés** comme dette technique

- **Création d'une couche fonctionnelle virtuelle** :
  - Les contrats d'événements représentent le **SI cible logique** (le "quoi"), indépendant de l'implémentation physique (le "comment")
  - Les applications sont des **réalisations physiques** qui produisent ou consomment ces événements
  - Le mapping Capacité → Événements → Application permet de piloter la transformation

- **Règle d'évolution** :
  - Tout nouvel événement ou modification d'événement existant doit être **justifié par une capacité** de la BCM
  - Les événements "hors BCM" sont considérés comme **dette technique** et doivent être migrés ou supprimés
  - En cas de remplacement applicatif, les **contrats d'événements restent stables** (contrat de continuité)

## Justification
Cette approche permet de **découpler le logique du physique** :

1. **SI cible par défaut** : La BCM définit le modèle de contrats d'événements cible. Par défaut, on est **toujours** dans le SI cible (au niveau logique), même si les applications legacy ne l'implémentent pas encore parfaitement.

2. **Dette technique pilotable** : L'écart entre événements existants (legacy) et événements fonctionnels (BCM) devient **mesurable et actionnable**. On peut prioriser la convergence en fonction de la valeur métier.

3. **Évolution dirigée** : Toute modification d'applicatif sait "vers où aller" (contrat d'événement cible). Pas de dérive, pas d'événement opportuniste.

4. **Transformation progressive** : On peut remplacer une application legacy par une autre sans changer les contrats d'événements (si bien conçus). Le métier ne voit pas la transformation technique.

5. **Gouvernance renforcée** : Les événements deviennent un actif gouverné (ownership, contrats, versioning, schémas) aligné sur les responsabilités métier.

6. **Architecture événementielle** : Favorise le découplage (producteurs/consommateurs indépendants), l'asynchronisme et la résilience du SI.

### Alternatives considérées

- **Événements définis par les applications** — rejeté car renforce les silos, empêche toute convergence vers un SI cible cohérent.
- **Événements définis par les projets** — rejeté car opportunisme, incohérence, multiplication des contrats, dette accumulée.
- **Bus d'événements sans référentiel fonctionnel** — rejeté car manque de stabilité, risque de "event spaghetti", absence de gouvernance.
- **Attendre le remplacement complet des applications** — rejeté car trop long, trop coûteux, ne permet pas d'amélioration continue.

## Impacts sur la BCM

### Structure

- Capacités impactées : toutes (chaque capacité L2/L3 peut définir des contrats d'événements).
- Les **capacités L2** définissent les **domaines événementiels** (ownership, périmètre fonctionnel, événements produits/consommés).
- Les **capacités L3** (exceptionnelles, cf. ADR-BCM-URBA-0004) définissent les **contrats détaillés** (schémas d'événements, règles métier).

### Événements (si applicable)

- Nouveau mapping : `Capacité L2 → Événements (produits/consommés) → Applications` (traçabilité logique/physique).
- Chaque événement doit être rattaché à **une et une seule** capacité L2 émettrice (ownership clair).
- Utiliser les fichiers `bcm/events-<L1>.yaml` pour décrire les contrats par capacité L1.
- Chaque événement produit indique la capacité L2 émettrice (`emitted_by_l2`).
- Chaque événement consommé indique la capacité L2 consommatrice (`handled_by_l2`) et la capacité L2 d'origine.

### Mapping SI / Data / Org

- Créer un fichier `bcm/mappings/apis-capabilities.yaml` pour tracer Capacité ↔ Application.
- Générer une vue "couverture événementielle".
- Les écarts (événements legacy hors BCM) sont tracés et revus périodiquement.
- Les objets métier véhiculés dans les événements doivent être documentés (schémas, propriétés).

## Conséquences
### Positives
- **Vision SI cible claire** : les contrats d'événements définissent "où on va", même si on n'y est pas encore.
- **Dette technique visible et mesurable** : écart événements existants vs événements cibles, priorisation objective.
- **Évolution dirigée** : chaque modification d'applicatif sait vers quels événements tendre (pas de dérive).
- **Découplage logique/physique** : on peut remplacer/moderniser les applications sans changer les contrats événementiels.
- **Gouvernance des interfaces** : ownership, contrats, schémas, versioning alignés sur les responsabilités métier (BCM).
- **Résilience transformation** : les contrats d'événements restent stables même si les applications changent.
- **Meilleure interopérabilité** : événements conçus "métier" (capacités) plutôt que "technique" (silos applicatifs).
- **Découplage producteurs/consommateurs** : architecture événementielle asynchrone favorisant la résilience et la scalabilité.
- **Traçabilité fonctionnelle** : chaque événement est relié à une capacité L2, facilitant l'audit et la compréhension des flux.

### Négatives / Risques
- **Complexité initiale** : nécessite de définir les contrats d'événements (effort de modélisation, ateliers).
- **Coût de convergence** : les applications legacy doivent progressivement s'aligner (investissement continu).
- **Couche d'adaptation** : peut nécessiter des adaptateurs/traducteurs temporaires (événements legacy → événements fonctionnels).
- **Discipline de gouvernance** : risque de dérive si les événements ne sont pas revus régulièrement.
- **Tentation du "big design"** : risque de vouloir tout définir en L3 (rappel : L3 exceptionnel, cf. [ADR-BCM-URBA-0004](ADR-BCM-URBA-0004-bon-niveau-de-decision.md)).
- **Gestion du versioning** : les schémas d'événements doivent évoluer sans casser les consommateurs (rétrocompatibilité, stratégies de migration).
- **Résistance au changement** : les équipes applicatives peuvent voir cela comme une contrainte supplémentaire (nécessite accompagnement).
- **Infrastructure événementielle** : nécessite un bus d'événements robuste (disponibilité, performance, monitoring).

### Dette acceptée
- Les **événements legacy existants** ne seront pas migrés immédiatement. Ils sont **documentés comme dette technique** et migrés progressivement lors des évolutions.
- Les **adaptateurs/traducteurs temporaires** peuvent être nécessaires en phase de transition (coût accepté pour garantir la convergence).
- Les **capacités L3** pour définir les schémas d'événements détaillés restent exceptionnelles (cf. [ADR-BCM-URBA-0004](ADR-BCM-URBA-0004-bon-niveau-de-decision.md)). On commence par L2 (domaine événementiel) et on descend en L3 uniquement si nécessaire.
- Les **événements techniques** (heartbeats, logs, métriques) ne sont pas forcément reliés à la BCM (focus sur les événements métier).

## Indicateurs de gouvernance

- Niveau de criticité : Élevé (décision structurante transverse).
- Date de revue recommandée : 2028-02-24.
- Indicateur de stabilité attendu : 100 % des événements métier rattachés à une capacité L2.

## Traçabilité

- Atelier : Urbanisation 2026-02-24
- Participants : EA / Urbanisation, Architecture SI, yremy, acoutant
- Références :
  - ADR-BCM-URBA-0003 — 1 capacité = 1 responsabilité → 1 domaine événementiel
  - ADR-BCM-URBA-0004 — L3 pour schémas d'événements détaillés (exceptionnel)
  - Fichiers : `bcm/events-*.yaml`
