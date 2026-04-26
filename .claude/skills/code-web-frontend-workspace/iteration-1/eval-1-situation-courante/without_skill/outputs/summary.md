# Eval 1 — WITHOUT skill — Résumé

## Fichiers créés dans `/home/yoann/banking/frontend-baseline/CAP.CAN.001.TAB/`

| Fichier | Description |
|---------|-------------|
| `index.html` | Page principale du tableau de bord |
| `styles.css` | CSS partagé |
| `api.js` | Couche API (endpoints déduits de la tâche) |
| `app.js` | Logique applicative |

## Contrat API déduit

- `GET /api/consent/{beneficiaireId}` — gate consentement
- `GET /api/dashboard/{beneficiaireId}/situation` — read model TASK-002
- `POST /api/events` — émission TableauDeBord.Consulté

## Observations

- 4 fichiers seulement (pas de structure css/ ou js/views/)
- Pas de js/config.js séparé — API_BASE_URL dans api.js directement
- Gate consentement implémentée (full-screen overlay)
- Règle de dignité respectée (progression d'abord dans le DOM)
- TableauDeBord.Consulté émis avec attributs requis
- Labels en français
- Pas de MOCK_DATA explicite — stubs inline dans api.js
- JavaScript : pas d'ES6 modules (pas de import/export), script tags classiques
