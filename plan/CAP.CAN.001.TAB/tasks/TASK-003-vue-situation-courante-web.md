---
task_id: TASK-003
capability_id: CAP.CAN.001.TAB
capability_name: Tableau de Bord Bénéficiaire
epic: Épic 2 — Tableau de bord web — situation courante
status: todo
priority: high
depends_on: [TASK-002]
---

# TASK-003 — Gate de consentement et vue situation courante web

## Contexte
C'est la première vue métier du tableau de bord : le bénéficiaire consulte son palier actif, ses enveloppes budgétaires par catégorie et son solde disponible sur l'interface web. La règle de dignité (ADR-BCM-FUNC-0009) impose que la progression accomplie soit présentée avant les restrictions. L'accès aux données est conditionné à `Consentement.Accordé` (CAP.SUP.001.CON) — une gate bloquante. Cette vue produit l'événement métier central de CAP.CAN.001.TAB : `TableauDeBord.Consulté`. Elle constitue le socle dont dépendent toutes les vues suivantes (TASK-004, TASK-005).

## Référence capacité
- Capacité : Tableau de Bord Bénéficiaire (CAP.CAN.001.TAB)
- Zone : CANAL
- ADR gouvernants : ADR-BCM-FUNC-0009, ADR-BCM-URBA-0009

## Ce qu'il faut produire

### Gate de consentement
Avant tout affichage de données bénéficiaire, vérifier que `Consentement.Accordé` est présent pour ce bénéficiaire auprès de CAP.SUP.001.CON (ou son stub en phase de développement). Si le consentement est absent ou révoqué, l'accès au tableau de bord est refusé avec un message explicatif.

### Vue situation courante (interface web)
L'interface web affiche pour le bénéficiaire authentifié :

1. **Section progression** (affichée en premier — règle de dignité) :
   - Palier courant avec son nom et sa description
   - Indication du prochain palier et ce qui le sépare du franchissement

2. **Section enveloppes** :
   - Liste des enveloppes budgétaires actives par catégorie de dépense
   - Pour chaque enveloppe : catégorie, solde disponible, montant total de la période
   - Les restrictions (catégories bloquées) apparaissent après les disponibilités

Les données sont lues depuis le read model maintenu par TASK-002.

### Production de l'événement métier
`TableauDeBord.Consulté` est émis à chaque consultation de cette vue, avec : identifiant bénéficiaire, palier affiché, horodatage, canal (`web`).

## Événements métier à produire
- `TableauDeBord.Consulté` — émis à chaque consultation de la vue par un bénéficiaire authentifié et consentant

## Objets métier impliqués
- **Bénéficiaire** — sujet de la consultation, authentifié préalablement
- **Palier** — état courant affiché (issu du read model de TASK-002)
- **Enveloppe** — soldes par catégorie affichés (issus du read model de TASK-002)

## Souscriptions événementielles requises
Aucune souscription directe — la vue lit le read model produit par TASK-002, qui est alimenté par les souscriptions définies dans cette tâche.

Dépendance de gate :
- `Consentement.Accordé` (de CAP.SUP.001.CON) — vérifié en précondition d'affichage (stub acceptable en développement)

## Définition de Done
- [ ] La gate de consentement bloque l'accès si `Consentement.Accordé` est absent pour le bénéficiaire
- [ ] La vue web affiche le palier courant et sa description
- [ ] La vue web affiche le prochain palier atteignable et l'écart de progression
- [ ] La vue web affiche toutes les enveloppes actives avec leur solde disponible et leur total de période
- [ ] La progression est présentée avant les restrictions (règle de dignité ADR-0009)
- [ ] `TableauDeBord.Consulté` est émis à chaque consultation avec les attributs requis (bénéficiaire, palier, canal=web, horodatage)
- [ ] La vue fonctionne avec le bénéficiaire de test alimenté par le stub de TASK-002
- [ ] validate_repo.py passe sans erreur
- [ ] validate_events.py passe sans erreur

## Critères d'acceptation (métier)
Un bénéficiaire de test qui consulte la page principale voit d'abord sa progression (palier atteint, prochain palier), puis ses enveloppes. Si son consentement est simulé comme révoqué, la page est inaccessible. Chaque consultation trace un événement `TableauDeBord.Consulté`.

## Dépendances
- **TASK-002** : le read model bénéficiaire (score, palier, enveloppes) doit être alimenté avant que la vue puisse afficher des données
- **CAP.SUP.001.CON** : gate `Consentement.Accordé` — stub acceptable en développement
- **CAP.REF.001.PAL** : définition des paliers (noms, descriptions, seuils de franchissement) — stub acceptable

## Questions ouvertes
Aucune bloquante pour démarrer (les données nécessaires sont dans TASK-001 et TASK-002).
