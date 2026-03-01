# Client API REST Asynchrone

Client REST asynchrone avec dashboard terminal en temps réel.

## Structure

```
├── config.py          # Variables d'environnement
├── main.py            # Point d'entrée + boucle de rafraîchissement
├── dashboard.py       # Dashboard Rich (palette Nord)
├── fetchers/
│   ├── resilience.py  # RateLimiter + CircuitBreaker
│   ├── base.py        # fetch() avec retry et timeouts
│   └── apis.py        # GitHub · OpenWeatherMap · NewsAPI
├── models/types.py    # TypedDict pour chaque réponse API
└── tests/             # Tests async avec aioresponses
```
