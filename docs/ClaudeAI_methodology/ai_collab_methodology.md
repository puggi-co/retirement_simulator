# AI-Collaborative Development Methodology
*For Enterprise Architects working with AI Assistants*

## Overview
This methodology enables efficient collaboration between seasoned enterprise architects and AI assistants, leveraging architectural expertise while maximizing AI capabilities for implementation and code generation.

## Core Principles

### 1. Architecture-First Approach
- Define data models, API contracts, and system interfaces before implementation
- Use schema-first development (OpenAPI, GraphQL schemas, database schemas)
- Establish clear boundaries between architectural decisions (human) and implementation details (AI)

### 2. Context Continuity
- Maintain persistent context across AI sessions
- Document architectural decisions and constraints
- Keep project state accessible and current

### 3. Iterative Collaboration
- Break complex problems into architectural components
- Use AI for rapid prototyping and boilerplate generation
- Apply enterprise review standards to AI-generated code

## Workspace Structure

```
project-root/
├── .vscode/
│   ├── settings.json          # Coding standards & preferences
│   ├── tasks.json             # Build and development tasks
│   └── extensions.json        # Recommended extensions
├── docs/
│   ├── architecture/
│   │   ├── ADRs/              # Architecture Decision Records
│   │   ├── data-models.md     # Data architecture documentation
│   │   └── api-contracts.md   # Service interfaces
│   ├── context/
│   │   ├── project-state.md   # Current development status
│   │   ├── constraints.md     # Technical and business constraints
│   │   └── ai-context.md      # Quick AI onboarding reference
│   └── README.md              # Project overview
├── schemas/                   # API schemas, data models
├── src/                       # Source code
└── tests/                     # Test suites
```

## Development Workflow

### Phase 1: Architectural Definition
1. **Requirements Analysis**
   - Document functional and non-functional requirements
   - Identify data flows and system boundaries
   - Define integration points and dependencies

2. **Data Architecture Design**
   - Create logical data models
   - Define data governance requirements
   - Establish data quality and security standards

3. **Service Architecture Design**
   - Define API contracts using OpenAPI/GraphQL
   - Establish service boundaries and communication patterns
   - Document authentication and authorization requirements

### Phase 2: AI-Assisted Implementation
1. **Context Preparation**
   - Update `ai-context.md` with current objectives
   - Reference relevant schemas and architectural decisions
   - Specify coding standards and patterns to follow

2. **Iterative Development**
   - Provide AI with clear, bounded implementation tasks
   - Share relevant context files and schemas
   - Review generated code for architectural compliance

3. **Integration & Testing**
   - Use AI for test case generation
   - Validate against architectural constraints
   - Perform enterprise-grade code review

### Phase 3: Documentation & Refinement
1. **Architecture Documentation Updates**
   - Update ADRs based on implementation learnings
   - Refine data models and API contracts
   - Document deployment and operational considerations

2. **Knowledge Capture**
   - Update context files for future AI sessions
   - Document patterns and solutions for reuse
   - Create templates for similar future projects

## AI Collaboration Best Practices

### Context Sharing
- Always provide relevant schema files and architectural documentation
- Include specific constraints and requirements in each request
- Reference previous architectural decisions when relevant

### Task Structuring
- Break large features into smaller, well-defined components
- Provide clear acceptance criteria for each task
- Specify expected patterns and coding standards

### Code Review Focus Areas
- **Security**: Authentication, authorization, data protection
- **Scalability**: Performance patterns, resource utilization
- **Maintainability**: Code organization, documentation, testability
- **Integration**: API compliance, data consistency, error handling

### Quality Gates
- Architectural review before major implementations
- Security review for authentication and data handling
- Performance review for data-intensive operations
- Integration testing for external system interactions

## VS Code Integration

### Essential Extensions
- REST Client (API testing and documentation)
- OpenAPI/Swagger Editor (schema editing)
- Database clients (for data architecture work)
- Git integration (for version control of architectural artifacts)

### Workspace Configuration
```json
// .vscode/settings.json example
{
    "files.associations": {
        "*.md": "markdown"
    },
    "editor.rulers": [80, 120],
    "editor.formatOnSave": true,
    "markdown.preview.openMarkdownLinks": "inEditor"
}
```

### Useful Tasks
- Schema validation
- API contract testing
- Documentation generation
- Architecture diagram updates

## Templates and Patterns

### AI Context Template
```markdown
## Current Objective
[Brief description of what you're trying to accomplish]

## Relevant Architecture
- Data Model: [Link to relevant schema/model]
- API Contract: [Link to OpenAPI spec]
- Constraints: [Key technical/business constraints]

## Implementation Requirements
- Language/Framework: [Specific technology stack]
- Patterns: [Required design patterns or conventions]
- Integration Points: [External systems or services]

## Success Criteria
[Clear, testable criteria for completion]
```

### Architecture Decision Record Template
```markdown
# ADR-XXX: [Title]

## Status
[Proposed | Accepted | Deprecated | Superseded]

## Context
[Description of the forces at play and constraints]

## Decision
[The architectural decision and rationale]

## Consequences
[Positive and negative consequences of the decision]

## Implementation Notes
[Specific guidance for developers and AI assistants]
```

## Continuous Improvement

### Regular Reviews
- Weekly architecture alignment checks
- Monthly methodology refinement sessions
- Quarterly technology and pattern updates

### Metrics and Feedback
- Track development velocity with AI assistance
- Monitor code quality metrics
- Gather feedback on methodology effectiveness

### Knowledge Evolution
- Update templates based on experience
- Refine AI interaction patterns
- Document new architectural patterns and solutions

---

*This methodology is a living document. Update it based on project experience and evolving AI capabilities.*