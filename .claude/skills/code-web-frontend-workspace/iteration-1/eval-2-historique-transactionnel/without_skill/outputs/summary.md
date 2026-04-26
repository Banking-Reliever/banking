# Eval 2 — WITHOUT skill — Résumé

## Fichiers créés dans `/home/yoann/banking/frontend-baseline2/CAP.CAN.001.TAB/`

| Fichier | Description |
|---------|-------------|
| `index.html` | Page d'accueil — situation courante (palier, enveloppes, lien vers historique) |
| `historique.html` | Vue historique — filtres, tri, tableau |
| `styles.css` | Styles partagés (variables CSS, header, table, badges, filtres, responsive mobile) |
| `stub-bsp004.js` | Stub BSP.004.AUT — 60 transactions simulées (autorisées + refusées) |
| `read-model.js` | Read model CQRS — projection, méthodes de requête (filtres + tri), émission TableauDeBord.Consulté |
| `historique.js` | Contrôleur vue historique — rendu, filtres, tri, wiring DOM |

## Observations

- 6 fichiers, structure plate (pas de css/ ou js/views/)
- Architecture plus complète que sans skill — stub et read-model séparés
- Filtres implémentés : période, catégorie, statut
- Tri : date et montant (2 sens)
- Refus : 6 codes d'erreur mappés en français
- Règle de dignité respectée dans index.html
- TableauDeBord.Consulté avec canal=web, vue=historique
- Pas d'ES6 modules — script tags classiques
- Pas de config.js séparé ni de MOCK_DATA structuré
