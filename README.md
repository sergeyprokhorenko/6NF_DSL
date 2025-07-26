# DSL for Bitemporal Sixth Normal Form with UUIDv7

Here is a concise, Excel-friendly and autogeneratable DSL for a bitemporal Sixth Normal Form DWH with UUIDv7 primary keys, along with equivalent PostgreSQL 18 SQL code.

This project is inspired by Anchor Modeling, Data Vault and Activity Schema.

## Table of Contents

- [1. Create Entity](#1-create-entity)
- [2. Create Reference](#2-create-reference)
- [3. Create Simple Attribute](#3-create-simple-attribute)
- [4. Create Attribute with Reference](#4-create-attribute-with-reference)
- [5. Create Struct of Attributes](#5-create-struct-of-attributes)
- [6. Create Relationship](#6-create-relationship)
- [7. Entity and Its Attributes Snapshot Query](#7-entity-and-its-attributes-snapshot-query)
- [8. Relationship Snapshot Query](#8-relationship-snapshot-query)
- [9. Table Normalization Query](#9-table-normalization-query)


## 1. Create Entity

```sql

-- EBNF


-- DSL
CREATE ENTITY <entity>;

-- Equivalent PostgreSQL 18 SQL
CREATE TABLE <entity> (
    id UUID PRIMARY KEY DEFAULT uuidv7()
);

```

## 2. Create Reference
Use a Reference with caution because it is not temporal. It is safer to use Entity and Simple Attribute.

```sql

-- EBNF


-- DSL
CREATE REFERENCE <reference> TYPE <data_type>;

-- Equivalent PostgreSQL 18 SQL
CREATE TABLE <reference> (
    id UUID PRIMARY KEY DEFAULT uuidv7(),
    value <data_type> UNIQUE NOT NULL
);

```

## 3. Create Simple Attribute

```sql

-- EBNF


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

## 4. Create Attribute with Reference

```sql

-- EBNF


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

## 5. Create Struct of Attributes
Use a Struct of Attributes for **input** attributes that change simultaneously - such as document or message attributes - or for **output** attributes of Activity Stream or other normalized data mart. For large numbers of attributes, the jsonb data type is recommended.

```sql

-- EBNF


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

## 6. Create Relationship

```sql

-- EBNF


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

## 7. Entity and Its Attributes Snapshot Query
The primary key entity_id is preserved.
Structs of Attributes can be used as sources alongside Simple Attributes and Attributes with Reference.

```sql

-- EBNF


-- DSL
SELECT <attributes> FROM ATTRIBUTES OF <entity> VALID AT <valid_at> LAST RECORDED BEFORE <last_recorded_before>;

-- Equivalent PostgreSQL 18 SQL
SELECT 
    <entity>.id,
    <attribute1>.value,
    <attribute2>.value,
    <attribute3>.value
FROM <entity>
LEFT JOIN LATERAL (
    SELECT value 
    FROM <attribute1>
    WHERE <attribute1>.entity_id = <entity>.id
      AND <attribute1>.valid_from <= <valid_at>
      AND <attribute1>.recorded_at <= <last_recorded_before>
    ORDER BY <attribute1>.valid_from DESC, <attribute1>.recorded_at DESC
    LIMIT 1
) <attribute1>_result ON true
LEFT JOIN LATERAL (
    SELECT value 
    FROM <attribute2>
    WHERE <attribute2>.entity_id = <entity>.id
      AND <attribute2>.valid_from <= <valid_at>
      AND <attribute2>.recorded_at <= <last_recorded_before>
    ORDER BY <attribute2>.valid_from DESC, <attribute2>.recorded_at DESC
    LIMIT 1
) <attribute2>_result ON true
LEFT JOIN LATERAL (
    SELECT value 
    FROM <attribute3>
    WHERE <attribute3>.entity_id = <entity>.id
      AND <attribute3>.valid_from <= <valid_at>
      AND <attribute3>.recorded_at <= <last_recorded_before>
    ORDER BY <attribute3>.valid_from DESC, <attribute3>.recorded_at DESC
    LIMIT 1
) <attribute3>_result ON true
ORDER BY <entity>.id;

```

## 8. Relationship Snapshot Query

```sql

-- EBNF


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
ORDER BY <relationship>.id;

```


## 9. Table Normalization Query

```sql

-- EBNF


-- DSL
NORMALIZE
    INTO <entity1> (<attribute_11>, <attribute_12>, <attribute_13>) SELECT col1, col2, col3 FROM <source_table>
    INTO <entity2> (<attribute_21>, <attribute_22>) SELECT col4, col5 FROM <source_table>
    INTO <entity3> (<attribute_31>) SELECT col6 FROM <source_table>
    etc.
RELATIONSHIPS  
    <relationship_1>, -- OF <entity1>, <entity2>
    <relationship_2>, -- OF <entity2>, <entity3>
    etc.
VALID FROM <valid_from> -- Timestamp in <source_table>
FROM <source_table>
WHERE <condition>;


-- Equivalent PostgreSQL 18 SQL

BEGIN;

-- Insert distinct records into entity1
INSERT INTO <entity1> (id, <attribute_11>, <attribute_12>, <attribute_13>, valid_from, recorded_at)
SELECT 
    uuidv7(),
    col1,
    col2,
    col3,
    valid_from,
    NOW()
FROM (
    SELECT DISTINCT col1, col2, col3, valid_from
    FROM <source_table>
    WHERE <condition>
) AS distinct_entity1;

-- Insert distinct records into entity2
INSERT INTO <entity2> (id, <attribute_21>, <attribute_22>, valid_from, recorded_at)
SELECT 
    uuidv7(),
    col4,
    col5,
    valid_from,
    NOW()
FROM (
    SELECT DISTINCT col4, col5, valid_from
    FROM <source_table>
    WHERE <condition>
) AS distinct_entity2;

-- Insert distinct records into entity3
INSERT INTO <entity3> (id, <attribute_31>, valid_from, recorded_at)
SELECT 
    uuidv7(),
    col6,
    valid_from,
    NOW()
FROM (
    SELECT DISTINCT col6, valid_from
    FROM <source_table>
    WHERE <condition>
) AS distinct_entity3;

-- Insert records into relationship_1 by joining source_table with entities
INSERT INTO <relationship_1> (id, <entity1_id>, <entity2_id>, valid_from, recorded_at)
SELECT
    uuidv7(),
    <entity1>.id,
    <entity2>.id,
    <source_table>.valid_from,
    NOW()
FROM <source_table>
JOIN <entity1> ON
    <entity1>.<attribute_11> = <source_table>.col1 AND
    <entity1>.<attribute_12> = <source_table>.col2 AND
    <entity1>.<attribute_13> = <source_table>.col3 AND
    <entity1>.valid_from = <source_table>.valid_from
JOIN <entity2> ON
    <entity2>.<attribute_21> = <source_table>.col4 AND
    <entity2>.<attribute_22> = <source_table>.col5 AND
    <entity2>.valid_from = <source_table>.valid_from
WHERE <condition>;

-- Insert records into relationship_2 by joining source_table with entities
INSERT INTO <relationship_2> (id, <entity2_id>, <entity3_id>, valid_from, recorded_at)
SELECT
    uuidv7(),
    <entity2>.id,
    <entity3>.id,
    <source_table>.valid_from,
    NOW()
FROM <source_table>
JOIN <entity2> ON
    <entity2>.<attribute_21> = <source_table>.col4 AND
    <entity2>.<attribute_22> = <source_table>.col5 AND
    <entity2>.valid_from = <source_table>.valid_from
JOIN <entity3> ON
    <entity3>.<attribute_31> = <source_table>.col6 AND
    <entity3>.valid_from = <source_table>.valid_from
WHERE <condition>;

COMMIT;


```

