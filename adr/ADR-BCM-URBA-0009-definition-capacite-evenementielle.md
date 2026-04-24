---
id: ADR-BCM-URBA-0009
title: "Définition complète d'une capacité — responsabilité, production et consommation d'événements"
status: Proposed
date: 2026-03-10

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
  - ORG

related_adr:
  - ADR-BCM-GOV-0001
  - ADR-BCM-URBA-0002
  - ADR-BCM-URBA-0007
  - ADR-BCM-URBA-0008
  
supersedes:
  - ADR-BCM-URBA-0003

tags:
  - BCM
  - Urbanisation
  - Ownership
  - event-driven
  - abonnement
  - production

stability_impact: Structural
---

# ADR-BCM-URBA-0009 — Définition complète d'une capacité — responsabilité, production et consommation d'événements

## Contexte

L'ADR-BCM-URBA-0003 établit qu'une capacité décrit une **responsabilité métier stable**, indépendante des solutions techniques. Cette définition fondamentale reste valide mais incomplète dans un contexte d'architecture événementielle.

Avec l'introduction du méta-modèle événementiel (ADR-BCM-URBA-0007) et des règles de modélisation à deux niveaux (ADR-BCM-URBA-0008), il devient nécessaire d'enrichir la définition d'une capacité pour inclure explicitement :

- sa **production d'événements** (ce qu'elle émet) ;
- sa **consommation d'événements** (ce à quoi elle souscrit).

Cette extension permet de caractériser une capacité non seulement par ce qu'elle *fait* (responsabilité), mais aussi par ce qu'elle *communique* (interactions événementielles).

## Décision

### Définition étendue d'une capacité

Une capacité est définie par :

1. **Une responsabilité métier stable** (reprise de l'ADR-BCM-URBA-0003)
   - Le "quoi" métier, indépendant de la solution technique.
   - Les applications et composants sont mappés sur les capacités, mais ne les définissent pas.
   - Aucune référence à un éditeur, outil ou technologie dans les libellés.

2. **Sa production d'événements**
   - Une capacité est **productrice** des événements qui matérialisent les jalons de son cycle de vie.
   - Elle a la **responsabilité exclusive** de la production de ces événements.

3. **Sa consommation d'événements**
   - Une capacité **consomme** des événements via des abonnements formalisés.
   - Ces abonnements définissent les **dépendances explicites** de la capacité.

---

### Règles par niveau d'abstraction

#### Niveau Métier

| Aspect | Règle |
|--------|-------|
| **Production** | La capacité a pour responsabilité la production de ses **événements métier**, représentant les jalons abstraits de son cycle de vie. |
| **Consommation** | La capacité souscrit à des **événements métier externes** uniquement si ces événements **impactent directement le cycle de vie du processus** de la capacité. |

**Critère décisionnel pour un abonnement métier :**
> L'événement métier externe déclenche-t-il ou influence-t-il un changement d'état dans le cycle de vie du processus porté par cette capacité ?
> - Si **oui** → abonnement métier justifiée.
> - Si **non** → ce n'est pas un abonnement métier (potentiellement un abonnement ressource).

#### Niveau Opérationnel

| Aspect | Règle |
|--------|-------|
| **Production** | La capacité a pour responsabilité la production de ses **événements ressource**, représentant les faits publiés spécialisés liés aux ressources qu'elle gère. |
| **Consommation** | La capacité souscrit à des **événements ressource** pour tout gisement de données impliqué dans la **production d'information**, que ce soit pour construire un **read model** ou pour des données impactant le cycle de vie du processus. |

**Critère décisionnel pour un abonnement ressource :**
> L'événement ressource externe fournit-il des données nécessaires à :
> - la construction d'un read model utilisé par la capacité ? → **oui**
> - l'exécution d'une règle métier ou d'un traitement de la capacité ? → **oui**
> - Si aucun des deux → pas d'abonnement ressource justifiée.

---

### Vue synthétique

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CAPACITÉ                                       │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    RESPONSABILITÉ MÉTIER                              │  │
│  │              (le "quoi", stable, indépendant du SI)                   │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌─────────────────────────┐       ┌─────────────────────────────────────┐  │
│  │      PRODUCTION         │       │         CONSOMMATION                │  │
│  │                         │       │                                     │  │
│  │  ┌───────────────────┐  │       │  ┌─────────────────────────────────┐│  │
│  │  │ Événements Métier │  │       │  │      Abonnements Métier         ││  │
│  │  │ (jalons du cycle  │  │       │  │  (événements impactant le       ││  │
│  │  │  de vie abstrait) │  │       │  │   cycle de vie du processus)    ││  │
│  │  └───────────────────┘  │       │  └─────────────────────────────────┘│  │
│  │                         │       │                                     │  │
│  │  ┌───────────────────┐  │       │  ┌─────────────────────────────────┐│  │
│  │  │ Événements        │  │       │  │   Abonnements Ressource         ││  │
│  │  │ Ressource         │  │       │  │  (données pour read model ou    ││  │
│  │  │ (faits publiés    │  │       │  │   production d'information)     ││  │
│  │  │  spécialisés)     │  │       │  └─────────────────────────────────┘│  │
│  │  └───────────────────┘  │       │                                     │  │
│  └─────────────────────────┘       └─────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### Critères vérifiables

| Critère | Vérification |
|---------|--------------|
| Toute capacité L2 doit émettre au moins un événement métier | Contrôle automatisé via `validate_events.py` |
| Chaque abonnement métier doit justifier un impact sur le cycle de vie | Champ `impact_cycle_de_vie` requis dans le template d'abonnement |
| Chaque abonnement ressource doit préciser son usage (read model ou traitement) | Champ `usage_type` requis dans le template d'abonnement |
| Une capacité ne souscrit pas à ses propres événements | Contrôle automatisé |

## Justification

Cette extension de la définition permet :

- d'**expliciter les contrats d'interaction** entre capacités ;
- de **clarifier les responsabilités** producteur/consommateur à chaque niveau ;
- de **distinguer les dépendances structurelles** (cycle de vie) des dépendances opérationnelles (read model) ;
- d'**outiller la gouvernance** avec des critères vérifiables automatiquement.

### Alternatives considérées

- **Option A — Conserver uniquement la définition par responsabilité :**
  Rejetée car insuffisante pour caractériser les interactions dans une architecture événementielle.

- **Option B — Définir les abonnements sans distinction métier/ressource :**
  Rejetée car ne permet pas de différencier les niveaux de couplage et d'identifier les vraies dépendances métier.

- **Option C — Laisser les abonnements implicites :**
  Rejetée car crée du shadow coupling non traçable et non gouvernable.

## Impacts sur la BCM

### Structure

- Capacités impactées : toutes (enrichissement de la définition).
- Templates de capacités à enrichir avec les sections `produced_events` et `subscriptions`.

### Événements

- Formalisation explicite de la relation `Capability -> Evenement` (production).
- Formalisation explicite de la relation `Capability + Abonnement -> Evenement` (consommation).

### Mapping SI / Data / Org

- **SI** : permet de cartographier les flux d'événements par capacité.
- **DATA** : clarifie les sources de données (abonnements ressource pour read models).
- **ORG** : responsabilité de production assignée explicitement à chaque capacité.

## Conséquences

### Positives

- Traçabilité complète des interactions inter-capacités.
- Gouvernance outillable : détection automatique des incohérences.
- Support pour l'analyse d'impact (qui produit, qui consomme).
- Clarification des niveaux de couplage (métier vs opérationnel).

### Négatives / Risques

- Complexité accrue de la documentation des capacités.
- Nécessité de maintenir la cohérence entre capacités, événements et abonnements.
- Discipline de gouvernance requise pour qualifier les abonnements.

### Dette acceptée

- Les capacités existantes peuvent temporairement ne pas avoir leurs événements et abonnements documentés.
- Migration progressive vers la définition complète.

## Indicateurs de gouvernance

- Niveau de criticité : Élevé (règle transverse structurante).
- Date de revue recommandée : 2028-03-10.
- Indicateurs de stabilité attendus :
  - 100% des capacités L2 avec au moins un événement métier documenté.
  - 100% des abonnements avec qualification d'usage documentée.
  - 0 abonnement métier sans justification d'impact cycle de vie.

## Traçabilité

Cet ADR **supersede** ADR-BCM-URBA-0003, en reprenant et enrichissant sa définition fondamentale.
