---
id: ADR-BCM-FUNC-0006
title: "L2 Breakdown de CAP.BSP.002 — Accès & Enrôlement"
status: Proposed
date: 2026-04-24

family: FUNC

decision_scope:
  level: L2
  zoning:
    - SERVICES_COEUR

impacted_capabilities:
  - CAP.BSP.002
  - CAP.BSP.002.ELI
  - CAP.BSP.002.ENR
  - CAP.BSP.002.CYC
  - CAP.BSP.002.SOR

impacted_events:
  - Bénéficiaire.IdentifiéÉligible
  - Bénéficiaire.EligibilitéRefusée
  - Bénéficiaire.Enrôlé
  - Bénéficiaire.PalierInitialActivé
  - Bénéficiaire.Suspendu
  - Bénéficiaire.Réactivé
  - Bénéficiaire.SortiDuDispositif
  - Bénéficiaire.TransféréVersAppliStandard

impacted_mappings:
  - SI
  - ORG

related_adr:
  - ADR-BCM-GOV-0001
  - ADR-BCM-URBA-0002
  - ADR-BCM-URBA-0009
  - ADR-BCM-URBA-0010
  - ADR-BCM-FUNC-0004

supersedes: []

tags:
  - BCM
  - L2
  - BSP
  - enrôlement
  - cycle-de-vie

stability_impact: Moderate
---

# ADR-BCM-FUNC-0006 — L2 Breakdown de CAP.BSP.002 — Accès & Enrôlement

## Contexte

CAP.BSP.002 gère l'entrée des individus dans le dispositif Reliever et leur cycle de vie jusqu'à la sortie. Sans cette capacité, aucun bénéficiaire ne peut être activé dans le programme, quel que soit le canal de prescription (banque, psychiatre, assistant social).

Ce L1 couvre trois phases temporellement distinctes : la qualification de l'éligibilité, l'enrôlement formel, et la gestion du cycle de vie jusqu'à la sortie du dispositif. La sortie au dernier palier est un événement clé : elle déclenche la bascule vers une application bancaire standard.

## Décision

CAP.BSP.002 est décomposé en **4 capacités L2** :

| ID | Nom | Responsabilité |
|----|-----|----------------|
| CAP.BSP.002.ELI | Qualification de l'Éligibilité | Qualifier un individu comme éligible au dispositif sur prescription bancaire, médicale ou sociale |
| CAP.BSP.002.ENR | Enrôlement | Formaliser l'entrée dans le dispositif, activer le palier initial, ouvrir les droits d'accès |
| CAP.BSP.002.CYC | Cycle de Vie du Bénéficiaire | Gérer les états actif / suspendu / sorti et les transitions entre eux |
| CAP.BSP.002.SOR | Sortie du Dispositif | Orchestrer la sortie du bénéficiaire — dernier palier atteint ou arrêt du programme |

### Événements métier par L2

| L2 | Événements produits | Événements consommés |
|----|---------------------|----------------------|
| CAP.BSP.002.ELI | `Bénéficiaire.IdentifiéÉligible`, `Bénéficiaire.EligibilitéRefusée` | `Override.DemandéParPrescripteur` (BSP.003.COD) pour forcer une éligibilité |
| CAP.BSP.002.ENR | `Bénéficiaire.Enrôlé`, `Bénéficiaire.PalierInitialActivé` | `Bénéficiaire.IdentifiéÉligible` (BSP.002.ELI) |
| CAP.BSP.002.CYC | `Bénéficiaire.Suspendu`, `Bénéficiaire.Réactivé` | `Bénéficiaire.Enrôlé` (BSP.002.ENR), `Signal.Rechute.Détecté` (BSP.001.SIG) |
| CAP.BSP.002.SOR | `Bénéficiaire.SortiDuDispositif`, `Bénéficiaire.TransféréVersAppliStandard` | `Palier.FranchiHausse` (BSP.001.PAL) — dernier palier atteint |

### Points de transfert

- **ELI → ENR** : l'éligibilité validée déclenche l'enrôlement formel
- **ENR → BSP.001.PAL** : l'enrôlement active le palier initial dans la remédiation comportementale
- **BSP.001.PAL → SOR** : le franchissement du dernier palier déclenche la sortie du dispositif

### Critères vérifiables

- Chaque L2 produit au moins un événement métier (ADR-BCM-URBA-0009)
- `Bénéficiaire.TransféréVersAppliStandard` est l'événement terminal du dispositif — aucune capacité ne produit d'événement après lui sauf CAP.REF.001 pour archivage

## Justification

La séparation ELI / ENR / CYC / SOR reflète des phases métier distinctes avec des règles, des acteurs et des rythmes différents. L'éligibilité peut être réévaluée sans déclencher un nouvel enrôlement. La gestion du cycle de vie est continue ; la sortie est un événement ponctuel irréversible (dans Reliever).

### Alternatives considérées

- **ELI + ENR fusionnés** — rejeté car l'éligibilité peut être validée par un prescripteur sans que l'enrôlement soit immédiat (délai de consentement, constitution du dossier)
- **SOR absorbé dans CYC** — rejeté car la sortie du dispositif déclenche des actions spécifiques (bascule applicative, archivage) qui ont leur propre logique et ne sont pas une simple transition d'état

## Impacts sur la BCM

### Structure

- 4 L2 créés sous CAP.BSP.002
- Aucun L3 nécessaire

### Événements

- 8 événements métier définis
- `Bénéficiaire.TransféréVersAppliStandard` est consommé par CAP.CAN.001 (bascule UX)

### Mapping SI / Data / Org

- **SI** : dépendance vers CAP.REF.001.BEN (identité canonique du bénéficiaire)
- **ORG** : owner recommandé : équipe "Accès & Relations Prescripteurs"

## Conséquences

### Positives

- Cycle de vie du bénéficiaire entièrement traçable via les événements
- La sortie du dispositif est un événement de première classe, pas un état silencieux

### Négatives / Risques

- La gestion du consentement (RGPD) est en tension entre BSP.002.ENR et CAP.SUP.001.CON — la règle est : ENR déclenche la demande de consentement, SUP.001.CON en est propriétaire

### Dette acceptée

- Les règles précises d'éligibilité (critères de fragilité financière) ne sont pas modélisées ici — à formaliser dans les spécifications métier

## Indicateurs de gouvernance

- Niveau de criticité : Élevé
- Date de revue recommandée : 2028-04-24
- Indicateur de stabilité attendu : chaîne événementielle ELI → ENR → SOR complète et traçable dans le repository

## Traçabilité

- Atelier : Session BCM Reliever — 2026-04-24
- Participants : yremy
- Références :
  - `/strategic-vision/strategic-vision.md` — SC.002
  - ADR-BCM-FUNC-0004, ADR-BCM-FUNC-0005
