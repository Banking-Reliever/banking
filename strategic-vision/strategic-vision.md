# Strategic Vision

## Service Offer (from product-vision/product.md)
> **Reliever** permet à des individus en fragilité financière de reprendre progressivement le contrôle de leur vie financière quotidienne grâce à un système de paliers d'autonomie croissante, ancré sur une carte dédiée et un score comportemental coordonné entre prescripteurs via open banking, même quand préserver leur dignité est aussi important que contraindre leurs comportements.

## Strategic Intent

Délivrer ce service offer exige que le business maîtrise un core domain unique — l'évaluation comportementale continue et le pilotage des paliers d'autonomie — qui n'existe nulle part ailleurs dans le secteur financier ou médico-social. Autour de ce core, le business doit construire une capacité de coordination multi-acteurs hétérogènes (banque, psychiatre, assistant social) et un contrôle actif des dépenses au point d'achat via open banking, sans dépendre d'aucun accord inter-bancaire. La dignité du bénéficiaire n'est pas une contrainte éthique ajoutée — c'est une condition fonctionnelle : un dispositif humiliant se sabote lui-même en provoquant le contournement qu'il cherche à prévenir.

## Strategic Capabilities

### L1 Capabilities

| ID | Nom | Responsabilité |
|----|-----|----------------|
| SC.001 | **Remédiation Comportementale** | Évaluer en continu la trajectoire financière du bénéficiaire, piloter ses paliers d'autonomie, détecter rechutes et progressions |
| SC.002 | **Accès & Enrollment** | Identifier les individus éligibles, orchestrer leur entrée dans le dispositif avec les prescripteurs, formaliser les conditions de prise en charge |
| SC.003 | **Coordination des Prescripteurs** | Permettre à la banque, au psychiatre et à l'assistant social d'agir de façon coordonnée sur un même bénéficiaire, avec droits et vues différenciés |
| SC.004 | **Contrôle des Dépenses** | Appliquer les règles du palier courant à chaque acte d'achat, gérer les autorisations en temps réel, alimenter le score comportemental |
| SC.005 | **Valorisation de la Progression** | Rendre visible et célébrer la trajectoire du bénéficiaire pour soutenir sa motivation et préserver sa dignité |
| SC.006 | **Gestion de l'Instrument Financier** | Émettre et piloter la carte dédiée, lier ses règles aux paliers, accéder aux données financières via open banking |
| SC.007 | **Conformité & Protection des Données** | Assurer la légalité du partage de données sensibles entre acteurs hétérogènes, garantir les obligations réglementaires |

### L2 Capabilities

#### SC.001 — Remédiation Comportementale

| ID | Nom | Responsabilité |
|----|-----|----------------|
| SC.001.01 | **Scoring Comportemental** | Calculer et mettre à jour en continu le score MMR du bénéficiaire à partir des événements d'achat et des signaux de contournement |
| SC.001.02 | **Gestion des Paliers** | Définir les règles associées à chaque palier, gérer les transitions algorithmiques et les overrides prescripteurs |
| SC.001.03 | **Détection des Signaux** | Identifier les signaux de rechute (enveloppe non consommée) et de progression, et les qualifier pour alimenter le score |
| SC.001.04 | **Arbitrage Algorithme / Humain** | Gérer la tension entre décision algorithmique et override prescripteur, et piloter la reprise de contrôle de l'algorithme |

#### SC.003 — Coordination des Prescripteurs

| ID | Nom | Responsabilité |
|----|-----|----------------|
| SC.003.01 | **Gestion des Rôles & Droits** | Définir et appliquer les périmètres de visibilité et d'action différenciés par type de prescripteur |
| SC.003.02 | **Tableau de Bord Prescripteur** | Offrir à chaque prescripteur une vue adaptée à son rôle sur la situation et la trajectoire du bénéficiaire |
| SC.003.03 | **Alertes & Notifications** | Notifier les prescripteurs concernés lors des événements significatifs — rechute, palier franchi, contournement détecté |
| SC.003.04 | **Co-décision** | Permettre à plusieurs prescripteurs de coordonner une décision d'override sur un même bénéficiaire |

#### SC.004 — Contrôle des Dépenses

| ID | Nom | Responsabilité |
|----|-----|----------------|
| SC.004.01 | **Autorisation à l'Achat** | Décider en temps réel d'autoriser ou refuser une transaction en appliquant les règles du palier courant |
| SC.004.02 | **Gestion des Enveloppes** | Allouer, suivre et ajuster les budgets par catégorie et par période pour chaque bénéficiaire |
| SC.004.03 | **Comparaison & Alternatives** | Proposer des alternatives de prix ou de produits au moment de l'acte d'achat pour aider le bénéficiaire à rester dans son enveloppe |
| SC.004.04 | **Remontée des Événements** | Transmettre chaque événement d'achat (effectué, refusé, contournement détecté) à SC.001 pour alimenter le score comportemental |

## Scope Decisions

### In Strategic Scope
- Évaluation comportementale et pilotage des paliers d'autonomie (core domain)
- Contrôle actif des dépenses au point d'achat via carte dédiée
- Coordination multi-acteurs prescripteurs avec droits différenciés
- Accès aux données financières via open banking exclusivement
- Gamification de la progression pour préserver la dignité du bénéficiaire

### Out of Strategic Scope
- Octroi de crédit et gestion de prêts — Reliever n'est pas un instrument de financement
- Gestion du compte bancaire principal — couche de remédiation uniquement
- Négociation de protocoles inter-bancaires — l'open banking élimine cette dépendance

## Key Tensions Identified

- **Contrôle vs. dignité** — la contrainte doit être perçue comme un soutien, non une punition ; la gamification et la transparence sur les règles sont des leviers fonctionnels, pas cosmétiques
- **Algorithme vs. jugement humain** — l'override prescripteur est nécessaire pour la finesse clinique, mais l'algorithme doit rester l'autorité continue pour éviter les biais individuels
- **Transparence vs. vie privée** — la coordination entre acteurs hétérogènes (banque, médecin, travailleur social) exige une gouvernance fine des périmètres de visibilité par rôle

## Alternatives Considered

- **Structure centrée sur le parcours bénéficiaire** : organiser les L1 autour des étapes de vie du bénéficiaire (entrée, accompagnement, sortie). Rejetée car elle mélange des domaines de responsabilité distincts (comportemental, paiement, coordination) dans une logique de flux plutôt que de capacité.
- **Structure centrée sur les acteurs** : un L1 par type d'acteur (bénéficiaire, banque, prescripteur médical). Rejetée car elle duplique les capacités transversales (scoring, instrument financier) et crée des chevauchements non gouvernables.

## Traceability to Service Offer

| ID | Contribution au service offer |
|----|-------------------------------|
| SC.001 | C'est le cœur différenciant — sans l'évaluation comportementale et les paliers, Reliever n'est qu'une carte prépayée |
| SC.002 | Sans enrollment structuré avec les prescripteurs, le dispositif ne peut pas être activé pour les individus qui en ont besoin |
| SC.003 | La coordination multi-acteurs est la condition de la prescription croisée (banque, psychiatre, assistant social) qui donne au dispositif sa légitimité |
| SC.004 | Le contrôle au point d'achat est le moment de vérité — c'est là que la règle du palier s'applique concrètement |
| SC.005 | La valorisation de la progression est la réponse directe à la tension contrôle/dignité — sans elle, le dispositif risque d'être vécu comme punitif |
| SC.006 | La carte dédiée et l'open banking sont les instruments techniques qui rendent le contrôle possible sans dépendance bancaire |
| SC.007 | Le cadre légal du partage de données entre acteurs hétérogènes est une condition de viabilité du dispositif |
