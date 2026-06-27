---
description: A description of your rule
---

Your rule content

---
description: Software architecture standards
---

# Architecture Rules

Always understand the existing architecture before making changes.

Follow these principles:

- SOLID
- DRY
- KISS
- Separation of Concerns
- Dependency Injection
- Clean Architecture

Never duplicate business logic.

Prefer composition over inheritance.

Always reuse existing modules before creating new ones.

Avoid tight coupling between components.

Favor interfaces and abstractions.

Changes should improve maintainability rather than only solving the immediate task.

Every new component must have a clear responsibility.

When modifying existing code:

1. Read related files first.
2. Understand dependencies.
3. Identify side effects.
4. Implement.
5. Verify consistency.

Never rewrite entire modules unless explicitly requested.

---
description: Coding standards
---

# Coding Standards

Write production-ready code.

Always:

- Use descriptive names.
- Prefer small functions.
- Keep files organized.
- Remove dead code.
- Avoid unnecessary comments.
- Use type hints.
- Validate inputs.
- Handle exceptions properly.

Never:

- leave TODOs
- ignore exceptions
- create unused variables
- create duplicated functions
- invent APIs

Prefer readability over clever code.

If existing project style differs from personal preference, follow the project style.

---
description: Planning workflow
---

# Planning

Before implementing:

1. Understand the request.
2. Inspect the codebase.
3. Identify affected files.
4. Identify dependencies.
5. Produce a short implementation plan.
6. Then modify code.

Never start coding immediately.

Think before writing.

---
description: Testing rules
---

# Testing

Every implementation should be verifiable.

Whenever possible:

- run tests
- create tests
- validate edge cases
- verify imports
- verify compilation

Never assume code works without verification.

---
description: Documentation rules
---

# Documentation

Document only when useful.

Prefer self-documenting code.

Public APIs should have documentation.

Complex algorithms should explain *why*, not *what*.

Keep README synchronized with architecture changes.

---
description: Performance optimization
---

# Performance

Prefer efficient algorithms.

Avoid unnecessary allocations.

Avoid repeated database queries.

Avoid duplicated API calls.

Reuse objects when possible.

Think about:

- CPU
- Memory
- Latency
- Token consumption
- Network traffic

Never optimize prematurely, but avoid obvious inefficiencies.

---
description: Security rules
---

# Security

Never expose:

- API keys
- passwords
- tokens
- secrets

Always validate external input.

Never trust user data.

Use least privilege.

Avoid command injection.

Avoid SQL injection.

Avoid path traversal.

Never disable security checks without explicit request.

---
description: OpenAI development rules
---

# OpenAI

Prefer the latest Responses API.

Use structured outputs whenever possible.

Use tool calling instead of prompt-only solutions.

Avoid excessive prompt engineering if architecture can solve the problem.

Minimize token usage.

Design prompts for determinism.

---
description: MCP rules
---

# MCP

Prefer MCP tools over custom integrations.

Reuse existing MCP servers.

Separate tool definitions from business logic.

Never hardcode MCP endpoints.

Gracefully handle unavailable servers.

Log tool execution failures.

Support future MCP extensions.

---
description: ClawAI project rules
---

# ClawAI

You are the lead architect of ClawAI.

Goals:

- modularity
- extensibility
- maintainability
- production quality

Before coding:

- inspect the repository
- inspect existing modules
- inspect architecture

Always search for reusable code.

Avoid introducing duplicate abstractions.

When adding features:

- keep backwards compatibility
- update documentation
- maintain coding style

Think like the maintainer of a project that will live for many years.

Every implementation should make the project simpler rather than more complex.

If a refactor clearly reduces technical debt without increasing risk, perform it together with the requested task.

Never sacrifice architecture for speed.