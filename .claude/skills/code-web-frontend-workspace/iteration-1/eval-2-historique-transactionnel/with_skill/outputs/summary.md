# Eval 2 — WITH skill — Résumé

## Fichiers créés dans `/home/yoann/banking/frontend-eval2/CAP.CAN.001.TAB/`

| Fichier | Rôle |
|---------|------|
| `index.html` | Page d'entrée — navigation hash, 4 conteneurs de vue |
| `css/style.css` | CSS vanilla — variables de thème, règle de dignité visuellement exprimée (progression DOM-first) |
| `js/config.js` | API_BASE_URL (port 5100 inféré), MOCK_DATA commenté (10 transactions test couvrant tous les filtres/tri), flag CONSENT_STUB_ACTIVE |
| `js/api.js` | Wrappers fetch — verifierConsentement, getSituationCourante, getHistoriqueTransactionnel (avec params filtres), notifierConsultation ; 3 types d'erreurs métier ; contrat documenté comme inféré |
| `js/views/situation-courante.js` | Vue Épic 2 — palier + barre progression + enveloppes (disponibles avant bloquées) + lien vers historique |
| `js/views/historique-transactionnel.js` | Vue Épic 3 — table filtrable (période, catégorie, statut) + tri (date/montant asc/desc) + motif refus toujours affiché + émission TableauDeBord.Consulté à l'entrée |
| `js/app.js` | Routeur hash (#situation-courante / #historique), gate consentement, orchestration des vues, messages bloquants |

## Règles métier appliquées

- **Règle de dignité ADR-BCM-FUNC-0009** : `#section-progression` rendu en premier dans le DOM ; enveloppes disponibles avant bloquées ; chaque transaction refusée affiche son `motifRefus` — jamais vide (fallback : "Motif non précisé — contactez votre conseiller")
- **Gate de consentement** : `verifierConsentement()` appelée à l'init — bloque tout affichage si absent ; stub dev toujours `true` (`CONSENT_STUB_ACTIVE`)
- **`TableauDeBord.Consulté`** : émis à chaque accès à la vue historique (`vue='historique', canal='web'`) — non-bloquant
- **Erreurs en langage métier** : HTTP 403 → "Votre consentement est requis", HTTP 401 → "Votre session a expiré", réseau → "Le service est momentanément indisponible"

## Contrat API

INFÉRÉ (pas de microservice dans `sources/` encore). Documenté en tête de `api.js`.

## Couverture DoD

- Filtres sur période, catégorie, statut : couverts (`appliquerFiltres()` + query params)
- Tri par date et montant dans les 2 sens : couvert (`trierTransactions()` + select + clic header colonne)
- Transactions refusées affichent motif intelligible : couvert (motifRefus obligatoire + fallback)
- `TableauDeBord.Consulté` émis à l'accès historique : couvert (en tête de `initHistorique()`)
- Fonctionne avec bénéficiaire test stub : couvert (MOCK_DATA dans config.js, à décommenter)
