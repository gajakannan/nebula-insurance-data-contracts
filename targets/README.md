# Targets

Platform-specific implementation guidance.

The core ODCS contracts are platform-neutral by default. Target folders describe how to implement or generate platform-specific artifacts without changing canonical business meaning.

## Target Folders

- `fabric/`
- `databricks/`
- `snowflake/`
- `dbt/`
- `kafka/`
- `api/`

## Allowed Target Guidance

Target implementations may define:

- Type mappings
- Naming conventions
- Deployment patterns
- Table or view generation
- Notebook generation
- dbt model generation
- Kafka topic or schema generation
- API schema generation
- Semantic model guidance

## Boundary

Target files may adapt canonical contracts to platform mechanics, but they must not redefine the canonical business concept, field meaning, relationship meaning, or lifecycle semantics.
