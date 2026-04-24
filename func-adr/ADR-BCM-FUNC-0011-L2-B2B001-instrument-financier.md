---
id: ADR-BCM-FUNC-0011
title: "L2 Breakdown de CAP.B2B.001 — Gestion de l'Instrument Financier"
status: Proposed
date: 2026-04-24

family: FUNC

decision_scope:
  level: L2
  zoning:
    - ECHANGE_B2B

impacted_capabilities:
  - CAP.B2B.001
  - CAP.B2B.001.CRT
  - CAP.B2B.001.OBK
  - CAP.B2B.001.FLX

impacted_events:
  - Carte.Émise
  - Carte.Activée
  - Carte.Suspendue
  - Carte.Résiliée
  - DonnéesFinancières.Rafraîchies
  - Alimentation.Effectuée

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

supersedes: []

tags:
  - BCM
  - L2
  - ECHANGE_B2B
  - open-banking
  - carte
  - instrument-financier

stability_impact: Structural
---

# ADR-BCM-FUNC-0011 — L2 Breakdown de CAP.B2B.001 — Gestion de l'Instrument Financier

## Contexte

CAP.B2B.001 est la capacité qui rend Reliever indépendant des établissements bancaires. Via l'open banking, Reliever accède aux données financières du compte principal sans accord inter-bancaire. Via la carte dédiée, il contrôle les dépenses sans modifier le compte principal.

C'est la zone ECHANGE_B2B qui porte cette capacité (ADR-BCM-URBA-0001) : il s'agit d'échanges avec l'écosystème financier externe (réseaux de paiement, établissements émetteurs, API open banking) avec des contraintes SLA, de traçabilité et de conformité réglementaire spécifiques.

## Décision

CAP.B2B.001 est décomposé en **3 capacités L2** :

| ID | Nom | Responsabilité |
|----|-----|----------------|
| CAP.B2B.001.CRT | Gestion de la Carte Dédiée | Piloter le cycle de vie de la carte dédiée — émission, activation, suspension, résiliation — et lier ses règles d'usage aux paliers courants |
| CAP.B2B.001.OBK | Intégration Open Banking | Accéder et rafraîchir les données financières du compte principal du bénéficiaire via les APIs open banking |
| CAP.B2B.001.FLX | Gestion des Flux Financiers | Orchestrer l'alimentation de la carte dédiée depuis le compte principal, assurer le rapprochement des flux |

### Événements métier par L2

| L2 | Événements produits | Événements consommés |
|----|---------------------|----------------------|
| CAP.B2B.001.CRT | `Carte.Émise`, `Carte.Activée`, `Carte.Suspendue`, `Carte.Résiliée` | `Bénéficiaire.Enrôlé` (BSP.002.ENR), `Palier.FranchiHausse` (BSP.001.PAL), `Palier.Rétrogradé` (BSP.001.PAL), `Bénéficiaire.SortiDuDispositif` (BSP.002.SOR) |
| CAP.B2B.001.OBK | `DonnéesFinancières.Rafraîchies` | `Bénéficiaire.Enrôlé` (BSP.002.ENR) — pour initialiser l'accès open banking |
| CAP.B2B.001.FLX | `Alimentation.Effectuée` | `Enveloppe.Allouée` (BSP.004.ENV), `Enveloppe.Épuisée` (BSP.004.ENV) |

### Points de transfert

- **BSP.001.PAL → B2B.001.CRT** : tout changement de palier met à jour les règles de la carte (plafonds, restrictions catégories)
- **BSP.002.ENR → B2B.001.CRT** : l'enrôlement déclenche l'émission de la carte
- **B2B.001.OBK → DAT.001** : les données financières rafraîchies alimentent l'analytique comportementale

### Contrainte réglementaire open banking

CAP.B2B.001.OBK opère sous le cadre PSD2/DSP2. L'accès aux données financières nécessite un consentement explicite géré par CAP.SUP.001.CON. La capacité open banking ne peut être activée qu'après `Consentement.Accordé`.

### Critères vérifiables

- Chaque L2 produit au moins un événement métier (ADR-BCM-URBA-0009)
- `Carte.Émise` ne peut être produit qu'après `Bénéficiaire.Enrôlé`
- `DonnéesFinancières.Rafraîchies` ne peut être produit qu'après `Consentement.Accordé` (SUP.001.CON)

## Justification

La séparation CRT / OBK / FLX reflète trois relations distinctes avec l'écosystème financier externe : l'émetteur de carte (partenaire de paiement), les banques du bénéficiaire (via open banking), et les flux de fonds entre les deux. Ces trois relations ont des partenaires, des SLAs et des réglementations différents.

### Alternatives considérées

- **CRT + FLX fusionnés** — rejeté car la carte et les flux financiers impliquent des partenaires externes différents (émetteur carte ≠ banque principale du bénéficiaire) ; leur cycle de vie et leurs SLAs sont distincts
- **OBK dans CAP.SUP.001** — rejeté car l'open banking est un échange avec l'écosystème externe (ECHANGE_B2B) ; la conformité de cet échange est gérée par SUP.001 mais la capacité d'échange elle-même appartient à B2B

## Impacts sur la BCM

### Structure

- 3 L2 créés sous CAP.B2B.001
- Dépendances entrantes fortes depuis BSP.001.PAL et BSP.002.ENR

### Mapping SI / Data / Org

- **SI** : nécessite un partenaire d'émission de carte (établissement de paiement agréé) et un agrégateur open banking
- **ORG** : owner recommandé : équipe "Partenariats Financiers & Paiements"

## Conséquences

### Positives

- Reliever est indépendant des banques grâce à l'open banking — pas d'accord inter-bancaire requis
- La carte est le seul point de contrôle universel

### Négatives / Risques

- Dépendance forte à un partenaire d'émission de carte (single point of failure potentiel)
- L'open banking est soumis à des révisions réglementaires (DSP3 en cours) — risque de refactoring de B2B.001.OBK

### Dette acceptée

- Le choix du partenaire d'émission de carte n'est pas formalisé ici — question ouverte critique

## Indicateurs de gouvernance

- Niveau de criticité : Élevé (infrastructure financière du dispositif)
- Date de revue recommandée : 2027-10-24
- Indicateur de stabilité attendu : partenaire d'émission identifié, accès open banking certifié DSP2

## Traçabilité

- Atelier : Session BCM Reliever — 2026-04-24
- Participants : yremy
- Références :
  - `/strategic-vision/strategic-vision.md` — SC.006
  - ADR-BCM-FUNC-0004
