---
name: implement-capability
description: Scaffold a new L2 or L3 business capability as a complete .NET microservice following Clean Architecture, DDD, and Event Storming patterns. Use this skill whenever someone says "implement a business capability", "new L2 capability", "new L3 capability", "scaffold a capability", "create a bounded context", "new microservice with DDD", or /implement-capability. Also trigger proactively when the user describes building a service that manages a domain concept end-to-end (orders, customers, policies, claims, enrolment, reservations, etc.) and the project follows the NaiveUnicorn/Foodaroo component stack.
---

# Implement Business Capability

Scaffold a complete .NET 10 microservice for a business capability following Clean Architecture, DDD, and Event Storming. Output goes in `sources/<capability-name>/` relative to the **current working directory**.

## Step 1 — Gather Information

Ask for (or infer from context):

| Field | Format | Example |
|-------|--------|---------|
| **Capability name** | PascalCase | `OrderPlacement`, `CustomerEnrolment` |
| **Namespace prefix** | PascalCase | `FoodarooExperience`, `Maif` |
| **Aggregate root name** | PascalCase | `FoodarooMealOrder`, `CustomerPolicy` |
| **Initial commands** | 1–3, imperative noun | `CreateOrder`, `AddItem` |
| **Initial events** | Past tense, one per command | `OrderCreated`, `ItemAdded` |
| **Bus channel name** | kebab-case | defaults to `{branch}-{ns-kebab}-{cap-kebab}-channel` |

Only ask for what you can't infer. Detect the namespace from existing `.sln` files in the project if not provided.

### Detect the current git branch

```bash
BRANCH=$(git branch --show-current 2>/dev/null | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/-\+/-/g' | sed 's/^-\|-$//g')
echo "Branch slug: $BRANCH"
```

If not in a git repo or the command fails, use `local` as the branch slug.
Use `{branch}` as a new placeholder throughout all generated artefacts.

## Step 2 — Generate a Unique Local Port

```bash
LOCAL_PORT=$(shuf -i 10000-59999 -n 1)
echo "Local port: $LOCAL_PORT"
```

Derive infrastructure ports from this base so capabilities never collide:
- MongoDB: `LOCAL_PORT + 100`
- RabbitMQ AMQP: `LOCAL_PORT + 200`
- RabbitMQ management UI: `LOCAL_PORT + 201`

## Step 3 — Create All Files

Read `references/templates.md` for every code template. Substitute all placeholders:

| Placeholder | Replace with |
|-------------|-------------|
| `{Namespace}` | e.g. `FoodarooExperience` |
| `{CapabilityName}` | e.g. `OrderPlacement` |
| `{AggregateName}` | e.g. `FoodarooMealOrder` |
| `{capability-lower}` | kebab/lowercase, e.g. `order-placement` |
| `{LOCAL_PORT}` | the generated port number |
| `{MONGO_PORT}` | LOCAL_PORT + 100 |
| `{RABBIT_PORT}` | LOCAL_PORT + 200 |
| `{RABBIT_MGMT_PORT}` | LOCAL_PORT + 201 |
| `{branch}` | slugified git branch name, e.g. `feature-my-branch` |
| `{channel}` | bus channel name (prefixed with `{branch}-`) |

### Output directory layout

```
sources/{capability-name}/
└── backend/
    ├── nuget.config
    ├── {Namespace}.{CapabilityName}.sln          ← generated via dotnet CLI
    ├── docker-compose.yml
    ├── config/
    │   ├── cold.json
    │   └── hot.json
    └── src/
        ├── {Namespace}.{CapabilityName}.Domain/
        │   ├── {Namespace}.{CapabilityName}.Domain.csproj
        │   ├── Errors/Code.cs
        │   └── Model/AR/{AggregateName}/
        │       ├── {AggregateName}AR.cs
        │       ├── DTO/{AggregateName}Dto.cs
        │       ├── Factory/I{AggregateName}Factory.cs
        │       └── Factory/{AggregateName}Factory.cs
        ├── {Namespace}.{CapabilityName}.Application/
        │   ├── {Namespace}.{CapabilityName}.Application.csproj
        │   ├── Contract/{AggregateName}/ICreate{AggregateName}Service.cs
        │   └── Service/{AggregateName}/Create{AggregateName}Service.cs
        ├── {Namespace}.{CapabilityName}.Infrastructure/
        │   ├── {Namespace}.{CapabilityName}.Infrastructure.csproj
        │   └── Data/Domain/{AggregateName}MongoRepository.cs
        ├── {Namespace}.{CapabilityName}.Presentation/
        │   ├── {Namespace}.{CapabilityName}.Presentation.csproj
        │   ├── Program.cs
        │   ├── AppSettings.cs
        │   ├── Dockerfile
        │   ├── config/
        │   │   ├── cold.json       ← same content as backend/config/cold.json
        │   │   └── hot.json        ← same content as backend/config/hot.json
        │   └── Controllers/
        │       ├── {AggregateName}CmdController.cs
        │       └── {AggregateName}ReadController.cs
        └── {Namespace}.{CapabilityName}.Contracts/
            ├── {Namespace}.{CapabilityName}.Contracts.csproj
            ├── Commands/Create{AggregateName}Command.cs
            └── Events/{AggregateName}Created.cs
```

For **each additional command** beyond the first, add:
- `Contract/{AggregateName}/I{Command}Service.cs`
- `Service/{AggregateName}/{Command}Service.cs`
- A new `[HttpPost]` action in `{AggregateName}CmdController.cs`
- Corresponding event in `Contracts/Events/`

### Create the solution file using the dotnet CLI

After writing all project files, wire them into a solution:

```bash
cd sources/{capability-name}/backend
dotnet new sln -n "{Namespace}.{CapabilityName}"
dotnet sln add src/{Namespace}.{CapabilityName}.Domain
dotnet sln add src/{Namespace}.{CapabilityName}.Application
dotnet sln add src/{Namespace}.{CapabilityName}.Infrastructure
dotnet sln add src/{Namespace}.{CapabilityName}.Presentation
dotnet sln add src/{Namespace}.{CapabilityName}.Contracts
```

## Step 4 — Print Summary

Note: the `GET /health` endpoint added to `{AggregateName}ReadController` allows the
`test-business-capability` skill to wait for the service to be ready before running integration tests.

```
✓ Capability scaffolded: sources/{capability-name}/

  Local port:           {LOCAL_PORT}
  MongoDB port:         {MONGO_PORT}
  RabbitMQ AMQP:        {RABBIT_PORT}
  RabbitMQ management:  {RABBIT_MGMT_PORT}

To start the local stack:
  cd sources/{capability-name}/backend
  docker-compose up -d
  dotnet run --project src/{Namespace}.{CapabilityName}.Presentation

⚠ Set GITHUB_USERNAME and GITHUB_TOKEN env vars before running dotnet restore
  (required for the naive-unicorn GitHub Packages feed in nuget.config)
```

---

## Naming Conventions

| Artifact | Convention | Example |
|----------|-----------|---------|
| Project | `{Namespace}.{Capability}.{Layer}` | `FoodarooExperience.OrderPlacement.Domain` |
| Aggregate root class | `{Name}AR` | `FoodarooMealOrderAR` |
| DTO class | `{Name}Dto` | `FoodarooMealOrderDto` |
| Repo interface | `IRepository{Name}` | `IRepositoryFoodarooMealOrder` |
| Repo implementation | `{Name}MongoRepository` | `FoodarooMealOrderMongoRepository` |
| Factory interface | `I{Name}Factory` | `IFoodarooMealOrderFactory` |
| Factory class | `{Name}Factory` | `FoodarooMealOrderFactory` |
| Commands | Imperative noun | `CreateOrder`, `AddItem` |
| Events | Past tense noun | `OrderCreated`, `ItemAdded` |
| Bus channel | `{branch}-{ns-kebab}-{cap-kebab}-channel` | `feature-xyz-foodaroo-experience-order-placement-channel` |
| MongoDB collection | PascalCase, matches DTO class | `FoodarooMealOrder` |
