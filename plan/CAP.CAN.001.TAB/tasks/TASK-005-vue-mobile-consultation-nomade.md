---
task_id: TASK-005
capability_id: CAP.CAN.001.TAB
capability_name: Tableau de Bord Bénéficiaire
epic: Épic 4 — Vue mobile — consultation nomade
status: todo
priority: medium
depends_on: [TASK-003]
---

# TASK-005 — Vue mobile — consultation nomade du tableau de bord

## Contexte
Le bénéficiaire doit pouvoir consulter sa situation financière en situation nomade, depuis un appareil mobile. L'interface mobile n'est pas une réduction de l'interface web : c'est un mode de lecture optimisé pour la rapidité, conçu pour les micro-instants de vérification avant un achat. Elle partage le même read model que TASK-003 (pas de nouvelles souscriptions événementielles) mais expose un sous-ensemble de données simplifié : palier courant et soldes des enveloppes principales, sans filtres, sans tri, sans colonnes secondaires. La règle de dignité s'applique identiquement. `TableauDeBord.Consulté` est produit avec le tag `canal=mobile` pour distinguer les usages analytiquement.

## Référence capacité
- Capacité : Tableau de Bord Bénéficiaire (CAP.CAN.001.TAB)
- Zone : CANAL
- ADR gouvernants : ADR-BCM-FUNC-0009, ADR-BCM-URBA-0009

## Ce qu'il faut produire

### Interface mobile — vue situation courante allégée
L'interface mobile affiche pour le bénéficiaire authentifié :

1. **Section progression** (affichée en premier — règle de dignité) :
   - Palier courant (nom et niveau uniquement, pas la description complète)
   - Indication visuelle simple du prochain palier

2. **Section enveloppes** :
   - Soldes des enveloppes principales (les catégories les plus fréquentes, déterminées par la définition du palier dans CAP.REF.001.PAL)
   - Pour chaque enveloppe : catégorie et solde disponible uniquement (pas le montant total de période, pas de graphique)
   - Pas de filtres, pas de tri, pas de colonnes secondaires

**Ce que la vue mobile n'expose pas** (réservé au web) :
- Historique transactionnel
- Filtres et tri
- Détail complet de toutes les enveloppes secondaires
- Description complète du palier

### Gate de consentement
La gate `Consentement.Accordé` de TASK-003 s'applique identiquement sur le canal mobile.

### Production de l'événement métier
`TableauDeBord.Consulté` est émis à chaque consultation de la vue mobile, avec le tag `canal=mobile`, pour permettre une distinction analytique des usages web et mobile.

## Événements métier à produire
- `TableauDeBord.Consulté` — émis à chaque consultation de la vue mobile (attributs : bénéficiaire, palier, canal=mobile, horodatage)

## Objets métier impliqués
- **Bénéficiaire** — sujet de la consultation
- **Palier** — affiché de manière simplifiée (nom + niveau)
- **Enveloppe** — soldes des enveloppes principales uniquement

## Souscriptions événementielles requises
Aucune souscription nouvelle — la vue mobile consomme le même read model que TASK-003, alimenté par les souscriptions de TASK-002.

## Définition de Done
- [ ] L'interface mobile affiche le palier courant (nom et niveau) en premier
- [ ] L'interface mobile affiche les soldes des enveloppes principales (catégorie + solde disponible uniquement)
- [ ] Aucun filtre, aucun tri, aucune colonne secondaire n'est présent dans l'interface mobile
- [ ] La gate `Consentement.Accordé` bloque l'accès si le consentement est absent
- [ ] `TableauDeBord.Consulté` est émis avec `canal=mobile` à chaque consultation
- [ ] La règle de dignité est respectée (progression avant restrictions)
- [ ] La vue fonctionne avec le bénéficiaire de test alimenté par le stub de TASK-002
- [ ] validate_repo.py passe sans erreur
- [ ] validate_events.py passe sans erreur

## Critères d'acceptation (métier)
Un bénéficiaire qui ouvre l'interface mobile voit immédiatement son palier et ses soldes principaux en deux ou trois éléments visuels. L'expérience est lisible en moins de cinq secondes sans défilement. Chaque ouverture trace un `TableauDeBord.Consulté` tagué `canal=mobile`.

## Dépendances
- **TASK-003** : le read model et la gate de consentement doivent exister — la vue mobile les réutilise sans modification

## Questions ouvertes
- Quelles enveloppes sont considérées "principales" sur mobile ? Sont-elles déterminées par le palier courant (CAP.REF.001.PAL) ou par la fréquence d'utilisation du bénéficiaire ?
- L'interface mobile est-elle une application native (iOS/Android) ou une webapp responsive ? Ce choix ne bloque pas la tâche mais peut impacter les sprints d'interface.
