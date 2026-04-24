---
task_id: TASK-002
capability_id: CAP.CAN.001.TAB
capability_name: Tableau de Bord Bénéficiaire
epic: Épic 1 — Infrastructure d'alimentation événementielle
status: todo
priority: high
depends_on: [TASK-001]
---

# TASK-002 — Stub d'alimentation et couche de consommation événementielle de CAP.CAN.001.TAB

## Contexte
CAP.CAN.001.TAB se développe en isolation totale des capacités COEUR (BSP.001.SCO, BSP.001.PAL, BSP.004.ENV), qui se construisent en parallèle. Un stub doit alimenter le point de souscription unique de CAP.CAN.001.TAB avec les trois événements définis en TASK-001, à une fréquence paramétrable. La couche de consommation lit ces événements et maintient un read model par bénéficiaire que les épics suivants afficheront. Quand le COEUR sera opérationnel (TASK-006), le stub sera remplacé sans toucher au code de consommation.

## Référence capacité
- Capacité : Tableau de Bord Bénéficiaire (CAP.CAN.001.TAB)
- Zone : CANAL
- ADR gouvernants : ADR-BCM-FUNC-0009, ADR-BCM-URBA-0007, ADR-BCM-URBA-0009

## Ce qu'il faut produire

### Point de souscription unique
Mettre en place le point de souscription dédié à CAP.CAN.001.TAB sur le bus événementiel. Toutes les capacités COEUR (actuelles et futures) publient sur ce point ; CAP.CAN.001.TAB le lit exclusivement.

### Stub d'alimentation
Un composant qui publie sur ce point de souscription les trois événements définis en TASK-001 :
- `ScoreComportemental.Recalculé` — avec un score simulé variant dans le temps
- `Palier.FranchiHausse` — avec transitions de palier simulées
- `Enveloppe.Consommée` — avec consommation budgétaire simulée par catégorie

Le stub doit être activable/désactivable par configuration d'environnement (inactif en production).

### Couche de consommation
Un composant qui lit les événements du point de souscription et maintient un **read model par bénéficiaire** contenant :
- Le score comportemental courant
- Le palier actif
- Les soldes d'enveloppes par catégorie

Ce read model est la seule source de données pour les vues TASK-003, TASK-004, TASK-005.

### Bénéficiaire de test
À l'issue de cette tâche, un bénéficiaire de test simulé doit être consultable de bout en bout (événements produits → read model alimenté) sans aucune dépendance au COEUR.

## Événements métier à produire
Aucun événement métier produit par cette tâche — elle pose l'infrastructure de consommation.

## Objets métier impliqués
- **Bénéficiaire** — clé de corrélation du read model
- **Score comportemental** — état courant maintenu dans le read model
- **Palier** — état courant maintenu dans le read model
- **Enveloppe** — solde par catégorie maintenu dans le read model

## Souscriptions événementielles requises
- `ScoreComportemental.Recalculé` (de CAP.BSP.001.SCO) — abonnement ressource : alimente le score dans le read model
- `Palier.FranchiHausse` (de CAP.BSP.001.PAL) — abonnement métier : met à jour le palier actif dans le read model
- `Enveloppe.Consommée` (de CAP.BSP.004.ENV) — abonnement ressource : met à jour les soldes d'enveloppes dans le read model

## Définition de Done
- [ ] Le point de souscription unique de CAP.CAN.001.TAB est opérationnel
- [ ] Le stub publie les trois événements (conforme au contrat de TASK-001) à fréquence paramétrable
- [ ] Le stub est désactivable par configuration d'environnement
- [ ] La couche de consommation lit les trois événements et maintient le read model par bénéficiaire
- [ ] Un bénéficiaire de test est consultable de bout en bout sans dépendance COEUR
- [ ] Le remplacement du stub par une source réelle ne nécessite aucune modification du code de consommation
- [ ] validate_repo.py passe sans erreur
- [ ] validate_events.py passe sans erreur

## Critères d'acceptation (métier)
Un développeur travaillant sur TASK-003 peut afficher les données d'un bénéficiaire de test sans attendre aucune autre équipe. Les données du read model sont cohérentes avec les événements publiés par le stub.

## Dépendances
- **TASK-001** : le contrat d'événements doit être gelé avant d'implémenter le stub et la couche de consommation

## Questions ouvertes
- Le bus événementiel (technologie) est-il déjà choisi pour le projet Reliever, ou laissé à l'implement-capability ?
- Le stub doit-il simuler plusieurs bénéficiaires distincts ou un seul bénéficiaire de test suffit-il pour les Épics 2-4 ?
