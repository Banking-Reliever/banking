---
id: ADR-BCM-FUNC-0009
title: "L2 Breakdown de CAP.CAN.001 — Parcours Bénéficiaire"
status: Proposed
date: 2026-04-24

family: FUNC

decision_scope:
  level: L2
  zoning:
    - CANAL

impacted_capabilities:
  - CAP.CAN.001
  - CAP.CAN.001.TAB
  - CAP.CAN.001.ACH
  - CAP.CAN.001.NOT

impacted_events:
  - TableauDeBord.Consulté
  - ScanProduit.Lancé
  - Alternative.Acceptée
  - NotificationBénéficiaire.Émise

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
  - ADR-BCM-FUNC-0005

supersedes: []

tags:
  - BCM
  - L2
  - CANAL
  - UX
  - bénéficiaire
  - gamification

stability_impact: Moderate
---

# ADR-BCM-FUNC-0009 — L2 Breakdown de CAP.CAN.001 — Parcours Bénéficiaire

## Contexte

CAP.CAN.001 est l'exposition CANAL du dispositif Reliever vers le bénéficiaire. C'est le point de contact direct avec l'utilisateur final — celui dont la dignité est la première contrainte fonctionnelle du service offer.

Ce L1 répond à la tension contrôle/dignité identifiée comme la plus critique dans la vision produit : l'expérience bénéficiaire doit être perçue comme un accompagnement motivant (modèle Strava), non comme une surveillance punitive. La gamification n'est pas un ornement — c'est une condition fonctionnelle.

Per ADR-BCM-URBA-0001, CAP.CAN.001 porte l'UX et l'exposition ; les règles métier (score, paliers, alternatives) restent dans SERVICES_COEUR.

## Décision

CAP.CAN.001 est décomposé en **3 capacités L2** :

| ID | Nom | Responsabilité |
|----|-----|----------------|
| CAP.CAN.001.TAB | Tableau de Progression | Exposer au bénéficiaire la visualisation gamifiée de sa progression, son budget disponible et sa trajectoire par palier |
| CAP.CAN.001.ACH | Assistance à l'Achat | Fournir l'UX au moment de l'achat — scan de produit, affichage de l'alternative proposée par BSP.004.ALT, feedback d'autorisation ou de refus |
| CAP.CAN.001.NOT | Notifications Bénéficiaire | Émettre les notifications push/SMS vers le bénéficiaire lors des événements clés — refus, palier franchi, budget proche, rechute |

### Événements métier par L2

| L2 | Événements produits | Événements consommés |
|----|---------------------|----------------------|
| CAP.CAN.001.TAB | `TableauDeBord.Consulté` | `ScoreComportemental.Recalculé` (BSP.001.SCO), `Palier.FranchiHausse` (BSP.001.PAL), `Enveloppe.Consommée` (BSP.004.ENV) |
| CAP.CAN.001.ACH | `ScanProduit.Lancé`, `Alternative.Acceptée` | `Transaction.Autorisée` (BSP.004.AUT), `Transaction.Refusée` (BSP.004.AUT), `Alternative.Proposée` (BSP.004.ALT) |
| CAP.CAN.001.NOT | `NotificationBénéficiaire.Émise` | `Transaction.Refusée` (BSP.004.AUT), `Palier.FranchiHausse` (BSP.001.PAL), `Enveloppe.Épuisée` (BSP.004.ENV), `Bénéficiaire.TransféréVersAppliStandard` (BSP.002.SOR) |

### Règle de dignité

CAP.CAN.001.TAB doit exposer la progression positivement (ce qui a été accompli) avant les restrictions (ce qui est interdit). Le refus d'achat doit être accompagné d'une explication motivée et d'une alternative quand disponible. Ces règles UX sont la responsabilité de ce L2, pas du COEUR.

### Critères vérifiables

- Chaque L2 produit au moins un événement métier (ADR-BCM-URBA-0009)
- CAP.CAN.001 ne contient aucune règle métier de palier ou de scoring — il consomme des événements et affiche des états

## Justification

La séparation TAB / ACH / NOT reflète trois moments d'interaction distincts : la consultation proactive (tableau de bord), l'interaction temps réel (acte d'achat), et la communication push (notifications). Ces trois moments ont des contraintes UX et des cycles de vie différents.

### Alternatives considérées

- **TAB + NOT fusionnés** — rejeté car le tableau de bord est une consultation pull (à l'initiative de l'utilisateur) ; les notifications sont push (à l'initiative du système) ; confondre ces deux logiques d'interaction nuit à la clarté de responsabilité
- **ACH dans BSP.004.ALT** — rejeté car l'UX de scan et d'affichage est une responsabilité CANAL (présentation, feedback, accessibilité) ; la logique de suggestion reste COEUR

## Impacts sur la BCM

### Structure

- 3 L2 créés sous CAP.CAN.001
- Consomme intensément des événements de BSP.001, BSP.002, BSP.004

### Mapping SI / Data / Org

- **SI** : CAP.CAN.001 est typiquement une application mobile ou webapp — mapping SI vers BSP.001, BSP.004 via API ou souscription événementielle
- **ORG** : owner recommandé : équipe "Expérience Bénéficiaire"

## Conséquences

### Positives

- La tension dignité/contrôle est adressée par une capacité CANAL dédiée, avec des règles UX explicites
- L'assistance à l'achat est un L2 de première classe — pas un afterthought

### Négatives / Risques

- CAP.CAN.001.ACH est dépendant de la latence de BSP.004.AUT — toute lenteur d'autorisation se traduit en friction UX au point de vente

### Dette acceptée

- Les règles de gamification précises (badges, jalons, comparaisons sociales éventuelles) ne sont pas modélisées ici

## Indicateurs de gouvernance

- Niveau de criticité : Élevé (tension dignité/contrôle)
- Date de revue recommandée : 2028-04-24
- Indicateur de stabilité attendu : règles UX de dignité documentées et testables (test utilisateur)

## Traçabilité

- Atelier : Session BCM Reliever — 2026-04-24
- Participants : yremy
- Références :
  - `/strategic-vision/strategic-vision.md` — SC.005
  - ADR-BCM-FUNC-0004, ADR-BCM-FUNC-0008
