# BCM Export vers EventCatalog

Script Python d'export automatisé du Business Capability Map (BCM) FOODAROO vers un EventCatalog compatible.

## Vue d'ensemble

Ce script transforme les données BCM structurées en YAML vers un EventCatalog navigable, en appliquant les règles de mapping suivantes :

- **CAP L1** → **Domain** EventCatalog
- **CAP L2** → **Service** EventCatalog  
- **OBJ.*** → **Entity** EventCatalog
- **EVT.*** → **Event** EventCatalog

Les éléments ressource (RES.*, EVT.RES.*) sont exclus de l'export.

En complément, les **processus métier externes** sont exportés vers des **flows EventCatalog** :

- `externals/processus-metier/processus-metier-*.yaml` → `flows/*/index.mdx`
- la section `documentation` du processus est exportée dans le **frontmatter** et rendue dans la page du flow (objectif, portée, scénarios, etc.)

Pour l'export SI, les **processus ressource externes** sont également exportés vers des **flows EventCatalog** :

- `externals/processus-ressource/processus-ressource-*.yaml` → `flows/*/index.mdx`
- la section `documentation` du processus est exportée dans le **frontmatter** et rendue dans la page du flow (objectif, portée, scénarios, etc.)

## Installation

### Prérequis

- Python 3.8+
- PyYAML 6.0+

### Installation des dépendances

```bash
cd tools/bcm_export
pip install -r requirements.txt
```

### Vérification installation

```bash
python bcm_export_metier.py --help
```

## Usage

### Export SI (ressources)

Pour générer le catalogue **FOODAROO-SI** basé sur :
- `RES.*` (ressources)
- `EVT.RES.*` (événements ressource)
- `ABO.RESSOURCE.*` (abonnements ressource)

```bash
python bcm_export_si.py --input ../../bcm --output ../../views/FOODAROO-SI
```

Validation seule :

```bash
python bcm_export_si.py --input ../../bcm --validate-only
```

### Export complet

```bash
python bcm_export_metier.py --input ../../bcm --output ../../views/FOODAROO-Metier
```

### Validation seule

```bash
python bcm_export_metier.py --input ../../bcm --validate-only
```

### Simulation (dry-run)

```bash  
python bcm_export_metier.py --input ../../bcm --output ../../views/FOODAROO-Metier --dry-run
```

### Mode verbose avec rapport

```bash
python bcm_export_metier.py --input ../../bcm --output ../../views/FOODAROO-Metier --verbose --report-json export_report.json
```

## Options CLI

| Option | Description |
|--------|-------------|
| `--input DIR` | Répertoire BCM source (requis) |
| `--output DIR` | Répertoire EventCatalog cible |
| `--dry-run` | Simule sans écrire de fichiers |
| `--validate-only` | Valide le BCM sans générer |
| `--verbose` | Mode de logging détaillé |
| `--report-json FILE` | Rapport détaillé en JSON |
| `--report-md FILE` | Rapport détaillé en Markdown |

## Structure d'entrée BCM attendue

```
bcm/
├── capabilities-L1.yaml                   # Capacités métier L1 (obligatoire)
├── capabilities-*-L2.yaml                 # Capacités métier L2 (au moins un)
├── evenement-metier/
│   └── evenement-metier-*.yaml           # Événements métier
├── objet-metier/
│   └── objet-metier-*.yaml               # Objets métier
├── evenement-ressource/                   # Ignoré à l'export
├── ressource/                             # Ignoré à l'export
└── vocab.yaml                             # Optionnel

externals/
└── processus-metier/
   └── processus-metier-*.yaml           # Processus métier exportés en flows EventCatalog
└── processus-ressource/
   └── processus-ressource-*.yaml        # Processus ressource exportés en flows EventCatalog (export SI)
```

## Structure de sortie EventCatalog générée

```
views/FOODAROO-Metier/
├── flows/
│   └── {flow-slug}/
│       └── index.mdx                     # Fichier flow (issu des processus métier)
├── domains/
│   └── {domain-slug}/
│       ├── index.mdx                     # Fichier domain
│       ├── services/
│       │   └── {service-slug}/
│       │       ├── index.mdx             # Fichier service
│       │       └── events/
│       │           └── {event-slug}/
│       │               └── index.mdx     # Fichier event
│       └── entities/
│           └── {entity-slug}/
│               └── index.mdx             # Fichier entity
└── .gitignore
```

## Synchronisation des suppressions BCM

L'export fonctionne en **mode synchronisé** : à chaque génération, l'arborescence
`domains/` est recréée entièrement avant réécriture des artefacts.

Concrètement :

- si une **capacité L2** est retirée du BCM, les services/événements/entités associés sont supprimés du catalogue ;
- si un **événement BCM** est retiré, son dossier EventCatalog correspondant est supprimé ;
- un **domaine devenu vide** (sans service, entité, ni événement) n'est plus généré.

Ce comportement évite les artefacts obsolètes après suppression dans les YAML source.

## Règles de transformation

### Génération des slugs

- `CAP.COEUR.005` → `coeur-005` (domain)
- `CAP.COEUR.005.DSP` → `dsp` (service)  
- `EVT.COEUR.005.DECLARATION_SINISTRE_RECUE` → `declaration-sinistre-recue`
- `OBJ.COEUR.005.DECLARATION_SINISTRE_RECUE` → `declaration-sinistre-recue`

### Normalisation des owners

- `Gestion Sinistres / Prestations` → `gestion-sinistres-prestations`
- Espaces → tirets, caractères spéciaux supprimés

### Relations préservées

- Service → Domain parent (via `parent` BCM)
- Event → Service émetteur (via `emitting_capability`)
- Event → Entity portée (via `carried_business_object`)
- Entity n'a pas de référence inverse vers Event (relation unidirectionnelle)

### Métadonnées de traçabilité

Tous les artefacts EventCatalog conservent leurs métadonnées BCM :

```yaml
metadata:
  bcm:
    source_id: "CAP.COEUR.005.DSP"
    source_file: "capabilities-COEUR-005-L2.yaml"
    bcm_type: "capability_l2" 
    parent_l1_id: "CAP.COEUR.005"
    exported_at: "2026-03-13T10:30:00Z"
```

## Validation et erreurs

### Validations automatiques

- ✅ Cohérence des relations (L2→L1, EVT→L2, EVT→OBJ)
- ✅ Unicité des slugs générés
- ✅ Format des identifiants BCM
- ✅ Présence des champs obligatoires

### Gestion des erreurs

- **Erreurs bloquantes** : arrêtent l'export (ex: relation manquante)
- **Warnings** : signalés mais n'empêchent pas l'export
- **Fallbacks** : valeurs par défaut pour champs optionnels

### Rapport de validation

```
📊 RÉSUMÉ D'EXPORT BCM → EventCatalog
================================================================================

✅ Statut: SUCCÈS

📥 Sources BCM analysées:
   • Capacités L1: 8
   • Capacités L2: 15
   • Événements métier: 42
   • Objets métier: 42

📤 Artefacts EventCatalog générés:
   • Domains: 8
   • Services: 15  
   • Events: 42
   • Entities: 42
   • Flows: 3

📁 Fichiers créés: 107
⏱️  Durée de génération: 1.23s

⚠️  Avertissements: 3
```

## Usage en tant que module Python

```python
from bcm_export import BCMParser, BCMNormalizer, EventCatalogGenerator
from pathlib import Path

# Parsing BCM
parser = BCMParser()
model = parser.parse_bcm_directory(Path("./bcm"))

# Normalisation
normalizer = BCMNormalizer()
normalized = normalizer.normalize_model(model)

# Génération EventCatalog
generator = EventCatalogGenerator(Path("./output"))
report = generator.generate_catalog(normalized)
```

## Développement et extension

### Structure du code

- `domain_model.py` - Classes Python du modèle BCM
- `parser_bcm.py` - Parseurs YAML BCM
- `normalizer.py` - Normalisation et transformation
- `eventcatalog_generator.py` - Génération fichiers EventCatalog
- `bcm_export_metier.py` - Script CLI principal

### Ajout de nouvelles validations

Étendre la méthode `validate_all()` dans `BCMModel` :

```python
def validate_custom_rules(self) -> List[str]:
    errors = []
    # Vos règles métier spécifiques
    return errors
```

### Personnalisation du mapping

Modifier les classes `*Normalizer` dans `normalizer.py` pour adapter les règles de transformation.

## Documentation complète

- [Règles d'export détaillées](mapping_rules.md)
- [Inventaire des données sources](source_inventory.md)  
- [Mapping champ par champ](field_mapping.md)

## Support et contribution

Pour signaler un problème ou contribuer :

1. Vérifier les logs en mode `--verbose`
2. Consulter la documentation des règles de mapping
3. Tester avec `--validate-only` pour isoler les erreurs de parsing
4. Utiliser `--dry-run` pour vérifier la transformation

## Limitations actuelles

- ❌ Pas de support des abonnements métier
- ❌ Pas de génération de schémas JSON/Avro pour les events
- ❌ Pas de gestion des channels/protocoles techniques
- ❌ Owners techniques non distingués des owners métier
- ⚠️ Un seul domaine L1 par L2 (pas de multi-rattachement)

## Roadmap

- [ ] Support des abonnements BCM → consumers EventCatalog
- [ ] Génération automatique de schémas depuis modèles `data` OBJ
- [ ] Mode incrémental (mise à jour plutôt que régénération complète)
- [ ] Validation sémantique avancée (détection de cycles, orphelins)
- [ ] Export vers d'autres formats (AsyncAPI, OpenAPI)

---

**Version**: 1.0.0  
**Équipe**: FOODAROO - Architecture & Urbanisation  
**Dernière mise à jour**: 13 mars 2026