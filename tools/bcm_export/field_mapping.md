# Mapping Détaillé Champ par Champ BCM → EventCatalog

## Vue d'ensemble

Ce document définit précisément la correspondance entre chaque champ source BCM et chaque champ cible EventCatalog, avec les règles de transformation applicables.

## Mapping Domain (L1 → Domain EventCatalog)

### Structure Cible EventCatalog Domain

```yaml
---
id: string                    # Identifiant unique du domain
name: string                  # Nom lisible du domain  
summary: string               # Description courte
version: string               # Version (optionnel)
owners: list[string]          # Liste des propriétaires
services: list[object]        # Services rattachés (auto-généré)
entities: list[object]        # Entités rattachées (auto-généré)
badges: list[object]          # Badges visuels (optionnel)
metadata: object              # Métadonnées custom
---
```

### Mapping Champs L1 → Domain

| Champ Source BCM | Champ Cible EventCatalog | Transformation | Fallback |
|------------------|--------------------------|----------------|----------|
| `id` | `id` | `SlugGenerator.from_bcm_id()` | **ERREUR** (obligatoire) |
| `name` | `name` | Direct, nettoyage espaces | `TitleGenerator.humanize_id(id)` |
| `description` | `summary` | Troncature à 200 caractères si nécessaire | **ERREUR** (obligatoire) |
| `owner` | `owners[0]` | `OwnerNormalizer.normalize_owner()` | `"unknown-owner"` |
| - | `version` | **Non mappé** | `"1.0.0"` |
| `zoning` | `metadata.bcm.zoning` | Direct | `""` |
| `adrs` | `metadata.bcm.adrs` | Direct (liste) | `[]` |
| `id` | `metadata.bcm.source_id` | Direct | **ERREUR** |
| `source.source_file` | `metadata.bcm.source_file` | Direct | `null` |
| - | `metadata.bcm.bcm_type` | Constante `"capability_l1"` | **ERREUR** |
| - | `metadata.bcm.exported_at` | `datetime.now().isoformat()` | **ERREUR** |

### Exemple de Transformation L1

```yaml
# Source BCM
- id: CAP.COEUR.005
  name: Sinistres & Prestations
  description: Déclaration, instruction, indemnisation, accompagnement.
  owner: Gestion Sinistres / Prestations
  zoning: SERVICES_COEUR

# Cible EventCatalog
---
id: coeur-005
name: Sinistres & Prestations
summary: Déclaration, instruction, indemnisation, accompagnement.
version: 1.0.0
owners:
  - gestion-sinistres-prestations
services: []  # Auto-généré
entities: []  # Auto-généré
metadata:
  bcm:
    source_id: CAP.COEUR.005
    source_file: capabilities-L1.yaml
    bcm_type: capability_l1
    zoning: SERVICES_COEUR
    exported_at: 2026-03-13T10:30:00Z
---
```

## Mapping Service (L2 → Service EventCatalog)

### Structure Cible EventCatalog Service

```yaml
---
id: string                    # Identifiant unique du service
name: string                  # Nom lisible du service
summary: string               # Description courte  
version: string               # Version (optionnel)
domain: string                # Slug du domain parent
owners: list[string]          # Liste des propriétaires
receives: list[object]        # Events reçus (non implémenté)
sends: list[object]           # Events émis (auto-généré)
metadata: object              # Métadonnées custom
---
```

### Mapping Champs L2 → Service

| Champ Source BCM | Champ Cible EventCatalog | Transformation | Fallback |
|------------------|--------------------------|----------------|----------|
| `id` | `id` | `SlugGenerator.from_bcm_id()` (dernière partie) | **ERREUR** |
| `name` | `name` | Direct, nettoyage espaces | `TitleGenerator.humanize_id(id)` |
| `description` | `summary` | Troncature à 200 caractères si nécessaire | **ERREUR** |
| `parent` | `domain` | `SlugGenerator.from_bcm_id(parent)` | **ERREUR** |
| `owner` | `owners[0]` | `OwnerNormalizer.normalize_owner()` | Hérite du L1 parent |
| - | `version` | **Non mappé** | `"1.0.0"` |
| - | `receives` | **Non implémenté** | `[]` |
| - | `sends` | **Auto-généré** depuis événements | `[]` |
| `id` | `metadata.bcm.source_id` | Direct | **ERREUR** |
| `parent` | `metadata.bcm.parent_l1_id` | Direct | **ERREUR** |
| `zoning` | `metadata.bcm.zoning` | Direct | `""` |
| `adrs` | `metadata.bcm.adrs` | Direct (liste) | `[]` |

### Exemple de Transformation L2

```yaml
# Source BCM  
- id: CAP.COEUR.005.DSP
  name: Déclaration du sinistre / de la prestation
  parent: CAP.COEUR.005
  description: Captation et qualification de l'événement garanti...
  owner: Gestion Sinistres / Prestations

# Cible EventCatalog
---
id: dsp
name: Déclaration du sinistre / de la prestation
summary: Captation et qualification de l'événement garanti...
version: 1.0.0
domain: coeur-005
owners:
  - gestion-sinistres-prestations
receives: []
sends: []  # Auto-généré depuis les EVT qui ont emitting_capability = CAP.COEUR.005.DSP
metadata:
  bcm:
    source_id: CAP.COEUR.005.DSP
    source_file: capabilities-COEUR-005-L2.yaml
    bcm_type: capability_l2
    parent_l1_id: CAP.COEUR.005
    zoning: SERVICES_COEUR
    exported_at: 2026-03-13T10:30:00Z
---
```

## Mapping Entity (OBJ → Entity EventCatalog)

### Structure Cible EventCatalog Entity

```yaml
---
id: string                    # Identifiant unique de l'entité
name: string                  # Nom lisible de l'entité
version: string               # Version (optionnel)
summary: string               # Description courte
identifier: string            # Champ identifiant principal (optionnel)
aggregateRoot: boolean        # Root d'agrégat (optionnel)
domain: string                # Slug du domain de rattachement
owners: list[string]          # Liste des propriétaires
properties: list[object]      # Propriétés de l'entité
schemaPath: string            # Chemin vers schéma (optionnel)
metadata: object              # Métadonnées custom
---
```

### Mapping Champs OBJ → Entity

| Champ Source BCM | Champ Cible EventCatalog | Transformation | Fallback |
|------------------|--------------------------|----------------|----------|
| `id` | `id` | `SlugGenerator.from_bcm_id()` (dernière partie) | **ERREUR** |
| `name` | `name` | Direct, nettoyage espaces | `TitleGenerator.humanize_id(id)` |
| `definition` | `summary` | Troncature à 200 caractères si nécessaire | **ERREUR** |
| - | `version` | **Non mappé** | `"1.0.0"` |
| - | `identifier` | **Détection auto** (premier champ required) | `null` |
| - | `aggregateRoot` | **Non mappé** | `false` |
| `emitting_capability` | `domain` | Résolution via L2→L1, puis slug | **ERREUR** |
| - | `owners` | **Non mappé** (pas d'owner pour entities) | `["unknown-owner"]` |
| `data[].name` | `properties[].name` | Direct | **ERREUR** si data présent |
| `data[].type` | `properties[].type` | Direct | **ERREUR** si data présent |
| `data[].description` | `properties[].description` | Direct | **ERREUR** si data présent |
| `data[].required` | `properties[].required` | Direct (boolean) | **ERREUR** si data présent |
| - | `schemaPath` | **Non mappé** | `null` |
| `id` | `metadata.bcm.source_id` | Direct | **ERREUR** |
| `emitting_capability` | `metadata.bcm.emitting_capability_id` | Direct | **ERREUR** |
| `tags` | `metadata.bcm.tags` | Direct (liste) | `[]` |

### Exemple de Transformation OBJ

```yaml
# Source BCM
- id: OBJ.COEUR.005.DECLARATION_SINISTRE_RECUE  
  name: Déclaration sinistre reçue
  definition: Objet représentant la réception brute d'une déclaration...
  emitting_capability: CAP.COEUR.005.DSP
  data:
    - name: identifiantDeclaration
      type: string
      description: Identifiant unique de la déclaration reçue.
      required: true
    - name: canalDeclaration
      type: string
      description: Canal d'entrée de la déclaration.
      required: true

# Cible EventCatalog
---
id: declaration-sinistre-recue
name: Déclaration sinistre reçue  
version: 1.0.0
summary: Objet représentant la réception brute d'une déclaration...
identifier: identifiantDeclaration
aggregateRoot: false
domain: coeur-005
owners:
  - unknown-owner
properties:
  - name: identifiantDeclaration
    type: string
    required: true
    description: Identifiant unique de la déclaration reçue.
  - name: canalDeclaration
    type: string  
    required: true
    description: Canal d'entrée de la déclaration.
metadata:
  bcm:
    source_id: OBJ.COEUR.005.DECLARATION_SINISTRE_RECUE
    source_file: objet-metier-COEUR-005.yaml
    bcm_type: business_object
    emitting_capability_id: CAP.COEUR.005.DSP
    exported_at: 2026-03-13T10:30:00Z
---
```

## Mapping Event (EVT → Event EventCatalog)

### Structure Cible EventCatalog Event

```yaml
---
id: string                    # Identifiant unique de l'événement
name: string                  # Nom lisible de l'événement
version: string               # Version sémantique
summary: string               # Description courte
service: string               # Slug du service émetteur
domain: string                # Slug du domain (via service)
owners: list[string]          # Liste des propriétaires  
entities: list[object]        # Entités associées
producers: list[object]       # Producteurs (optionnel)
consumers: list[object]       # Consommateurs (non implémenté)
schemaPath: string            # Chemin vers schéma (optionnel)
badges: list[object]          # Badges visuels (optionnel)
metadata: object              # Métadonnées custom
---
```

### Mapping Champs EVT → Event

| Champ Source BCM | Champ Cible EventCatalog | Transformation | Fallback |
|------------------|--------------------------|----------------|----------|
| `id` | `id` | `SlugGenerator.from_bcm_id()` (dernière partie) | **ERREUR** |
| `name` | `name` | Direct, nettoyage espaces | `TitleGenerator.humanize_id(id)` |
| `version` | `version` | Direct (validation semver recommandée) | **ERREUR** |
| `definition` | `summary` | Troncature à 200 caractères si nécessaire | **ERREUR** |
| `emitting_capability` | `service` | Résolution L2→slug | **ERREUR** |
| `emitting_capability` | `domain` | Résolution L2→L1→slug | **ERREUR** |
| - | `owners` | **Non mappé** (pas d'owner pour events) | `["unknown-owner"]` |
| `carried_business_object` | `entities[0].id` | `SlugGenerator.from_bcm_id()` | **ERREUR** |
| - | `producers` | **Auto-généré** (service émetteur) | `[]` |
| - | `consumers` | **Non implémenté** | `[]` |
| - | `schemaPath` | **Non mappé** | `null` |
| `scope` | `badges[0].content` | `"Scope: {scope}"` si != public | `[]` |
| `tags` | `badges` | Conversion en badges couleur | `[]` |
| `id` | `metadata.bcm.source_id` | Direct | **ERREUR** |
| `emitting_capability` | `metadata.bcm.emitting_capability_id` | Direct | **ERREUR** |
| `carried_business_object` | `metadata.bcm.business_object_id` | Direct | **ERREUR** |
| `scope` | `metadata.bcm.scope` | Direct | **ERREUR** |
| `adrs` | `metadata.bcm.adrs` | Direct (liste) | `[]` |
| `tags` | `metadata.bcm.tags` | Direct (liste) | `[]` |

### Exemple de Transformation EVT

```yaml
# Source BCM
- id: EVT.COEUR.005.DECLARATION_SINISTRE_RECUE
  name: Déclaration de sinistre reçue
  version: 1.0.0
  definition: Un signalement de sinistre est reçu, horodaté et tracé...
  emitting_capability: CAP.COEUR.005.DSP
  carried_business_object: OBJ.COEUR.005.DECLARATION_SINISTRE_RECUE
  scope: public
  tags:
    - sinistre
    - declaration

# Cible EventCatalog
---
id: declaration-sinistre-recue
name: Déclaration de sinistre reçue
version: 1.0.0
summary: Un signalement de sinistre est reçu, horodaté et tracé...
service: dsp
domain: coeur-005
owners:
  - unknown-owner
entities:
  - id: declaration-sinistre-recue
producers:
  - service: dsp
consumers: []
schemaPath: null
badges:
  - content: "Tag: sinistre"
    backgroundColor: blue
    textColor: white
  - content: "Tag: declaration"
    backgroundColor: blue  
    textColor: white
metadata:
  bcm:
    source_id: EVT.COEUR.005.DECLARATION_SINISTRE_RECUE
    source_file: evenement-metier-COEUR-005.yaml
    bcm_type: business_event
    emitting_capability_id: CAP.COEUR.005.DSP
    business_object_id: OBJ.COEUR.005.DECLARATION_SINISTRE_RECUE
    scope: public
    adrs: []
    tags: [sinistre, declaration]
    exported_at: 2026-03-13T10:30:00Z
---
```

## Relations Auto-générées

### Services dans Domains

Les domain EventCatalog incluent automatiquement la liste des services rattachés :

```yaml
# Domain
services:
  - id: dsp        # Tous les L2 ayant parent = ce L1
  - id: oed
  - id: ind
```

### Events dans Services

Les service EventCatalog incluent automatiquement la liste des événements émis :

```yaml
# Service
sends:
  - id: declaration-sinistre-recue    # Tous les EVT ayant emitting_capability = ce L2
    version: 1.0.0
  - id: declaration-sinistre-qualifiee
    version: 1.0.0
```

### Entities dans Domains

Les domain EventCatalog incluent automatiquement la liste des entités :

```yaml
# Domain  
entities:
  - id: declaration-sinistre-recue    # Tous les OBJ rattachés via leur emitting_capability L2→L1
  - id: dossier-sinistre
```

## Règles de Validation des Mappings

### Champs Obligatoires

**Erreur bloquante si absent :**
- Tous les `id` sources et cibles
- `name` ou possibilité de humaniser l'ID
- `description/definition` → `summary`
- Relations obligatoires (parent, emitting_capability)

### Champs Optionnels avec Fallback

**Warning si absent, valeur par défaut :**
- `version` → `"1.0.0"`
- `owners` → `["unknown-owner"]`
- `tags` → `[]`
- `adrs` → `[]`

### Validation de Cohérence

1. **Unicité des slugs** dans chaque scope (domain/service)
2. **Références valides** : toutes les relations pointent vers des éléments existants
3. **Format des slugs** : respect du pattern EventCatalog `^[a-z0-9-]+$`
4. **Longueur des summary** : <= 500 caractères recommandé

## Métadonnées BCM Préservées

Toutes les données sources BCM sont préservées dans `metadata.bcm` pour :
- **Traçabilité** : retrouver la source d'un élément EventCatalog  
- **Reconstruction** : pouvoir régénérer le BCM depuis EventCatalog
- **Debugging** : identifier les erreurs de mapping
- **Évolution** : faciliter les migrations de versions futures