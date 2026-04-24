# 🛠 Outils BCM

Ce répertoire contient les scripts utilitaires du référentiel BCM :
validation, génération de vues et export de diagrammes.

## Pré-requis

```bash
pip install -r tools/requirements.txt
```

Seule dépendance : **PyYAML** (`pyyaml`).

---

## Sommaire

| Script | Description |
|--------|-------------|
| [`render_drawio.py`](#render_drawiopy) | Génère un diagramme draw.io L1 (`.drawio`) à partir d'un fichier YAML de capacités |
| [`render_drawio_l2.py`](#render_drawio_l2py) | Génère un diagramme draw.io L2 (`.drawio`) avec les capacités L2 groupées dans leurs L1 |
| [`render_drawio_capability_chain.py`](#render_drawio_capability_chainpy) | Génère une chaîne production/consommation interne à une capacité L1 |
| [`render_drawio_subscriptions.py`](#render_drawio_subscriptionspy) | Génère une vue draw.io des abonnements métier à partir du template de abonnement |
| [`validate_events.py`](#validate_eventspy) | Valide les références d'événements contre les capacités BCM |
| [`validate_repo.py`](#validate_repopy) | Validation structurelle du repository (fichiers, YAML, cohérence) |
| [`check_docs_links.py`](#check_docs_linkspy) | Vérifie les liens Markdown internes (fichiers + ancres) pour CI/CD |
| [`semantic_review.py`](#semantic_reviewpy) | Agent CI de cohérence sémantique PR (ADR puis ADR+BCM) + rapport PR |
| [`concat_files.py`](#concat_filespy) | Concatène tous les fichiers ADR et BCM en un seul document |
| [`run_eventcatalogs.sh`](#run_eventcatalogssh) | Lance FOODAROO-Metier et FOODAROO-SI en parallèle avec arrêt propre |
---

## run_eventcatalogs.sh

Lance simultanément les deux instances EventCatalog :

- `views/FOODAROO-Metier` (port par défaut `4444`)
- `views/FOODAROO-SI` (port par défaut `4445`)

Le script :

- vérifie la présence des projets (`package.json`) ;
- installe automatiquement les dépendances npm si `node_modules` est absent ;
- démarre les deux serveurs en parallèle ;
- gère un arrêt propre des deux processus (`Ctrl+C`).

### Usage

```bash
# Depuis la racine du repository
bash tools/run_eventcatalogs.sh

# Ports personnalisés
METIER_PORT=3010 SI_PORT=3011 bash tools/run_eventcatalogs.sh
```

### Variables d'environnement

| Variable | Description | Défaut |
|----------|-------------|--------|
| `METIER_PORT` | Port de `views/FOODAROO-Metier` | `4444` |
| `SI_PORT` | Port de `views/FOODAROO-SI` | `4445` |

---

## render_drawio.py

Génère un diagramme draw.io **L1** (`.drawio`) à partir d'un fichier YAML de capacités,
avec la disposition classique du POS.
Chaque capacité L1 est une boîte colorée placée dans sa zone.

### Fonctionnalités

- **7 zones colorées** disposées selon le layout BCM standard
- **Couleurs pastels distinctives** par capacité L1 (palette de 16 couleurs en cycle)
- **Disposition en grille** automatique des boîtes à l'intérieur de chaque zone
- **Zones vides** rendues comme rectangles colorés (se remplissent quand les capacités sont ajoutées au YAML)

### Disposition des zones

```
┌──────────────────────────────────────────────────────┐
│                    PILOTAGE                          │
├──────────┬──────────────────────────────┬────────────┤
│          │  SERVICES_COEUR │            │
│  B2B     ├──────────────────────────────┤  CANAL   │
│ EXCHANGE │       SUPPORT               │            │
│          ├──────────────────────────────┤            │
│          │      REFERENTIEL            │            │
├──────────┴──────────────────────────────┴────────────┤
│                 DATA_ANALYTIQUE                       │
└──────────────────────────────────────────────────────┘
```

### Usage

```bash
# Génération par défaut
#   entrée : bcm/capabilities-L1.yaml
#   sortie : views/BCM-L1-generated.drawio
python tools/render_drawio.py

# Fichier d'entrée spécifique
python tools/render_drawio.py --input bcm/capabilities-L1.yaml

# Fichier de sortie personnalisé
python tools/render_drawio.py --output views/mon-bcm.drawio

# Modifier le nombre de colonnes dans les zones centrales (défaut : 4)
python tools/render_drawio.py --cols 3
```

### Options

| Option | Description | Défaut |
|--------|-------------|--------|
| `-i`, `--input` | Fichier YAML source des capacités | `bcm/capabilities-L1.yaml` |
| `-o`, `--output` | Chemin du fichier `.drawio` généré | `views/BCM-L1-generated.drawio` |
| `--cols` | Nombre de colonnes dans les zones centrales | `4` |

### Format YAML attendu

Le fichier d'entrée doit suivre la structure de `bcm/capabilities-L1.yaml` :

```yaml
meta:
  bcm_name: BCM Urbanisation
  version: 0.1.0

capabilities:
  - id: CAP.COEUR.001
    name: Produits & Tarification
    level: L1
    zoning: SERVICES_COEUR   # détermine la zone de placement
    description: ...
    owner: ...
    adrs: []
```

Le champ `zoning` détermine dans quelle zone la capacité sera placée.
Valeurs reconnues : `PILOTAGE`, `SERVICES_COEUR`, `SUPPORT`,
`REFERENTIEL`, `ECHANGE_B2B`, `CANAL`, `DATA_ANALYTIQUE`.

### Sortie

Le fichier `.drawio` généré s'ouvre directement dans :

- **draw.io Desktop** (fichier → ouvrir)
- **draw.io Web** ([app.diagrams.net](https://app.diagrams.net))
- **Extension VS Code** draw.io

Le diagramme peut être enrichi manuellement après génération.

---

## render_drawio_l2.py

Génère un diagramme draw.io **L2** (`.drawio`) à partir de **tous** les fichiers
`capabilities-*.yaml` du répertoire `bcm/`.
Chaque capacité L1 est un *groupe draw.io* contenant ses boîtes L2.

### Fonctionnalités

- **Lecture automatique** de tous les fichiers `bcm/capabilities-*.yaml` (L1 + L2)
- **Hiérarchie L1 → L2** : les L2 sont rattachées à leur parent via le champ `parent`
- **Groupes draw.io** : chaque L1 est un groupe contenant un fond coloré, un titre et les boîtes L2
- **Couleurs fidèles au template** `BCM L2 template.drawio` :
  - Zones : mêmes codes couleur que `render_drawio.py` (`ZONE_CONFIG`)
  - Fonds L1 : palette pastel tournante (`CAPABILITY_PALETTE`, 16 couleurs)
  - Boîtes L2 : couleur par zone (pêche `#ffe6cc` pour COEUR, bleu ciel `#dae8fc` pour Pilotage, doré `#FFE599` pour B2B/Canal, lavande `#e1d5e7` pour Data)
- **Placeholder** pour les L1 sans L2 défini
- **Contenu 100 % YAML** — rien n'est inventé

### Disposition

Même layout que `render_drawio.py` :

```
┌──────────────────────────────────────────────────────┐
│                    PILOTAGE                          │
├──────────┬──────────────────────────────┬────────────┤
│          │  COEUR  ┌─────────┐ ┌────────┐│            │
│  B2B     │       │ L1      │ │ L1     ││  CANAL   │
│ EXCHANGE │       │  ┌─L2─┐ │ │ (vide) ││            │
│          │       │  └────┘ │ └────────┘│            │
│          ├───────┴─────────┴───────────┤            │
│          │       SUPPORT               │            │
│          ├─────────────────────────────┤            │
│          │      REFERENTIEL            │            │
├──────────┴─────────────────────────────┴────────────┤
│                 DATA_ANALYTIQUE                       │
└──────────────────────────────────────────────────────┘
```

### Usage

```bash
# Génération par défaut
#   entrée : bcm/capabilities-*.yaml
#   sortie : views/BCM-L2-generated.drawio
python tools/render_drawio_l2.py

# Répertoire d'entrée spécifique
python tools/render_drawio_l2.py --input-dir bcm

# Fichier de sortie personnalisé
python tools/render_drawio_l2.py --output views/mon-bcm-l2.drawio

# Modifier le nombre de colonnes L2 dans un groupe L1 (défaut : 2)
python tools/render_drawio_l2.py --l2-cols 3

# Modifier le nombre de groupes L1 par ligne dans les zones centrales (défaut : 3)
python tools/render_drawio_l2.py --l1-cols 4
```

### Options

| Option | Description | Défaut |
|--------|-------------|--------|
| `-d`, `--input-dir` | Répertoire contenant les `capabilities-*.yaml` | `bcm/` |
| `-o`, `--output` | Chemin du fichier `.drawio` généré | `views/BCM-L2-generated.drawio` |
| `--l2-cols` | Nombre de colonnes L2 dans un groupe L1 | `2` |
| `--l1-cols` | Nombre de groupes L1 par ligne (zones centrales) | `3` |

### Format YAML attendu

Le script attend des fichiers `capabilities-*.yaml` avec des entrées L1 et L2 :

```yaml
capabilities:
  # Capacité L1
  - id: CAP.COEUR.005
    name: Sinistres & Prestations
    level: L1
    zoning: SERVICES_COEUR
    ...

  # Capacité L2 (rattachée via parent)
  - id: CAP.COEUR.005.DSP
    name: Déclaration du sinistre
    level: L2
    parent: CAP.COEUR.005              # ← rattachement au L1
    zoning: SERVICES_COEUR
    ...
```

---

## render_drawio_subscriptions.py

Génère une vue draw.io des **abonnements métier** en appliquant la géométrie
et les styles du template `views/template-abonnement.drawio` :

- **sans argument** : rend toutes les capacités souscriptrices, un fichier par capacité,
  dans `views/abonnements/`,
- capacité émettrice → événement (ancre haut vers milieu),
- événement → capacité consommatrice (flèche pointillée, ancre haut/bas selon position),
- mode consolidé par capacité souscriptrice : une seule brique avec toutes ses abonnements,
  et toutes les capacités émettrices alignées sur une même colonne.

### Usage

```bash
# Génération par défaut (batch: toutes les capacités souscriptrices)
python tools/render_drawio_subscriptions.py

# Rendu consolidé pour une capacité souscriptrice
python tools/render_drawio_subscriptions.py \
  --consumer-capacité CAP.COEUR.005.CAD

# Nom de fichier auto basé sur l'ID de la capacité souscriptrice si --output n'est pas fourni
# ex: views/COEUR.005.CAD-abonnements.drawio

# Répertoire de sortie personnalisé en mode batch
python tools/render_drawio_subscriptions.py --output-dir views/abonnements

# Fichier de sortie explicite (mode mono-capacité uniquement)
python tools/render_drawio_subscriptions.py \
  --consumer-capacité CAP.COEUR.005.CAD \
  --output views/abonnements/COEUR.005.CAD-abonnements.drawio

# Filtrage sur un parent L1 (ex: CAP.COEUR.005)
python tools/render_drawio_subscriptions.py --focus-parent-l1 CAP.COEUR.005

# Entrées/sortie personnalisées
python tools/render_drawio_subscriptions.py \
  --bcm-dir bcm \
  --events-dir bcm/evenement-metier \
  --template views/template-abonnement.drawio \
  --output views/abonnements-metier-generated.drawio
```

### Options

| Option | Description | Défaut |
|--------|-------------|--------|
| `--bcm-dir` | Répertoire contenant les `capabilities-*.yaml` | `bcm` |
| `--events-dir` | Répertoire des `evenement-metier-*.yaml` et `abonnement-metier-*.yaml` | `bcm/evenement-metier` |
| `--template` | Template draw.io de référence | `views/template-abonnement.drawio` |
| `--output` | Fichier `.drawio` généré (mono-capacité uniquement) | *(optionnel)* |
| `--output-dir` | Répertoire de sortie des rendus | `views/abonnements` |
| `--focus-parent-l1` | Filtre sur un parent L1 | *(optionnel)* |
| `--consumer-capacité` | Capacité souscriptrice cible ; active le rendu consolidé | *(optionnel)* |
| `--diagram-name` | Nom de l'onglet draw.io | `Abonnements metier` |

En mode `--consumer-capacité`, si `--output` n'est pas précisé,
le nom du fichier est généré automatiquement avec le format `<ID_L2>-abonnements.drawio`
(ex: `COEUR.005.CAD-abonnements.drawio`).

Sans `--consumer-capacité`, le script rend toutes les capacités souscriptrices et écrit
un fichier par capacité dans `--output-dir`.

---

## render_drawio_capability_chain.py

Génère un rendu Draw.io de la **chaîne de production/consommation** au sein d'une
capacité **L1** (capabilités L2/L3 internes), en s'alignant sur le template
`views/capacites/COEUR.005-chaine-abonnements-template.drawio`.

Principes de rendu :

- toutes les capacités de la L1 sont incluses,
- la chaîne principale est positionnée de gauche à droite,
- les événements intermédiaires sont rendus entre producteur et consommateur,
  plus haut que leur capacité productrice,
- les origines/cibles des flèches sont individualisées pour limiter les croisements,
- placement des événements avec évitement de collision pour réduire la superposition des textes.

### Usage

```bash
# Batch par défaut : toutes les L1 ayant une chaîne interne détectée
python tools/render_drawio_capability_chain.py

# Rendu ciblé sur une L1
python tools/render_drawio_capability_chain.py --l1-capacité CAP.COEUR.005

# Répertoire de sortie personnalisé
python tools/render_drawio_capability_chain.py --output-dir views/capacites
```

### Options

| Option | Description | Défaut |
|--------|-------------|--------|
| `--bcm-dir` | Répertoire contenant les `capabilities-*.yaml` | `bcm` |
| `--events-dir` | Répertoire des `evenement-metier-*.yaml` et `abonnement-metier-*.yaml` | `bcm/evenement-metier` |
| `--template` | Template draw.io de référence | `views/capacites/COEUR.005-chaine-abonnements-template.drawio` |
| `--l1-capacité` | Capacité L1 ciblée | *(optionnel)* |
| `--output` | Fichier `.drawio` généré (mono-capacité uniquement) | *(optionnel)* |
| `--output-dir` | Répertoire de sortie des rendus | `views/capacites` |
| `--diagram-name` | Nom de l'onglet draw.io | `Chaine capacite L1` |

Le nom de fichier suit le format `<ID_L1>-chaine-abonnements.drawio`
(ex: `COEUR.005-chaine-abonnements.drawio`).

---

## validate_events.py

Valide **en masse** les assets d'événements (sous-répertoires de `bcm/`) contre les capacités BCM
(`bcm/capabilities-*.yaml`) et vérifie les relations cross-assets :

- événements métier ↔ objets métier,
- relation unidirectionnelle événement métier → objet métier (pas de référence inverse dans l'objet métier),
- événements ressource ↔ ressources ↔ événements métier,
- abonnements métier ↔ événements métier,
- abonnements ressource ↔ événements ressource ↔ abonnements métier,
- objets métier ↔ capacités L2/L3 avec contrainte `emitting_capability_L3` si la L2 référencée possède des L3.
- processus externes ↔ capacités/événements :
  - `externals/processus-metier/*.yaml` : vérifie l'existence des capacités, événements métier **et abonnements métier** référencés,
  - `externals/processus-ressource/*.yaml` : vérifie l'existence des capacités, événements ressource **et abonnements ressource** référencés.

Les fichiers `template-*.yaml` sont ignorés automatiquement.

### Usage

```bash
# Mode batch (défaut recommandé)
python tools/validate_events.py

# Mode batch avec répertoires personnalisés
python tools/validate_events.py \
  --bcm-dir bcm \
  --events-dir bcm

# Mode legacy fichier unique (compatibilité)
python tools/validate_events.py \
  --bcm bcm/capabilities-L1.yaml \
  --events bcm/evenement-metier/evenement-metier-COEUR-005.yaml
```

### Options

| Option | Description | Défaut |
|--------|-------------|--------|
| `--bcm-dir` | Répertoire contenant les `capabilities-*.yaml` | `bcm` |
| `--events-dir` | Répertoire racine contenant les assets événements | `bcm` |
| `--bcm` | Mode legacy : fichier unique de capacités | *(optionnel)* |
| `--events` | Mode legacy : fichier unique d'événements métier | *(optionnel)* |

---
---

## validate_repo.py

Validation structurelle du référentiel BCM.
Charge **tous** les fichiers `bcm/capabilities-*.yaml` et vérifie la cohérence
globale des capacités, tous fichiers confondus.

### Règles actuelles (extraites du code)

Le script applique les règles suivantes, dans cet ordre.

#### 0) Pré-contrôles bloquants (`FATAL`)

1. `bcm/vocab.yaml` doit exister, sinon arrêt immédiat.
2. Au moins un fichier `bcm/capabilities-*.yaml` doit exister, sinon arrêt immédiat.

#### 1) Passe 1 — Validation individuelle de chaque capacité

1. `id` obligatoire.
2. `id` unique sur l'ensemble des fichiers chargés.
3. `level` doit appartenir à `vocab.yaml -> levels`.
4. `zoning` doit appartenir à `vocab.yaml -> zoning`.
5. Règle `parent` par niveau :
  - si `level == L1` : le champ `parent` ne doit pas être présent ;
  - sinon (L2/L3/...) : le champ `parent` est obligatoire.
6. Heatmap (optionnelle) : si `heatmap.maturity` est renseigné,
  alors sa valeur doit appartenir à `vocab.yaml -> heatmap_scales -> maturity`
  **uniquement si** cette liste est définie et non vide dans le vocabulaire.

#### 2) Passe 2 — Cohérence des relations parent/enfant

Appliquée uniquement aux capacités non-L1 qui ont un `parent` :

1. Le `parent` référencé doit exister dans l'ensemble des capacités chargées.
2. Le niveau du parent doit être conforme à la hiérarchie codée en dur :
  - un `L2` doit avoir un parent `L1` ;
  - un `L3` doit avoir un parent `L2`.

> Note: cette hiérarchie est portée par `LEVEL_HIERARCHY = {"L2": "L1", "L3": "L2"}`.
> Aucun contrôle supplémentaire n'est défini pour d'autres niveaux.

#### 2 bis) Contrôles cross-assets (fichiers `bcm/**` non-template)

1. **Événement métier**
  - `emitting_capability` obligatoire, existante, et de niveau `L2` ou `L3`.
  - `version` obligatoire.
  - `carried_business_object` obligatoire et existant dans `business-object-*.yaml`.
2. **Objet métier**
  - `emitting_capability` obligatoire, existante, et de niveau `L2` ou `L3`.
  - si `emitting_capability` pointe une **L2 qui possède des L3**, alors `emitting_capability_L3` est obligatoire,
    doit être une liste non vide, et chaque entrée doit être une L3 existante rattachée à cette même L2.
  - si la L2 ne possède aucune L3, `emitting_capability_L3` est interdit.
  - `emitting_business_event` / `emitting_business_events` interdits (la relation est portée par l'événement métier).
3. **Événement ressource**
  - `carried_resource` obligatoire et existant dans `resource-*.yaml`.
  - `business_event` obligatoire (valeur unique) et doit exister dans `business-event-*.yaml`.
4. **Ressource**
  - `business_object` obligatoire et existant dans `objet-metier-*.yaml`.
5. **Abonnement métier**
  - `consumer_capability` obligatoire, existante, et de niveau `L2` ou `L3`.
  - `subscribed_event.id` obligatoire et existant dans `evenement-metier-*.yaml`.
  - `subscribed_event.version` obligatoire et égale à la version de l'événement métier.
  - `subscribed_event.emitting_capability` obligatoire et cohérente avec l'événement métier.
6. **Abonnement ressource**
  - `consumer_capability` obligatoire, existante, et de niveau `L2` ou `L3`.
  - `linked_business_subscription` obligatoire et existante dans `abonnement-metier-*.yaml`.
  - `subscribed_resource_event.id` obligatoire et existant dans `evenement-ressource-*.yaml`.
  - `subscribed_resource_event.emitting_capability` obligatoire et cohérente avec l'événement ressource.
  - `subscribed_resource_event.linked_business_event` obligatoire et cohérent avec le `business_event` de l'événement ressource.
  - cohérence entre abonnement ressource et abonnement métier liée (consumer, événement métier, émetteur).
7. **Couverture croisée des abonnements**
  - toute abonnement métier doit être référencée par au moins une abonnement ressource.

Des contrôles d'unicité d'`id` sont également appliqués, par type d'asset,
sur les fichiers chargés dans `bcm/`.

#### 2 ter) Contrôles processus externes (`externals/processus-*/*.yaml`)

1. **Processus métier** (`processus_metier`)
  - les capacités référencées (ex: `parent_capability`, `decision_point`, `internal_capabilities`, `event_capability_chain[].capability`) doivent exister dans `bcm/capabilities-*.yaml` ;
  - les événements métier référencés (ex: `entry_event`, `business_assets.evenements_metier`, `event_subscription_chain`, `exits_metier`) doivent exister dans `bcm/evenement-metier/*.yaml`.
  - les abonnements métier référencées (ex: `business_assets.abonnements_metier`, `event_subscription_chain[].via_subscription`) doivent exister dans `bcm/evenement-metier/abonnement-metier-*.yaml`.
2. **Processus ressource** (`processus_ressource`)
  - les capacités référencées doivent exister dans `bcm/capabilities-*.yaml` ;
  - les événements ressource référencés (ex: `entry_event`, `resource_assets.evenements_ressource`, `event_subscription_chain`, `exits_ressource`) doivent exister dans `bcm/evenement-ressource/*.yaml`.
  - les abonnements ressource référencées (ex: `resource_assets.abonnements_ressource`, `event_subscription_chain[].via_subscription`) doivent exister dans `bcm/evenement-ressource/abonnement-ressource-*.yaml`.

Convention de préfixes appliquée dans ces contrôles :
- `OBJ.*` pour les objets métier,
- `RES.*` pour les ressources,
- `ABO.METIER.*` et `ABO.RESSOURCE.*` pour les abonnements.

#### 3) Rapport final

- S'il existe au moins une erreur: sortie `[FAIL]` + code de sortie `1`.
- Sinon: sortie `[OK]` avec le nombre de capacités et la répartition L1/L2/L3.
- Les warnings seraient affichés en `[WARN]`, mais aucune règle actuelle n'alimente cette liste.

### Usage

```bash
# Validation complète du référentiel
python tools/validate_repo.py

# Validation ciblée d'un seul objet métier
python tools/validate_repo.py --objet-metier OBJ.COEUR.005.DECLARATION_SINISTRE
python tools/validate_repo.py -o OBJ.COEUR.005.DECLARATION_SINISTRE
```

#### Options

| Option | Alias | Description |
|--------|-------|-------------|
| `--objet-metier ID` | `-o ID` | Valide un objet métier spécifique et affiche un rapport détaillé |

Sans argument, le script parcourt automatiquement `bcm/capabilities-*.yaml`
et `bcm/vocab.yaml` depuis la racine du repository.

### Exemple de sortie

#### Validation complète

```
[INFO] Fichiers chargés :
  • capabilities-COEUR-005-L2.yaml: 10 capacité(s)
  • capabilities-L1.yaml: 8 capacité(s)

[OK] Validation réussie — 18 capacités (8 L1, 10 L2) dans 2 fichier(s)
```

En cas d'erreur :

```
[FAIL] 1 erreur(s) détectée(s) :

  ✗ [capabilities-COEUR-005-L2.yaml] CAP.COEUR.005.DSP: parent 'CAP.COEUR.099' introuvable
    dans l'ensemble des capacités chargées
```

#### Validation d'un objet métier

```
================================================================================
              RAPPORT DE VALIDATION — OBJET MÉTIER
================================================================================

📋 INFORMATIONS GÉNÉRALES
--------------------------------------------------------------------------------
  ID       : OBJ.COEUR.005.DECLARATION_SINISTRE
  Nom      : Déclaration de sinistre qualifiée
  Source   : bcm/objet-metier/objet-metier-COEUR-005.yaml

🏢 CAPACITÉ L2 ÉMETTRICE
--------------------------------------------------------------------------------
  Événement métier : EVT.COEUR.005.SINISTRE_DECLARE
  Capacité         : CAP.COEUR.005.DSP (Déclaration de Sinistre et Prestations)

📦 ÉVÉNEMENT MÉTIER PORTEUR
--------------------------------------------------------------------------------
  ID      : EVT.COEUR.005.SINISTRE_DECLARE
  Nom     : Déclaration de Sinistre Qualifiée
  Version : 1.0.0

📝 PROPRIÉTÉS DE L'OBJET MÉTIER
--------------------------------------------------------------------------------
  #   Propriété                         Couverture    Ressources
  --- --------------------------------- ------------- ---------------------------
  1   numeroContrat                     ✓ Couverte    RES.COEUR.005.SINISTRE_HABITATION_DEGAT_DES_EAUX, ...
  2   dateDeclaration                   ✓ Couverte    RES.COEUR.005.SINISTRE_HABITATION_DEGAT_DES_EAUX, ...
  ...

🔗 RESSOURCES IMPLÉMENTANT CET OBJET
--------------------------------------------------------------------------------
  #   ID Ressource                                    Nom
  --- ----------------------------------------------- ---------------------------
  1   RES.COEUR.005.SINISTRE_HABITATION_DEGAT_DES_... Déclaration Sinistre Dégât...
  2   RES.COEUR.005.DECLARATION_SINISTRE_HABITATION_VOL Déclaration Sinistre Vol
  3   RES.COEUR.005.DECLARATION_SINISTRE_HABITATION_INCENDIE Déclaration Sinistre Incendie

================================================================================
✅ RÉSUMÉ : Objet métier valide — 3 ressource(s), 10/10 propriétés couvertes
================================================================================
```

---

## check_docs_links.py

Vérifie la cohérence documentaire Markdown du repository :

- liens internes vers fichiers (ex: `path/to/file.md`) ;
- liens d'ancres (ex: `file.md#section` ou `#section`).

Le script est conçu pour la CI/CD : il retourne `0` si tout est valide,
`1` si au moins une incohérence est détectée.

### Usage

```bash
# Depuis la racine du repository
python tools/check_docs_links.py

# Racine personnalisée
python tools/check_docs_links.py --root .
```

### Exemple d'intégration CI

  ```bash
  python tools/check_docs_links.py
  ```

---

## semantic_review.py

Agent de cohérence sémantique pour Pull Request, en **2 phases** :

1. **ADR** : vérification structure ADR + contrôles de cohérence documentaire ADR + revue LLM urbaniste SI,
2. **ADR + BCM** : exécution des validateurs de référentiel (`validate_repo.py` et `validate_events.py`).

Le script génère :

- un rapport Markdown (`semantic-review.md`) prêt à être injecté dans la description de PR,
- une synthèse JSON (`semantic-review.json`) exploitable par le workflow CI.

Code retour :

- `0` : cohérence globalement positive,
- `1` : défauts majeurs détectés (build à faire échouer).

Comportement des sévérités LLM :

- **major_defects** : bloquants (échec du build),
- **minor_defects** : non bloquants (propositions d'amélioration seulement).

Format exploitable retourné dans `semantic-review.json` (clé `llm`) :

- `score` : note de cohérence ADR (0..100)
- `summary` : synthèse courte
- `findings[]` : constats structurés (`id`, `severity`, `adr_refs`, `rationale`, `impact`, `proposed_fix`, `priority`, `effort`, `owner_hint`)
- `action_plan[]` : actions prêtes à exécuter (`id`, `action`, `targets`, `severity`, `priority`, `owner_hint`, `due_hint`)

### Usage

```bash
python tools/semantic_review.py \
  --scope pr \
  --base-ref <sha_base_pr> \
  --head-ref <sha_head_pr> \
  --llm-mode required \
  --report-file semantic-review.md \
  --json-file semantic-review.json
```

Mode full repository :

```bash
python tools/semantic_review.py \
  --scope full \
  --llm-mode required \
  --report-file semantic-review-full.md \
  --json-file semantic-review-full.json
```

Configuration LLM via variables d'environnement :

- `SEMANTIC_LLM_API_KEY` (obligatoire en mode `required`),
- `SEMANTIC_LLM_MODEL` (défaut `gpt-4.1`),
- `SEMANTIC_LLM_API_URL` (défaut `https://api.openai.com/v1/chat/completions`),
- `SEMANTIC_LLM_MODE` (`required`, `optional`, `off`).
- `SEMANTIC_LLM_MAX_ADR_CHARS` (défaut `3500`) : budget max de caractères par ADR envoyé au LLM.
- `SEMANTIC_LLM_MAX_TOTAL_CHARS` (défaut `50000`) : budget global de caractères ADR dans le prompt.
- `SEMANTIC_LLM_MAX_RETRIES` (défaut `3`) et `SEMANTIC_LLM_RETRY_DELAY_SECONDS` (défaut `2`) : retries/backoff sur rate-limit (`429`).

Scripts racine associés :

- `./test.sh` → mode `full`
- `./test-ci.sh` → mode `pr` (fichiers impactés par la PR courante)

---

## concat_files.py

Concatène tous les fichiers des dossiers `adr/`, `bcm/`, `templates/` et `externals-templates/` en un seul document.
Utile pour alimenter un LLM avec le contexte complet du référentiel BCM,
ou pour créer un export consolidé de la documentation.

### Fonctionnalités

- **Parcours récursif** des dossiers `adr/`, `bcm/`, `templates/` et `externals-templates/`
- **Filtrage par extension** : `.md`, `.yaml`, `.yml` par défaut
- **Séparateurs visuels** indiquant le chemin relatif de chaque fichier
- **Sortie flexible** : stdout ou fichier
- **Modes de filtrage** : ADR uniquement, BCM uniquement, ou les deux

### Usage

```bash
# Afficher tout sur stdout
python tools/concat_files.py

# Sauvegarder dans un fichier
python tools/concat_files.py -o context.txt

# ADR uniquement
python tools/concat_files.py --adr-only

# BCM uniquement
python tools/concat_files.py --bcm-only

# Templates (internes + externes) uniquement
python tools/concat_files.py --templates-only

# Filtrer par extension (YAML uniquement)
python tools/concat_files.py --ext .yaml --ext .yml

# Markdown uniquement
python tools/concat_files.py --ext .md
```

### Options

| Option | Description | Défaut |
|--------|-------------|--------|
| `-o`, `--output` | Fichier de sortie | stdout |
| `--adr-only` | Concatène uniquement les fichiers ADR | *(désactivé)* |
| `--bcm-only` | Concatène uniquement les fichiers BCM | *(désactivé)* |
| `--templates-only` | Concatène uniquement les fichiers templates (`templates/` + `externals-templates/`) | *(désactivé)* |
| `--ext` | Extensions à inclure (répétable) | `.md`, `.yaml`, `.yml` |
| `--no-separator` | Désactive les séparateurs entre fichiers | *(désactivé)* |

### Exemple de sortie

```
================================================================================
FILE: adr/ADR-BCM-URBA-0001-BCM-SI-orienté-TOGAF.md
================================================================================
---
id: ADR-BCM-URBA-0001
title: "BCM SI orienté TOGAF étendu (7 zones)"
status: Proposed
...

================================================================================
FILE: bcm/capabilities-L1.yaml
================================================================================
meta:
  bcm_name: BCM Urbanisation
  version: 0.1.0
...

# Total: 25 fichiers concaténés
```

---

## Arborescence

```
tools/
├── README.md              # Ce fichier
├── check_docs_links.py    # Vérification liens Markdown (fichiers + ancres)
├── concat_files.py        # Concaténation ADR + BCM
├── run_eventcatalogs.sh   # Lancement FOODAROO-Metier + FOODAROO-SI
├── render_drawio.py       # Génération draw.io L1
├── render_drawio_l2.py    # Génération draw.io L2
├── validate_events.py     # Validation événements
├── validate_repo.py       # Validation repository
└── requirements.txt       # Dépendances Python (pyyaml)
```
