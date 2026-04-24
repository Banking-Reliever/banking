# Service Offer

> **Reliever** permet à des individus en fragilité financière de reprendre progressivement le contrôle de leur vie financière quotidienne grâce à un système de paliers d'autonomie croissante, ancré sur une carte dédiée et un score comportemental coordonné entre prescripteurs via open banking, même quand préserver leur dignité est aussi important que contraindre leurs comportements.

## Problem Statement

Les dispositifs existants de lutte contre le surendettement (dossiers Banque de France, plans de redressement) interviennent trop tard, quand la spirale est déjà enclenchée. Ils ne permettent pas d'accompagner les individus au moment des micro-décisions d'achat quotidiennes. Le problème n'est pas l'ignorance — les personnes concernées ont conscience de leur fragilité — mais l'absence d'un soutien concret et d'une autorité externe au moment précis où la décision se pose.

## Primary Beneficiary

Un individu conscient de sa fragilité financière, identifié par la banque, un psychiatre ou un assistant social. Il n'arrive pas à modifier son comportement d'achat seul — non par ignorance, mais par manque d'un soutien doté d'autorité dans l'instant de la décision. Le succès signifie pour lui une autonomie progressive restaurée, jusqu'à la gestion autonome de sa vie financière.

## Scope

### In Scope
- Contrôle des dépenses au moment de l'achat via une carte dédiée dont les règles suivent le palier courant
- Visualisation gamifiée du budget et de la progression (modèle Strava)
- Coordination multi-acteurs (banque, psychiatre, assistant social) avec droits différenciés par rôle

### Out of Scope
- Prêts et virements — Reliever n'est pas un instrument de crédit ni de transfert de fonds
- Gestion du compte bancaire principal — Reliever est une couche de remédiation, pas un compte bancaire
- Intégration aux systèmes bancaires propriétaires — l'open banking est le seul canal d'accès, aucun accord inter-établissements n'est requis

### Open Questions
- Gouvernance des données entre prescripteurs : quelles données le psychiatre voit-il ? La banque voit-elle le diagnostic ?
- Critères précis de transition de palier : quels indicateurs comportementaux l'algorithme mesure-t-il ?
- Émission de la carte dédiée : quel établissement de paiement est le partenaire ?
- Que se passe-t-il quand l'enveloppe est épuisée avant la fin de période ?

## Core Domain Concepts

1. **Bénéficiaire** — l'individu en remédiation financière
2. **Prescripteur** — banque, psychiatre, assistant social
3. **Palier** — niveau d'autonomie courant avec ses règles associées
4. **Score comportemental** — l'équivalent MMR, calculé en continu par l'algorithme
5. **Enveloppe** — budget alloué par catégorie et par période
6. **Événement d'achat** — le moment où la carte est présentée et la règle du palier s'applique
7. **Contournement** — le comportement de bypasser le canal contrôlé (signal : enveloppe non consommée)
8. **Progression** — la trajectoire visible du bénéficiaire, valorisée comme une performance

## Core Events

1. **Achat effectué** — carte présentée, règle du palier appliquée, enveloppe consommée
2. **Achat refusé** — palier bloquant, décision motivée retournée à l'individu
3. **Enveloppe non consommée** — signal de contournement, déclencheur de réévaluation du score
4. **Palier modifié** — par algorithme ou override prescripteur ; l'algorithme reprend le dessus si la réalité comportementale contredit la décision manuelle
5. **Rechute détectée** — score chute, prescripteurs notifiés
6. **Autonomie restituée** — dernier palier atteint, bascule vers application bancaire standard

## Core Tensions

- **Contrôle vs. dignité** — contraindre sans infantiliser ; la dignité n'est pas une valeur morale ajoutée, c'est une condition fonctionnelle : un outil humiliant se sabote lui-même en provoquant le contournement
- **Algorithme vs. jugement humain** — l'override prescripteur peut forcer un palier, mais l'algorithme reste l'autorité continue et reprend le dessus si le saut n'est pas validé par les comportements
- **Transparence vs. vie privée** — partage de données entre acteurs de natures différentes (banque, médecin, travailleur social) ; les périmètres de visibilité par rôle sont une question ouverte critique

## Alternatives Considered

- **Option 1 — Sandbox alimentaire** : micro-compte limité aux courses. Livrable aujourd'hui, mais vision trop étroite — ne couvre pas la vie financière globale et maintient la dépendance aux accords inter-bancaires.
- **Option 2 — Compte sous gestion progressive** : intégration au compte principal avec contrôle gradué par palier. Nécessite un protocole bancaire partagé impossible à obtenir aujourd'hui.
- **Option 3 — Protocole de remédiation ouvert (retenu)** : couche indépendante des établissements bancaires via open banking. La carte dédiée est le seul point de contrôle universel. Résout la fragmentation bancaire sans nécessiter d'accord inter-établissements.
