---
id: ADR-BCM-FUNC-0005
title: "L2 Breakdown de CAP.BSP.001 — Remédiation Comportementale"
status: Proposed
date: 2026-04-24

family: FUNC

decision_scope:
  level: L2
  zoning:
    - SERVICES_COEUR

impacted_capabilities:
  - CAP.BSP.001
  - CAP.BSP.001.SCO
  - CAP.BSP.001.PAL
  - CAP.BSP.001.SIG
  - CAP.BSP.001.ARB

impacted_events:
  - ScoreComportemental.Recalculé
  - ScoreComportemental.SeuilAtteint
  - Palier.FranchiHausse
  - Palier.Rétrogradé
  - Palier.Override.Appliqué
  - Signal.Rechute.Détecté
  - Signal.Progression.Détecté
  - Arbitrage.Override.Validé
  - Arbitrage.AlgorithmeRéaffirmé

impacted_mappings:
  - SI
  - ORG

related_adr:
  - ADR-BCM-GOV-0001
  - ADR-BCM-URBA-0002
  - ADR-BCM-URBA-0007
  - ADR-BCM-URBA-0008
  - ADR-BCM-URBA-0009
  - ADR-BCM-URBA-0010
  - ADR-BCM-FUNC-0004

supersedes: []

tags:
  - BCM
  - L2
  - BSP
  - scoring
  - remédiation
  - core-domain

stability_impact: Structural
---

# ADR-BCM-FUNC-0005 — L2 Breakdown de CAP.BSP.001 — Remédiation Comportementale

## Contexte

CAP.BSP.001 est le **core domain** de Reliever (ADR-BCM-FUNC-0004). C'est la capacité différenciante : sans l'évaluation comportementale continue et le pilotage des paliers, Reliever n'est qu'une carte prépayée.

Ce L1 concentre la logique MMR-like du dispositif :
- un score calculé en continu depuis les événements d'achat
- des paliers d'autonomie avec leurs règles associées
- la détection de signaux de rechute paradoxaux (enveloppe non consommée = contournement)
- la tension entre autorité algorithmique et override prescripteur humain

Le L2 doit décomposer ces responsabilités sans créer de couplage excessif entre le calcul du score, la gestion des paliers, la détection des signaux et l'arbitrage humain/algorithme.

## Décision

CAP.BSP.001 est décomposé en **4 capacités L2** :

| ID | Nom | Responsabilité |
|----|-----|----------------|
| CAP.BSP.001.SCO | Scoring Comportemental | Calculer et mettre à jour le score du bénéficiaire à partir des événements de transaction et des signaux de contournement reçus |
| CAP.BSP.001.PAL | Gestion des Paliers | Définir les règles associées à chaque palier, piloter les transitions algorithmiques, appliquer les overrides prescripteurs |
| CAP.BSP.001.SIG | Détection des Signaux | Identifier et qualifier les signaux de rechute (enveloppe non consommée) et de progression, les transmettre au scoring |
| CAP.BSP.001.ARB | Arbitrage Algorithme / Humain | Gérer la reprise de contrôle de l'algorithme après un override, valider ou invalider la décision prescripteur dans le temps |

### Événements métier par L2

| L2 | Événements produits | Événements consommés |
|----|---------------------|----------------------|
| CAP.BSP.001.SCO | `ScoreComportemental.Recalculé`, `ScoreComportemental.SeuilAtteint` | `Transaction.Autorisée` (BSP.004.AUT), `Transaction.Refusée` (BSP.004.AUT), `Signal.Rechute.Détecté` (BSP.001.SIG), `Signal.Progression.Détecté` (BSP.001.SIG) |
| CAP.BSP.001.PAL | `Palier.FranchiHausse`, `Palier.Rétrogradé`, `Palier.Override.Appliqué` | `ScoreComportemental.SeuilAtteint` (BSP.001.SCO), `Override.DemandéParPrescripteur` (BSP.003.COD) |
| CAP.BSP.001.SIG | `Signal.Rechute.Détecté`, `Signal.Progression.Détecté` | `Enveloppe.NonConsommée` (BSP.004.ENV), `Transaction.Autorisée` (BSP.004.AUT) |
| CAP.BSP.001.ARB | `Arbitrage.Override.Validé`, `Arbitrage.AlgorithmeRéaffirmé` | `Palier.Override.Appliqué` (BSP.001.PAL), `ScoreComportemental.Recalculé` (BSP.001.SCO) |

### Points de transfert

- **BSP.004.AUT → BSP.001.SCO** : chaque transaction autorisée ou refusée déclenche un recalcul du score
- **BSP.004.ENV → BSP.001.SIG** : une enveloppe non consommée en fin de période déclenche la détection de signal de rechute
- **BSP.001.SIG → BSP.001.SCO** : les signaux qualifiés alimentent le scoring
- **BSP.001.SCO → BSP.001.PAL** : un seuil de score atteint déclenche une transition de palier candidate
- **BSP.003.COD → BSP.001.PAL** : un override demandé par prescripteur force une transition de palier
- **BSP.001.PAL → BSP.001.ARB** : tout override appliqué ouvre une fenêtre d'arbitrage algorithme/humain

### Règle clé — Enveloppe non consommée

Un budget non dépensé en fin de période est un signal de rechute (contournement du canal contrôlé), non un signal de succès. CAP.BSP.001.SIG est responsable exclusive de cette qualification contre-intuitive.

### Critères vérifiables

- Chaque L2 produit au moins un événement métier (ADR-BCM-URBA-0009)
- Aucun L2 ne souscrit à ses propres événements
- CAP.BSP.001.ARB ne produit pas d'événement de palier : il valide ou invalide, c'est CAP.BSP.001.PAL qui reste propriétaire de l'état du palier

## Justification

La séparation SCO / PAL / SIG / ARB évite de concentrer toute la logique dans un monolithe comportemental. Chaque L2 a un cycle de vie distinct :
- SCO : continu, déclenché par chaque transaction
- PAL : déclenché par seuil ou override
- SIG : déclenché par fin de période ou pattern d'achat
- ARB : déclenché uniquement lors d'un override prescripteur

### Alternatives considérées

- **SCO + PAL fusionnés** — rejeté car le calcul du score et la décision de transition de palier ont des rythmes et des propriétaires différents ; les confondre crée un couplage fort entre la logique analytique et les règles métier de palier
- **SIG absorbé dans SCO** — rejeté car la logique de détection du contournement (enveloppe non consommée) est une règle métier distincte, contre-intuitive, qui mérite une responsabilité dédiée et traçable
- **ARB absent (algorithme seul)** — rejeté car la capacité d'override prescripteur est une exigence métier explicite ; son absence rendrait le dispositif rigide et incompatible avec le jugement clinique

## Impacts sur la BCM

### Structure

- 4 L2 créés sous CAP.BSP.001
- Aucun L3 nécessaire à ce stade

### Événements

- 9 événements métier définis, tous rattachés à une L2 émettrice unique (ADR-BCM-URBA-0010)
- Flux événementiel principal : BSP.004 → BSP.001.SIG / SCO → BSP.001.PAL → BSP.001.ARB

### Mapping SI / Data / Org

- **SI** : CAP.BSP.001 constitue le bounded context central de Reliever — son implémentation doit être isolée des autres contextes
- **ORG** : owner recommandé : équipe "Remédiation" (data scientists + domain experts)

## Conséquences

### Positives

- Core domain clairement isolé et décomposé
- Flux événementiel traçable depuis la transaction jusqu'à la transition de palier
- La règle de rechute (enveloppe non consommée) est explicitement propriété de SIG

### Négatives / Risques

- BSP.001.ARB est un L2 à faible volume d'événements (déclenché uniquement sur override) — risque de sous-investissement ; surveiller en revue de stabilité

### Dette acceptée

- Les seuils précis de transition de palier (critères du scoring) ne sont pas modélisés dans cet ADR — à formaliser dans les spécifications du modèle comportemental

## Indicateurs de gouvernance

- Niveau de criticité : Élevé (core domain)
- Date de revue recommandée : 2027-10-24
- Indicateur de stabilité attendu : 4 L2 présents, chacun avec au moins un événement métier documenté et une équipe owner identifiée

## Traçabilité

- Atelier : Session BCM Reliever — 2026-04-24
- Participants : yremy
- Références :
  - `/strategic-vision/strategic-vision.md` — SC.001
  - ADR-BCM-FUNC-0004
  - ADR-BCM-URBA-0009 — Définition complète d'une capacité
  - ADR-BCM-URBA-0010 — L2 pivot
