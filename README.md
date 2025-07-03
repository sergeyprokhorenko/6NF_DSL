# DSL for Bitemporal Anchor Modeling with UUIDv7

Here is a concise, Excel-friendly DSL for a bitemporal Anchor Model DWH with UUIDv7 primary keys, along with equivalent PostgreSQL 18 SQL code and detailed keyword explanations.

## 1. DSL Syntax (Excel-friendly, concise)

### DSL Keywords

| Keyword | Meaning |
| :-- | :-- |
| ANCHOR | Defines an anchor entity (table with UUIDv7 PK) |
| KNOT | Defines a knot (finite value set, immutable, UUIDv7 PK) |
| ATTRIBUTE | Defines an attribute (historized, optionally knotted, bitemporal, UUIDv7 PK) |
| TIE | Defines a tie (relationship, optionally knotted, bitemporal, UUIDv7 PK) |
| TEMPORAL | Marks an attribute/tie as bitemporal (application and system time) |
| GOLDEN | Creates a "golden record" view (current valid record for each anchor) |
| SNAPSHOT | Query as-of a specific point in time (bitemporal snapshot) |
| EVOLVE | Incremental ETL/ELT operation, with change detection |
| NORMALIZE | Flatten anchor/attribute structure for reporting |
| DENORMALIZE | Denormalized view/table for performance |

### Create Knot

```sql

-- DSL
CREATE KNOT <knot_name> TYPE <data_type>;

-- Equivalent PostgreSQL 18 SQL
CREATE TABLE <knot_name> (
    id UUID PRIMARY KEY DEFAULT uuidv7(),
    value <data_type> UNIQUE NOT NULL
);

```

### Create Anchor

```sql

-- DSL
CREATE ANCHOR <anchor_name>;

-- Equivalent PostgreSQL 18 SQL
CREATE TABLE <anchor_name> (
    id UUID PRIMARY KEY DEFAULT uuidv7()
);

```

### Create Plain Attribute

```sql

-- DSL
CREATE ATTRIBUTE <attribute_name> ANCHOR <anchor_name> TYPE <data_type>;

-- Equivalent PostgreSQL 18 SQL
CREATE TABLE <attribute_name> (
    id UUID PRIMARY KEY DEFAULT uuidv7(),
    anchor_id UUID NOT NULL REFERENCES <anchor_name>(id),
    value <data_type> UNIQUE NOT NULL,
    application_time TIMESTAMPTZ NOT NULL,
    system_time TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (anchor_id, application_time, system_time)
);

```

### Create Knotted Attribute

```sql

-- DSL
CREATE ATTRIBUTE <attribute_name> ANCHOR <anchor_name> KNOT <knot_name>;

-- Equivalent PostgreSQL 18 SQL
CREATE TABLE <attribute_name> (
    id UUID PRIMARY KEY DEFAULT uuidv7(),
    anchor_id UUID NOT NULL REFERENCES <anchor_name>(id),
    knot_id UUID NOT NULL REFERENCES <knot_name>(id),
    application_time TIMESTAMPTZ NOT NULL,
    system_time TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (anchor_id, application_time, system_time)
);

```

### Create Tie

```sql

-- DSL
CREATE TIE <tie_name> OF
	    anchor_or_knot_1_id, 
	    anchor_or_knot_2_id,
	    -- etc.
	    anchor_or_knot_n_id;

-- Equivalent PostgreSQL 18 SQL
CREATE TABLE <tie_name> (
    id UUID PRIMARY KEY DEFAULT uuidv7(),
    anchor_or_knot_1_id UUID NOT NULL REFERENCES <anchor_or_knot_1_name>(id),
    anchor_or_knot_2_id UUID NOT NULL REFERENCES <anchor_or_knot_2_name>(id),
    -- etc.
    anchor_or_knot_n_id UUID NOT NULL REFERENCES <anchor_or_knot_n_name>(id),
    application_time TIMESTAMPTZ NOT NULL,
    system_time TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (
        anchor_or_knot_1_id, 
        anchor_or_knot_2_id,
        -- etc.
        anchor_or_knot_n_id,
        application_time,
        system_time
    )
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


## 3. Excel Metadata Structure

### Entities Sheet

| entity_type | entity_name | attribute_name | data_type | is_knotted | is_temporal |
| :-- | :-- | :-- | :-- | :-- | :-- |
| KNOT | Numbers | value | TEXT |  |  |
| KNOT | Types | value | TEXT |  |  |
| ANCHOR | Account |  |  |  |  |
| ANCHOR | Document |  |  |  |  |
| ATTRIBUTE | Account | Number |  | TRUE | TRUE |
| ATTRIBUTE | Account | Name | TEXT | FALSE | TRUE |

### Ties Sheet

| tie_name | anchor1 | anchor2 | knot | is_temporal |
| :-- | :-- | :-- | :-- | :-- |
| AccountDocumentType | Account | Document | Types | TRUE |

### ETL Sheet

| target_attribute | source_table | match_on | set_fields |
| :-- | :-- | :-- | :-- |
| Account.Name | staging_accounts | Account.Number | Name, application_time |

## 4. Keyword List with Comments

| Keyword | Description |
| :-- | :-- |
| ANCHOR | Defines an entity with UUIDv7 PK and created_at |
| KNOT | Defines a finite, immutable value set with UUIDv7 PK |
| ATTRIBUTE | Defines a property, can be knotted (references KNOT) and/or temporal (bitemporal) |
| TIE | Defines a relationship (n-ary, knotted, temporal) |
| TEMPORAL | Marks attribute or tie as bitemporal (application_time, system_time) |
| GOLDEN | Creates a "golden record" view (latest valid record for anchor) |
| EVOLVE | Incremental ETL/ELT operation, detects changes and inserts new versions |
| NORMALIZE | Creates a flattened view for reporting |
| DENORMALIZE | Creates a denormalized table/view for performance |

## 5. Usage Example

**DSL:**

```sql
ANCHOR Account;
ATTRIBUTE Account.Name TEXT TEMPORAL;
KNOT Numbers (value TEXT);
ATTRIBUTE Account.Number KNOT Numbers TEMPORAL;
GOLDEN Account_Current AS Account WITH LATEST (Number, Name);
```

**PostgreSQL 18:**

```sql
CREATE TABLE account (
    id UUID PRIMARY KEY DEFAULT uuidv7(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE account_name (
    id UUID PRIMARY KEY DEFAULT uuidv7(),
    account_id UUID NOT NULL REFERENCES account(id),
    name TEXT NOT NULL,
    application_time TIMESTAMPTZ NOT NULL,
    system_time TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE numbers (
    id UUID PRIMARY KEY DEFAULT uuidv7(),
    value TEXT UNIQUE NOT NULL
);

CREATE TABLE account_number (
    id UUID PRIMARY KEY DEFAULT uuidv7(),
    account_id UUID NOT NULL REFERENCES account(id),
    number_id UUID NOT NULL REFERENCES numbers(id),
    application_time TIMESTAMPTZ NOT NULL,
    system_time TIMESTAMPTZ DEFAULT NOW()
);

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

**This approach ensures:**

- All PKs are UUIDv7.
- Bitemporal attributes use only application_time (start) and system_time (record creation).
- Only standard PostgreSQL 18 features are used.
- The DSL is concise, Excel-friendly, and autogeneratable.
- The model is fully compatible with Anchor Modeling best practices, but critically adapted for PostgreSQL 18 and UUIDv7.


