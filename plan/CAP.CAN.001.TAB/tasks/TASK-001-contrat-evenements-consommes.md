---
task_id: TASK-001
capability_id: CAP.CAN.001.TAB
capability_name: Tableau de Bord Bénéficiaire
epic: Épic 1 — Infrastructure d'alimentation événementielle
status: todo
priority: high
depends_on: []
---

# TASK-001 — Gel du contrat des événements consommés par CAP.CAN.001.TAB

## Contexte
CAP.CAN.001.TAB consomme trois événements produits par les capacités COEUR (BSP.001.SCO, BSP.001.PAL, BSP.004.ENV) via un point de souscription unique. Comme le COEUR se construit en parallèle, un stub alimentera ce point en phase de développement. Pour que stub et COEUR soient interchangeables sans régression, le schéma de chaque événement doit être défini et gelé avant toute implémentation. Ce contrat est la précondition bloquante de TASK-002.

## Référence capacité
- Capacité : Tableau de Bord Bénéficiaire (CAP.CAN.001.TAB)
- Zone : CANAL
- ADR gouvernants : ADR-BCM-FUNC-0009, ADR-BCM-URBA-0007, ADR-BCM-URBA-0009

## Ce qu'il faut produire
Définir et documenter le schéma contractuel des trois événements que CAP.CAN.001.TAB consomme, de sorte que le stub (TASK-002) et les capacités COEUR réelles (TASK-006) puissent les produire de manière interchangeable.

Pour chaque événement, le contrat doit spécifier :
- Le nom canonique de l'événement (tel que défini dans le BCM)
- La capacité productrice
- Les champs obligatoires et leur type sémantique (ex. identifiant bénéficiaire, valeur numérique du score, horodatage)
- La cardinalité (un événement par bénéficiaire par recalcul, par changement de palier, par transaction)
- Le type d'abonnement : métier (impact cycle de vie) ou ressource (alimentation read model)

Les trois événements à contractualiser :

| Événement | Producteur | Type d'abonnement |
|-----------|-----------|-------------------|
| `ScoreComportemental.Recalculé` | CAP.BSP.001.SCO | Ressource — alimentation du read model score |
| `Palier.FranchiHausse` | CAP.BSP.001.PAL | Métier — change l'état courant affiché |
| `Enveloppe.Consommée` | CAP.BSP.004.ENV | Ressource — mise à jour des soldes affichés |

## Événements métier à produire
Aucun — cette tâche produit un artefact de contrat, pas un événement métier.

## Objets métier impliqués
- **Bénéficiaire** — identifiant de corrélation présent dans chaque événement
- **Score comportemental** — valeur numérique portée par `ScoreComportemental.Recalculé`
- **Palier** — niveau d'autonomie porté par `Palier.FranchiHausse`
- **Enveloppe** — catégorie et solde restant portés par `Enveloppe.Consommée`

## Souscriptions événementielles requises
Aucune — cette tâche définit les contrats ; la souscription est implémentée en TASK-002.

## Définition de Done
- [ ] Le schéma de `ScoreComportemental.Recalculé` est documenté (champs, types, cardinalité)
- [ ] Le schéma de `Palier.FranchiHausse` est documenté (champs, types, cardinalité)
- [ ] Le schéma de `Enveloppe.Consommée` est documenté (champs, types, cardinalité)
- [ ] Le type d'abonnement (métier / ressource) est qualifié pour chaque événement avec justification (ADR-BCM-URBA-0009)
- [ ] Le contrat est validé par les interlocuteurs des capacités productrices (BSP.001 et BSP.004)
- [ ] Le contrat est versionné (v1.0) et constitue la référence pour TASK-002 et TASK-006
- [ ] validate_repo.py passe sans erreur
- [ ] validate_events.py passe sans erreur

## Critères d'acceptation (métier)
Un développeur de TASK-002 peut construire le stub sans poser de questions sur la structure des événements. Un développeur de TASK-006 peut connecter les capacités COEUR réelles sans modifier le code de consommation de CAP.CAN.001.TAB.

## Dépendances
Aucune dépendance amont. Cette tâche doit être terminée avant TASK-002.

## Questions ouvertes
- Qui est l'interlocuteur côté BSP.001 (SCO et PAL) pour valider le contrat ?
- Qui est l'interlocuteur côté BSP.004 (ENV) pour valider le contrat ?
- L'identifiant bénéficiaire est-il le même across tous les événements (golden record de CAP.REF.001.BEN) ?
