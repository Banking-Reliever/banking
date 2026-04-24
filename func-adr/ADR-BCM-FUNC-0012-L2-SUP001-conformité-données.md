---
id: ADR-BCM-FUNC-0012
title: "L2 Breakdown de CAP.SUP.001 — Conformité & Protection des Données"
status: Proposed
date: 2026-04-24

family: FUNC

decision_scope:
  level: L2
  zoning:
    - SUPPORT

impacted_capabilities:
  - CAP.SUP.001
  - CAP.SUP.001.CON
  - CAP.SUP.001.AUD
  - CAP.SUP.001.RET

impacted_events:
  - Consentement.Accordé
  - Consentement.Révoqué
  - AccèsDonnées.Journalisé
  - DroitExercé.Traité

impacted_mappings:
  - SI
  - ORG

related_adr:
  - ADR-BCM-GOV-0001
  - ADR-BCM-URBA-0001
  - ADR-BCM-URBA-0002
  - ADR-BCM-URBA-0009
  - ADR-BCM-URBA-0010
  - ADR-BCM-FUNC-0004
  - ADR-BCM-FUNC-0007

supersedes: []

tags:
  - BCM
  - L2
  - SUPPORT
  - RGPD
  - conformité
  - données-sensibles

stability_impact: Moderate
---

# ADR-BCM-FUNC-0012 — L2 Breakdown de CAP.SUP.001 — Conformité & Protection des Données

## Contexte

CAP.SUP.001 adresse la tension transparence/vie privée identifiée comme critique dans le service offer. Reliever concentre des données de natures hétérogènes (financières, médicales, sociales) sur un même individu, partagées entre des acteurs dont les réglementations sont distinctes (banque : RGPD + DSP2 ; médecin : RGPD + secret médical ; assistant social : RGPD + CASF).

Cette capacité est transverse à tout le dispositif — aucune capacité ne peut accéder à des données d'un bénéficiaire sans passer par les règles définies ici. Elle est propriétaire des consentements, de la traçabilité des accès, et des droits des bénéficiaires.

## Décision

CAP.SUP.001 est décomposé en **3 capacités L2** :

| ID | Nom | Responsabilité |
|----|-----|----------------|
| CAP.SUP.001.CON | Gestion des Consentements | Recueillir, stocker, gérer et honorer les consentements RGPD du bénéficiaire pour chaque type de partage de données |
| CAP.SUP.001.AUD | Audit & Traçabilité | Journaliser l'ensemble des accès et actions sur les données bénéficiaires, toutes capacités confondues |
| CAP.SUP.001.RET | Droits des Bénéficiaires | Traiter les exercices de droits RGPD (accès, rectification, effacement, portabilité, opposition) |

### Événements métier par L2

| L2 | Événements produits | Événements consommés |
|----|---------------------|----------------------|
| CAP.SUP.001.CON | `Consentement.Accordé`, `Consentement.Révoqué` | `Bénéficiaire.Enrôlé` (BSP.002.ENR) — déclenche la collecte de consentement |
| CAP.SUP.001.AUD | `AccèsDonnées.Journalisé` | Tout événement impliquant un accès à des données bénéficiaire (transverse) |
| CAP.SUP.001.RET | `DroitExercé.Traité` | `Bénéficiaire.SortiDuDispositif` (BSP.002.SOR) — déclenche la revue des droits post-sortie |

### Règle de blocage

`Consentement.Accordé` est une précondition obligatoire pour :
- `Bénéficiaire.Enrôlé` (BSP.002.ENR) — pas d'enrôlement sans consentement
- `DonnéesFinancières.Rafraîchies` (B2B.001.OBK) — pas d'accès open banking sans consentement
- Toute consultation dans CAP.CAN.002.VUE

Si `Consentement.Révoqué`, toutes les capacités consommatrices doivent cesser l'accès aux données du bénéficiaire.

### Critères vérifiables

- Chaque L2 produit au moins un événement métier (ADR-BCM-URBA-0009)
- Aucune capacité ne peut accéder aux données d'un bénéficiaire sans que `Consentement.Accordé` soit dans l'état courant
- 100% des accès aux données bénéficiaires produisent `AccèsDonnées.Journalisé`

## Justification

La séparation CON / AUD / RET reflète trois responsabilités distinctes de conformité. Les consentements sont dynamiques (accordés/révoqués). L'audit est continu et transverse. Les droits sont des demandes ponctuelles avec des délais légaux (1 mois RGPD). Les confondre créerait un L2 trop large avec des contraintes légales incompatibles.

### Alternatives considérées

- **CON dans BSP.002.ENR** — rejeté car le consentement est une responsabilité transverse qui va au-delà de l'enrôlement (il peut être révoqué à tout moment, indépendamment du cycle de vie du bénéficiaire dans le dispositif)
- **AUD dans CAP.PIL.001** — rejeté car l'audit des accès données est une obligation réglementaire RGPD (SUPPORT) ; le pilotage du programme est une préoccupation métier (PILOTAGE) — les niveaux et les acteurs sont distincts

## Impacts sur la BCM

### Structure

- 3 L2 créés sous CAP.SUP.001
- Capacité transverse : toutes les autres capacités en dépendent pour l'accès aux données

### Mapping SI / Data / Org

- **SI** : nécessite un DMP (Data Management Platform) ou équivalent pour la gestion des consentements
- **ORG** : owner recommandé : DPO (Data Protection Officer)

## Conséquences

### Positives

- La tension transparence/vie privée est adressée par une capacité dédiée avec des règles de blocage explicites
- L'audit est de première classe — toute action est traçable

### Négatives / Risques

- Le partage de données entre prescripteurs de natures différentes (banque, médecin, assistant social) reste une zone grise réglementaire — nécessite un avis juridique

### Dette acceptée

- Les bases légales précises de traitement pour chaque type de prescripteur ne sont pas modélisées ici

## Indicateurs de gouvernance

- Niveau de criticité : Élevé (obligation réglementaire, condition de viabilité)
- Date de revue recommandée : 2027-10-24
- Indicateur de stabilité attendu : 100% des accès données journalisés, 0 enrôlement sans consentement documenté

## Traçabilité

- Atelier : Session BCM Reliever — 2026-04-24
- Participants : yremy
- Références :
  - `/strategic-vision/strategic-vision.md` — SC.007
  - ADR-BCM-FUNC-0004, ADR-BCM-FUNC-0007
