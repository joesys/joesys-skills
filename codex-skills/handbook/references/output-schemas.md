# Output Schemas — $handbook

Structured output contracts for all agents dispatched by `$handbook`.

---

## Analysis Agent Output Schema

All 6 analysis agents return a JSON object with these shared fields plus agent-specific fields.

### Shared Fields (required for all agents)

```json
{
  "agent": "<agent-name>",
  "modules": ["module1", "module2"],
  "claims": [
    {
      "text": "The auth module uses JWT tokens for session management",
      "citation": "src/auth/jwt.ts:15",
      "confidence": "high"
    }
  ],
  "diagrams": [
    {
      "title": "Module Dependency Graph",
      "type": "graph",
      "mermaid": "graph TD\n  auth --> db\n  api --> auth"
    }
  ],
  "unresolved": [
    "Why was Redis chosen over Memcached for session storage?"
  ]
}
```

### Agent-Specific Fields

#### Architecture Analyst
```json
{
  "dependency_graph": "<mermaid source>",
  "layers": [
    {"name": "Presentation", "modules": ["src/routes", "src/views"]},
    {"name": "Business Logic", "modules": ["src/services"]},
    {"name": "Data Access", "modules": ["src/repositories"]}
  ],
  "patterns": [
    {"name": "Repository Pattern", "files": ["src/repositories/user.ts:1"]}
  ],
  "folder_map": [
    {"path": "src/", "description": "Application source code"},
    {"path": "src/routes/", "description": "HTTP route handlers"}
  ],
  "naming_conventions": [
    {"scope": "files", "pattern": "kebab-case", "example": "user-service.ts"},
    {"scope": "classes", "pattern": "PascalCase", "example": "UserService"}
  ]
}
```

#### Code Flow Tracer
```json
{
  "entry_points": [
    {"file": "src/index.ts:1", "type": "main", "description": "Application entry"}
  ],
  "main_flow": {
    "title": "Application Startup",
    "steps": [
      {"description": "Load config", "file": "src/config.ts:10", "next": "Connect DB"}
    ],
    "mermaid": "<sequence diagram source>"
  },
  "hot_paths": [
    {
      "name": "HTTP Request Lifecycle",
      "frequency": "Every incoming request",
      "steps": [],
      "mermaid": "<sequence diagram source>"
    }
  ]
}
```

#### Domain & Data Analyst
```json
{
  "entities": [
    {"name": "User", "file": "src/models/user.ts:5", "fields": ["id", "email", "role"]}
  ],
  "glossary": [
    {"term": "Workspace", "definition": "A container for related projects", "defined_in": "src/models/workspace.ts:1"}
  ],
  "state_transitions": [
    {"entity": "Order", "mermaid": "<stateDiagram source>"}
  ],
  "invariants": [
    {"description": "A user must belong to at least one workspace", "enforced_at": "src/services/user.ts:42"}
  ]
}
```

#### Dependency Analyst
```json
{
  "dependencies": [
    {
      "name": "express",
      "version": "4.18.2",
      "purpose": "HTTP server framework",
      "import_sites": ["src/server.ts:1", "src/routes/index.ts:1"],
      "replaceability": "Medium — used for routing and middleware; Fastify or Koa would require route handler rewrites"
    }
  ],
  "external_apis": [
    {"name": "Stripe", "purpose": "Payment processing", "client_file": "src/integrations/stripe.ts:1"}
  ],
  "config_system": {
    "loader": "src/config.ts",
    "env_vars": [
      {"name": "DATABASE_URL", "required": true, "default": null}
    ]
  }
}
```

#### Git Archaeologist
```json
{
  "churn_hotspots": [
    {"file": "src/billing/charge.ts", "commits_6mo": 47, "contributors": 3}
  ],
  "major_refactors": [
    {"date": "2026-01", "description": "Migrated from REST to GraphQL", "commits": ["abc123"]}
  ],
  "fragile_areas": [
    {"file": "src/legacy/parser.ts", "signal": "Appears in 12 bug-fix commits", "test_coverage": "low"}
  ],
  "contributor_map": [
    {"module": "src/auth/", "primary_contributors": ["alice", "bob"]}
  ]
}
```

#### Beginner Path Scout
```json
{
  "prerequisites": [
    {"tool": "Node.js", "version": ">=18", "install": "nvm install 18"}
  ],
  "setup_steps": [
    {"step": 1, "command": "git clone <repo>", "expected": "Repository cloned"},
    {"step": 2, "command": "npm install", "expected": "Dependencies installed, no errors"}
  ],
  "common_errors": [
    {"symptom": "EACCES permission denied", "cause": "Global npm install without sudo", "fix": "Use nvm or configure npm prefix"}
  ],
  "dev_workflow": {
    "edit_test_cycle": "npm run dev → edit files → browser auto-reloads",
    "test_command": "npm test",
    "seed_data": "npm run db:seed"
  }
}
```

---

## Chapter Writer Output Schema

All chapter writers return:

```json
{
  "title": "Chapter Title",
  "content": "<full markdown content>",
  "cross_references": [
    {"target_chapter": "Extension Guide", "anchor": "change-recipes-style", "context": "See change recipes for step-by-step guides"}
  ],
  "diagrams": [
    {"title": "Diagram Title", "mermaid": "<mermaid source>"}
  ]
}
```

The `content` field contains the full markdown for the chapter, including all headings (starting at H2 level — the chapter title H1 is added during assembly).
