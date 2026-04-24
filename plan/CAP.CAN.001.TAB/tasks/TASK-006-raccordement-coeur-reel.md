---
task_id: TASK-006
capability_id: CAP.CAN.001.TAB
capability_name: Tableau de Bord Bénéficiaire
epic: Épic 5 — Raccordement aux capacités COEUR réelles
status: todo
priority: low
depends_on: [TASK-002, TASK-003, TASK-004, TASK-005]
---

# TASK-006 — Raccordement aux capacités COEUR réelles et décommissionnement du stub

## Contexte
Les Épics 1 à 4 ont permis de construire et valider intégralement le tableau de bord en isolation, grâce au stub (TASK-002). Dès que les capacités COEUR (BSP.001.SCO, BSP.001.PAL, BSP.004.ENV, BSP.004.AUT) sont opérationnelles et publient leurs événements réels sur les points de souscription convenus, le stub peut être retiré. Cette tâche est déclenchée par la disponibilité du COEUR — pas par le calendrier interne de CAP.CAN.001.TAB. Elle est une condition de mise en production réelle du tableau de bord, mais pas une condition de livraison des vues elles-mêmes.

## Référence capacité
- Capacité : Tableau de Bord Bénéficiaire (CAP.CAN.001.TAB)
- Zone : CANAL
- ADR gouvernants : ADR-BCM-FUNC-0009, ADR-BCM-URBA-0007, ADR-BCM-URBA-0009

## Ce qu'il faut produire

### Vérification de compatibilité des contrats
Avant le raccordement, vérifier que les événements produits par les capacités COEUR réelles sont conformes aux schémas contractualisés en TASK-001 :
- Schéma de `ScoreComportemental.Recalculé` conforme au contrat v1.0
- Schéma de `Palier.FranchiHausse` conforme au contrat v1.0
- Schéma de `Enveloppe.Consommée` conforme au contrat v1.0
- Schéma de `Transaction.Autorisée` et `Transaction.Refusée` conforme au contrat BSP.004.AUT

Toute divergence doit être résolue avant le décommissionnement du stub. Le code de consommation de CAP.CAN.001.TAB ne doit pas être modifié pour absorber une divergence : c'est au COEUR de respecter le contrat défini en TASK-001.

### Décommissionnement du stub
Retirer le stub d'alimentation par configuration d'environnement en production. Le point de souscription de CAP.CAN.001.TAB reste inchangé — seule la source qui publie dessus change.

### Validation sans régression
Valider sur les deux canaux (web et mobile) que :
- La vue situation courante (TASK-003) affiche des données cohérentes avec les événements COEUR réels
- L'historique transactionnel (TASK-004) est alimenté par les vraies transactions
- La vue mobile (TASK-005) reflète le palier et les enveloppes réels

### Supervision en production
Confirmer, via la supervision, que le flux événementiel réel alimente le read model de CAP.CAN.001.TAB en continu et sans interruption. Aucune régression de `TableauDeBord.Consulté` n'est acceptable.

## Événements métier à produire
`TableauDeBord.Consulté` continue d'être produit normalement — aucun changement sur les événements produits.

## Objets métier impliqués
- **Bénéficiaire** — les données affichées sont désormais réelles
- **Score comportemental**, **Palier**, **Enveloppe**, **Transaction** — tous alimentés par les capacités COEUR réelles

## Souscriptions événementielles requises
Identiques à TASK-002 et TASK-004 — le câblage est inchangé, seul le producteur (stub → COEUR réel) change.

## Définition de Done
- [ ] La compatibilité des schémas d'événements COEUR réels avec les contrats de TASK-001 est vérifiée et documentée
- [ ] Le stub est désactivé en environnement de production
- [ ] La vue situation courante web (TASK-003) affiche des données réelles sans régression
- [ ] L'historique transactionnel web (TASK-004) est alimenté par les vraies transactions sans régression
- [ ] La vue mobile (TASK-005) affiche les données réelles sans régression
- [ ] `TableauDeBord.Consulté` continue d'être produit correctement sur les deux canaux
- [ ] La supervision confirme le flux événementiel réel en production
- [ ] validate_repo.py passe sans erreur
- [ ] validate_events.py passe sans erreur

## Critères d'acceptation (métier)
Un bénéficiaire réel inscrit dans le dispositif consulte son tableau de bord et voit ses données réelles (palier effectif, enveloppes réelles, historique de ses vraies transactions). Les données du tableau de bord sont cohérentes avec les décisions prises par les capacités COEUR.

## Dépendances
- **TASK-002** : l'infrastructure stub/souscription doit être opérationnelle et ses tests validés
- **TASK-003, TASK-004, TASK-005** : toutes les vues doivent être validées sur stub avant le raccordement
- **CAP.BSP.001.SCO** — opérationnel et publiant `ScoreComportemental.Recalculé`
- **CAP.BSP.001.PAL** — opérationnel et publiant `Palier.FranchiHausse`
- **CAP.BSP.004.ENV** — opérationnel et publiant `Enveloppe.Consommée`
- **CAP.BSP.004.AUT** — opérationnel et publiant `Transaction.Autorisée` / `Transaction.Refusée`

## Questions ouvertes
- En cas de divergence de schéma entre le contrat (TASK-001) et la production COEUR réelle, quel est le processus d'arbitrage (qui tranche, quel délai) ?
- Y a-t-il une période de double-alimentation (stub + COEUR en parallèle) pour valider avant de couper le stub ?
