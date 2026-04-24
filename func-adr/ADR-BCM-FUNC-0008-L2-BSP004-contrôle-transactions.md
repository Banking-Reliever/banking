---
id: ADR-BCM-FUNC-0008
title: "L2 Breakdown de CAP.BSP.004 — Contrôle des Transactions"
status: Proposed
date: 2026-04-24

family: FUNC

decision_scope:
  level: L2
  zoning:
    - SERVICES_COEUR

impacted_capabilities:
  - CAP.BSP.004
  - CAP.BSP.004.AUT
  - CAP.BSP.004.ENV
  - CAP.BSP.004.ALT

impacted_events:
  - Transaction.Autorisée
  - Transaction.Refusée
  - Enveloppe.Allouée
  - Enveloppe.Consommée
  - Enveloppe.NonConsommée
  - Enveloppe.Épuisée
  - Alternative.Proposée

impacted_mappings:
  - SI
  - ORG

related_adr:
  - ADR-BCM-GOV-0001
  - ADR-BCM-URBA-0002
  - ADR-BCM-URBA-0009
  - ADR-BCM-URBA-0010
  - ADR-BCM-FUNC-0004
  - ADR-BCM-FUNC-0005

supersedes: []

tags:
  - BCM
  - L2
  - BSP
  - transactions
  - autorisation
  - enveloppes
  - temps-réel

stability_impact: Structural
---

# ADR-BCM-FUNC-0008 — L2 Breakdown de CAP.BSP.004 — Contrôle des Transactions

## Contexte

CAP.BSP.004 est le point de vérité opérationnel de Reliever : c'est là que la règle du palier s'applique concrètement, à chaque acte d'achat, en temps réel. Sans cette capacité, le dispositif est un tableau de bord sans effet.

Ce L1 concentre trois logiques complémentaires : la décision d'autorisation (temps réel, contrainte par le palier), la gestion des enveloppes budgétaires (allocation, suivi, signal de non-consommation), et l'assistance à l'achat (comparaison de prix, proposition d'alternatives).

La capacité stratégique SC.004.04 "Remontée des Événements" est ici absorbée dans l'architecture événementielle : les événements produits par BSP.004.AUT et BSP.004.ENV sont directement consommés par BSP.001.SCO et BSP.001.SIG. Il n'y a pas de L2 de "remontée" — les événements sont des faits de première classe.

## Décision

CAP.BSP.004 est décomposé en **3 capacités L2** :

| ID | Nom | Responsabilité |
|----|-----|----------------|
| CAP.BSP.004.AUT | Autorisation à l'Achat | Décider en temps réel d'autoriser ou refuser une transaction en appliquant les règles du palier courant |
| CAP.BSP.004.ENV | Gestion des Enveloppes | Allouer, suivre et ajuster les budgets par catégorie et par période ; détecter et émettre le signal d'enveloppe non consommée |
| CAP.BSP.004.ALT | Comparaison & Alternatives | Proposer des alternatives de prix ou de produits au moment de l'achat pour aider le bénéficiaire à rester dans son enveloppe |

### Événements métier par L2

| L2 | Événements produits | Événements consommés |
|----|---------------------|----------------------|
| CAP.BSP.004.AUT | `Transaction.Autorisée`, `Transaction.Refusée` | `Palier.FranchiHausse` (BSP.001.PAL), `Palier.Rétrogradé` (BSP.001.PAL), `Palier.Override.Appliqué` (BSP.001.PAL) — pour mettre à jour les règles actives |
| CAP.BSP.004.ENV | `Enveloppe.Allouée`, `Enveloppe.Consommée`, `Enveloppe.NonConsommée`, `Enveloppe.Épuisée` | `Bénéficiaire.Enrôlé` (BSP.002.ENR), `Palier.FranchiHausse` (BSP.001.PAL) — pour recalibrer les enveloppes |
| CAP.BSP.004.ALT | `Alternative.Proposée` | `Transaction.Refusée` (BSP.004.AUT) — une alternative est proposée suite à un refus |

### Points de transfert

- **BSP.001.PAL → BSP.004.AUT** : tout changement de palier met à jour les règles d'autorisation actives
- **BSP.004.AUT → BSP.001.SCO** : chaque transaction autorisée/refusée alimente le calcul du score
- **BSP.004.ENV → BSP.001.SIG** : une enveloppe non consommée en fin de période déclenche la détection de signal de rechute
- **BSP.004.AUT → BSP.004.ALT** : un refus déclenche la recherche d'alternatives pertinentes

### Règle clé — Enveloppe non consommée

`Enveloppe.NonConsommée` est émis par BSP.004.ENV en fin de période si le budget n'a pas été consommé à hauteur d'un seuil minimal. Ce signal est counter-intuitif (non-dépense = signal négatif) et doit être documenté explicitement. La logique de qualification reste dans BSP.001.SIG.

### Critères vérifiables

- BSP.004.AUT répond en temps réel (SLA < 500ms) — contrainte technique à respecter lors du mapping SI
- Chaque L2 produit au moins un événement métier (ADR-BCM-URBA-0009)
- BSP.004.ENV est le seul producteur de `Enveloppe.NonConsommée`

## Justification

La séparation AUT / ENV / ALT reflète des logiques métier et des contraintes de performance distinctes. L'autorisation est temps réel et contrainte par la latence du réseau de paiement. La gestion des enveloppes est périodique et batch en partie. Les alternatives sont un service d'enrichissement asynchrone qui ne doit pas bloquer l'autorisation.

### Alternatives considérées

- **AUT + ENV fusionnés** — rejeté car l'autorisation est temps réel avec des contraintes de SLA strictes (réseau de paiement) ; la gestion des enveloppes a un cycle de vie différent (périodique, batch) ; les confondre créerait un L2 avec des contraintes de performance incompatibles
- **ALT dans CAP.CAN.001** — rejeté car la logique de comparaison de prix est une règle métier (quelles alternatives sont pertinentes pour quel palier) qui appartient au COEUR, même si son affichage appartient au CANAL

## Impacts sur la BCM

### Structure

- 3 L2 créés sous CAP.BSP.004
- Aucun L3 nécessaire

### Événements

- 7 événements métier définis
- `Transaction.Autorisée` et `Transaction.Refusée` sont les événements les plus fréquents du système — volume à anticiper dans l'architecture

### Mapping SI / Data / Org

- **SI** : BSP.004.AUT dépend de CAP.B2B.001.CRT (règles de la carte dédiée) et CAP.REF.001.PAL (définition des paliers)
- **ORG** : owner recommandé : équipe "Transactions & Paiements"

## Conséquences

### Positives

- Le moment de vérité (acte d'achat) est modélisé avec précision
- La séparation AUT/ENV/ALT permet une évolution indépendante des trois logiques

### Négatives / Risques

- La latence de BSP.004.AUT est critique : toute dépendance synchrone vers d'autres L2 peut dégrader l'expérience au point de vente
- BSP.004.ALT nécessite des données de prix en temps réel — dépendance vers un flux externe à modéliser dans CAP.B2B.001

### Dette acceptée

- Le modèle de comparaison de prix (sources, fréquence de mise à jour) n'est pas modélisé ici

## Indicateurs de gouvernance

- Niveau de criticité : Élevé (point de vérité opérationnel)
- Date de revue recommandée : 2027-10-24
- Indicateur de stabilité attendu : SLA de BSP.004.AUT documenté et mesuré

## Traçabilité

- Atelier : Session BCM Reliever — 2026-04-24
- Participants : yremy
- Références :
  - `/strategic-vision/strategic-vision.md` — SC.004
  - ADR-BCM-FUNC-0004, ADR-BCM-FUNC-0005
