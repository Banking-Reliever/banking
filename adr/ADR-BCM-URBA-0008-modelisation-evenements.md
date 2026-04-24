---
id: ADR-BCM-URBA-0008
title: "Modélisation des événements — Guide à deux niveaux"
status: Proposed
date: 2026-03-09

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
  - ADR-BCM-GOV-0001
  - ADR-BCM-URBA-0003
  - ADR-BCM-URBA-0004
  - ADR-BCM-URBA-0007
  - ADR-BCM-FUNC-0003
supersedes: []

tags:
  - event-driven
  - objet-metier
  - evenement-metier
  - ressource
  - modelisation
  - guide
  - polymorphisme
  - abstraction

stability_impact: Structural
---

# ADR-BCM-URBA-0008 — Modélisation des événements — Guide à deux niveaux

## Contexte

Le méta-modèle BCM (ADR-BCM-URBA-0007) introduit une architecture événementielle
structurée en **deux niveaux d'abstraction** :

| Niveau | Objets | Événements | Abonnements |
|--------|--------|------------|---------------|
| **Métier** | Objet métier | Événement métier | Abonnement métier |
| **opérationnel** | Ressource | Événement ressource | Abonnement ressource |

Cette structure répond à un besoin récurrent : modéliser des variantes métier
structurellement hétérogènes pour un même jalon de cycle de vie, tout en préservant
une abstraction stable pour les consommateurs transverses.

**Exemple concret :**
- Jalon de cycle de vie : *Sinistre déclaré*
- Variantes métier : *Dégât des eaux*, *Vol*, *Incendie* — chacune avec des
  propriétés spécifiques.

Cet ADR formalise les règles de modélisation à chaque niveau et leurs relations.

## Décision

### Vue d'ensemble : architecture à deux niveaux

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           NIVEAU MÉTIER (abstraction)                       │
│                                                                             │
│   ┌─────────────────────┐         ┌─────────────────────┐                   │
│   │    Objet Métier     │◄────────│  Événement Métier   │                   │
│   │  (propriétés        │ porté   │  (jalon de cycle    │                   │
│   │   communes)         │         │   de vie)           │                   │
│   └─────────────────────┘         └─────────────────────┘                   │
│             ▲                               ▲                               │
│             │ business_object               │ business_event               │
│             │                               │                               │
├─────────────┼───────────────────────────────┼───────────────────────────────┤
│             │                               │                               │
│             │   NIVEAU RESSOURCE (implémentation)                           │
│             │                               │                               │
│   ┌─────────┴───────────┐         ┌─────────┴───────────┐                   │
│   │     Ressource       │◄────────│ Événement Ressource │                   │
│   │  (propriétés        │ portée  │  (fait publié       │                   │
│   │   spécialisées)     │         │   spécialisé)       │                   │
│   └─────────────────────┘         └─────────────────────┘                   │
│                                                                             │
│   Ressource.data[].business_object_property → Objet Métier.data[].name      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Niveau 1 : Modélisation Métier

### 1.1 Objet Métier — Le socle commun de propriétés

L'**objet métier** définit les propriétés **abstraites et stables** partagées par
toutes les variantes d'un même concept.

**Règles de modélisation :**

| Règle | Description |
|-------|-------------|
| **Abstraction** | Ne contient que les propriétés communes à toutes les variantes |
| **Stabilité** | Les propriétés sont conçues pour rester stables dans le temps |
| **Indépendance** | Ne dépend pas de détails d'implémentation technique |
| **Sens des références** | Ne référence pas d'événement métier ; la relation est portée uniquement par `EVT.carried_business_object` |
| **Complétude** | Chaque propriété doit être référencée par au moins une ressource |

**Exemple — Objet métier `OBJ.COEUR.005.DECLARATION_SINISTRE` :**

```yaml
data:
  - name: identifiantDeclaration      # Commun à toutes les variantes
  - name: dateSurvenance              # Commun à toutes les variantes
  - name: identifiantContrat          # Commun à toutes les variantes
  - name: canalDeclaration            # Commun à toutes les variantes
  - name: statutVerificationCouverture # Commun à toutes les variantes
```

**À éviter :**
- Propriétés spécifiques à une seule variante (ex. `origineFuite` pour dégât des eaux)
- Propriétés techniques ou d'implémentation
- Propriétés polymorphes nécessitant un décodage

### 1.2 Événement Métier — Le jalon de cycle de vie

L'**événement métier** représente un **jalon abstrait du cycle de vie** d'un
agrégat métier. Il porte un objet métier.

**Règles de modélisation :**

| Règle | Description |
|-------|-------------|
| **Unicité du jalon** | Un seul événement métier par jalon de cycle de vie |
| **Abstraction** | Décrit le *quoi* (le fait métier), pas le *comment* (l'implémentation) |
| **Porteur d'objet métier** | Référence obligatoirement un objet métier via `carried_business_object` |
| **Pas de publication directe** | N'est pas publié tel quel ; sert de point d'abstraction |

**Exemple — Événement métier `EVT.COEUR.005.SINISTRE_DECLARE` :**

```yaml
id: EVT.COEUR.005.SINISTRE_DECLARE
name: Sinistre déclaré
carried_business_object: OBJ.COEUR.005.DECLARATION_SINISTRE
emitting_capability: CAP.COEUR.005.DSP
```

### 1.3 Abonnement Métier — La consommation transverse

Un **abonnement métier** permet à un consommateur de s'abonner à un **événement
métier**, recevant ainsi **tous les événements ressource** qui l'implémentent.

**Règles de modélisation :**

| Règle | Description |
|-------|-------------|
| **Cible abstraite** | Référence un événement métier, pas un événement ressource |
| **Résolution automatique** | Est résolue vers tous les événements ressource liés |
| **Propriétés communes** | Le consommateur ne peut lire que les propriétés de l'objet métier |

**Cas d'usage :**
- Consommateur généraliste (ex. reporting, audit, data lake)
- Consommateur qui n'a pas besoin des détails spécialisés

---

## Niveau 2 : Modélisation Ressource

### 2.1 Ressource — L'implémentation spécialisée

La **ressource** implémente un objet métier avec des **propriétés spécialisées**
propres à une variante.

**Règles de modélisation :**

| Règle | Description |
|-------|-------------|
| **Spécialisation** | Contient les propriétés spécifiques à la variante |
| **Référence obligatoire** | Référence l'objet métier via `business_object` |
| **Traçabilité des propriétés** | Chaque propriété commune référence sa source via `business_object_property` |
| **Autonomie** | Doit être compréhensible seule, sans jointure avec d'autres ressources |

**Exemple — Ressource `RES.COEUR.005.DECLARATION_SINISTRE_HABITATION_DEGAT_EAUX` :**

```yaml
id: RES.COEUR.005.DECLARATION_SINISTRE_HABITATION_DEGAT_EAUX
business_object: OBJ.COEUR.005.DECLARATION_SINISTRE

data:
  # Propriétés communes (référencent l'objet métier)
  - name: identifiantDeclaration
    business_object_property: identifiantDeclaration
  - name: dateSurvenance
    business_object_property: dateSurvenance
  - name: identifiantContrat
    business_object_property: identifiantContrat

  # Propriétés spécialisées (propres à cette variante)
  - name: origineFuite           # Spécifique dégât des eaux
  - name: zoneImpactee           # Spécifique dégât des eaux
  - name: tiersImpactes          # Spécifique dégât des eaux
```

### 2.2 Événement Ressource — Le fait publié

L'**événement ressource** est le **fait réellement publié** sur le bus. Il porte
une ressource et implémente un événement métier.

**Règles de modélisation :**

| Règle | Description |
|-------|-------------|
| **Publication effective** | C'est l'événement réellement publié et consommé |
| **Spécialisé** | Un type d'événement ressource par variante métier |
| **Référence double** | Référence une ressource (`carried_resource`) et un unique événement métier (`business_event`) |
| **Autonomie** | Compréhensible sans décodage polymorphe ni jointure |

**Exemple — Événement ressource `EVT.RES.COEUR.005.SINISTRE_HABITATION_DEGAT_EAUX_DECLARE` :**

```yaml
id: EVT.RES.COEUR.005.SINISTRE_HABITATION_DEGAT_EAUX_DECLARE
name: Sinistre habitation dégât des eaux déclaré
carried_resource: RES.COEUR.005.DECLARATION_SINISTRE_HABITATION_DEGAT_EAUX
business_event: EVT.COEUR.005.SINISTRE_DECLARE
emitting_capability: CAP.COEUR.005.DSP
```

### 2.3 Abonnement Ressource — La consommation spécialisée

Un **abonnement ressource** permet à un consommateur de s'abonner à un
**événement ressource spécifique**.

**Règles de modélisation :**

| Règle | Description |
|-------|-------------|
| **Cible précise** | Référence un événement ressource spécifique |
| **Lien métier** | Référence l'abonnement métier associée via `linked_business_subscription` |
| **Propriétés complètes** | Le consommateur accède à toutes les propriétés (communes + spécialisées) |

**Cas d'usage :**
- Consommateur spécialisé qui traite une variante particulière
- Consommateur qui a besoin des propriétés spécialisées

---

## Relations entre les deux niveaux

### Tableau de synthèse des relations

| Relation | Source | Cible | Champ |
|----------|--------|-------|-------|
| Porte | Événement Métier | Objet Métier | `carried_business_object` |
| Implémente | Ressource | Objet Métier | `business_object` |
| Implémente | Ressource.data[] | Objet Métier.data[] | `business_object_property` |
| Porte | Événement Ressource | Ressource | `carried_resource` |
| Implémente | Événement Ressource | Événement Métier | `business_event` |
| Cible | Abonnement Métier | Événement Métier | `subscribed_event` |
| Cible | Abonnement Ressource | Événement Ressource | `subscribed_resource_event` |
| Lie | Abonnement Ressource | Abonnement Métier | `linked_business_subscription` |

### Exemple complet de modélisation

```
Niveau Métier
─────────────
OBJ.COEUR.005.DECLARATION_SINISTRE
    └── data: identifiantDeclaration, dateSurvenance, identifiantContrat...

EVT.COEUR.005.SINISTRE_DECLARE
    └── carried_business_object: OBJ.COEUR.005.DECLARATION_SINISTRE

Niveau Ressource (Variante 1 : Dégât des eaux)
──────────────────────────────────────────────
RES.COEUR.005.DECLARATION_SINISTRE_HABITATION_DEGAT_EAUX
    ├── business_object: OBJ.COEUR.005.DECLARATION_SINISTRE
    └── data: identifiantDeclaration (→BO), dateSurvenance (→BO), origineFuite, zoneImpactee...

EVT.RES.COEUR.005.SINISTRE_HABITATION_DEGAT_EAUX_DECLARE
  ├── carried_resource: RES.COEUR.005.DECLARATION_SINISTRE_HABITATION_DEGAT_EAUX
  └── business_event: EVT.COEUR.005.SINISTRE_DECLARE

Niveau Ressource (Variante 2 : Vol)
───────────────────────────────────
RES.COEUR.005.DECLARATION_SINISTRE_HABITATION_VOL
    ├── business_object: OBJ.COEUR.005.DECLARATION_SINISTRE
    └── data: identifiantDeclaration (→BO), dateSurvenance (→BO), typeVol, biensVoles...

EVT.RES.COEUR.005.SINISTRE_HABITATION_VOL_DECLARE
  ├── carried_resource: RES.COEUR.005.DECLARATION_SINISTRE_HABITATION_VOL
  └── business_event: EVT.COEUR.005.SINISTRE_DECLARE
```

---

## Règles de validation

Le référentiel BCM valide automatiquement les règles suivantes :

| Règle | Niveau | Description |
|-------|--------|-------------|
| V1 | Métier | Tout événement métier référence un objet métier existant |
| V2 | Ressource | Toute ressource référence un unique objet métier existant |
| V3 | Ressource | Tout événement ressource référence un unique événement métier existant |
| V4 | Traçabilité | Toute propriété d'objet métier est référencée par au moins une ressource |
| V5 | Abonnement | Toute abonnement ressource référence une abonnement métier existante |
| V6 | Cohérence | L'événement métier de l'abonnement ressource correspond à celui de l'abonnement métier liée |

---

## Anti-patterns à éviter

### ❌ Événement générique avec typologie

```yaml
# INCORRECT — force le décodage polymorphe côté consommateur
id: EVT.RES.COEUR.005.SINISTRE_DECLARE
data:
  - name: typologie        # "DEGAT_EAUX", "VOL", "INCENDIE"
  - name: payloadGenerique # structure variable selon typologie
```

### ❌ Double publication pour le même fait

```yaml
# INCORRECT — impose une corrélation côté consommateur
# Publication 1 : événement générique
id: EVT.RES.COEUR.005.SINISTRE_DECLARE
# Publication 2 : événement spécialisé (en parallèle, même instant)
id: EVT.RES.COEUR.005.SINISTRE_HABITATION_DEGAT_EAUX_DECLARE
```

### ❌ Événement ressource dépendant d'un pair

```yaml
# INCORRECT — nécessite une jointure pour être compris
id: EVT.RES.COEUR.005.SINISTRE_HABITATION_DEGAT_EAUX_DECLARE
data:
  - name: parentEventId    # pointe vers un événement publié en parallèle
    required: true
```

---

## Justification

Cette architecture à deux niveaux permet de :

- **Séparer l'abstraction de l'implémentation** : l'événement métier abstrait le
  jalon, l'événement ressource matérialise la variante
- **Supporter les variantes sans complexité** : pas de nouveau concept, exploitation
  du méta-modèle existant
- **Faciliter la consommation transverse** : abonnement métier pour les consommateurs
  généralistes
- **Garantir la traçabilité** : chaque propriété de ressource peut être tracée vers
  l'objet métier source
- **Simplifier la gouvernance** : distinction claire entre abstraction et implémentation

---

## Impacts

### Structure
- Aucune extension du méta-modèle (ADR-BCM-URBA-0007)
- Clarification de l'usage des relations existantes

### Validation
- Règle ajoutée : toute propriété d'objet métier doit être référencée par au moins
  une ressource via `business_object_property`

### Outillage
- Les outils de génération et validation exploitent les deux niveaux pour produire
  documentation et diagrammes cohérents

---

## Indicateurs de gouvernance

- **Couverture objet métier** : % de propriétés d'objet métier référencées par des ressources
- **Cohérence événementielle** : tous les événements ressource référencent un événement métier
- **Autonomie des événements** : aucun événement ressource ne dépend d'un pair pour être compris

---

## Traçabilité

- Atelier : Modélisation événementielle BCM
- Participants : Urbanisme SI, Architecture, Lead BA, BA, Lead Dev
- Références : ADR-BCM-URBA-0007, ADR-BCM-FUNC-0003
