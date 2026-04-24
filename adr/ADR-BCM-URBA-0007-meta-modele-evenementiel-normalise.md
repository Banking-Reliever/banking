---
id: ADR-BCM-URBA-0007
title: "Méta-modèle événementiel normalisé guidé par les capabilities"
status: Proposed
date: 2026-03-05

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

impacted_capabilities: []
impacted_events: []
impacted_mappings:
  - SI
  - DATA
  - ORG

related_adr:
  - ADR-BCM-URBA-0002
  - ADR-BCM-URBA-0003
  
supersedes: []

tags:
  - event-driven
  - metamodel
  - normalisation
  - cartographie-si

stability_impact: Structural
---

# ADR-BCM-URBA-0007 — Méta-modèle événementiel normalisé guidé par les capabilities

## Contexte

La BCM évolue vers une cartographie SI construite **par modèle** et non par projection ( vues, cartographies ). Les projections s'appuient sur un ensemble de données produites selon des règles. Une projection n'est alors qu'un modèle de lecture, un usage pour accompagner une intention. Ce qui est défini ici sont le modèle d'écriture, les règles régissant comment les données décrivant le SI sont assemblées de manière normalisée.
Les assets événementiels existent déjà (`EVT`, `OBJ`, `RES`, `ABO.*`) mais les liens
structurels ne sont pas encore explicités comme un méta-modèle de référence unique.

L'objectif cible est de préparer la future cartographie SI FOODAROO et de converger vers
une **Event-Driven Enterprise** reposant sur des concepts normalisés, traçables et
vérifiables automatiquement.

## Décision

Le méta-modèle cible explicite les relations suivantes comme règles directrices :

- `Capability -> Evenement Metier` (production)
- `Capability + Evenement Metier -> Capability` (abonnement)
- `Evenement Metier -> Objet Metier` (1 événement métier porte 1 objet métier)
- `Objet Metier <- Ressource` (1 ressource référence 1 objet métier)
- `Evenement Metier <- Evenement Ressource` (1 événement ressource référence 1 événement métier)
- `Evenement Ressource -> Ressource` (1 événement ressource référence 1 ressource)

Le terme **abonnement** reflète une **souscription** à un contrat d'évènement. Dans le jargon d'assurance, le terme de souscription peut être confondu avec celui inhérent à la souscription d'un contrat d'assurance, c'est la raison pour laquelle , le terme abonnement sera privilégié.

Le terme évenement porte lui aussi à confusion. Car dans le jargon de l'assurance, il indique l'occurence d'un sinistre. MAlheureusement, il n'existe pas d'équivalent avec la même charge sémantique que l'on pour utiliser sans dénaturer trop avant le propos et provoquer de la confusion. Il faudra donc faire la différence entre un évènement du système d'inforamtion et un évènement dans le contexte de la déclration d'un sinistre. Cette distinction semble claire et facilement acquérable parmi les acteurs qui s'occupe de Sinistres & Prestations.

Critères vérifiables attendus (niveau cadre) :

- chaque relation est représentable explicitement dans les assets YAML ;
- chaque relation est contrôlable par validation automatique de cohérence ;
- le modèle reste indépendant d'un outil de dessin.

### Templates par type d'entité

Les templates suivants constituent le **modèle d'écriture** de référence pour chaque type d'entité :

| Type d'entité | Préfixe d'ID attendu | Template de référence |
|---|---|---|
| Capability | `CAP.*` | `templates/capacité-template.yaml` |
| Événement métier | `EVT.*` | `templates/evenement-metier/template-evenement-metier.yaml` |
| Objet métier | `OBJ.*` | `templates/objet-metier/template-objet-metier.yaml` |
| Ressource | `RES.*` | `templates/ressource/template-ressource.yaml` |
| Événement ressource | `EVT.RES.*` | `templates/evenement-ressource/template-evenement-ressource.yaml` |
| Abonnement métier | `ABO.METIER.*` | `templates/evenement-metier/template-abonnement-metier.yaml` |
| Abonnement ressource | `ABO.RESSOURCE.*` | `templates/evenement-ressource/template-abonnement-ressource.yaml` |

Règle d'usage : toute nouvelle entité introduite dans le modèle doit être initialisée
à partir du template correspondant, puis validée par les scripts de contrôle du repository.

## Justification

Cette décision fournit un socle minimal commun pour relier capacités, contrats
événementiels et matérialisation des données opérationnelles.

Elle améliore :

- la lisibilité des responsabilités producteur/consommateur ;
- la traçabilité de bout en bout (capacité -> événement -> objet -> ressource) ;
- la capacité à industrialiser les contrôles de cohérence.

### Alternatives considérées

- Option A — Continuer sans méta-modèle explicite : rejetée car la cohérence globale
  dépend d'interprétations locales.
- Option B — Cartographier uniquement par diagrammes : rejetée car peu industrialisable
  pour le contrôle automatique et la gouvernance continue.

## Règles avancées envisagées (non implémentées à ce stade)

À titre de perspective (inspirations de pratiques avancées), les règles suivantes pourront être étudiées ultérieurement :

- gouvernance avancée de versionnement et compatibilité des événements ;
- qualification des contrats (stabilité, exposition, criticité, SLA/SLO) ;
- anti-patterns de couplage (chaînes fragiles, dépendances circulaires, sur-subscription) ;
- contrôles de qualité de domaine (ownership explicite, lifecycle, obsolescence) ;
- règles de publication/consommation outillées via registry.


Ces règles ne sont **pas** imposées par cet ADR et ne doivent pas être implémentées
dans cette phase.

## Impacts sur la BCM

### Structure

- Impact principal : explicitation du graphe conceptuel cross-level.
- Pas de split/merge immédiat de capabilities.

### Événements (si applicable)

- Clarification des liens entre événements métier et événements ressource.
- Formalisation de la place des abonnements comme relation capacité-consommation.

### Mapping SI / Data / Org

- SI : prépare la cartographie applicative par modèle.
- DATA : prépare la chaîne logique événement -> objet -> ressource.
- ORG : clarifie les responsabilités producer/consumer autour des capabilities.

## Conséquences

### Positives

- Base commune pour construire la cartographie SI FOODAROO par modèle.
- Alignement progressif vers une Event-Driven Enterprise normalisée.
- Meilleure auditabilité des liens métier/opérationnels.

### Négatives / Risques

- Risque d'ambiguïté si les règles détaillées ne sont pas découpées en ADR dédiés.
- Risque de surcharge documentaire si le périmètre reste trop large trop longtemps.

### Dette acceptée

Cet ADR est volontairement **cadre**. Il est destiné à être superseded, en plusieurs
itérations, par des ADR plus précis couvrant les parties non encore prises en charge,
notamment (liste non exhaustive- application:

- application
- topic (Kafka)
- API
- schema
- database/table
- organisation
- processus
- data-dictionary
- registre des risques / contrôles / dépendances DORA
- infrastructure

## Indicateurs de gouvernance

- Niveau de criticité : élevé (structurant).
- Date de revue recommandée : 2026-06-30.
- Indicateur de stabilité attendu : modéré (ADR de transition vers un cadre détaillé).

## Traçabilité

- Atelier : cadrage urbanisation événementielle BCM.
- Participants : Urbanisme SI, Architecture, Référents domaines métier.
- Références : ADR URBA 0002/0003, README ADR.
