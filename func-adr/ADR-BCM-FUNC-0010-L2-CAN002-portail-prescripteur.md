---
id: ADR-BCM-FUNC-0010
title: "L2 Breakdown de CAP.CAN.002 — Portail Prescripteur"
status: Proposed
date: 2026-04-24

family: FUNC

decision_scope:
  level: L2
  zoning:
    - CANAL

impacted_capabilities:
  - CAP.CAN.002
  - CAP.CAN.002.VUE
  - CAP.CAN.002.ACT
  - CAP.CAN.002.RAP

impacted_events:
  - DossierBénéficiaire.Consulté
  - OverrideUX.Déclenché
  - Rapport.Généré

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
  - CANAL
  - prescripteurs
  - portail
  - UX

stability_impact: Moderate
---

# ADR-BCM-FUNC-0010 — L2 Breakdown de CAP.CAN.002 — Portail Prescripteur

## Contexte

CAP.CAN.002 est l'exposition CANAL du dispositif vers les prescripteurs (banque, psychiatre, assistant social). Elle complète CAP.BSP.003 (Coordination des Prescripteurs) qui porte la logique métier ; CAP.CAN.002 porte l'interface par laquelle les prescripteurs exercent leurs droits.

Per ADR-BCM-URBA-0001, la logique de coordination (règles, droits, co-décision) reste dans SERVICES_COEUR (BSP.003) ; l'UX est ici dans CANAL.

Chaque type de prescripteur voit une interface adaptée à son rôle, filtrée par les droits définis dans CAP.BSP.003.ROL. Le portail est la surface de contact entre le monde médico-social et le dispositif financier.

## Décision

CAP.CAN.002 est décomposé en **3 capacités L2** :

| ID | Nom | Responsabilité |
|----|-----|----------------|
| CAP.CAN.002.VUE | Vue Bénéficiaire | Exposer à chaque prescripteur une vue adaptée à son rôle sur la situation et la trajectoire du bénéficiaire |
| CAP.CAN.002.ACT | Actions Prescripteur | Fournir l'UX permettant de déclencher un override, valider une co-décision, ou annoter une situation bénéficiaire |
| CAP.CAN.002.RAP | Rapports & Exports | Permettre aux prescripteurs de générer des rapports de suivi adaptés à leur contexte (rapport clinique, rapport social, rapport bancaire) |

### Événements métier par L2

| L2 | Événements produits | Événements consommés |
|----|---------------------|----------------------|
| CAP.CAN.002.VUE | `DossierBénéficiaire.Consulté` | `ScoreComportemental.Recalculé` (BSP.001.SCO), `Palier.FranchiHausse` (BSP.001.PAL), `Signal.Rechute.Détecté` (BSP.001.SIG), `PrescripteurRole.Attribué` (BSP.003.ROL) |
| CAP.CAN.002.ACT | `OverrideUX.Déclenché` | `Override.CoValidé` (BSP.003.COD), `Override.Refusé` (BSP.003.COD) |
| CAP.CAN.002.RAP | `Rapport.Généré` | `DossierBénéficiaire.Consulté` (CAN.002.VUE) |

### Règle de visibilité filtrée

CAP.CAN.002.VUE applique les filtres de droits définis par CAP.BSP.003.ROL : un psychiatre ne voit pas les détails de transaction bancaire ; une banque ne voit pas les annotations cliniques. Cette règle est enforced au niveau CANAL (affichage) ET au niveau COEUR (données transmises).

### Critères vérifiables

- Chaque L2 produit au moins un événement métier (ADR-BCM-URBA-0009)
- `OverrideUX.Déclenché` est produit exclusivement par CAN.002.ACT et consommé exclusivement par BSP.003.COD

## Justification

La séparation VUE / ACT / RAP reflète trois modes d'interaction prescripteur distincts : la consultation (lecture), l'action (écriture/décision), et le reporting (export). Ces trois modes ont des droits, des fréquences et des contraintes différents.

### Alternatives considérées

- **VUE + ACT fusionnés** — rejeté car certains prescripteurs ont un droit de lecture sans droit d'action (ex : un assistant social peut consulter sans pouvoir déclencher un override) ; la séparation permet une gouvernance fine des droits
- **RAP dans CAP.DAT.001** — rejeté car les rapports prescripteurs sont des exports opérationnels adaptés à chaque rôle métier ; les rapports programme globaux appartiennent à DATA_ANALYTIQUE, mais les rapports individuels sont une responsabilité CANAL

## Impacts sur la BCM

### Structure

- 3 L2 créés sous CAP.CAN.002
- Dépendance forte vers CAP.BSP.003 (logique) et CAP.REF.001.PRE (identité prescripteurs)

### Mapping SI / Data / Org

- **SI** : portail web ou application desktop pour les prescripteurs professionnels
- **ORG** : owner recommandé : équipe "Expérience Prescripteurs"

## Conséquences

### Positives

- L'UX prescripteur est une responsabilité explicite, pas une fonction cachée dans le COEUR
- La visibilité filtrée par rôle est tracée à deux niveaux (COEUR + CANAL)

### Négatives / Risques

- La multiplicité des types de prescripteurs (banque, psychiatre, assistant social) peut complexifier le développement de CAP.CAN.002.VUE — surveiller le scope creep UX

### Dette acceptée

- Les maquettes et règles UX spécifiques à chaque type de prescripteur ne sont pas modélisées ici

## Indicateurs de gouvernance

- Niveau de criticité : Modéré
- Date de revue recommandée : 2028-04-24
- Indicateur de stabilité attendu : 3 profils prescripteurs (banque, psychiatre, assistant social) avec vues distinctes documentées

## Traçabilité

- Atelier : Session BCM Reliever — 2026-04-24
- Participants : yremy
- Références :
  - `/strategic-vision/strategic-vision.md` — SC.003
  - ADR-BCM-FUNC-0007
