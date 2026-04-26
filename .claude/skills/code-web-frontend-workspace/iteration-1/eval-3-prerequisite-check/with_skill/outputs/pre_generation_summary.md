Prêt à générer le frontend pour TASK-003 : Gate de consentement et vue situation courante web

Capacité    : Tableau de Bord Bénéficiaire (CAP.CAN.001.TAB) — Zone CANAL
Épic        : Épic 2 — Tableau de bord web — situation courante

Vues à produire :
  - gate-consentement : Vérification bloquante de Consentement.Accordé auprès de CAP.SUP.001.CON (stub en développement) avant tout affichage de données bénéficiaire
  - situation-courante : Vue principale affichant — dans l'ordre de la règle de dignité — la section progression (palier courant, prochain palier, écart) puis la section enveloppes (soldes par catégorie, restrictions après disponibilités)

Contrat API détecté (inféré — microservice non scaffoldé) :
  GET  /beneficiaire/{id}/situation     → SituationCouranteDto { palierCourant, palierSuivant, ecartFranchissement, enveloppes[] }
  GET  /beneficiaire/{id}/consentement  → ConsentementDto { accordé: bool, motif?: string }
  POST /tableau-de-bord/consulte        ← TableauDeBordConsulteCommand { beneficiaireId, palierAffiche, canal, horodatage }
  Port local : 5000  (configurable dans js/config.js)

  NOTE : contrat inféré depuis les DTOs et événements décrits dans TASK-003 et le plan.
  À ajuster une fois le microservice scaffoldé.

Règles métier appliquées dans l'UI :
  - Règle de dignité (ADR-BCM-FUNC-0009) : la section progression (palier accompli, prochain palier) est positionnée DOM avant la section enveloppes/restrictions
  - Gate bloquante : si Consentement.Accordé est absent ou révoqué, aucune donnée bénéficiaire n'est affichée — message explicatif affiché à la place
  - Les catégories bloquées (restrictions) apparaissent après les enveloppes disponibles dans la liste
  - Emission de TableauDeBord.Consulté à chaque consultation avec beneficiaireId, palierAffiche, canal=web, horodatage
  - Les erreurs API sont exprimées en langage métier (pas de codes HTTP bruts)
  - V0 sans gamification : palier + enveloppes, pas de badges ni de score visible

Output : frontend-eval3/CAP.CAN.001.TAB/

Dois-je procéder ?
