# Plan — Tableau de Bord Bénéficiaire (CAP.CAN.001.TAB)

## Résumé de la capacité
> Exposer au bénéficiaire une vue synthétique de sa situation financière adaptée à son palier : solde disponible, enveloppes, historique des transactions. L'interface est calibrée pour encourager sans infantiliser — la dignité est une contrainte fonctionnelle.

## Alignement stratégique
- **Service offer** : Reliever permet à des individus en fragilité financière de reprendre progressivement le contrôle de leur vie financière quotidienne grâce à un système de paliers d'autonomie croissante
- **Capacité stratégique L1** : SC.005 — Valorisation de la Progression
- **Zone BCM** : CANAL
- **ADR gouvernants** : ADR-BCM-FUNC-0009

## Décisions de cadrage

- **V0 sans gamification** — la visualisation gamifiée (badges, score visible, jalons) est reportée aux itérations suivantes ; V0 expose palier + enveloppes + historique
- **Architecture stub/COEUR découplée** — un point de souscription unique par capacité ; le stub alimente ce point en phase de développement, le COEUR le remplace dès qu'il est opérationnel ; les développements sont strictement isolés
- **Deux canaux planifiés** — web (dashboard riche, filtres et tri complets) et mobile (vue allégée, moins de colonnes, sans filtres complexes) ; V0 centrée sur le web
- **Règle de dignité** (ADR-BCM-FUNC-0009) : la progression accomplie est toujours affichée avant les restrictions ; les refus sont accompagnés d'une explication

---

## Épics d'implémentation

### Épic 1 — Infrastructure d'alimentation événementielle
**Objectif** : Poser le point de souscription unique de `CAP.CAN.001.TAB` et le stub qui produit les événements COEUR, permettant au tableau de bord d'être développé en isolation totale.

**Condition d'entrée** : Le pattern de point de souscription unique par capacité est validé architecturalement (topic/queue dédié par capacité côté bus événementiel).

**Condition de sortie (DoD)** :
- Un stub publie `ScoreComportemental.Recalculé`, `Palier.FranchiHausse`, `Enveloppe.Consommée` sur le point de souscription `CAP.CAN.001.TAB` à fréquence paramétrable
- La couche de consommation du tableau de bord lit ces événements et les rend disponibles aux épics suivants
- Un bénéficiaire de test est simulable de bout en bout sans aucune dépendance au COEUR

**Complexité** : M

**Événements métier débloqués** : pipeline de consommation opérationnel (aucun événement métier externe produit à ce stade)

**Dépendances** : aucune (épic fondateur)

---

### Épic 2 — Tableau de bord web — situation courante
**Objectif** : Le bénéficiaire peut consulter son palier actif, ses enveloppes budgétaires par catégorie et son solde disponible sur l'interface web ; `TableauDeBord.Consulté` est produit à chaque consultation.

**Condition d'entrée** :
- Épic 1 terminé (stub opérationnel)
- État courant du bénéficiaire disponible : `CAP.BSP.002.CYC` ou stub équivalent
- Vérification de `Consentement.Accordé` possible : `CAP.SUP.001.CON` ou stub gate

**Condition de sortie (DoD)** :
- L'interface web affiche : palier courant, enveloppes par catégorie avec solde disponible, indication du prochain palier atteignable
- La progression accomplie est présentée avant les restrictions (règle de dignité ADR-0009)
- `TableauDeBord.Consulté` est produit à chaque accès à la page principale
- L'accès est bloqué si `Consentement.Accordé` est absent

**Complexité** : M

**Événements métier débloqués** : `TableauDeBord.Consulté`

**Dépendances** :
- Épic 1
- `CAP.BSP.002.CYC` — état courant du bénéficiaire (stub acceptable)
- `CAP.SUP.001.CON` — gate `Consentement.Accordé` (stub acceptable)
- `CAP.REF.001.PAL` — définition des paliers et seuils (stub acceptable)

---

### Épic 3 — Tableau de bord web — historique transactionnel
**Objectif** : Le bénéficiaire accède à l'historique complet de ses transactions sur le web avec filtres (date, catégorie, statut) et tri ; les refus affichent leur motif.

**Condition d'entrée** :
- Épic 2 terminé (vue situation courante opérationnelle)
- Événements transactionnels disponibles : `Transaction.Autorisée` et `Transaction.Refusée` depuis `CAP.BSP.004.AUT` ou stub

**Condition de sortie (DoD)** :
- L'historique des transactions est consultable avec filtres sur : période, catégorie de dépense, statut (autorisée / refusée)
- Le tri par date et par montant fonctionne
- Chaque transaction refusée affiche le motif de refus (règle du palier appliquée)
- `TableauDeBord.Consulté` est produit à chaque accès à l'historique

**Complexité** : M

**Événements métier débloqués** : `TableauDeBord.Consulté` enrichi du contexte historique

**Dépendances** :
- Épic 2
- `CAP.BSP.004.AUT` — flux `Transaction.Autorisée` / `Transaction.Refusée` (stub acceptable)

---

### Épic 4 — Vue mobile — consultation nomade
**Objectif** : Le bénéficiaire peut consulter sa situation clé depuis un appareil mobile : palier courant et soldes des enveloppes principales, sans filtres ni colonnes secondaires.

**Condition d'entrée** :
- Épic 2 terminé (tableau de bord web opérationnel, données disponibles)

**Condition de sortie (DoD)** :
- L'interface mobile affiche : palier courant, soldes des enveloppes principales (sans détail catégoriel exhaustif)
- Pas de filtres, pas de tri, pas de colonnes secondaires — lecture rapide optimisée
- `TableauDeBord.Consulté` est produit avec le tag `canal=mobile`
- La règle de dignité s'applique identiquement (progression avant restriction)

**Complexité** : M

**Événements métier débloqués** : `TableauDeBord.Consulté` (canal mobile)

**Dépendances** :
- Épic 2 (les données et la logique de consommation sont réutilisées)

---

### Épic 5 — Raccordement aux capacités COEUR réelles
**Objectif** : Remplacer le stub par les souscriptions événementielles réelles dès que `BSP.001.SCO`, `BSP.001.PAL` et `BSP.004.ENV` sont opérationnels ; décommissionner le stub sans régression fonctionnelle.

**Condition d'entrée** :
- `CAP.BSP.001.SCO`, `CAP.BSP.001.PAL`, `CAP.BSP.004.ENV` sont opérationnels et publient sur les points de souscription convenus
- Les tests fonctionnels du tableau de bord sont validés sur stub (Épics 2, 3, 4 terminés)
- Le schéma des événements COEUR est conforme au contrat du stub (vérification de compatibilité)

**Condition de sortie (DoD)** :
- Le stub est décommissionné
- Le tableau de bord consomme les événements réels sans régression fonctionnelle sur les deux canaux (web et mobile)
- La supervision confirme le flux événementiel réel en production

**Complexité** : S

**Événements métier débloqués** : tous les événements précédents, désormais alimentés par les données comportementales réelles

**Dépendances** :
- `CAP.BSP.001.SCO` — opérationnel
- `CAP.BSP.001.PAL` — opérationnel
- `CAP.BSP.004.ENV` — opérationnel

---

## Carte des dépendances

| Épic | Dépend de | Type |
|------|-----------|------|
| Épic 2 | Épic 1 | Séquentiel |
| Épic 3 | Épic 2 | Séquentiel |
| Épic 4 | Épic 2 | Séquentiel |
| Épic 5 | Épics 2, 3, 4 | Séquentiel (tests validés) |
| Épic 2 | CAP.BSP.002.CYC | Cross-capacité (stub acceptable) |
| Épic 2 | CAP.SUP.001.CON | Cross-capacité (gate bloquante) |
| Épic 2 | CAP.REF.001.PAL | Cross-capacité (stub acceptable) |
| Épic 3 | CAP.BSP.004.AUT | Cross-capacité (stub acceptable) |
| Épic 5 | CAP.BSP.001.SCO | Cross-capacité (opérationnel requis) |
| Épic 5 | CAP.BSP.001.PAL | Cross-capacité (opérationnel requis) |
| Épic 5 | CAP.BSP.004.ENV | Cross-capacité (opérationnel requis) |

---

## Risques

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| Divergence de schéma stub/COEUR — le stub produit des événements avec un contrat légèrement différent de celui que finalise le COEUR, rendant l'Épic 5 plus coûteux | M | M | Définir et geler le contrat d'événement (schéma JSON/Avro) dès l'Épic 1 ; le stub doit respecter ce contrat |
| Gate consentement non disponible au démarrage de l'Épic 2 — si CAP.SUP.001.CON n'a pas de stub, l'accès aux données est bloqué | L | H | Prévoir un stub de gate consentement minimal dès l'Épic 1 (réponse toujours `Accordé` en environnement de développement) |
| Règles d'enveloppes non stabilisées — si les catégories ou la périodicité des enveloppes évoluent pendant l'Épic 2, l'affichage doit être refactorisé | M | M | Aligner avec CAP.REF.001.PAL dès l'Épic 1 sur le modèle de données des enveloppes avant de construire l'affichage |

---

## Séquencement recommandé

```
Épic 1 ──────────────────────────────────────────────────────────►
         └─► Épic 2 ──────────────────────────────────────────────►
                      └─► Épic 3 (web historique) ───────────────►
                      └─► Épic 4 (mobile) ───────────────────────►
                                    └─► Épic 5 (COEUR réel) ─────►
                                         [déclenché par COEUR opérationnel]
```

**Chemin critique** : Épic 1 → Épic 2 → Épic 3  
**Parallélisable** : Épic 3 et Épic 4 peuvent se développer en parallèle dès que l'Épic 2 est terminé  
**Épic 5** : hors chemin critique interne — déclenché par la disponibilité des capacités COEUR, indépendamment de l'avancement des Épics 3 et 4

---

## Questions ouvertes

- La gamification (badges, visualisation de la trajectoire, jalons) est reportée — quel horizon est visé pour la V1 avec gamification, afin d'anticiper les points d'extension dans l'Épic 2 ?
- La règle de dignité ("progression avant restriction") est posée dans l'ADR — nécessite-t-elle un atelier UX dédié pour être spécifiée sous forme de critères testables avant l'Épic 2 ?
- Le contrat d'événement (schéma des trois événements consommés) doit être co-construit avec les équipes COEUR dès l'Épic 1 — qui est l'interlocuteur côté BSP.001 et BSP.004 ?
