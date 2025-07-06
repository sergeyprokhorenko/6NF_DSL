# DSL for Bitemporal Sixth Normal Form with UUIDv7

Here is a concise, Excel-friendly and autogeneratable DSL for a bitemporal Sixth Normal Form DWH with UUIDv7 primary keys, along with equivalent PostgreSQL 18 SQL code.

This project is inspired by Anchor Modeling, Data Vault and Activity Schema.

## 1. DSL Syntax

### Create Entity

```sql

-- DSL
CREATE ENTITY <entity_name>;

-- Equivalent PostgreSQL 18 SQL
CREATE TABLE <entity_name> (
    id UUID PRIMARY KEY DEFAULT uuidv7()
);

```

### Create Reference
Use a Reference with caution because it is not temporal. It is safer to use Entity and Simple Attribute.

```sql

-- DSL
CREATE REFERENCE <reference_name> TYPE <data_type>;

-- Equivalent PostgreSQL 18 SQL
CREATE TABLE <reference_name> (
    id UUID PRIMARY KEY DEFAULT uuidv7(),
    value <data_type> UNIQUE NOT NULL
);

```

### Create Simple Attribute

```sql

-- DSL
CREATE ATTRIBUTE <attribute_name> FOR ENTITY <entity_name> TYPE <data_type>;

-- Equivalent PostgreSQL 18 SQL
CREATE TABLE <attribute_name> (
    entity_id UUID NOT NULL REFERENCES <entity_name>(id),
    value <data_type> UNIQUE NOT NULL,
    valid_from TIMESTAMPTZ DEFAULT NOW(),
    recorded_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (entity_id, valid_from, recorded_at)
);

```

### Create Attribute with Reference

```sql

-- DSL
CREATE ATTRIBUTE <attribute_name> FOR ENTITY <entity_name> REFERENCE <reference_name>;

-- Equivalent PostgreSQL 18 SQL
CREATE TABLE <attribute_name> (
    entity_id UUID NOT NULL REFERENCES <entity_name>(id),
    reference_id UUID NOT NULL REFERENCES <reference_name>(id),
    valid_from TIMESTAMPTZ DEFAULT NOW(),
    recorded_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (entity_id, valid_from, recorded_at)
);

```

### Create Struct of Attributes
Use a Struct of Attributes for **input** attributes that change simultaneously - such as document or message attributes - or for **output** attributes of Activity Stream or other normalized data mart. For large numbers of attributes, the jsonb data type is recommended.

```sql

-- DSL
CREATE STRUCT <struct_name> FOR ENTITY <entity_name> (
<attribute_name> TYPE <data_type>,
-- etc.
<attribute_name> REFERENCE <reference_name>
);

-- Equivalent PostgreSQL 18 SQL
CREATE TABLE <struct_name> (
    entity_id UUID NOT NULL REFERENCES <entity_name>(id), -- for example, event_id
    <attribute_name> <data_type> UNIQUE NOT NULL,
    -- etc.
    <attribute_name> UUID NOT NULL REFERENCES <reference_name>(id),
    valid_from TIMESTAMPTZ DEFAULT NOW(),
    recorded_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (entity_id, valid_from, recorded_at)
);

```

### Create Relationship

```sql

-- DSL
CREATE RELATIONSHIP <relationship_name> OF
    <entity_or_reference_1_name>, 
    <entity_or_reference_2_name>,
    -- etc.
    <entity_or_reference_n_name>;

-- Equivalent PostgreSQL 18 SQL
CREATE TABLE <relationship_name> (
    id UUID DEFAULT uuidv7() UNIQUE,
    /*It is not recommended to create external references to this auxiliary key (id) for implementing business logic.*/
    /*Use this key only for technical purposes: logging, API, data exchange, debugging, auditing, manual analysis*/
    <entity_or_reference_1_name_id> UUID NOT NULL REFERENCES <entity_or_reference_1_name>(id),
    <entity_or_reference_2_name_id> UUID NOT NULL REFERENCES <entity_or_reference_2_name>(id),
    -- etc.
    <entity_or_reference_n_name_id> UUID NOT NULL REFERENCES <entity_or_reference_n_name>(id),
    valid_from TIMESTAMPTZ DEFAULT NOW(),
    recorded_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (
        <entity_or_reference_1_name_id>, 
        <entity_or_kreference_2_name_id>,
        -- etc.
        <entity_or_reference_n_name_id>,
        valid_from,
        recorded_at
    )
);

```

### Snapshot Query
The primary key entity_id is preserved. Window functions are applied.

```sql

-- DSL
SELECT <attributes> FROM ATTRIBUTES OF <entity_name> VALID AT <valid_at> LAST RECORDED BEFORE <last_recorded_before>;

-- Equivalent PostgreSQL 18 SQL
SELECT 
    entity_name.id,
    attribute1_result.value,
    attribute2_result.value,
    attribute3_result.value
FROM entity_name
LEFT JOIN LATERAL (
    SELECT value 
    FROM attribute1_name 
    WHERE attribute1_name.entity_id = entity_name.id
      AND attribute1_name.valid_from <= <valid_at>
      AND attribute1_name.recorded_at <= <last_recorded_before>
    ORDER BY attribute1_name.valid_from DESC, attribute1_name.recorded_at DESC
    LIMIT 1
) attribute1_result ON true
LEFT JOIN LATERAL (
    SELECT value 
    FROM attribute2_name 
    WHERE attribute2_name.entity_id = entity_name.id
      AND attribute2_name.valid_from <= <valid_at>
      AND attribute2_name.recorded_at <= <last_recorded_before>
    ORDER BY attribute2_name.valid_from DESC, attribute2_name.recorded_at DESC
    LIMIT 1
) attribute2_result ON true
LEFT JOIN LATERAL (
    SELECT value 
    FROM attribute3_name 
    WHERE attribute3_name.entity_id = entity_name.id
      AND attribute3_name.valid_from <= <valid_at>
      AND attribute3_name.recorded_at <= <last_recorded_before>
    ORDER BY attribute3_name.valid_from DESC, attribute3_name.recorded_at DESC
    LIMIT 1
) attribute3_result ON true
ORDER BY entity_name.id;

```



