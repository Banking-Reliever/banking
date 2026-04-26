---
id: ADR-TECH-TACT-001
title: "Tactical Stack — CAP.CAN.001.TAB: Progression Dashboard"
status: Proposed
date: 2026-04-26

family: TECH
tech_domain: TACTICAL_STACK

capability_id: CAP.CAN.001.TAB
capability_name: "Progression Dashboard"
zone: CANAL

domain_classification:
  type: supporting
  coordinates:
    x: 0.45
    y: 0.35

grounded_in_urba:
  - ADR-BCM-URBA-0003   # isolation des responsabilités — TAB ne dépasse pas le BFF
  - ADR-BCM-URBA-0009   # TAB produit TableauDeBord.Consulté — ownership événementiel
  - ADR-BCM-URBA-0010   # L2 comme pivot — TAB est un L3 sous CAN.001

grounded_in_func:
  - ADR-BCM-FUNC-0009   # L2 breakdown CAP.CAN.001 — Beneficiary Journey

grounded_in_tech_strat:
  - ADR-TECH-STRAT-001   # event infrastructure — BFF publie sur RabbitMQ, frontend n'y touche pas
  - ADR-TECH-STRAT-002   # runtime — TAB est un module du déployable reliever-can
  - ADR-TECH-STRAT-003   # API contract — REST/HTTP BFF↔frontend, ETag standard HTTP
  - ADR-TECH-STRAT-004   # data — LocalStorage client, PII exclus, pas de base serveur à ce niveau L3
  - ADR-TECH-STRAT-005   # observabilité — OTel sur BFF, traceparent propagé depuis le frontend
  - ADR-TECH-STRAT-006   # déploiement — assets statiques dans namespace reliever-can

strategic_overrides: []

related_adr:
  - ADR-BCM-FUNC-0005   # BSP.001.SCO — émetteur de ScoreComportemental.Recalculé
  - ADR-BCM-FUNC-0008   # BSP.004 — émetteur de Enveloppe.Consommée

supersedes: []

tags:
  - vanilla-js
  - frontend
  - bff
  - etag
  - polling
  - local-storage
  - canal
  - dashboard
  - pii-exclusion

stability_impact: Minor
---

# ADR-TECH-TACT-001 — Tactical Stack: CAP.CAN.001.TAB — Progression Dashboard

## Capability Summary

`CAP.CAN.001.TAB` est le L3 responsable de la visualisation gamifiée de la progression du
bénéficiaire dans le programme Reliever : score comportemental, palier actif et trajectoire,
enveloppe budgétaire disponible.

Il ne contient aucune règle métier de scoring ou de palier — il consomme des événements
produits par `CAP.BSP.001.SCO` (score), `CAP.BSP.001.PAL` (palier) et `CAP.BSP.004.ENV`
(enveloppe), les expose via le BFF `CAP.CAN.001`, et produit l'événement
`TableauDeBord.Consulté` lors de chaque consultation effective.

La contrainte dignité (ADR-BCM-FUNC-0009) s'applique à ce L3 : la progression positive
est exposée avant les restrictions. Cette règle UX est sous la responsabilité de TAB,
pas du cœur IS.

## Scope

### In Scope

- Technologie frontend : langage, syntaxe, modalité de rendu
- Stratégie de rafraîchissement des données BFF→frontend
- Stratégie de cache client (LocalStorage) et règles d'exclusion PII
- Contrat API BFF exposé spécifiquement à TAB (endpoints, mécanique ETag)
- Approche de visualisation gamifiée (build vs buy)
- SLO propres à TAB (chargement initial, fraîcheur de donnée)
- Propagation OTel depuis le frontend

### Out of Scope

- Runtime et langage du BFF (décision L2 — ADR `CAP.CAN.001` à produire)
- Framework BFF et infrastructure du déployable `reliever-can` (L2)
- Authentification bénéficiaire et OpenFGA au niveau BFF (L2)
- Migration future polling → SSE/WebSocket (dette acceptée, voir ci-dessous)
- Ressources K8s et politique de scaling (L2)

## Strategic Constraints Applied

**TECH-STRAT-001 (Event Infrastructure)**
Le frontend ne communique pas avec RabbitMQ. Le BFF `CAP.CAN.001` est l'unique pont :
il maintient un cache local des événements `ScoreComportemental.Recalculé`,
`Palier.FranchiHausse` et `Enveloppe.Consommée` reçus via ses abonnements RabbitMQ, et
publie `TableauDeBord.Consulté` sur son exchange lorsque TAB signale une consultation.

**TECH-STRAT-002 (Runtime)**
TAB est un module du déployable `reliever-can`. Les assets statiques (HTML/CSS/JS) sont
servis depuis ce déployable. TAB ne communique qu'avec le BFF — jamais directement avec
les L2 BSP.

**TECH-STRAT-003 (API Contract)**
REST/HTTP entre le frontend et le BFF. Convention d'URL : `/can/can001/tab/{resource}`.
Le mécanisme ETag/`If-None-Match` est un standard HTTP RFC 7232 — pleinement compatible
avec la règle REST/HTTP de TECH-STRAT-003.

**TECH-STRAT-004 (Data)**
TAB ne possède pas de base de données serveur à ce niveau L3. Le LocalStorage est de
l'état client éphémère, sous contrôle de l'appareil de l'utilisateur — la règle "1 base
par L2" s'applique au BFF, pas au frontend. Les données nominatives (identifiant
bénéficiaire, nom) sont explicitement exclues du cache client pour supprimer tout risque
RGPD sur appareil partagé.

**TECH-STRAT-005 (Observabilité)**
OTel instrumenté côté BFF avec `capability_id = CAP.CAN.001.TAB`. Le frontend vanilla JS
propage le header W3C `traceparent` sur chaque requête HTTP vers le BFF, permettant la
corrélation du trace distribué frontend→BFF→BSP sans instrumentation OTel native côté
browser.

**TECH-STRAT-006 (Déploiement)**
Assets statiques servis depuis le namespace `reliever-can`. Aucun réseau externe requis
pour TAB — toutes les requêtes restent intra-cluster vers le BFF.

## Strategic Overrides

*(Aucun override — toutes les décisions sont compatibles avec les règles TECH-STRAT.)*

---

## Decision

### Runtime & Language

**Décision :** Vanilla JavaScript (ES2022+), HTML5, CSS3. Aucun framework. Aucun outil de
build à l'amorçage.

**Rationale :** TAB est une surface d'affichage d'état avec un modèle de données simple
(3 valeurs agrégées). La complexité d'état ne justifie pas l'introduction d'un framework
réactif à ce stade. Un framework représenterait une dépendance de mise à niveau
permanente pour une valeur marginale sur ce périmètre.

Confirmed rules:
- TAB est packagé en assets statiques dans le déployable `reliever-can` (TECH-STRAT-002).
- Il communique exclusivement avec le BFF via REST/HTTP — aucun appel direct aux L2 BSP.

### Cache Client (LocalStorage)

**Décision :** Cache LocalStorage limité aux agrégats non nominatifs suivants :

| Clé | Contenu | Type |
|-----|---------|------|
| `reliever.tab.score` | Valeur numérique du score comportemental | Number |
| `reliever.tab.tier` | Libellé du palier actif | String |
| `reliever.tab.envelope` | Montant disponible de l'enveloppe | Number |
| `reliever.tab.etag` | ETag de la dernière réponse BFF | String |
| `reliever.tab.updated_at` | Timestamp ISO de la dernière mise à jour | String |

**Données explicitement exclues du cache :** identifiant bénéficiaire, nom, prénom,
toute donnée permettant d'identifier la personne. Ces données ne transitent jamais par
le LocalStorage — elles sont portées par la session authentifiée côté BFF uniquement.

**Rationale de l'exclusion PII :** Reliever cible des populations financièrement
vulnérables susceptibles d'utiliser des appareils partagés. Stocker des données
nominatives dans le LocalStorage exposerait des informations comportementales et
financières à tout accès ultérieur à l'appareil sans authentification.

Confirmed rules:
- La responsabilité RGPD sur les données nominatives reste côté BFF (TECH-STRAT-004).
- Le LocalStorage est purgeable à tout moment par l'utilisateur — pas de source de vérité.

### Stratégie de Rafraîchissement — ETag / Polling

**Décision :** Polling HTTP avec détection de changement via ETag (`If-None-Match` /
`If-Modified-Since`). Intervalle de poll : 5 minutes (bien en-deçà du SLO fraîcheur < 1h).

**Mécanique :**

```
Première visite (pas d'ETag en cache) :
  GET /can/can001/tab/snapshot
  → 200 OK + ETag: "abc123" + payload complet
  → Stockage dans LocalStorage + ETag sauvegardé

Visites suivantes (ETag présent) :
  GET /can/can001/tab/snapshot
  If-None-Match: "abc123"
  → 304 Not Modified  (rien n'a changé → affichage depuis LocalStorage)
  → 200 OK + ETag: "def456" + payload mis à jour (données ont changé → update LocalStorage)
```

**Rationale :** L'ETag ramène le coût d'un poll sans changement à un aller-retour HTTP
sans payload — compatible avec un intervalle court (5 min) sans surcharger le BFF. Ce
patron prépare naturellement la migration vers SSE : le BFF dispose déjà de la logique
de détection de changement d'état.

### Contrat API BFF pour TAB

**Convention d'URL :** `/can/can001/tab/{resource}` (TECH-STRAT-003)

| Méthode | Endpoint | Description | Supporte ETag |
|---------|----------|-------------|---------------|
| `GET` | `/can/can001/tab/snapshot` | Agrégat score + palier + enveloppe | Oui — 304 si inchangé |
| `POST` | `/can/can001/tab/view` | Signal de consultation → déclenche publication de `TableauDeBord.Consulté` côté BFF | Non |

**Payload `GET /snapshot` (200 OK) :**
```
{
  score: Number,          // valeur 0–100
  tier: String,           // libellé du palier actif
  tier_trend: String,     // "hausse" | "stable" | "baisse"
  envelope_available: Number,  // montant en centimes
  envelope_total: Number
}
```
*(pas d'identifiant bénéficiaire dans le payload — le BFF résout l'identité depuis la session)*

**Authentification :** portée par le BFF (cookie de session ou token opaque) — hors
périmètre de cet ADR L3.

### Visualisation Gamifiée — Build

**Décision :** Tout est construit en vanilla SVG / CSS animations. Aucune librairie de
chart externe.

| Composant | Implémentation | Justification |
|-----------|----------------|---------------|
| Jauge de score | Arc SVG animé (stroke-dashoffset) | Rendu simple, aucune dépendance, accessible |
| Progression de palier | Barre CSS `width: X%` avec transition | Trivial en CSS, pas de JS complexe |
| Enveloppe disponible | Barre CSS + montant textuel | Même patron que palier |

**Rationale :** les trois composants visuels de TAB sont des affichages de valeurs
scalaires simples. L'introduction d'une librairie charting (Chart.js, D3) représenterait
une surface de dépendance permanente sans apport technique sur ce périmètre.

### Observabilité

**SLO cibles :**

| Métrique | Cible | Seuil d'alerte |
|----------|-------|----------------|
| Chargement initial (premier affichage de donnée) | < 500ms p95 | > 750ms p95 |
| Réponse poll `200 OK` (payload complet) | < 200ms p95 | > 400ms p95 |
| Réponse poll `304 Not Modified` | < 50ms p95 | > 100ms p95 |
| Fraîcheur de la donnée affichée | < 1h garanti | > 1h (bug poll) |

**Métriques custom (sur le BFF, dimension `capability_id="CAP.CAN.001.TAB"`) :**
- `tab_poll_304_ratio` — ratio de 304 sur total des polls (indicateur de stabilité du cache)
- `tab_snapshot_load_duration_ms` — durée de construction du snapshot côté BFF

**Propagation OTel depuis le frontend :**
Le frontend lit le header `traceparent` retourné par le BFF sur la réponse `GET /snapshot`
et le renvoie sur la requête `POST /view`, permettant la corrélation de la chaîne :
frontend → BFF → publication RabbitMQ `TableauDeBord.Consulté`.

---

## Justification

TAB est une capacité Supporting à faible complexité de modèle (y=0.35). La valeur produit
réside dans le cœur IS (BSP.001), pas dans la couche d'affichage. Les choix retenus
minimisent la dette de dépendance et maximisent la lisibilité du code pour une pizza team :
vanilla JS sans outillage est le point d'entrée le plus bas pour tout développeur ; le
mécanisme ETag est un standard RFC maîtrisé ; le cache LocalStorage non-PII est sûr et
trivial à purger.

### Alternatives Considérées

**Frontend — Framework JS (Vue, React, Svelte)**
Rejeté : la complexité de state management de TAB (3 valeurs scalaires) ne justifie pas
l'overhead d'un framework réactif. Un framework introduit une dépendance de version et
une courbe d'apprentissage pour une surface d'affichage statique. Ré-évaluer si TAB
évolue vers un état interactif complexe (filtres, historique, graphiques temporels).

**Rafraîchissement — WebSocket / SSE dès J0**
Rejeté : la maturité opérationnelle d'une connexion persistante (reconnexion, load
balancing stateful, backpressure) est supérieure à celle d'un poll ETag pour une équipe
au lancement. Le poll ETag avec 5 min d'intervalle répond au SLO de fraîcheur < 1h.
Migration planifiée comme dette explicite.

**Visualisation — Chart.js ou D3**
Rejeté : les composants visuels de TAB (arc, barres de progression) sont reproductibles
en SVG/CSS natif en moins de 50 lignes chacun. L'introduction d'une librairie charting
pour trois composants scalaires simples est disproportionnée.

**Cache — SessionStorage plutôt que LocalStorage**
Écarté : SessionStorage est perdu à la fermeture de l'onglet, ce qui forcerait un rechargement
complet à chaque ouverture de l'application — incompatible avec l'objectif de <500ms au
chargement initial. LocalStorage avec exclusion PII est le bon compromis.

## Technical Impact

### Sur le déployable `reliever-can`
Les assets statiques (HTML/CSS/JS) sont servis depuis un conteneur Nginx léger dans le
déployable `reliever-can`. La charge sur le BFF est dominée par les polls ETag — le taux
de 304 attendu est élevé (données stables entre sessions), ce qui maintient la charge BFF
faible.

### Sur les L2 dépendants
Le BFF `CAP.CAN.001` doit maintenir un cache local des événements issus de BSP.001.SCO,
BSP.001.PAL et BSP.004.ENV pour construire le snapshot sans appel synchrone à ces L2 lors
de chaque poll. Cette exigence sera décidée dans l'ADR tactique L2 `CAP.CAN.001`.

### Sur l'équipe plateforme
Aucune demande de provisionnement spécifique à ce L3. La base de données et les ressources
K8s sont décidées au niveau L2.

## Consequences

### Positive
- Zéro dépendance de framework → surface de mise à niveau minimale
- ETag/304 rend le polling compatible avec un intervalle court sans overhead réseau
- Exclusion PII du LocalStorage supprime tout risque sur appareil partagé
- Vanilla JS lisible par n'importe quel développeur de l'équipe sans formation spécifique

### Negative / Risks
- La gestion d'état vanilla JS se complexifie si TAB acquiert de l'interactivité (filtres,
  historique de score) — absence de reactive binding
- Un intervalle de poll de 5 min implique un délai perçu entre un événement BSP (ex. :
  transaction refusée → score recalculé) et son apparition sur le tableau de bord
- Sans CDN, la latence de chargement des assets dépend du temps de réponse de l'ingress K8s

### Accepted Debt
- **Migration polling → SSE** : le mécanisme ETag prépare cette migration (le BFF a déjà
  la logique de détection de changement). À déclencher lorsque les tests utilisateurs
  révèlent un décalage perçu inacceptable entre action et affichage.
- **Outil de build (esbuild/Vite)** : acceptable sans bundler au lancement pour une surface
  JS de < 500 lignes. À introduire si TAB dépasse ce seuil ou si le découpage en modules
  ES devient nécessaire.

## Governance Indicators

- **Review trigger :** tests utilisateurs révélant un délai perçu > 2s entre événement BSP
  et mise à jour du tableau de bord (déclenche la migration SSE) ; ou croissance de la
  surface JS au-delà de 500 lignes (déclenche l'évaluation d'un outil de build)
- **Expected stability :** 12 mois — stable jusqu'à la première vague de tests terrain ;
  la migration SSE est prévue mais non datée

## Traceability

- Session : Tactical tech brainstorming 2026-04-26
- Participants : yremy
- Grounded in :
  - ADR-BCM-FUNC-0009 — définition fonctionnelle de CAP.CAN.001 et CAP.CAN.001.TAB
  - ADR-TECH-STRAT-001 à 006 — contraintes stratégiques appliquées
  - RFC 7232 — HTTP Conditional Requests (ETag / If-None-Match)
  - ADR-BCM-URBA-0009 — ownership événementiel (TableauDeBord.Consulté)
