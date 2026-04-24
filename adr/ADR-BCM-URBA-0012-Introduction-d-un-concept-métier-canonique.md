---
id: ADR-BCM-URBA-0012
title: "Introduction d’un concept métier canonique"
status: Proposed
date: 2026-03-19

family: URBA

decision_scope:
  level: Cross-Level
  zoning:
    - SERVICES_COEUR
    - SUPPORT
    - REFERENTIEL
    - ECHANGE_B2B
    - DATA_ANALYTIQUE

impacted_capabilities: []
impacted_events: []
impacted_mappings:
  - SI
  - DATA
  - ORG

related_adr:
  - ADR-BCM-GOV-0001
  - ADR-BCM-URBA-0008
  - ADR-BCM-URBA-0009
  - ADR-BCM-URBA-0010

supersedes: []

tags:
  - BCM
  - URBA
  - concept-metier
  - canonique
  - objet-metier
  - ressource

stability_impact: Structural
---

# ADR-BCM-URBA-0012 — Introduction d’un concept métier canonique

## Contexte

Le cadre BCM distingue aujourd’hui :
- les **capacités L2**, qui portent les responsabilités métier ;
- les **objets métiers**, rattachés à une responsabilité ;
- les **ressources**, qui déclinent ces objets pour les besoins opérationnels.

Les travaux récents ont mis en évidence un besoin complémentaire : disposer d’un niveau plus transverse pour désigner simplement des notions comme **Déclaration de sinistre** ou **Dossier sinistre**, sans pour autant fusionner dans un même objet métier des responsabilités différentes.

En effet, un objet métier unique partagé entre plusieurs capacités L2 conduirait à :
- brouiller les responsabilités ;
- renforcer les couplages ;
- créer des objets trop larges ou partiellement remplis ;
- confondre modélisation métier et détail d’implémentation technique.

## Décision

Il est introduit un niveau supplémentaire : le **concept métier ou modèle canonique**.

Le **concept métier ou modèle canonique** :
- représente une notion métier transverse et stable ;
- sert de référence sémantique commune ;
- ne porte pas à lui seul de responsabilité opérationnelle ;
- ne se substitue ni à l’**objet métier**, ni à la **ressource**.

Le cadre BCM est donc lu selon la hiérarchie suivante :

```text
Concept métier ou modèle canonique
        ↓
Objet métier
        ↓
Ressource
```

## Règles

1. Un **concept métier ou modèle canonique** peut être décliné en plusieurs **objets métiers**.
2. Chaque **objet métier** reste rattaché à une responsabilité explicite portée par une capacité L2.
3. Chaque **objet métier** peut être décliné en une ou plusieurs **ressources** selon les besoins opérationnels.
4. Un **concept métier ou modèle canonique** ne doit pas être utilisé directement comme objet d’échange ou d’implémentation.
5. Un détail technique de payload ou de sérialisation ne justifie pas, à lui seul, la fusion de plusieurs objets métiers.

## Exemple
| Concept métier canonique | Objet métier                      | Ressource                                      |
| ------------------------ | --------------------------------- | ---------------------------------------------- |
| Déclaration de sinistre  | Déclaration de sinistre reçue     | Déclaration de sinistre reçue                  |
| ^^                       | Déclaration sinistre              | Déclaration sinistre dégâts des eaux           |
| ^^                       | ^^                                | Déclaration sinistre incendie                  |
| ^^                       | ^^                                | Déclaration sinistre vol                       |


## Justification

Cette décision permet :

* de conserver un langage métier transverse commun ;
* de préserver le découpage par responsabilités L2 ;
* d’éviter la création d’objets métiers trop larges ou ambigus ;
* de maintenir la distinction entre modélisation métier et implémentation technique.

## Conséquences
### Positives

* Meilleure clarté sémantique.
* Meilleur respect des responsabilités métier.
* Réduction du risque de couplage fort entre capacités.
* Meilleure articulation entre vision transverse et déclinaisons opérationnelles.

### Risques

* Introduction d’un niveau conceptuel supplémentaire.
* Risque de confusion si le terme canonique est compris comme un schéma technique unique.

## Traçabilité

Cette décision s’inscrit dans la continuité :

* de la gouvernance BCM ;
* du guide de modélisation des événements ;
* de la définition des capacités ;
* du principe selon lequel les capacités L2 constituent le pivot d’urbanisation.

