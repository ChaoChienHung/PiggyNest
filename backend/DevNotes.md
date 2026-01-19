# Development Notes

1. **Models vs Domain vs Services**:  
    In the backend, these three layers serve different purposes and should be kept separate to maintain clarity and flexibility.  
    - **Models** define **how data is stored in the database**. They are SQLAlchemy ORM classes representing tables, columns, and relationships. Models are “dumb” — they hold data but do not contain business rules or API logic.  
    - **Domain** contains **business rules and core logic**. It decides what operations are allowed, enforces invariants, and implements the “rules of the system” independent of the database or API. For example, domain logic checks if a withdrawal exceeds the account balance.  
    - **Services** orchestrate **application workflows**. They call domain logic, manage repositories or database access, handle transactions, and coordinate multiple operations into a complete use case. Services act as the bridge between the API layer and the domain layer.  

    Keeping these layers separate allows:  
    - Easy testing of business logic without touching the database  
    - Flexibility to change storage (database) or API without breaking rules  
    - Clear responsibilities: Models store data, Domain enforces rules, Services orchestrate actions

1. **Choices between `app/api/v1` structures**:  
    Different API structures exist because they optimize for **different stages of development and team size**. There is no universally “correct” structure; instead, each reflects a trade-off between simplicity, scalability, and maintainability.
    1. **Single `routes.py` per API version (Centralized Routing)**  
      This structure groups all endpoints for a version into a single file:
        ```bash
        api/
        └── v1/
            ├── dependencies.py
            └── router.py
        ```
        - Best suited for early-stage projects, MVPs, and AI-heavy backends
        - Encourages a thin API layer with most logic in services or agents
        - Easier to apply shared dependencies (auth, rate limiting, throttling)
        - Faster iteration with less boilerplate
        - Downside: the file can grow large and harder to navigate as endpoints increase

    1. **Router per domain/resource (Modular Routing)**
      This structure splits endpoints by domain or resource:
        ```bash
        api/
          └── v1/
              ├── auth.py
              ├── notes.py
              ├── scrape.py
              ├── reports.py
        ```
        - Best suited for larger applications or multi-developer teams
        - Improves discoverability and ownership of endpoints
        - Maps naturally to RESTful resource design
        - Reduces merge conflicts
        - Downside: introduces more boilerplate and potential dependency duplication

    1. **Hybrid approach (Recommended evolution path)**
      A common mature pattern combines both approaches:
        ```bash
          api/
          └── v1/
              ├── dependencies.py
              ├── router.py        # Aggregates all routers
              ├── notes.py
              ├── scrape.py
        ```
        
        - Keeps endpoints modular while preserving centralized composition
        - Makes API versioning (v2) clean and predictable
        - Allows gradual scaling without early over-engineering

# TODO
