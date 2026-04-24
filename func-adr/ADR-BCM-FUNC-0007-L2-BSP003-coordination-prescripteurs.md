---
id: ADR-BCM-FUNC-0007
title: "L2 Breakdown de CAP.BSP.003 — Coordination des Prescripteurs"
status: Proposed
date: 2026-04-24

family: FUNC

decision_scope:
  level: L2
  zoning:
    - SERVICES_COEUR

impacted_capabilities:
  - CAP.BSP.003
  - CAP.BSP.003.ROL
  - CAP.BSP.003.NOT
  - CAP.BSP.003.COD

impacted_events:
  - PrescripteurRole.Attribué
  - PrescripteurRole.Révoqué
  - Prescripteur.Alerté
  - Override.DemandéParPrescripteur
  - Override.CoValidé
  - Override.Refusé

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
  - BSP
  - prescripteurs
  - coordination
  - multi-acteurs

stability_impact: Moderate
---

# ADR-BCM-FUNC-0007 — L2 Breakdown de CAP.BSP.003 — Coordination des Prescripteurs

## Contexte

CAP.BSP.003 gère la logique de coordination entre les trois types de prescripteurs (banque, psychiatre, assistant social) agissant sur un même bénéficiaire. Ces acteurs ont des natures hétérogènes (financière, médicale, sociale), des droits différenciés, et peuvent être amenés à co-décider d'un override de palier.

La distinction clé avec CAP.CAN.002 (Portail Prescripteur) : CAP.BSP.003 porte les règles métier de coordination (qui peut voir quoi, qui peut décider quoi, comment se coordonner) — CAP.CAN.002 porte l'exposition UX de ces règles. Cette séparation est exigée par ADR-BCM-URBA-0001.

## Décision

CAP.BSP.003 est décomposé en **3 capacités L2** :

| ID | Nom | Responsabilité |
|----|-----|----------------|
| CAP.BSP.003.ROL | Gestion des Rôles & Droits | Définir et appliquer les périmètres de visibilité et d'action différenciés par type de prescripteur |
| CAP.BSP.003.NOT | Alertes & Notifications | Émettre les alertes vers les prescripteurs concernés lors des événements significatifs — rechute, palier franchi, contournement détecté |
| CAP.BSP.003.COD | Co-décision | Orchestrer la coordination multi-prescripteurs pour valider ou refuser un override de palier sur un même bénéficiaire |

### Événements métier par L2

| L2 | Événements produits | Événements consommés |
|----|---------------------|----------------------|
| CAP.BSP.003.ROL | `PrescripteurRole.Attribué`, `PrescripteurRole.Révoqué` | `Bénéficiaire.Enrôlé` (BSP.002.ENR) |
| CAP.BSP.003.NOT | `Prescripteur.Alerté` | `Signal.Rechute.Détecté` (BSP.001.SIG), `Palier.FranchiHausse` (BSP.001.PAL), `Palier.Rétrogradé` (BSP.001.PAL), `Enveloppe.NonConsommée` (BSP.004.ENV) |
| CAP.BSP.003.COD | `Override.DemandéParPrescripteur`, `Override.CoValidé`, `Override.Refusé` | `OverrideUX.Déclenché` (CAN.002.ACT) |

### Points de transfert

- **BSP.003.COD → BSP.001.PAL** : un override validé déclenche une transition de palier forcée
- **BSP.001.SIG / PAL → BSP.003.NOT** : les événements significatifs du core domain déclenchent les alertes prescripteurs
- **CAN.002.ACT → BSP.003.COD** : l'action UX du prescripteur sur le portail déclenche le processus de co-décision COEUR

### Règle de gouvernance des données

La visibilité croisée entre prescripteurs est contrainte par CAP.SUP.001.CON :
- La banque ne voit pas les données médicales ou sociales
- Le psychiatre ne voit que les données comportementales nécessaires à son suivi clinique
- L'assistant social a une vue sociale et budgétaire, pas financière détaillée

Ces règles sont définies dans CAP.BSP.003.ROL et enforced par CAP.SUP.001.

### Critères vérifiables

- Chaque L2 produit au moins un événement métier (ADR-BCM-URBA-0009)
- `Override.DemandéParPrescripteur` est produit exclusivement par BSP.003.COD et consommé exclusivement par BSP.001.PAL

## Justification

La séparation ROL / NOT / COD reflète trois logiques distinctes : la gouvernance des droits (statique, rarement modifiée), les notifications (réactives, haute fréquence), et la co-décision (événementielle, nécessitant une orchestration multi-parties). Les confondre créerait un L2 trop large avec des cycles de vie et des responsabilités incompatibles.

### Alternatives considérées

- **NOT absorbé dans COD** — rejeté car les notifications sont des événements unilatéraux (information) ; la co-décision implique un workflow multi-parties avec validation ; les confondre mélange information et décision
- **ROL dans CAP.REF.001** — rejeté car les droits prescripteurs sont des règles métier dynamiques (un prescripteur peut être révoqué) ; ce ne sont pas des données de référence stables

## Impacts sur la BCM

### Structure

- 3 L2 créés sous CAP.BSP.003
- CAP.CAN.002 (Portail Prescripteur) est la face CANAL de ce L1 — dépendance explicite

### Événements

- 6 événements métier définis
- `Override.DemandéParPrescripteur` est l'événement clé de couplage avec BSP.001

### Mapping SI / Data / Org

- **SI** : dépendance vers CAP.REF.001.PRE (identité canonique des prescripteurs)
- **ORG** : owner recommandé : équipe "Relations Prescripteurs & Gouvernance"

## Conséquences

### Positives

- La logique de droits différenciés est explicitement propriété d'un L2 dédié
- La co-décision est un L2 de première classe, traçable et auditable

### Négatives / Risques

- La tension transparence/vie privée (identifiée comme risque dans la vision produit) est partiellement adressée par ROL mais nécessite une gouvernance fine avec SUP.001.CON

### Dette acceptée

- Les règles précises de visibilité par rôle (que voit exactement un psychiatre vs une banque) ne sont pas modélisées ici — à formaliser dans les spécifications de CAP.BSP.003.ROL

## Indicateurs de gouvernance

- Niveau de criticité : Élevé (tension dignité/contrôle et vie privée)
- Date de revue recommandée : 2027-10-24
- Indicateur de stabilité attendu : règles de visibilité par rôle documentées et testables

## Traçabilité

- Atelier : Session BCM Reliever — 2026-04-24
- Participants : yremy
- Références :
  - `/strategic-vision/strategic-vision.md` — SC.003
  - ADR-BCM-FUNC-0004
