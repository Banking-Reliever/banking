# ADR — Architecture Decision Records (BCM)

Ce dossier contient l’ensemble des décisions formalisées relatives au POS (BCM).

Chaque évolution du modèle doit être tracée par un ADR.

Une modification non documentée n’est pas considérée comme valide.

---

## 🎯 Finalité des ADR

Les ADR permettent :

- D’expliciter les décisions prises
- De conserver le contexte et les alternatives rejetées
- D’éviter la dérive implicite du modèle
- D’assurer la traçabilité des évolutions
- De stabiliser la gouvernance de la BCM

La BCM évolue uniquement par décision formalisée.

---

## 🏛 Taxonomie des ADR

Les ADR sont organisés selon trois familles complémentaires :

### 1️⃣ GOV — Gouvernance

Définissent le cadre institutionnel du modèle :

- Organisation du collège BCM
- Processus d’arbitrage
- Règles de validation
- Cycle de vie des décisions
- Principes anti-dogme

Ces ADR structurent **la manière dont les décisions sont prises**.

---

### 2️⃣ URBA — Principes structurants

Définissent les règles globales d’urbanisation et de modélisation :

- Zoning
- Niveaux L1/L2/L3
- Règle "1 capacité = 1 responsabilité"
- Découplage logique / physique
- Principes événementiels

Ces ADR définissent **les règles du jeu du modèle**.

### Convention d'identifiants à respecter

Les ADR URBA/FUNC qui introduisent ou modifient des assets doivent respecter la convention suivante :

- `CAP.*` pour les capacités
- `EVT.*` pour les événements
- `OBJ.*` pour les objets métier
- `RES.*` pour les ressources
- `ABO.METIER.*` pour les abonnements métier
- `ABO.RESSOURCE.*` pour les abonnements ressource

Règle de cohérence attendue : une ressource (`RES.*`) implémente un objet métier (`OBJ.*`),
et ne se substitue pas à lui. Cardinalités attendues :
- une ressource référence **un seul** objet métier ;
- un événement ressource référence **un seul** événement métier.

---

### 3️⃣ FUNC — Décisions fonctionnelles

Appliquent les principes URBA à des cas concrets :

- Split / merge de capabilities
- Ajustement de périmètre
- Création ou suppression de L3
- Évolution d’événements métier
- Placement d’une capacité dans une zone

Ces ADR définissent **l’évolution opérationnelle du modèle**.

---

## ⚖️ Hiérarchie décisionnelle

La hiérarchie des décisions est la suivante :

```text
GOV
  ↓
URBA
  ↓
FUNC
```

Règles associées :

- Un ADR FUNC ne peut pas contredire un ADR URBA.
- Un ADR URBA doit respecter les principes définis par GOV.
- Un ADR GOV ne peut être remplacé que par un autre ADR GOV.
- Toute modification de la BCM doit passer par un ADR Accepted.

### Règle de classification

```text
Est-ce que cette décision concerne la manière dont on décide ?
→ GOV

Est-ce que cette décision change les règles globales du modèle ?
→ URBA

Est-ce que cette décision applique les règles à un périmètre précis ?
→ FUNC
```
## 🗺 Impacted Mappings

Le champ `impacted_mappings` du YAML header indique **quels axes de cartographie** sont affectés par la décision. Il permet d'anticiper les impacts au-delà de la BCM elle-même.

| Valeur | Axe de cartographie | Exemples d'impacts |
|--------|---------------------|---------------------|
| `SI`   | Cartographie applicative | Applications à recâbler, modules à renommer, composants à découper |
| `DATA` | Cartographie des données | Flux de données à modifier, domaines de données à réaligner, référentiels impactés |
| `ORG`  | Cartographie organisationnelle | Équipes à réaffecter, rôles à redéfinir, responsabilités opérationnelles à ajuster |

**Règle d'usage :**
- Toujours renseigner au moins une valeur si la décision a un impact concret au-delà du modèle BCM.
- Laisser vide (`[]`) uniquement pour les ADR purement conceptuels sans répercussion directe sur le SI, les données ou l'organisation.
- Un ADR FUNC aura presque toujours au moins `SI` renseigné.

---
## 🧩 Structure d’un ADR

Chaque ADR contient :

Des métadonnées structurées (YAML header)

- Un contexte
- Une décision testable
- Une justification
- Les impacts sur la BCM
- Les conséquences
- La traçabilité

Le template officiel doit être utilisé.

---


## 🔁 Cycle de vie

Statuts possibles :

- Proposed : en discussion
- Accepted : validé
- Deprecated : obsolète
- Superseded : remplacé

Un ADR Accepted constitue la référence officielle.

---

## 🏛 Collège BCM

Les ADR sont instruits et arbitrés par le Collège BCM.

Composition :

- Architectes SI
- Lead Business Analysts
- Urbaniste garant(e) de cohérence

Le collège :

- Assure la cohérence transversale
- Intègre les retours terrain
- Statue sur les propositions
- Documente les décisions

Les évolutions peuvent être proposées par les équipes projet, notamment via les retours d’Event Storming Big Picture.

---

🧠 Principe d’évolutivité

La BCM est un modèle vivant.

Aucune règle n’est intangible.
Tout ADR peut être challengé.

Le principe directeur est :

La cohérence du modèle ne doit jamais primer sur la valeur métier.

---

## ✍️ Proposer un ADR

1. Créer un fichier ADR-BCM-<GOV|URBA|FUNC>-<NNNN>.md
2. Utiliser le template officiel
3. Renseigner les métadonnées
4. Définir le statut Proposed
5. Présenter au Collège BCM

---

🚫 Ce que les ADR ne sont pas

- Pas des comptes rendus de réunion
- Pas des tickets projets
- Pas des documents techniques applicatifs

Ils documentent des décisions de modèle.

---

## 📊 Bonnes pratiques

- Une décision = un ADR
- Être explicite et testable
- Documenter les alternatives rejetées
- Maintenir la traçabilité
- Relier toute modification du fichier capabilities.yaml à un ADR Accepted

### Ce qui est une bonne pratique dans un ADR func

Inclure des décisions précises quand elles portent sur :
 * le **périmètre** d’une capacité ;
 * les **frontières** entre capacités ;
 * les **responsabilités** ;
 * les **points de transfert** ;
 * les **règles de rattachement** d’objets métier ;
 * le **nommage d’événements** quand ce nommage a une portée contractuelle ou lève une ambiguïté durable.

C’est exactement ce que vos ADR font déjà correctement sur DSP et IND.

### Ce qui devient une mauvaise pratique 

Cela devient une mauvaise pratique si l’ADR func descend jusqu’à :

* l’ordre d’exécution détaillé de variantes de traitement ;
* des cas métier trop fins ou spécifiques à une ligne produit ;
* des payloads exhaustifs ;
* des règles qui vont probablement changer en atelier ou pendant l’implémentation ;
* des choix de sequencing ou d’orchestration qui relèvent plus du design de solution que de la décision fonctionnelle stable.

### Le bon test pratique

Pour décider si un détail mérite d’être dans un ADR func, posez-vous trois questions :

1. Si on ne l’écrit pas, la frontière entre équipes ou capacités redevient-elle ambiguë ?
Si oui, mettez-le.
2. Ce point a-t-il une portée contractuelle sur SI / DATA / ORG ?
Si oui, mettez-le.
3. Pense-t-on que ce détail doit rester stable au-delà de l’atelier courant ?
Si non, laissez-le hors ADR.

