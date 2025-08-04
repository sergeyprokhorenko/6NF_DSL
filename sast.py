from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List, Tuple


@dataclass
class Named(ABC):
    name: str


class NamedPromise(Named):
    def __init__(self, stree: "STree", name: str):
        self._stree = stree
        self.name = name

    @abstractmethod
    def resolve(self):
        pass

    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name})"

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.name == other.name

    def __ne__(self, other):
        return not self.__eq__(other)

    def _raise_verr(self, msg):
        raise ValueError(msg)


class ReferencePromise(NamedPromise):
    def resolve(self) -> "Reference":
        return self._stree.reg_references.get(self.name) or self._raise_verr(
            f"unable to find reference [{self.name}] in registry"
        )


class EntityPromise(NamedPromise):
    def resolve(self) -> "Entity":
        return self._stree.reg_entities.get(self.name) or self._raise_verr(
            f"unable to find entity [{self.name}] in registry"
        )


class AttributePromise(NamedPromise):
    def resolve(self) -> "Attribute":
        return self._stree.reg_attributes.get(self.name) or self._raise_verr(
            f"unable to find attribute [{self.name}] in registry"
        )


class EntityOrReferencePromise(NamedPromise):
    def resolve(self) -> "Entity|Reference":
        return (
            self._stree.reg_entities.get(self.name)
            or self._stree.reg_references.get(self.name)
            or self._raise_verr(f"unable to find reference or entity [{self.name}] in registry")
        )


class RelationshipPromise(NamedPromise):
    def resolve(self) -> "Relationship":
        return self._stree.reg_relationships.get(self.name) or self._raise_verr(
            f"unable to find relationship [{self.name}] in registry"
        )


@dataclass
class Entity(Named):
    pass


@dataclass
class Reference(Named):
    dt: str


@dataclass
class StructAttribute(Named):
    dt: str | None
    reference: ReferencePromise | None


@dataclass
class Struct(Named):
    entity: EntityPromise
    attributes: List[StructAttribute]


@dataclass
class Attribute(Named):
    entity: EntityPromise

    dt: str | None
    reference: ReferencePromise | None


@dataclass
class Relationship(Named):
    erefs: List[EntityOrReferencePromise]


@dataclass
class AttributesSnapshot(Named):
    # TODO(name): poor DSL?
    attributes: List[AttributePromise]
    entity: EntityPromise
    valid_at: str
    last_recorded_before: str


@dataclass
class RelationshipSnapshot(Named):
    erefs: List[EntityOrReferencePromise]
    relationship: RelationshipPromise
    valid_at: str
    last_recorded_before: str


@dataclass
class TableNormalizationInto(Named):
    entity: EntityPromise
    attributes: List[AttributePromise]
    cols: List[str]
    source_table: str


@dataclass
class CriteriaOperator(ABC):
    pass


@dataclass
class OperandProperty(CriteriaOperator):
    name: str

    def __repr__(self):
        return f"{self.name}"


@dataclass
class OperandValue(CriteriaOperator):
    value: str

    def __repr__(self):
        return f"{self.value}"


class BinaryOperatorType(Enum):
    EQ = auto()
    NOT_EQ = auto()
    LESS_OR_EQUAL = auto()
    GREATER_OR_EQUAL = auto()
    LESS = auto()
    GREATER = auto()


class GroupOperatorType(Enum):
    AND = auto()
    OR = auto()


@dataclass
class GroupOperator(CriteriaOperator):
    op: GroupOperatorType
    ol: List[CriteriaOperator]

    def __repr__(self):
        return f" {repr(self.op.name)} ".join([repr(oli) for oli in self.ol])


@dataclass
class BinaryOperator(CriteriaOperator):
    l: CriteriaOperator
    op: BinaryOperatorType
    r: CriteriaOperator

    def __repr__(self):
        return f"{repr(self.l)} {repr(self.op.name)} {repr(self.r)}"


@dataclass
class InOperator(CriteriaOperator):
    l: OperandProperty
    v: List[OperandValue]

    def __repr__(self):
        return f"{repr(self.l)} IN ({', '.join(repr(vi) for vi in self.v)})"


@dataclass
class TableNormalization(Named):
    intos: List[TableNormalizationInto]
    relationships: List[RelationshipPromise]
    valid_from: str
    source_table: str
    condition: CriteriaOperator | None


class STree:
    def __init__(self):
        self.reg_entities: Dict[str, Entity] = dict()
        self.reg_references: Dict[str, Reference] = dict()
        self.reg_attributes: Dict[Tuple[str, str], Attribute] = dict()
        self.reg_structs: Dict[Tuple[str, str], Struct] = dict()
        self.reg_relationships: Dict[str, Relationship] = dict()
        self.reg_attribute_snapshots: Dict[str, AttributesSnapshot] = dict()
        self.reg_relationship_snapshots: Dict[str, RelationshipSnapshot] = dict()
        self.reg_table_normalization: Dict[str, TableNormalization] = dict()

    def add_table_normalization(self, rs: TableNormalization):
        exists = self.reg_table_normalization.get(rs.name)
        if not exists:
            self.reg_table_normalization[rs.name] = rs
            return

        if exists != rs:
            raise ValueError(f"TableNormalization {exists.name} with other property values already registered")

    def add_relationship_snapshot(self, rs: RelationshipSnapshot):
        exists = self.reg_relationship_snapshots.get(rs.name)
        if not exists:
            self.reg_relationship_snapshots[rs.name] = rs
            return

        if exists != rs:
            raise ValueError(f"RelationshipSnapshot {exists.name} with other property values already registered")

    def add_relationship(self, r: Relationship):
        exists = self.reg_relationships.get(r.name)
        if not exists:
            self.reg_relationships[r.name] = r
            return

        if exists != r:
            raise ValueError(f"Relationship {exists.name} with other property values already registered")

    def add_attribute_snapshot(self, r: Relationship):
        exists = self.reg_attribute_snapshots.get(r.name)
        if not exists:
            self.reg_attribute_snapshots[r.name] = r
            return

        if exists != r:
            raise ValueError(f"AttributeShapshot {exists.name} with other property values already registered")

    def add_struct(self, s: Struct):
        sk = ((s.entity.name), (s.name))
        exists = self.reg_structs.get(sk)
        if not exists:
            self.reg_structs[sk] = s
            return

        if exists != s:
            raise ValueError(
                f"Struct {exists.name} on entity {exists.entity} with other property values already registered"
            )

    def add_attribute(self, a: Attribute):
        ak = ((a.entity.name), (a.name))
        exists = self.reg_attributes.get(ak)
        if not exists:
            self.reg_attributes[ak] = a
            return

        if exists != a:
            raise ValueError(
                f"Attribute {exists.name} on entity {exists.entity} with other property values already registered"
            )

    def add_entities(self, el: List[Entity]):
        for e in el:
            if e.name in self.reg_entities:
                raise ValueError(f"Entity {e.name} already registered")
            self.reg_entities[e.name] = e

    def add_reference(self, r: Reference):
        exists = self.reg_references.get(r.name)
        if not exists:
            self.reg_references[r.name] = r
            return

        if exists != r:
            raise ValueError(f"Reference {exists.name} with other property values already registered")

    def __repr__(self):
        rv: List[str] = []
        rv.append("Entities:")
        rv.append("\n".join(["  " + repr(e) for e in self.reg_entities.values()]))

        rv.append("References:")
        rv.append("\n".join(["  " + repr(r) for r in self.reg_references.values()]))

        rv.append("Attributes:")
        rv.append("\n".join(["  " + repr(a) for a in self.reg_attributes.values()]))

        rv.append("Structs:")
        rv.append("\n".join(["  " + repr(s) for s in self.reg_structs.values()]))

        rv.append("Relationships:")
        rv.append("\n".join(["  " + repr(s) for s in self.reg_relationships.values()]))

        rv.append("AttributeSnapshots:")
        rv.append("\n".join(["  " + repr(s) for s in self.reg_attribute_snapshots.values()]))

        rv.append("RelationshipSnapshots:")
        rv.append("\n".join(["  " + repr(s) for s in self.reg_relationship_snapshots.values()]))

        rv.append("TableNormalization:")
        rv.append("\n".join(["  " + repr(s) for s in self.reg_table_normalization.values()]))

        return "\n".join(rv)
