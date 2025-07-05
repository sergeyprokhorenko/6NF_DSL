# DSL for Bitemporal Sixth Normal Form with UUIDv7

Here is a concise, Excel-friendly and autogeneratable DSL for a bitemporal Sixth Normal Form DWH with UUIDv7 primary keys, along with equivalent PostgreSQL 18 SQL code.

This project is inspired by Anchor Modeling, Data Vault and Activity Schema.

## 1. DSL Syntax


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

### Create Entity

```sql

-- DSL
CREATE ENTITY <entity_name>;

-- Equivalent PostgreSQL 18 SQL
CREATE TABLE <entity_name> (
    id UUID PRIMARY KEY DEFAULT uuidv7()
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
    id UUID PRIMARY KEY DEFAULT uuidv7(),
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

### Create Struct of Attributes
Use a Struct of Attributes for **input** attributes that change simultaneously - such as document or message attributes - or for **output** attributes of Activity Stream data mart. For large numbers of attributes, the jsonb data type is recommended.

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


## ПРОДОЛЖИТЬ ОТСЮДА ВНИЗ


-- Golden Record
GOLDEN Account_Current AS
    Account WITH LATEST (Number, Name);

-- Incremental Load
EVOLVE Account.Name
    FROM staging_accounts
    MATCH ON Account.Number = staging_accounts.number
    SET Name = staging_accounts.name, application_time = staging_accounts.effective_date;
```


## 2. Equivalent PostgreSQL 18 SQL




### Golden Record (current valid record for each anchor)

```sql
CREATE VIEW account_current AS
SELECT
    a.id,
    n.name,
    num.value AS number
FROM account a
LEFT JOIN LATERAL (
    SELECT name
    FROM account_name
    WHERE account_id = a.id
    ORDER BY application_time DESC, system_time DESC
    LIMIT 1
) n ON TRUE
LEFT JOIN LATERAL (
    SELECT numbers.value
    FROM account_number
    JOIN numbers ON account_number.number_id = numbers.id
    WHERE account_number.account_id = a.id
    ORDER BY application_time DESC, system_time DESC
    LIMIT 1
) num ON TRUE;
```


### Incremental Load (EVOLVE)

```sql
WITH staged AS (
    SELECT
        s.number,
        s.name,
        s.effective_date
    FROM staging_accounts s
),
matched AS (
    SELECT a.id AS account_id, n.id AS name_id, s.name, s.effective_date
    FROM account a
    JOIN account_number an ON an.account_id = a.id
    JOIN numbers num ON an.number_id = num.id
    LEFT JOIN account_name n ON n.account_id = a.id
    JOIN staged s ON num.value = s.number
    WHERE n.name IS DISTINCT FROM s.name
)
INSERT INTO account_name (id, account_id, name, application_time)
SELECT uuidv7(), account_id, name, effective_date
FROM matched;
```


- Bitemporal attributes use only application_time (start) and system_time (record creation).

