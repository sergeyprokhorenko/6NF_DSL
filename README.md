# DSL for Bitemporal Sixth Normal Form with UUIDv7

Here is a concise, Excel-friendly and autogeneratable DSL for a bitemporal Sixth Normal Form DWH with UUIDv7 primary keys, along with equivalent PostgreSQL 18 SQL code.

This project is inspired by Anchor Modeling, Data Vault and Activity Schema.

## 1. DSL Syntax

### Create Entity

```sql

-- DSL
CREATE ENTITY <entity>;

-- Equivalent PostgreSQL 18 SQL
CREATE TABLE <entity> (
    id UUID PRIMARY KEY DEFAULT uuidv7()
);

```

### Create Reference
Use a Reference with caution because it is not temporal. It is safer to use Entity and Simple Attribute.

```sql

-- DSL
CREATE REFERENCE <reference> TYPE <data_type>;

-- Equivalent PostgreSQL 18 SQL
CREATE TABLE <reference> (
    id UUID PRIMARY KEY DEFAULT uuidv7(),
    value <data_type> UNIQUE NOT NULL
);

```

### Create Simple Attribute

```sql

-- DSL
CREATE ATTRIBUTE <attribute> FOR ENTITY <entity> TYPE <data_type>;

-- Equivalent PostgreSQL 18 SQL
CREATE TABLE <attribute> (
    entity_id UUID NOT NULL REFERENCES <entity>(id),
    value <data_type> UNIQUE NOT NULL,
    valid_from TIMESTAMPTZ DEFAULT NOW(),
    recorded_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (entity_id, valid_from, recorded_at)
);

```

### Create Attribute with Reference

```sql

-- DSL
CREATE ATTRIBUTE <attribute> FOR ENTITY <entity> REFERENCE <reference>;

-- Equivalent PostgreSQL 18 SQL
CREATE TABLE <attribute> (
    entity_id UUID NOT NULL REFERENCES <entity>(id),
    reference_id UUID NOT NULL REFERENCES <reference>(id),
    valid_from TIMESTAMPTZ DEFAULT NOW(),
    recorded_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (entity_id, valid_from, recorded_at)
);

```

### Create Struct of Attributes
Use a Struct of Attributes for **input** attributes that change simultaneously - such as document or message attributes - or for **output** attributes of Activity Stream or other normalized data mart. For large numbers of attributes, the jsonb data type is recommended.

```sql

-- DSL
CREATE STRUCT <struct> FOR ENTITY <entity> (
<attribute> TYPE <data_type>,
-- etc.
<attribute> REFERENCE <reference>
);

-- Equivalent PostgreSQL 18 SQL
CREATE TABLE <struct> (
    entity_id UUID NOT NULL REFERENCES <entity>(id), -- for example, event_id
    <attribute> <data_type> UNIQUE NOT NULL, -- for example, metadata from the source
    -- etc.
    <attribute> UUID NOT NULL REFERENCES <reference>(id),
    valid_from TIMESTAMPTZ DEFAULT NOW(),
    recorded_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (entity_id, valid_from, recorded_at)
);

```

### Create Relationship

```sql

-- DSL
CREATE RELATIONSHIP <relationship> OF
    <entity_or_reference_1>, 
    <entity_or_reference_2>,
    -- etc.
    <entity_or_reference_n>;

-- Equivalent PostgreSQL 18 SQL
CREATE TABLE <relationship> (
    id UUID DEFAULT uuidv7() UNIQUE,
    /*It is not recommended to create external references to this auxiliary key (id) for implementing business logic.*/
    /*Use this key only for technical purposes: logging, API, data exchange, debugging, auditing, manual analysis*/
    <entity_or_reference_1_id> UUID NOT NULL REFERENCES <entity_or_reference_1>(id),
    --For example:     user_id UUID NOT NULL REFERENCES user(id),
    <entity_or_reference_2_id> UUID NOT NULL REFERENCES <entity_or_reference_2>(id),
    -- etc.
    <entity_or_reference_n_id> UUID NOT NULL REFERENCES <entity_or_reference_n>(id),
    valid_from TIMESTAMPTZ DEFAULT NOW(),
    recorded_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (
        <entity_or_reference_1_id>, 
        <entity_or_kreference_2_id>,
        -- etc.
        <entity_or_reference_n_id>,
        valid_from,
        recorded_at
    )
);

```

### Entity and Its Attributes Snapshot Query
The primary key entity_id is preserved.
Structs of Attributes can be used as sources alongside Simple Attributes and Attributes with Reference.

```sql

-- DSL
SELECT <attributes> FROM ATTRIBUTES OF <entity> VALID AT <valid_at> LAST RECORDED BEFORE <last_recorded_before>;

-- Equivalent PostgreSQL 18 SQL
SELECT 
    entity.id,
    attribute1_result.value,
    attribute2_result.value,
    attribute3_result.value
FROM entity
LEFT JOIN LATERAL (
    SELECT value 
    FROM attribute1
    WHERE attribute1.entity_id = entity.id
      AND attribute1.valid_from <= <valid_at>
      AND attribute1.recorded_at <= <last_recorded_before>
    ORDER BY attribute1.valid_from DESC, attribute1.recorded_at DESC
    LIMIT 1
) attribute1_result ON true
LEFT JOIN LATERAL (
    SELECT value 
    FROM attribute2 
    WHERE attribute2.entity_id = entity.id
      AND attribute2.valid_from <= <valid_at>
      AND attribute2.recorded_at <= <last_recorded_before>
    ORDER BY attribute2.valid_from DESC, attribute2.recorded_at DESC
    LIMIT 1
) attribute2_result ON true
LEFT JOIN LATERAL (
    SELECT value 
    FROM attribute3
    WHERE attribute3.entity_id = entity.id
      AND attribute3.valid_from <= <valid_at>
      AND attribute3.recorded_at <= <last_recorded_before>
    ORDER BY attribute3.valid_from DESC, attribute3.recorded_at DESC
    LIMIT 1
) attribute3_result ON true
ORDER BY entity.id;

```

### Relationship Snapshot Query

```sql

-- DSL
SELECT <entities_and_references> FROM <relationship> VALID AT <valid_at> LAST RECORDED BEFORE <last_recorded_before>;

-- Equivalent PostgreSQL 18 SQL
SELECT
    id,
    <entity_or_reference_1_id>,
    <entity_or_reference_2_id>,
    -- etc.
    <entity_or_reference_n_id>,
    valid_from,
    recorded_at
FROM (
    SELECT
        id,
        <entity_or_reference_1_id>,
        <entity_or_reference_2_id>,
        -- etc.
        <entity_or_reference_n_id>,
        valid_from,
        recorded_at,
        ROW_NUMBER() OVER (
            PARTITION BY
                <entity_or_reference_1_id>,
                <entity_or_reference_2_id>
                -- etc.
                <entity_or_reference_n_id>
            ORDER BY
                valid_from DESC,
                recorded_at DESC
        ) AS rn
    FROM <relationship>
    WHERE
        valid_from <= <valid_at>
        AND recorded_at <= <last_recorded_before>
) 
WHERE rn = 1
ORDER BY relationship.id;

```


### Table Normalization Query

```sql

-- DSL
NORMALIZE
    INTO <entity1> (<attribute_11>,  <attribute_12>,  etc., <attribute_1n>) SELECT …
    INTO <entity2> (<attribute_21>,  <attribute_22>,  etc., <attribute_2m>) SELECT …
    etc.
RELATIONSHIPS  
    <relationship_1>,
    <relationship_2>,
    etc.,
    <relationship_k>
FROM <table> 
WHERE <conditions>;

```

### Сделано искусственным интеллектом:

```sql

-- DSL
NORMALIZE
    INTO <entity1> (<attribute_11>, <attribute_12>, <attribute_13>) SELECT DISTINCT col1, col2, col3 FROM <source_table>
    INTO <entity2> (<attribute_21>, <attribute_22>) SELECT DISTINCT col4, col5 FROM <source_table>
    INTO <entity3> (<attribute_31>) SELECT DISTINCT col6 FROM <source_table>
RELATIONSHIPS  
    <relationship_1> OF <entity1>, <entity2>,
    <relationship_2> OF <entity2>, <entity3>
FROM <source_table> 
WHERE <condition>;

-- Equivalent PostgreSQL 18 SQL
WITH entity1_insert AS (
    INSERT INTO <entity1> (id, <attribute_11>, <attribute_12>, <attribute_13>, valid_from, recorded_at)
    SELECT 
        uuidv7(),
        DISTINCT col1, 
        col2, 
        col3,
        NOW(),
        NOW()
    FROM <source_table>
    WHERE <condition>
    ON CONFLICT (<attribute_11>, <attribute_12>, <attribute_13>, valid_from, recorded_at) DO NOTHING
    12>, <attribute_13>
),
entity2_insert AS (
    INSERT INTO <entity2> (id, <attribute_21>, <attribute_22>, valid_from, recorded_at)
    SELECT 
        uuidv7(),
        DISTINCT col4,
        col5,
        NOW(),
        NOW()
    FROM <source_table>
    WHERE <condition>
    ON CONFLICT (<attribute_21>, <attribute_22>, valid_from, recorded_at) DO NOTHING
    RETURNING id, <attribute_21>, <attribute_22>
),
entity3_insert AS (
    INSERT INTO <entity3> (id, <attribute_31>, valid_from, recorded_at)
    SELECT 
        uuidv7(),
        DISTINCT col6,
        NOW(),
        NOW()
    FROM <source_table>
    WHERE <condition>
    ON CONFLICT (<attribute_31>, valid_from, recorded_at) DO NOTHING
    RETURNING id, <attribute_31>
),
relationship1_insert AS (
    INSERT INTO <relationship_1> (
        id,
        <entity1_id>,
        <entity2_id>,
        valid_from,
        recorded_at
    )
    SELECT 
        uuidv7(),
        e1.id,
        e2.id,
        NOW(),
        NOW()
    FROM entity1_insert e1
    JOIN <source_table> s ON (e1.<attribute_11> = s.col1 AND e1.<attribute_12> = s.col2 AND e1.<attribute_13> = s.col3)
    JOIN entity2_insert e2 ON (e2.<attribute_21> = s.col4 AND e2.<attribute_22> = s.col5)
    WHERE <condition>
    ON CONFLICT (<entity1_id>, <entity2_id>, valid_from, recorded_at) DO NOTHING
    RETURNING id, <entity1_id>, <entity2_id>
),
relationship2_insert AS (
    INSERT INTO <relationship_2> (
        id,
        <entity2_id>,
        <entity3_id>,
        valid_from,
        recorded_at
    )
    SELECT 
        uuidv7(),
        e2.id,
        e3.id,
        NOW(),
        NOW()
    FROM entity2_insert e2
    JOIN <source_table> s ON (e2.<attribute_21> = s.col4 AND e2.<attribute_22> = s.col5)
    JOIN entity3_insert e3 ON (e3.<attribute_31> = s.col6)
    WHERE <condition>
    ON CONFLICT (<entity2_id>, <entity3_id>, valid_from, recorded_at) DO NOTHING
    RETURNING id, <entity2_id>, <entity3_id>
)
SELECT 
    'entity1' AS table_name, 
    COUNT(*) AS inserted_rows 
FROM entity1_insert
UNION ALL
SELECT 
    'entity2' AS table_name, 
    COUNT(*) AS inserted_rows 
FROM entity2_insert
UNION ALL
SELECT 
    'entity3' AS table_name, 
    COUNT(*) AS inserted_rows 
FROM entity3_insert
UNION ALL
SELECT 
    'relationship_1' AS table_name, 
    COUNT(*) AS inserted_rows 
FROM relationship1_insert
UNION ALL
SELECT 
    'relationship_2' AS table_name, 
    COUNT(*) AS inserted_rows 
FROM relationship2_insert;


```



