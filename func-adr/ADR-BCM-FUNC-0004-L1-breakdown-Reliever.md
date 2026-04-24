---
id: ADR-BCM-FUNC-0004
title: "L1 Breakdown des capacités IS de Reliever sur les 7 zones TOGAF"
status: Proposed
date: 2026-04-24

family: FUNC

decision_scope:
  level: L1
  zoning:
    - PILOTAGE
    - SERVICES_COEUR
    - SUPPORT
    - REFERENTIEL
    - ECHANGE_B2B
    - CANAL
    - DATA_ANALYTIQUE

impacted_capabilities:
  - CAP.BSP.001
  - CAP.BSP.002
  - CAP.BSP.003
  - CAP.BSP.004
  - CAP.CAN.001
  - CAP.CAN.002
  - CAP.B2B.001
  - CAP.SUP.001
  - CAP.REF.001
  - CAP.DAT.001
  - CAP.PIL.001

impacted_events: []
impacted_mappings:
  - SI
  - DATA
  - ORG

related_adr:
  - ADR-BCM-GOV-0001
  - ADR-BCM-URBA-0001
  - ADR-BCM-URBA-0002
  - ADR-BCM-URBA-0004
  - ADR-BCM-URBA-0009
  - ADR-BCM-URBA-0010

supersedes: []

tags:
  - BCM
  - L1
  - Reliever
  - breakdown
  - remédiation-financière

stability_impact: Structural
---

# ADR-BCM-FUNC-0004 — L1 Breakdown des capacités IS de Reliever

## Contexte

Reliever est un dispositif de remédiation financière à paliers, prescriptible par la banque, un psychiatre ou un assistant social. Il accompagne des individus financièrement fragiles depuis une assistance maximale sur les micro-décisions d'achat jusqu'à la restitution complète de leur autonomie, via une carte dédiée et un score comportemental coordonné entre prescripteurs via open banking.

Le service offer validé est :
> Reliever permet à des individus en fragilité financière de reprendre progressivement le contrôle de leur vie financière quotidienne grâce à un système de paliers d'autonomie croissante, ancré sur une carte dédiée et un score comportemental coordonné entre prescripteurs via open banking, même quand préserver leur dignité est aussi important que contraindre leurs comportements.

La carte IS L1 doit :
- Traduire 1:1 les 7 capacités stratégiques en capacités IS zonées
- Ajouter les IS L1 transverses exigés par le modèle TOGAF étendu (ADR-BCM-URBA-0001) absents de la carte stratégique
- Respecter le principe 1 capacité = 1 responsabilité (ADR-BCM-URBA-0009)
- Affecter chaque L1 à une zone parmi les 7 (ADR-BCM-URBA-0001)

## Décision

La carte IS L1 de Reliever est structurée en **11 capacités** réparties sur **6 des 7 zones TOGAF**.

### SERVICES_COEUR — Cœur de métier Reliever

| ID | Nom | Responsabilité | Source stratégique |
|----|-----|----------------|--------------------|
| CAP.BSP.001 | Remédiation Comportementale | Évaluer en continu la trajectoire financière du bénéficiaire, piloter ses paliers d'autonomie, détecter rechutes et progressions | SC.001 |
| CAP.BSP.002 | Accès & Enrôlement | Identifier les individus éligibles, orchestrer leur entrée dans le dispositif avec les prescripteurs, formaliser les conditions de prise en charge | SC.002 |
| CAP.BSP.003 | Coordination des Prescripteurs | Permettre à la banque, au psychiatre et à l'assistant social d'agir de façon coordonnée sur un même bénéficiaire, avec droits et vues différenciés | SC.003 |
| CAP.BSP.004 | Contrôle des Transactions | Appliquer les règles du palier courant à chaque acte d'achat, gérer les autorisations en temps réel, alimenter le score comportemental | SC.004 |

### CANAL — Exposition utilisateurs

| ID | Nom | Responsabilité | Source stratégique |
|----|-----|----------------|--------------------|
| CAP.CAN.001 | Parcours Bénéficiaire | Exposer au bénéficiaire la visualisation gamifiée de sa progression, l'assistance à l'achat et les notifications | SC.005 |
| CAP.CAN.002 | Portail Prescripteur | Offrir aux prescripteurs une UX adaptée à leur rôle pour consulter les situations et déclencher des actions | Transverse (exposition CANAL de SC.003) |

### ECHANGE_B2B — Écosystème financier externe

| ID | Nom | Responsabilité | Source stratégique |
|----|-----|----------------|--------------------|
| CAP.B2B.001 | Gestion de l'Instrument Financier | Émettre et piloter la carte dédiée, lier ses règles aux paliers, accéder aux données financières via open banking | SC.006 |

### SUPPORT — Fonctions transverses IS

| ID | Nom | Responsabilité | Source stratégique |
|----|-----|----------------|--------------------|
| CAP.SUP.001 | Conformité & Protection des Données | Assurer la légalité du partage de données sensibles entre acteurs hétérogènes, garantir les obligations réglementaires | SC.007 |

### REFERENTIEL — Master data partagée

| ID | Nom | Responsabilité | Source stratégique |
|----|-----|----------------|--------------------|
| CAP.REF.001 | Référentiels Communs | Porter les identités canoniques du Bénéficiaire, du Prescripteur et des définitions de Palier, consommées par toutes les zones | Transverse TOGAF |

### DATA_ANALYTIQUE — Analytique et pilotage data

| ID | Nom | Responsabilité | Source stratégique |
|----|-----|----------------|--------------------|
| CAP.DAT.001 | Analytique Comportementale | Ingérer les événements comportementaux, alimenter et améliorer le modèle analytique du score, produire les rapports programme | Transverse TOGAF |

### PILOTAGE — Gouvernance et steering

| ID | Nom | Responsabilité | Source stratégique |
|----|-----|----------------|--------------------|
| CAP.PIL.001 | Pilotage du Programme | Gouverner le programme de remédiation, mesurer son efficacité, assurer la conformité réglementaire à l'échelle | Transverse TOGAF |

### Règles de déambiguïsation

- **CAP.BSP.003** (coordination logic) ≠ **CAP.CAN.002** (portail UX prescripteur) : la logique de droits et de co-décision reste COEUR ; l'exposition reste CANAL — per ADR-BCM-URBA-0001
- **CAP.BSP.001** (scoring opérationnel temps réel) ≠ **CAP.DAT.001** (modèle analytique batch/stream) : le score transactionnel est COEUR ; l'amélioration du modèle et le reporting sont DATA_ANALYTIQUE
- **CAP.SUP.001** (conformité IS transverse) ≠ **CAP.PIL.001** (pilotage programme métier) : SUP couvre RGPD, audit, droits ; PIL couvre gouvernance, KPIs, conformité réglementaire programme

### Critères vérifiables

- Toute capacité L1 est affectée à exactement une des 7 zones TOGAF
- Aucun L1 n'est nommé d'après une application, un éditeur ou une technologie
- Chaque L1 est décomposable en L2 sans chevauchement de périmètre
- La totalité du service offer est couverte par au moins un L1

## Justification

La traduction 1:1 des 7 capacités stratégiques en IS L1 zonés garantit la traçabilité directe entre la vision business et la carte IS. Les 4 IS L1 transverses ajoutés (CAP.CAN.002, CAP.REF.001, CAP.DAT.001, CAP.PIL.001) sont exigés par le modèle TOGAF étendu (ADR-BCM-URBA-0001) : ils adressent des préoccupations IS structurantes absentes d'une carte stratégique pure.

### Alternatives considérées

- **Tout regrouper en SERVICES_COEUR** — rejeté car perd la séparation COEUR/CANAL (confusion entre logique de coordination et UX prescripteur), efface la gouvernance data, et nuit à la lisibilité d'urbanisation
- **Séparer Scoring et Paliers en deux L1 distincts** — rejeté car ils partagent le même domaine de responsabilité (remédiation comportementale) et leur couplage est inhérent au modèle MMR ; la séparation appartient au L2

## Impacts sur la BCM

### Structure

- Création de 11 capacités L1 dans 6 zones
- Zone ECHANGE_B2B couverte par 1 seul L1 (instrument financier) : acceptable à ce stade, le périmètre open banking est délimité
- Chaque L1 sera décomposé en L2 par les ADRs FUNC-0005 à FUNC-0015

### Événements

- Les événements métier seront définis au niveau L2 (ADR-BCM-URBA-0009)

### Mapping SI / Data / Org

- **SI** : chaque L1 constitue un domaine fonctionnel auquel les composants applicatifs seront mappés
- **ORG** : chaque L1 a un propriétaire métier à identifier lors de la phase d'organisation
- **DATA** : les flux inter-L1 seront formalisés lors des ADRs L2

## Conséquences

### Positives

- Carte IS lisible, zonée, traçable depuis le service offer
- Séparation claire COEUR / CANAL / B2B / SUPPORT / REF / DAT / PIL
- Base stable pour les 11 ADRs L2 suivants

### Négatives / Risques

- 11 L1 est dans la borne haute de lisibilité (ADR-BCM-URBA-0004 recommande ~10 max par zone) — acceptable car répartis sur 6 zones, pas 1 seule
- La zone PILOTAGE ne contient qu'un seul L1 : à surveiller en revue de stabilité

### Dette acceptée

- Les owners organisationnels par L1 ne sont pas encore identifiés — à compléter lors de la phase d'organisation

## Indicateurs de gouvernance

- Niveau de criticité : Élevé (décision structurante Reliever)
- Date de revue recommandée : 2028-04-24
- Indicateur de stabilité attendu : 11 L1 présents dans capabilities.yaml avec zone et owner renseignés

## Traçabilité

- Atelier : Session BCM Reliever — 2026-04-24
- Participants : yremy
- Références :
  - `/product-vision/product.md`
  - `/strategic-vision/strategic-vision.md`
  - ADR-BCM-URBA-0001 — Zoning TOGAF étendu
  - ADR-BCM-URBA-0009 — Définition complète d'une capacité
  - ADR-BCM-URBA-0010 — L2 pivot d'urbanisation
