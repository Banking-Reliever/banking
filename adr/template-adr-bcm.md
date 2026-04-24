---
id: ADR-BCM-<GOV|URBA|FUNC>-<NNNN>
title: "<Titre>"
status: Proposed | Accepted | Suspended | Deprecated | Superseded
date: YYYY-MM-DD
# Si status: Suspended, ajouter :
# suspension_date: YYYY-MM-DD
# suspension_reason: <raison de la mise en pause>

family: GOV | URBA | FUNC

decision_scope:
  level: L1 | L2 | L3 | Cross-Level
  zoning: []
  # Valeurs possibles :
  # - PILOTAGE                    → pilotage stratégique, gouvernance, arbitrage, reporting direction
  # - SERVICES_COEUR → cœur de métier, production de services, gestion opérationnelle
  # - SUPPORT                     → fonctions transverses (RH, finance, juridique, achats)
  # - REFERENTIEL                 → données de référence, référentiels partagés, MDM
  # - ECHANGE_B2B                → échanges inter-entreprises, partenaires, fournisseurs, EDI
  # - CANAL                     → canaux de distribution, relation client, portails, apps
  # - DATA_ANALYTIQUE              → données analytiques, BI, reporting, data science

impacted_capabilities: []
impacted_events: []           # événements PRODUITS par les L2 de cet ADR
impacted_subscriptions: []    # événements CONSOMMÉS — format: "NomEvénement (emitting_capability: CAP.ZONE.NNN.SUB)"
impacted_mappings: []
  # Valeurs possibles :
  #   - SI    → applications, modules, composants techniques
  #   - DATA  → flux de données, domaines de données, référentiels
  #   - ORG   → équipes, rôles, responsabilités opérationnelles

related_adr: []
supersedes: []

tags: []

stability_impact: Structural | Moderate | Minor
---

# ADR-BCM-<FAM>-<NNNN> — <Titre court>

## Contexte

Décrire :
- La tension (ex : lisibilité vs actionnabilité)
- Les contraintes (zoning, 1 capacité = 1 responsabilité, L2 pivot)
- L’état actuel

## Décision

Décision formulée de manière **testable** :

- Règle 1 :
- Règle 2 :
- Critère vérifiable :

Exemple :
> Toute capacité L2 doit émettre au moins un événement métier.

## Justification

Pourquoi cette option.

### Alternatives considérées

- Option A — rejetée car…
- Option B — rejetée car…

## Impacts sur la BCM

### Structure

- Impact sur L1/L2/L3 :
- Split / Merge / Déplacement :

### Événements (si applicable)

- Nouveaux événements :
- Événements supprimés :
- Événements modifiés :

### Mapping SI / Data / Org

- Applications impactées :
- Flux impactés :

## Conséquences

### Positives

### Négatives / Risques

### Dette acceptée

## Indicateurs de gouvernance

- Niveau de criticité :
- Date de revue recommandée :
- Indicateur de stabilité attendu :

## Traçabilité

- Atelier :
- Participants :
- Références :