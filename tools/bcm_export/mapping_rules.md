# Règles d'Export BCM vers EventCatalog

## Vue d'ensemble

Ce document formalise les règles de transformation des éléments BCM (Business Capability Map) vers un EventCatalog compatible.

## Conventions BCM Sources

### Préfixes et Hiérarchie

- **CAP.COEUR.XXX** : Capacité métier de niveau L1 (domaine)
- **CAP.COEUR.XXX.YYY** : Capacité métier de niveau L2 (service) avec parent L1
- **EVT.COEUR.XXX.ZZZ** : Événement métier émis par une capacité L2
- **OBJ.COEUR.XXX.AAA** : Objet métier porté par un événement

### Relations Structurelles BCM

1. **Hiérarchie Capacités** : `CAP.L2.parent → CAP.L1.id`
2. **Production d'Événements** : `EVT.emitting_capability → CAP.L2.id`
3. **Portage d'Objet** : `EVT.carried_business_object → OBJ.id`
4. **Unidirectionnalité** : l'objet métier ne référence pas l'événement en retour

## Conventions Cibles EventCatalog

### Mapping des Types

| Type BCM | Type EventCatalog | Structure Cible |
|----------|-------------------|-----------------|
| CAP L1   | Domain           | `domains/{slug}/index.mdx` |
| CAP L2   | Service          | `domains/{domain-slug}/services/{slug}/index.mdx` |
| OBJ.*    | Entity           | `domains/{domain-slug}/entities/{slug}/index.mdx` |
| EVT.*    | Event            | `domains/{domain-slug}/services/{service-slug}/events/{slug}/index.mdx` |

### Exclusions

**Totalement exclus de l'export :**
- `RES.*` : Ressources techniques
- `EVT.RES.*` : Événements ressource
- `ABO.RESSOURCE.*` : Abonnements aux événements ressource

## Règles de Nommage Cible

### Generation des Slugs

```
CAP.COEUR.005 → coeur-005
CAP.COEUR.005.DSP → dsp
EVT.COEUR.005.DECLARATION_SINISTRE_RECUE → declaration-sinistre-recue
OBJ.COEUR.005.DECLARATION_SINISTRE_RECUE → declaration-sinistre-recue
```

**Algorithme :**
1. Extraire la partie après le dernier point
2. Convertir en lowercase
3. Remplacer les underscore par des tirets
4. Supprimer les caractères spéciaux

### Génération des Titres

```
CAP.COEUR.005 + name: "Sinistres & Prestations" → "Sinistres & Prestations"
EVT.COEUR.005.DECLARATION_SINISTRE_RECUE + name: "Déclaration de sinistre reçue" → "Déclaration de sinistre reçue"
```

**Règles :**
1. Utiliser le champ `name` si présent
2. Sinon, humaniser l'ID (capitaliser, remplacer _ par espaces)
3. Préserver les accents et caractères spéciaux métier

## Règles de Relations

### Domain ← Service

```yaml
# Service
domain: coeur-005  # slug du L1 parent
```

### Service ← Event  

```yaml
# Event
service: dsp  # slug du L2 émetteur (emitting_capability)
```

### Event → Entity

```yaml
# Event  
entities:
  - id: declaration-sinistre-recue  # slug de l'objet métier porté
```

## Règles de Traçabilité

### Métadonnées de Source

Chaque artefact exporté conserve :

```yaml
# Métadonnées communes
metadata:
  bcm:
    source_id: "CAP.COEUR.005.DSP"
    source_file: "capabilities-COEUR-005-L2.yaml" 
    bcm_type: "capability_l2"
    exported_at: "2026-03-13T10:30:00Z"
```

### Reconstruction des Relations

Les relations BCM sont préservées via :
- **ID de source** : `metadata.bcm.source_id`
- **Relations directes** : champs `domain`, `service`, `entities`
- **Relations inverses** : calculables depuis les métadonnées

## Règles de Validation

### Cohérence Structurelle

1. **L2 a un parent L1** : `capabilities[level=L2].parent` existe dans `capabilities[level=L1]`
2. **Event a un producteur L2** : `events.emitting_capability` existe dans `capabilities[level=L2]`
3. **Event référence un objet valide** : `events.carried_business_object` existe dans `objects`
4. **Pas d'exclus exporté** : aucun `RES.*`, `EVT.RES.*`, `ABO.RESSOURCE.*`

### Unicité

1. **Slugs uniques par type** dans un même scope (domain/service)
2. **IDs BCM uniques** dans les sources

## Conventions d'Ownership

### Priorité d'Attribution

1. **Champ `owner` explicite** dans les données BCM
2. **Owner hérité du parent** (L2 hérite de L1)
3. **Owner par défaut** : équipe propriétaire du domaine L1

### Format Owners EventCatalog

```yaml
owners:
  - gestion-sinistres    # slug normalisé
  - prestations-team
```