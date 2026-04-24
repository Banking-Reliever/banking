---
id: ADR-BCM-URBA-0010
title: "Les capacités L2 constituent le pivot d'urbanisation et le point d'ancrage des relations du modèle"
status: Proposed
date: 2026-03-11

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
  - ADR-BCM-GOV-0001
  - ADR-BCM-URBA-0002
  - ADR-BCM-URBA-0004
  - ADR-BCM-URBA-0007
  - ADR-BCM-URBA-0009

supersedes: []

tags:
  - BCM
  - Urbanisation
  - L2
  - Pivot
  - Traçabilité
  - Mapping
  - Découplage

stability_impact: Structural
---

# ADR-BCM-URBA-0010 — Les capacités L2 constituent le pivot d'urbanisation et le point d'ancrage des relations du modèle

## Contexte

La BCM doit simultanément :
- rester lisible pour le métier,
- guider l'urbanisation du SI,
- permettre la traçabilité vers les applications, les flux de données et l'organisation,
- sans dériver vers une cartographie purement technique ni vers une process map.

Les principes déjà établis dans le repository convergent vers le fait que le niveau **L2** est le bon niveau d'arbitrage :
- le modèle est structuré en **L1 / L2 / L3**, avec un besoin d'actionnabilité sans perdre en stabilité ;
- le **L3** reste exceptionnel et ne doit pas devenir le niveau standard de pilotage ;
- les événements métier et les contrats d'interface sont déjà pensés autour d'un rattachement à une **capacité L2** ;
- le découplage logique / physique impose de ne pas faire dépendre la structure cible des applications existantes ;
- les assets et mappings techniques doivent s'ancrer sur un identifiant stable et non sur un libellé applicatif.

En pratique, le repository comporte plusieurs types d'éléments : capacités, événements métier, événements ressource, objets métier, ressources, abonnements, mappings SI / DATA / ORG, et potentiellement demain des référentiels applicatifs, techniques ou externes. Sans règle transversale explicite, il existe un risque de dérive :
- multiplication de liens directs entre éléments de bas niveau,
- couplage excessif entre référentiel métier et implémentation technique,
- perte de lisibilité du modèle,
- ambiguïtés d'ownership,
- inflation de relations opportunistes non gouvernées.

Le besoin est donc d'instituer formellement la capacité **L2** comme **pivot d'urbanisation**, c'est-à-dire comme point d'ancrage par défaut des relations entre le modèle BCM et les autres référentiels.

## Décision

### 1) Le niveau L2 est le pivot d'urbanisation obligatoire du modèle BCM

Toute relation structurante entrant dans le scope de l'urbanisation du SI doit, par défaut, être exprimée via une **capacité L2**.

Par "relation structurante", on entend notamment :
- le rattachement d'un événement métier,
- le rattachement d'un objet métier ou d'une ressource,
- le rattachement d'une application ou d'un composant applicatif,
- le rattachement d'un flux ou d'un domaine de données, d'un produit data,
- le rattachement d'une responsabilité organisationnelle,
- le rattachement d'un contrôle ou d'une exigence transverse.


Le L1 sert au cadrage et à la lisibilité.
Le L3 sert à préciser un cas lorsque cela est nécessaire.
Le **L2** est le niveau normal d'ancrage des relations d'urbanisation.

### 2) Tout élément du méta-modèle doit référencer une capacité L2 lorsqu'il porte une responsabilité, un ownership ou une finalité métier

Les éléments décrits dans le méta-modèle, en particulier ceux couverts par l'ADR 007, doivent s'appuyer sur une capacité L2 dès lors qu'ils expriment :
- une émission,
- une consommation,
- une responsabilité métier,
- une portée fonctionnelle,
- un besoin de traçabilité ou d'audit.

Exemples attendus :
- tout **événement métier** référence une capacité L2 émettrice ;
- toute **consommation métier** d'un événement référence une capacité L2 consommatrice ;
- tout **objet métier** ou toute **ressource** porte une capacité L2 de rattachement ;
- tout **abonnement** métier ou ressource indique la capacité L2 consommatrice ;
- tout **mapping applicatif** se fait d'abord vers une capacité L2, puis seulement vers les artefacts techniques concernés.

### 3) Les relations directes entre éléments non-L2 sont autorisées uniquement dans deux cas

#### Cas A — relation strictement opérationnelle
Une relation directe est autorisée lorsqu'elle est purement nécessaire à l'exploitation, à l'inventaire ou au déploiement technique, sans modifier la lecture urbanistique du modèle.

Exemples :
- application ↔ serveur,
- application ↔ base technique,
- topic ↔ cluster,
- composant ↔ runtime,
- job ↔ ordonnanceur,
- API ↔ gateway.

Ces relations doivent être portées dans un **registre de mapping opérationnel** dédié.
Elles ne remplacent pas le rattachement de ces éléments à une capacité L2.

#### Cas B — relation exceptionnelle, explicitement motivée
Une relation directe hors pivot L2 est autorisée lorsqu'un besoin réglementaire, d'audit, de sécurité, de continuité, ou de conformité l'exige explicitement.

Exemples :
- application ↔ processus DORA,
- application ↔ contrôle de résilience,
- composant ↔ exigence réglementaire,
- flux ↔ dispositif de conformité.

Dans ce cas :
- la relation directe doit être **motivée**,
- la motivation doit être documentée dans le référentiel ou dans un ADR,
- la relation ne doit pas court-circuiter le rattachement principal à la capacité L2.

### 4) Le pivot L2 est prioritaire sur les liens directs pour toutes les vues de référence

Les vues de référence produites à partir du repository doivent privilégier les chaînes de lecture suivantes :
- **Capacité L2 → Événements → Applications**
- **Capacité L2 → Objets métier / Ressources → Données**
- **Capacité L2 → Owner / équipe / responsabilité**
- **Capacité L2 → Contrôles / exigences / conformités**

Les liens directs entre éléments non-L2 ne doivent apparaître que :
- dans des vues opérationnelles spécialisées,
- ou dans des vues de conformité explicitement identifiées comme telles.

### 5) Les registres dédiés portent les détails, pas les identifiants métier

Le nom d'un élément ne doit pas être surchargé pour remplacer l'information portée par un registre.

Les détails suivants doivent être portés dans des mappings ou registres dédiés :
- une application implémentant plusieurs composants,
- une application déployée sur plusieurs serveurs,
- une interface exposée via plusieurs canaux,
- une application concernée par un ou plusieurs contrôles DORA,
- une dépendance technique temporaire.

Le modèle BCM conserve la responsabilité métier ; le registre opérationnel porte la matérialisation technique.

### 6) Critères vérifiables

La décision est considérée comme respectée si les règles suivantes sont vraies :

- R1. Tout élément métier publiable du méta-modèle référence au moins une capacité L2 de rattachement.
- R2. Tout événement métier possède une et une seule capacité L2 émettrice.
- R3. Toute consommation métier d'événement possède une capacité L2 consommatrice.
- R4. Tout mapping applicatif fonctionnel passe par une capacité L2.
- R5. Toute relation directe entre deux éléments non-L2 est soit :
  - portée par un registre opérationnel,
  - soit justifiée par un besoin exceptionnel documenté.
- R6. Aucune vue d'urbanisation transverse ne repose principalement sur des relations directes application ↔ application, application ↔ serveur, ou composant ↔ composant sans passage par une capacité L2.
- R7. Les relations directes de conformité ou d'exploitation n'annulent jamais le rattachement métier principal à la capacité L2.

## Justification

Cette décision formalise et généralise des principes déjà présents dans le repository.

Le niveau **L2** est déjà présenté comme :
- le bon compromis entre stabilité et précision pour l'urbanisation,
- le niveau naturel de rattachement des événements,
- le point à partir duquel on peut découpler logique métier et implémentation physique,
- le niveau de décision pertinent pour guider les mappings SI / DATA / ORG.

En faisant du L2 le pivot explicite :
- on évite que les applications existantes dictent la structure cible,
- on préserve la possibilité de moderniser ou remplacer le SI sans casser le modèle métier,
- on améliore l'ownership,
- on rend la dette technique visible,
- on garde un modèle lisible et auditable.

Cette règle n'interdit pas les liens directs.
Elle les **cadre** :
- les liens opérationnels restent possibles là où ils sont nécessaires,
- les liens de conformité restent possibles là où ils sont exigés,
- mais ils deviennent secondaires par rapport au pivot métier.

### Alternatives considérées

- **Option A — Laisser coexister librement des liens directs entre tous les éléments**  
  Rejetée car elle conduit à une dérive opportuniste, à la perte de lisibilité et à un couplage progressif du modèle BCM avec le SI physique.

- **Option B — Faire du L1 le pivot d'urbanisation**  
  Rejetée car trop macro pour piloter les événements, les applications, les données ou la conformité avec une granularité utile.

- **Option C — Faire du L3 le pivot d'urbanisation**  
  Rejetée car trop fin et trop instable ; cela ferait dériver la BCM vers une modélisation détaillée de processus ou de micro-découpage.

- **Option D — Utiliser directement l'application comme pivot de traçabilité**  
  Rejetée car cela recrée le couplage logique / physique et fige la cible sur l'existant.

## Impacts sur la BCM

### Structure

- Aucun changement de structure L1 / L2 / L3.
- Renforcement du rôle du L2 comme point d'ancrage transversal.
- Clarification de la frontière entre :
  - référentiel métier BCM,
  - référentiels de mapping,
  - référentiels opérationnels / conformité.

### Événements (si applicable)

- Confirmation de la règle : tout événement métier est rattaché à une capacité L2 émettrice.
- Confirmation de la règle : toute consommation métier d'un événement est rattachée à une capacité L2 consommatrice.
- Les événements purement techniques restent hors pivot BCM, sauf s'ils portent un besoin de traçabilité métier.

### Mapping SI / Data / Org

- **SI** : les mappings capability ↔ application deviennent le point d'entrée obligatoire ; les liens application ↔ serveur ou composant ↔ runtime sont relégués dans des tables opérationnelles dédiées.
- **DATA** : les flux et objets sont rattachés à des capacités L2 avant toute déclinaison technique.
- **ORG** : les owners et responsabilités sont rattachés en priorité aux capacités L2.
- **Conformité** : les liens directs application ↔ contrôle / dispositif réglementaire sont possibles mais doivent être explicitement identifiés comme exception motivée.

## Conséquences

### Positives

- Règle transverse simple et lisible pour tous les référentiels.
- Découplage renforcé entre métier et implémentation.
- Traçabilité homogène entre capacités, événements, applications, données et organisation.
- Auditabilité accrue des choix d'urbanisation.
- Réduction du "graphe spaghetti" de dépendances opportunistes.
- Meilleure capacité à produire des vues cohérentes pour la transformation et la gouvernance.
- Compatibilité avec des besoins spécifiques d'exploitation et de conformité sans dégrader le modèle cible.

### Négatives / Risques

- Effort initial de cadrage pour classer correctement les relations.
- Nécessité de créer ou maintenir plusieurs registres complémentaires :
  - mapping fonctionnel,
  - mapping opérationnel,
  - mapping conformité.
- Risque de débats sur ce qui relève d'un lien "strictement opérationnel" ou "exceptionnellement motivé".
- Besoin de discipline de gouvernance pour éviter qu'une exception devienne la norme.

### Dette acceptée

- Certains référentiels existants pourront continuer temporairement à porter des liens directs historiques sans pivot L2.
- Ces liens sont acceptés comme dette transitoire s'ils sont :
  - identifiés,
  - documentés,
  - et revus périodiquement.
- Certains cas de conformité (ex. DORA) pourront imposer une modélisation supplémentaire directe avant que le mapping via L2 soit complet.

## Indicateurs de gouvernance

- Niveau de criticité : Élevé (règle structurante transverse).
- Date de revue recommandée : 2028-03-11.
- Indicateurs de stabilité attendus :
  - 100 % des événements métier rattachés à une capacité L2.
  - 100 % des mappings applicatifs fonctionnels passant par une capacité L2.
  - 100 % des relations directes non-L2 classées comme `operational` ou `exceptional_justified`.
  - 0 vue transverse d'urbanisation reposant principalement sur des dépendances techniques directes.
  - existence d'au moins un registre dédié pour les mappings opérationnels.

## Traçabilité

- Atelier : Gouvernance BCM / Urbanisation transverse
- Participants : EA / Urbanisation, Architecture SI, Business Architecture
- Références :
  - ADR-BCM-GOV-0001
  - ADR-BCM-URBA-0002
  - ADR-BCM-URBA-0004
  - ADR-BCM-URBA-0007
  - fichiers `bcm/events-*.yaml`
  - fichiers de mapping SI / DATA / ORG