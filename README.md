# agent-eval-harness

QA automatisé pour agents IA — même logique qu'un outil de tests de non-régression
(Compuware QA Manager hier, Playwright aujourd'hui) mais appliqué au **comportement d'un agent LLM**
plutôt qu'à une UI web.

## Pourquoi
Un agent IA n'est pas un LLM nu : il décide, appelle des tools, boucle, peut halluciner un appel,
dépasser un budget de tokens/latence, ou dériver de la consigne. Ce harness fait tourner un jeu de
cas de test fixes contre l'agent et vérifie le comportement, pas juste le texte de sortie.

## Statut
v0 — squelette + 2 cas de test de démo (mock agent). Rien de branché sur un vrai agent encore.

## Concepts testés (v0 → v1)
- **Assertions de contenu** : la réponse contient/ne contient pas X
- **Assertions de comportement** : le bon tool a été appelé, avec les bons arguments
- **Budgets** : tokens, latence, nombre de tours
- **Non-régression** : diff vs une baseline de run précédente (`reports/baseline.json`)

## Structure
- `harness/` — runner + modèle d'assertions
- `tests/cases/` — cas de test déclaratifs (YAML/JSON), un fichier = un scénario
- `reports/` — sorties de run (JSON) + baseline

## Lancer
```bash
pip install -r requirements.txt
pytest -q
```

## Roadmap
- [ ] v0: runner pytest + mock agent + assertions de contenu (fait)
- [ ] v1: brancher un vrai agent (OpenAI/Claude function-calling) via un adaptateur
- [ ] v2: budgets tokens/latence + rapport HTML diffable
- [ ] v3: cas adversariaux (prompt injection, tool misuse) inspirés de Building Scalable Agentic Systems (DataCamp)
