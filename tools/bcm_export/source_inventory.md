# Inventaire des Données Sources BCM

## Vue d'ensemble

Ce document recense exhaustivement les champs disponibles dans les fichiers YAML source du BCM, leur sémantique et leur utilité pour l'export EventCatalog.

## Fichiers Sources Identifiés

### Structure des Répertoires BCM

```
bcm/
├── capabilities-L1.yaml                    # Capacités métier niveau 1 (domaines)
├── capabilities-COEUR-005-L2.yaml          # Capacités métier niveau 2 pour COEUR.005 
├── evenement-metier/
│   ├── evenement-metier-COEUR-005.yaml     # Événements métier COEUR.005
│   └── abonnement-metier-COEUR-005.yaml  # Abonnements (à analyser si utile)
├── objet-metier/
│   └── objet-metier-COEUR-005.yaml         # Objets métier COEUR.005
├── evenement-ressource/                     # À EXCLURE de l'export
├── ressource/                               # À EXCLURE de l'export
└── vocab.yaml                               # Vocabulaire et définitions
```

## Inventaire Détaillé par Type

### 1. Capacités L1 (`capabilities-L1.yaml`)

**Structure générale :**
```yaml
meta:                          # Métadonnées du fichier
  bcm_name: string
  version: string  
  last_updated: date
  owners: list[string]

capabilities: list             # Liste des capacités L1
```

**Champs par capacité L1 :**

| Champ | Type | Obligatoire | Description | Utilité Export |
|-------|------|-------------|-------------|----------------|
| `id` | string | ✅ | Identifiant unique `CAP.COEUR.XXX` | Clé primaire, génération slug |
| `name` | string | ✅ | Nom lisible du domaine métier | Titre EventCatalog |
| `level` | string | ✅ | Toujours "L1" pour ce fichier | Validation de type |
| `zoning` | string | ✅ | Zone d'urbanisation (ex: SERVICES_COEUR) | Métadonnée BCM |
| `description` | string | ✅ | Description métier du domaine | Description EventCatalog |
| `owner` | string | ✅ | Équipe/Direction responsable | Owner EventCatalog |
| `adrs` | list[string] | ❌ | Références aux ADR liés | Métadonnées + liens |

**Exemples de valeurs :**
```yaml
- id: CAP.COEUR.005
  name: Sinistres & Prestations
  level: L1
  zoning: SERVICES_COEUR
  description: Déclaration, instruction, indemnisation, accompagnement.
  owner: Gestion Sinistres / Prestations
  adrs:
    - ADR-BCM-FUNC-0001
    - ADR-BCM-FUNC-0002
```

### 2. Capacités L2 (`capabilities-COEUR-005-L2.yaml`)

**Champs par capacité L2 :**

| Champ | Type | Obligatoire | Description | Utilité Export |
|-------|------|-------------|-------------|----------------|
| `id` | string | ✅ | Identifiant unique `CAP.COEUR.XXX.YYY` | Clé primaire, génération slug |
| `name` | string | ✅ | Nom lisible du service métier | Titre EventCatalog |
| `level` | string | ✅ | Toujours "L2" pour ce fichier | Validation de type |
| `parent` | string | ✅ | ID de la capacité L1 parente | Relation service → domain |
| `zoning` | string | ✅ | Zone d'urbanisation héritée | Métadonnée BCM |
| `description` | string | ✅ | Description métier du service | Description EventCatalog |
| `owner` | string | ✅ | Équipe responsable du service | Owner EventCatalog |
| `adrs` | list[string] | ❌ | Références aux ADR liés | Métadonnées + liens |

**Exemples de valeurs :**
```yaml
- id: CAP.COEUR.005.DSP
  name: Déclaration du sinistre / de la prestation
  level: L2
  parent: CAP.COEUR.005
  zoning: SERVICES_COEUR
  description: >-
    Captation et qualification de l'événement garanti (multicanal :
    sociétaire, intermédiaire, partenaire) ; rattachement au contrat.
  owner: Gestion Sinistres / Prestations
  adrs:
    - ADR-BCM-FUNC-0002
```

### 3. Événements Métier (`evenement-metier/evenement-metier-COEUR-005.yaml`)

**Structure générale :**
```yaml
meta:                          # Métadonnées identiques aux capacités
evenements_metier: list        # Liste des événements métier
```

**Champs par événement métier :**

| Champ | Type | Obligatoire | Description | Utilité Export |
|-------|------|-------------|-------------|----------------|
| `id` | string | ✅ | Identifiant unique `EVT.COEUR.XXX.YYY` | Clé primaire, génération slug |
| `name` | string | ✅ | Nom lisible de l'événement | Titre EventCatalog |
| `version` | string | ✅ | Version sémantique (ex: 1.0.0) | Version EventCatalog |
| `definition` | string | ✅ | Description métier détaillée | Description EventCatalog |
| `emitting_capability` | string | ✅ | ID de la capacité L2 émettrice | Relation event → service |
| `carried_business_object` | string | ✅ | ID de l'objet métier associé | Relation event → entity |
| `scope` | string | ✅ | Visibilité (public, internal, private) | Métadonnée EventCatalog |
| `adrs` | list[string] | ❌ | Références aux ADR liés | Métadonnées + liens |
| `tags` | list[string] | ❌ | Tags métier pour classification | Tags EventCatalog |

**Exemples de valeurs :**
```yaml
- id: EVT.COEUR.005.DECLARATION_SINISTRE_RECUE
  name: Déclaration de sinistre reçue
  version: 1.0.0
  definition: >-
    Un signalement de sinistre est reçu, horodaté et tracé depuis un canal
    d'entrée (mail, téléphone, portail, partenaire), avec un niveau de données
    initial potentiellement incomplet.
  emitting_capability: CAP.COEUR.005.DSP
  carried_business_object: OBJ.COEUR.005.DECLARATION_SINISTRE_RECUE
  scope: public
  adrs:
    - ADR-BCM-FUNC-0002
    - ADR-BCM-FUNC-0003
  tags:
    - sinistre
    - declaration
```

### 4. Objets Métier (`objet-metier/objet-metier-COEUR-005.yaml`)

**Structure générale :**
```yaml
meta:                          # Métadonnées identiques
resources: list                # Liste des objets métier (nom historique)
```

**Champs par objet métier :**

| Champ | Type | Obligatoire | Description | Utilité Export |
|-------|------|-------------|-------------|----------------|
| `id` | string | ✅ | Identifiant unique `OBJ.COEUR.XXX.YYY` | Clé primaire, génération slug |
| `name` | string | ✅ | Nom lisible de l'objet | Titre EventCatalog |
| `definition` | string | ✅ | Description métier de l'objet | Description EventCatalog |
| `emitting_capability` | string | ✅ | Capacité L2 responsable de l'objet | Métadonnée de responsabilité |
| `data` | list[field] | ❌ | Modèle de données détaillé | Propriétés EventCatalog |
| `adrs` | list[string] | ❌ | Références aux ADR liés | Métadonnées + liens |
| `tags` | list[string] | ❌ | Tags métier pour classification | Tags EventCatalog |

**Champs du modèle de données (`data`) :**

| Champ | Type | Obligatoire | Description | Utilité Export |
|-------|------|-------------|-------------|----------------|
| `name` | string | ✅ | Nom du champ de données | Nom propriété EventCatalog |
| `type` | string | ✅ | Type de données (string, boolean, datetime...) | Type propriété EventCatalog |
| `description` | string | ✅ | Description du champ | Description propriété |
| `required` | boolean | ✅ | Caractère obligatoire du champ | Attribut required EventCatalog |

**Exemples de valeurs :**
```yaml
- id: OBJ.COEUR.005.DECLARATION_SINISTRE_RECUE
  name: Déclaration sinistre reçue
  definition: >-
    Objet représentant la réception brute d'une déclaration de sinistre,
    horodatée et tracée, avant qualification complète.
  emitting_capability: CAP.COEUR.005.DSP
  data:
    - name: identifiantDeclaration
      type: string
      description: Identifiant unique de la déclaration reçue.
      required: true
    - name: canalDeclaration
      type: string  
      description: Canal d'entrée de la déclaration (mail, téléphone, portail, partenaire).
      required: true
```

## Analyse de Complétude

### Champs Toujours Disponibles ✅

- **Identifiants** : Tous les objets ont un `id` unique et structuré
- **Noms** : Tous les objets ont un `name` lisible  
- **Descriptions** : Toutes les entités ont une description métier
- **Relations** : Les relations structurelles sont explicites et cohérentes

### Champs Optionnels ou Partiels ⚠️

- **ADRs** : Présents mais pas systématiquement sur tous les objets
- **Tags** : Présents sur événements et objets mais pas sur capacités  
- **Modèles de données** : Très détaillés pour les objets mais peuvent être absents
- **Owners normalisés** : Parfois équipes, parfois directions (besoin normalisation)

### Champs Manquants pour EventCatalog 🔴

- **Schémas événements** : Pas de schéma JSON/Avro défini
- **Owners techniques** : Pas d'équipes techniques distinctes du métier
- **Channels/Protocols** : Pas d'info sur les canaux techniques (Kafka, REST...)
- **SLA/Performance** : Pas de données non-fonctionnelles

## Stratégies de Gestion des Données Manquantes

### Fallbacks par Défaut

1. **Owner manquant** : Utiliser l'owner de la capacité L2 ou L1 parente
2. **Description courte** : Tronquer la définition si trop longue
3. **Tags absents** : Générer des tags depuis l'ID et la hiérarchie
4. **Schémas manquants** : Générer un schéma minimal depuis le modèle `data`

### Warnings à Générer

- Objet métier sans modèle de données détaillé
- Événement sans tags de classification  
- Owner non normalisé (contient espaces, caractères spéciaux)
- Description trop longue pour le format cible

## Cas Particuliers Identifiés

### Abonnements Métier

Fichier `abonnement-metier-COEUR-005.yaml` présent mais non analysé.
**Action** : Analyser pour voir si utile pour les relations EventCatalog.

### Vocabulaire Partagé

Fichier `vocab.yaml` présent mais non analysé.
**Action** : Vérifier s'il contient des définitions ou métadonnées utiles.