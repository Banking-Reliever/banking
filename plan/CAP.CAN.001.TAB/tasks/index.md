# Index des tâches — Tableau de Bord Bénéficiaire (CAP.CAN.001.TAB)

## Épic 1 — Infrastructure d'alimentation événementielle

| ID | Titre | Priorité | Statut | Dépend de |
|----|-------|----------|--------|-----------|
| TASK-001 | Gel du contrat des événements consommés | high | todo | — |
| TASK-002 | Stub d'alimentation et couche de consommation événementielle | high | todo | TASK-001 |

## Épic 2 — Tableau de bord web — situation courante

| ID | Titre | Priorité | Statut | Dépend de |
|----|-------|----------|--------|-----------|
| TASK-003 | Gate de consentement et vue situation courante web | high | todo | TASK-002 |

## Épic 3 — Tableau de bord web — historique transactionnel

| ID | Titre | Priorité | Statut | Dépend de |
|----|-------|----------|--------|-----------|
| TASK-004 | Stub BSP.004.AUT et historique transactionnel web | medium | todo | TASK-003 |

## Épic 4 — Vue mobile — consultation nomade

| ID | Titre | Priorité | Statut | Dépend de |
|----|-------|----------|--------|-----------|
| TASK-005 | Vue mobile — consultation nomade du tableau de bord | medium | todo | TASK-003 |

## Épic 5 — Raccordement aux capacités COEUR réelles

| ID | Titre | Priorité | Statut | Dépend de |
|----|-------|----------|--------|-----------|
| TASK-006 | Raccordement COEUR réel et décommissionnement du stub | low | todo | TASK-002, TASK-003, TASK-004, TASK-005 |

---

## Graphe de dépendances

```
TASK-001
  └─► TASK-002
        └─► TASK-003
              ├─► TASK-004 (parallel)
              └─► TASK-005 (parallel)
                    └─► TASK-006 (déclenché par COEUR opérationnel)
```

**Chemin critique** : TASK-001 → TASK-002 → TASK-003 → TASK-004  
**Parallélisable** : TASK-004 et TASK-005 s'exécutent en parallèle dès TASK-003 terminée  
**TASK-006** : hors cadence interne — déclenchée par la disponibilité des capacités COEUR (BSP.001, BSP.004)

---

## Événements métier produits

| Événement | Produit par |
|-----------|-------------|
| `TableauDeBord.Consulté` (canal=web) | TASK-003, TASK-004 |
| `TableauDeBord.Consulté` (canal=mobile) | TASK-005 |

## Point de départ recommandé

Commencer par **TASK-001** — la définition du contrat d'événements nécessite une coordination avec les équipes BSP.001 et BSP.004 et conditionne tout le reste.
