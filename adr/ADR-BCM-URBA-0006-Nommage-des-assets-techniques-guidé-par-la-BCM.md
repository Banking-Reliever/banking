---
id: ADR-BCM-URBA-0006
title: "Nommage des assets techniques guidé par la BCM (ancrage L2)"
status: Suspended
date: 2026-02-26
suspension_date: 2026-03-10
suspension_reason: >
  Reflète un niveau de maturité non présent encore dans l'entreprise.
  Risque d'amener plus de confusion que d'éclaircissements pour le moment.

family: URBA

decision_scope:
  level: Cross-Level
  zoning:
    - PILOTAGE
    - SERVICES_COEUR
    - SUPPORT
    - REFERENTIEL
    - ECHANGE_B2B
    - CANAL
    - DATA_ANALYTIQUE

impacted_capabilities: []   # transversal
impacted_events: []         # transversal
impacted_mappings:
  - SI
  - DATA
  - ORG

related_adr:
  - ADR-BCM-GOV-0001  # hiérarchie GOV → URBA → FUNC
  - ADR-BCM-URBA-0001  # zoning TOGAF étendu
  - ADR-BCM-URBA-0002  # 3 niveaux
  - ADR-BCM-URBA-0003  # 1 capa = 1 responsabilité
  - ADR-BCM-URBA-0005  # contrats guidés par BCM (APIs/événements)

supersedes: []
tags:
  - naming
  - capacité
  - events
  - topic
  - api
  - database
stability_impact: Structural
---

# ADR-BCM-URBA-0006 — Nommage des assets techniques guidé par la BCM (ancrage L2)

## Contexte

Le SI comporte de nombreux assets techniques (topics d’événements, APIs, bases, schémas, composants applicatifs, fonctions serverless, buckets…).
Sans convention commune, on observe :
- une difficulté à rattacher un asset à une responsabilité métier,
- une hétérogénéité de nommage entre équipes,
- une faible traçabilité entre urbanisation fonctionnelle et implémentation technique.

La BCM est le référentiel de responsabilités métier stable, et le niveau L2 est le pivot d’arbitrage d’urbanisation (stabilité vs précision).

## Décision

### 1) Ancrage obligatoire sur une capacité L2

Tout asset technique doit être rattaché à UNE capacité d’ownership unique, au niveau L2.

- Le rattachement est matérialisé par l’inclusion de l’ID L2 dans le nom de l’asset.
- Le rattachement ne doit pas dépendre d’un libellé humain : uniquement d’un identifiant stable.

### 2) Convention de nommage

Le pattern standard est :

`<capability_l2_id>.<asset_type>.<asset_name>[.<qualifier>...]`

- `<capability_l2_id>` : identifiant stable (ex : `bsp-005-sin-03`)
- `<asset_type>` : `topic | evt | api | bff | spa | svc | fn | db | schema | bucket | queue | job | blob ...`
- `<asset_name>` : nom métier court et stable (kebab-case)
- `<qualifier>` : version majeure / variante (`v1`, `dlq`, `public`, `private`…)

Règles :
- kebab-case `[a-z0-9-]`
- séparateur hiérarchique `.`
- pas d’accents / pas d’espaces

Conventions BCM complémentaires (obligatoires pour les assets fonctionnels) :
- `OBJ.<ZONE>.<L1>.<CODE>` pour les objets métier
- `RES.<ZONE>.<L1>.<CODE>` pour les ressources opérationnelles
- `ABO.METIER.<ZONE>.<L1>.<CODE>` pour les abonnements métier
- `ABO.RESSOURCE.<ZONE>.<L1>.<CODE>` pour les abonnements ressource

Ces conventions sont distinctes :
- un objet métier (`OBJ.*`) représente une abstraction fonctionnelle,
- une ressource (`RES.*`) représente un artefact opérationnel implémentant cet objet métier.

### 3) Cas particuliers

- Si un asset est réellement transverse, son ownership doit être placé dans une capacité transverse (Support, Referentiel, DATA_ANALYTIQUE, ECHANGE_B2B, Canal) conformément au zoning.
- Les composants “fourre-tout” (multi-capabilities) sont considérés comme une dette de découpage : l’ownership doit rester unique, et un plan de découpe est à envisager.

### 4) Registre de mapping

En complément du nommage, un registre de mapping est maintenu (ex : `bcm/mappings/assets.yaml`) pour décrire :
- owner capacité L2
- équipe responsable
- environnement(s)
- techno / plateforme
- criticité / SLA
- liens vers repo / IaC / runbooks

Le registre constitue la source d’information exhaustive.
Le nom ne doit pas être surchargé pour remplacer un registre.

## Justification

- Le niveau L2 est le bon niveau de décision d’urbanisation : assez précis pour guider le SI, assez stable pour éviter des renamings fréquents.
- La règle “1 capacité = 1 responsabilité” garantit un ownership clair et réduit les ambiguïtés.
- L’approche “contrats guidés par la BCM” assure la cohérence entre modèle et interfaces (APIs/événements).

### Alternatives considérées

- Nommage libre par équipe — rejeté car hétérogénéité et perte de traçabilité.
- Nommage ancré sur l'application plutôt que la capacité — rejeté car couplage SI physique.
- Nommage au niveau L3 — rejeté car trop instable (L3 est transitoire).

## Impacts sur la BCM

### Structure

- Nécessité de disposer d'identifiants L2 stables (non dépendants des libellés).

### Événements (si applicable)

- Les conventions d'événements/topics deviennent cohérentes avec les capacités émettrices/consommatrices.

### Mapping SI / Data / Org

- Renforcement du mapping Capability ↔ Assets techniques via un registre dédié.

## Conséquences

### Positives
- Traçabilité immédiate asset → responsabilité (L2).
- Homogénéité de nommage inter-équipes.
- Urbanisation mesurable (capacité coverage).
- Réduction du “shadow naming” par projet.

### Négatives / Risques
- Coût initial d’adoption.
- Risque de renaming si les IDs L2 ne sont pas stabilisés rapidement.
- Risque d’ownership arbitraire si les règles “transverse vs métier” ne sont pas appliquées.

### Dette acceptée

- Certains assets legacy ne pourront pas être renommés immédiatement. Ils seront progressivement migrés lors des évolutions.

## Indicateurs de gouvernance

- Niveau de criticité : Modéré (convention de nommage).
- Date de revue recommandée : 2028-02-26.
- Indicateur de stabilité attendu : 100 % des nouveaux assets nommés selon la convention.

## Traçabilité

- Atelier : gouvernance BCM, retours projets, event storming big picture
- Participants : EA / Urbanisation
- Références : ADR-BCM-URBA-0001, ADR-BCM-URBA-0002, ADR-BCM-URBA-0003, ADR-BCM-URBA-0005