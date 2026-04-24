---
id: ADR-BCM-URBA-0001
title: "BCM SI orienté TOGAF étendu (7 zones)"
status: Proposed
date: 2026-02-27

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
  - ADR-BCM-GOV-0001  # hiérarchie GOV → URBA → FUNC
supersedes: []

tags:
  - BCM
  - Modélisation
  - TOGAF
  - Zoning

stability_impact: Structural
---

# ADR-BCM-URBA-0001 — BCM SI orienté TOGAF étendu (7 zones)

## Contexte
Il faut une carto permettant de donner les fondations du système d'informations.
Cette cartographie doit permettre d'individualiser et de responsabiliser la production d'information au sein du SI.

Elle doit permettre de coordonner et de localiser les différents applicatifs.

Sans structuration claire, le risque est double :
- une BCM "plate" (sans zoning) mélange pilotage, production métier et support,
- une BCM custom non standardisée complique le dialogue avec les éditeurs, partenaires et l'alignement sur les bonnes pratiques du marché.

La méthodologie TOGAF permet un premier niveau de standardisation permettant de cadrer les capacités de production d'un SI en découpant en différentes zones les capacités du SI.

Cependant, pour une mutuelle/assurance moderne, TOGAF seul (3 zones : Pilotage, COEUR, Support) est **insuffisant** pour adresser :
- la distinction entre capacités métier core et capacités transverses d'exposition (parcours omnicanaux, portails),
- la gestion des référentiels master (données pivot partagées),
- les échanges avec l'écosystème externe (partenaires, délégataires, régulateur, prestataires),
- les capacités DATA_ANALYTIQUE (gouvernance, BI, IA) qui ne sont ni du "support" pur ni de la "production métier".

D'où l'extension proposée à **7 zones** :
- **PILOTAGE** : pilotage d'entreprise, conformité, gouvernance
- **SERVICES COEUR** : cœur de métier (produits, distribution, souscription, contrats, sinistres, service client...)
- **SUPPORT** : fonctions support transverses (cybersecurity, gestion documentaire, interopérabilité interne, comptabilité...)
- **REFERENTIEL** : référentiels master partagés (Personne, Adresse, Contrat, Produit, Bancaire, Organisation...)
- **ECHANGE_B2B** : échanges avec l'écosystème externe (onboarding partenaires, hub d'échanges, API externes, traçabilité des flux tiers)
- **CANAL** : exposition omnicanale et parcours utilisateurs (portails adhérent/entreprise, poste conseiller, acquisition digitale, centre de contact)
- **DATA_ANALYTIQUE** : gouvernance des données, ingestion, plateformes data, BI/reporting, analytique avancé & IA

## Décision
- La BCM est structurée selon le modèle **TOGAF étendu** avec sept zones principales :
  - **PILOTAGE** : capacités de pilotage et de conformité
  - **SERVICES COEUR** : capacités métier cœur
  - **SUPPORT** : capacités support transverses
  - **REFERENTIEL** : référentiels master et données pivot partagées
  - **ECHANGE_B2B** : échanges avec l'écosystème externe (partenaires, délégataires, régulateur, prestataires)
  - **CANAL** : exposition omnicanale et parcours utilisateurs finaux
  - **DATA_ANALYTIQUE** : gouvernance data, ingestion, plateformes, BI, analytique & IA

- Chaque capacité dispose d'un attribut **zoning** dans `bcm/capabilities.yaml` faisant référence à l'une de ces sept zones.

- Les vues générées (Mermaid, graphes) doivent visualiser cette séparation pour faciliter les arbitrages d'urbanisation.

- Règles de disambiguation claires :
  - **CANAL** (UX, parcours, exposition front) ≠ **Canaux & Intermédiation** (COEUR : règles de distribution + réseaux)
  - **ECHANGE_B2B** (écosystème, flux externes, SLA) ≠ **Interopérabilité** (SUPPORT : intégration interne SI)
  - **DATA_ANALYTIQUE** (ingestion analytique décorrélée) ≠ **Interopérabilité** (échanges opérationnels transactionnels)
  - **REFERENTIEL** (master data partagées) ≠ capacités de production utilisant ces référentiels

## Justification
TOGAF est un standard reconnu qui permet :
- un langage commun avec l'écosystème (éditeurs, intégrateurs, consultants),
- une séparation claire entre pilotage, production et support,
- une meilleure gouvernance de la couverture SI (éviter que le support déborde sur le métier, ou que le pilotage soit noyé dans le COEUR).

**Extension avec 4 zones supplémentaires** :

1. **REFERENTIEL** : Les référentiels (Personne, Adresse, Contrat, Produit...) sont des **données pivot** consommées par toutes les zones. Les isoler permet :
   - une gouvernance claire de la master data (ownership, qualité, cycle de vie),
   - d'éviter la duplication et les incohérences,
   - de piloter séparément les investissements "référentiels" vs "production".

2. **ECHANGE_B2B** : La "façade écosystème" (partenaires, délégataires, régulateur, réseaux de soin, prestataires) a des contraintes spécifiques (SLA, onboarding, traçabilité, formats normalisés, preuves) distinctes de l'interopérabilité interne (SUPPORT). Séparer permet :
   - de piloter la relation externe vs intégration interne,
   - de gérer les exigences réglementaires sur les échanges (RGPD, traçabilité, archivage probatoire),
   - d'industrialiser l'onboarding partenaires et la gouvernance des API externes.


3. **CANAL** : L'expérience omnicanale (portails, parcours, poste conseiller, centre de contact) n'est ni du "Service Client" (COEUR : traitement métier des demandes) ni du pur "Support". C'est la **couche d'exposition** aux utilisateurs finaux. Séparer permet :
   - de piloter l'expérience utilisateur indépendamment de la production métier,
   - d'éviter la confusion entre "capacité métier" (ex : Souscription) et "canal d'accès" (ex : tunnel digital),
   - de mesurer et optimiser les parcours (conversion, abandon, NPS/CSAT).
Elle regroupe l'esemble des applicatifs pur permettant d'interfacer le backend du système d'information de l'entreprise qui lui est porté par la zone COEUR.

4. **DATA_ANALYTIQUE** : La gouvernance data, l'ingestion analytique, le BI et l'IA ne sont ni "production transactionnelle" (COEUR) ni "support technique" pur. Les isoler permet :
   - de piloter la stratégie data (gouvernance, qualité, data products),
   - de distinguer flux analytiques (décorrélés, batch/stream) vs flux transactionnels (opérationnels),
   - de valoriser les investissements analytique & IA séparément.

### Alternatives considérées

- **TOGAF 3 zones pur** — rejeté car insuffisant pour adresser parcours omnicanaux, échanges écosystème, master data, analytique.
- **Tout dans SUPPORT** — rejeté car perte de visibilité, mélange de responsabilités hétérogènes.
- **Modèle custom complet (sans TOGAF)** — rejeté car perte d'alignement avec standards, coût de formation.
- **8+ zones** (ex : séparer "Payments" de "ECHANGE_B2B") — reporté (ajouté si besoin identifié, pour l'instant limité à 7 zones pour garder lisibilité).

## Impacts sur la BCM

### Structure

- Capacités impactées : toutes (ajout obligatoire du champ `zoning` dans `capabilities.yaml` avec une des 7 valeurs).
- L1/L2/L3 + zoning (deux dimensions orthogonales).
- Règles de placement (testables via validation) :
  - Pilotage → **PILOTAGE**
  - Cœur métier assurance/mutuelle → **SERVICES COEUR**
  - Fonctions support IT transverses (cybersecurity, GED, interopérabilité interne) → **SUPPORT**
  - Master data partagées → **REFERENTIEL**
  - Échanges avec tiers externes → **ECHANGE_B2B**
  - Parcours et exposition utilisateurs → **CANAL**
  - Gouvernance data, BI, analytique, IA → **DATA_ANALYTIQUE**
- Disambiguation obligatoire :
  - "Canaux & Intermédiation" (règles distribution) reste **COEUR**, "Canal" (parcours UX) est **CANAL**
  - "Interopérabilité" (SI interne) reste **SUPPORT**, échanges tiers vont en **ECHANGE_B2B**
  - Flux transactionnels → **SUPPORT/Interopérabilité**, flux analytiques → **DATA_ANALYTIQUE/Ingestion**

### Événements (si applicable)

- Aucun impact direct sur les événements métier.

### Mapping SI / Data / Org

- Applications, domaines de données et équipes peuvent être **mappés** par zone, facilitant les analyses de couverture et de responsabilité.

## Conséquences
### Positives
- **Lisibilité renforcée** : distinction claire entre what (COEUR), how we steer (PILOTAGE), how we support (SUPPORT), what we share (REFERENTIEL), how we expose (CANAL), how we exchange (ECHANGE_B2B), how we analyze (DATA_ANALYTIQUE).
- **Standardisation** : alignement avec TOGAF facilite l'onboarding, les revues externes, les benchmarks.
- **Gouvernance** : règles de placement (7 zones) deviennent testables et auditables.
- **Communication** : dialogue simplifié avec partenaires/éditeurs qui connaissent TOGAF, enrichi par des zones métier spécifiques au contexte assurance/mutuelle.
- **Pilotage différencié** : 
  - investissements référentiels (master data) vs production,
  - stratégie omnicanale (CANAL) vs capacités métier (COEUR),
  - gouvernance DATA_ANALYTIQUE séparée,
  - roadmap écosystème (ECHANGE_B2B) vs intégration interne (SUPPORT).
- **Disambiguation** : plus de risque de mélanger parcours client (CANAL) et capacité métier (COEUR), ou échanges tiers (ECHANGE_B2B) et interopérabilité interne (SUPPORT).

### Négatives / Risques
- **Complexité** : 7 zones au lieu de 3 → plus de règles à maîtriser, risque de débats sur le placement (ex : "Notifications" → CANAL ou SUPPORT ? "Portail partenaire" → CANAL ou ECHANGE_B2B ?).
- **Formation** : nécessite une acculturation des équipes au vocabulaire TOGAF **étendu** (zones custom).
- **Rigidité** : débats possibles sur le placement de certaines capacités (ex : "Gestion des paiements" → ECHANGE_B2B ou COEUR ?).
- **Distinction infrastructure vs capacité** : les plateformes transverses (ESB, API Gateway, bus d'événements) ne sont **pas** des capacités à zoner. Ce qui doit être localisé, ce sont les **topics/événements produits par chaque capacité** et les **capacités métier/SI** utilisant ces plateformes.
- **Gouvernance renforcée** : nécessite des critères de placement documentés et des revues régulières pour éviter les dérives.
- **Outillage** : les vues générées doivent supporter 7 zones (complexité visuelle, besoin de légende claire).

### Dette acceptée
- Certaines capacités peuvent avoir des **zones multiples** (ex : une API exposée en CANAL **et** consommant ECHANGE_B2B). Pour l'instant, on force un **placement unique** (zone principale) et on documente les interactions via les ADRs de capacités.

## Indicateurs de gouvernance

- Niveau de criticité : Élevé (décision structurante transverse).
- Date de revue recommandée : 2028-01-21.
- Indicateur de stabilité attendu : toutes les capabilities possèdent un attribut `zoning` parmi les 7 valeurs.

## Traçabilité

- Atelier : Urbanisation 2026-02-27
- Participants : EA / Urbanisation, yremy, acoutant
- Références : —
