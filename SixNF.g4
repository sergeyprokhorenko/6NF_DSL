grammar SixNF;

parse
    : expr* EOF
    ;
    

expr
    : create_entities
    | create_reference
    | create_attribute
    | create_struct
    | create_relationship
    | select_attributes
    | select_relationship
    | select_relationship_snapshot
    | normalize
    ;


create_entities
    : K_CREATE K_ENTITIES identifier_list ';'
    ;

data_type
    : K_DT_UUID
    | K_DT_INT
    | K_DT_TIMESTAMPTZ
    | K_DT_TEXT
    | K_DT_NUMERIC ('(' INT_NUMBER ',' INT_NUMBER ')')?
    | K_DT_DATE
    ;
    
create_reference
    : K_CREATE K_REFERENCE name=identifier dt=data_type ';'
    ;

create_attribute
    : create_attribute_simple
    | create_attribute_ref
    ;

create_attribute_simple
    : K_ENTITY entity=identifier K_HAS K_ATTRIBUTE name=identifier dt=data_type ';'
    ;

create_attribute_ref
    : K_ENTITY entity=identifier K_HAS K_ATTRIBUTE name=identifier K_REFERENCE ref=identifier ';'
    ;

create_struct
    : K_CREATE K_STRUCT name=identifier K_FOR K_ENTITY entity=identifier '(' struct_item_list ')' ';'
    ;

struct_item_list
    : struct_item (',' struct_item)* ','?
    ;

struct_item
    : struct_item_simple
    | struct_item_ref
    ;

struct_item_simple
    : name=identifier dt=data_type 
    ;

struct_item_ref:
    | name=identifier K_REFERENCE ref=identifier
    ;

create_relationship
    : K_CREATE K_RELATIONSHIP name=identifier K_OF identifier_list ';'
    ;

select_relationship
    : K_SELECT selection K_FROM identifier K_VALID K_AT timestamp K_LAST K_RECORDED K_BEFORE timestamp ';'
    ;

select_relationship_snapshot
    : K_SELECT selection K_FROM K_RELATIONSHIP rname=identifier K_VALID K_AT valid_at=timestamp K_LAST K_RECORDED K_BEFORE last_recorded_before=timestamp ';'
    ;

normalize
    : K_NORMALIZE into_clauses K_RELATIONSHIPS identifier_list K_VALID K_FROM valid_from=identifier K_FROM source_table=identifier (K_WHERE condition=where_clause)? ';'
    ;

where_clause
    : '(' where_clause ')'
    | where_clause K_AND where_clause
    | where_clause K_OR where_clause
    | where_clause_binary
    | where_clause_in
    ;

where_clause_binary
    : identifier where_binary_query_operator where_operand_value
    ;

where_binary_query_operator
    : K_OP_EQ
    | K_OP_NOT_EQ 
    | K_OP_NOT_EQ_v2
    | K_OP_LESS_OR_EQUAL
    | K_OP_GREATER_OR_EQUAL
    | K_OP_LESS
    | K_OP_GREATER
    ;

where_clause_in
    : identifier where_in_query_operator '(' where_operand_value (',' where_operand_value)* ','? ')'
    ;

where_in_query_operator
    : K_IN
    | K_NOT K_IN
    ;

where_operand_value
    : INT_NUMBER
    | FLOAT_NUMBER
    | TIMESTAMP
    | QSTRING
    ;

into_clauses
    : into_clause+
    ;

into_clause
    : K_INTO entity=identifier '(' alist=identifier_list ')' K_SELECT clist=identifier_list K_FROM source_table=identifier
    ;

identifier
    : IDENTIFIER
    ;

identifier_list
    : identifier (',' identifier)* ','?
    ;

select_attributes
    : K_SELECT selection K_FROM K_ATTRIBUTES K_OF entity=identifier K_VALID K_AT valid_at=timestamp K_LAST K_RECORDED K_BEFORE last_recorded_before=timestamp ';'
    ;

selection
    : '*'
    | identifier_list
    ;

timestamp
    : TIMESTAMP
    ;

// ****************************************************************
K_CREATE : C R E A T E;
K_ENTITY: E N T I T Y;
K_ENTITIES: E N T I T I E S;
K_REFERENCE: R E F E R E N C E;
K_HAS: H A S;
K_ATTRIBUTE: A T T R I B U T E;
K_STRUCT: S T R U C T;
K_FOR: F O R;
K_OF: O F;
K_SELECT: S E L E C T;
K_FROM: F R O M;
K_VALID: V A L I D;
K_AT: A T;
K_ATTRIBUTES: A T T R I B U T E S;
K_LAST: L A S T;
K_RECORDED: R E C O R D E D;
K_BEFORE: B E F O R E;
K_NORMALIZE: N O R M A L I Z E;
K_RELATIONSHIP: R E L A T I O N S H I P;
K_RELATIONSHIPS: R E L A T I O N S H I P S;
K_INTO: I N T O;
K_WHERE: W H E R E;
K_AND: A N D;
K_OR: O R;
K_IN: I N;
K_NOT: N O T;

K_DT_UUID: U U I D;
K_DT_INT: I N T;
K_DT_TIMESTAMPTZ: T I M E S T A M P T Z;
K_DT_TEXT: T E X T;
K_DT_NUMERIC: N U M E R I C;
K_DT_DATE: D A T E;

K_OP_EQ : '=';
K_OP_NOT_EQ : '!=';
K_OP_NOT_EQ_v2 : '<>';
K_OP_LESS: '<';
K_OP_LESS_OR_EQUAL: '<=';
K_OP_GREATER: '>';
K_OP_GREATER_OR_EQUAL: '>=';

IDENTIFIER
    : [a-zA-Z0-9_.]+
    | '"' (~'"')+ '"'
    ;

COMMENT
    : ('--' .*? '\n') -> skip
    ;

WS
    : (' ' | '\t' | '\n' | '\r') -> skip
;

//FIXME: fix timestamp format
TIMESTAMP
    : '\'' [0-9]+ '-' [0-9]+ '-' [0-9]+ '\''
    ;

QSTRING
    : '\'' (~'\'' | '\'\'')* '\''
    ;

INT_NUMBER
    : ( '+' | '-' )? [0-9]+
    ;

FLOAT_NUMBER
    : ( '+' | '-' )? [0-9]+ '.' [0-9]+
    ;

fragment A : [aA];
fragment B : [bB];
fragment C : [cC];
fragment D : [dD];
fragment E : [eE];
fragment F : [fF];
fragment G : [gG];
fragment H : [hH];
fragment I : [iI];
fragment J : [jJ];
fragment K : [kK];
fragment L : [lL];
fragment M : [mM];
fragment N : [nN];
fragment O : [oO];
fragment P : [pP];
fragment Q : [qQ];
fragment R : [rR];
fragment S : [sS];
fragment T : [tT];
fragment U : [uU];
fragment V : [vV];
fragment W : [wW];
fragment X : [xX];
fragment Y : [yY];
fragment Z : [zZ];
