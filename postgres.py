from io import FileIO
import textwrap
from sast import STree


class PostgresNameFormatter:
    def obj(self, *vargs):
        return '"' + "__".join([t.strip('"') for t in vargs]) + '"'

    def type(self, t: str):
        return t.lower()

    def col(self, c: str):
        return '"' + c.strip('"') + '"'


class Postgres:
    def __init__(self, sast: STree, fmt: PostgresNameFormatter):
        self.sast = sast
        self.fmt = fmt

    def dump(self, out: FileIO):
        _write_entitites(self.sast, self.fmt, out)
        _write_references(self.sast, self.fmt, out)
        _write_attributes(self.sast, self.fmt, out)
        _write_structs(self.sast, self.fmt, out)
        _write_relationships(self.sast, self.fmt, out)
        _write_attribute_snapshots(self.sast, self.fmt, out)
        _write_relationship_snapshots(self.sast, self.fmt, out)
        _write_table_normalization(self.sast, self.fmt, out)


def _write_entitites(sast: STree, fmt: PostgresNameFormatter, out: FileIO):
    out.write("\n\n-- ####### ENTITIES #######\n")
    for e in sast.reg_entities.values():
        out.write(
            textwrap.dedent(f"""
                    CREATE TABLE {fmt.obj(e.name)} (
                        id UUID PRIMARY KEY DEFAULT uuidv7()
                    );
                  """)
        )


def _write_references(sast: STree, fmt: PostgresNameFormatter, out: FileIO):
    out.write("\n\n-- ####### REFERENCES #######\n")
    for a in sast.reg_references.values():
        out.write(
            textwrap.dedent(f"""
                    CREATE TABLE {fmt.obj(a.name)} (
                        id UUID PRIMARY KEY DEFAULT uuidv7(),
                        value {fmt.type(a.dt)} UNIQUE NOT NULL
                    );
                  """)
        )


def _write_attributes(sast: STree, fmt: PostgresNameFormatter, out: FileIO):
    out.write("\n\n-- ####### ATTRIBUTES #######\n")
    for a in sast.reg_attributes.values():
        ae = a.entity.resolve()

        if a.reference is None:
            # simple attribute
            out.write(
                textwrap.dedent(f"""
                        CREATE TABLE {fmt.obj(ae.name, a.name)} (
                            entity_id UUID NOT NULL REFERENCES {fmt.obj(ae.name)}(id),
                            value {a.dt.lower()} NOT NULL,
                            valid_from TIMESTAMPTZ DEFAULT NOW(),
                            recorded_at TIMESTAMPTZ DEFAULT NOW(),
                            PRIMARY KEY (entity_id, valid_from, recorded_at)
                        );
                    """)
            )
        else:
            # attribute with reference
            r = a.reference.resolve()
            out.write(
                textwrap.dedent(f"""
                        CREATE TABLE {fmt.obj(ae.name, a.name)} (
                            entity_id UUID NOT NULL REFERENCES {fmt.obj(ae.name)}(id),
                            reference_id UUID NOT NULL REFERENCES {fmt.obj(r.name)}(id),
                            valid_from TIMESTAMPTZ DEFAULT NOW(),
                            recorded_at TIMESTAMPTZ DEFAULT NOW(),
                            PRIMARY KEY (entity_id, valid_from, recorded_at)
                        );
                    """)
            )


def _write_structs(sast: STree, fmt: PostgresNameFormatter, out: FileIO):
    out.write("\n\n-- ####### STRUCTS #######\n")
    for s in sast.reg_structs.values():
        e = s.entity.resolve()
        out.write(
            textwrap.dedent(f"""
                        CREATE TABLE {fmt.obj(e.name, s.name)} (
                            entity_id UUID NOT NULL REFERENCES {fmt.obj(e.name)}(id)
                    """)
        )

        for sa in s.attributes:
            if sa.reference is None:
                # simple struct attribute
                out.write(f"    ,{fmt.col(sa.name)} {fmt.type(sa.dt)} NOT NULL\n")
            else:
                # struct attribute with reference
                r = sa.reference.resolve()
                out.write(f"    ,{fmt.col(sa.name)} UUID NOT NULL REFERENCES {fmt.obj(r.name)}(id)\n")

        out.write(")\n")


def _write_relationships(sast: STree, fmt: PostgresNameFormatter, out: FileIO):
    out.write("\n\n-- ####### RELATIONSHIPS #######\n")
    for r in sast.reg_relationships.values():
        out.write(
            textwrap.dedent(f"""
                        CREATE TABLE {fmt.obj(r.name)} (
                            id UUID DEFAULT uuidv7() UNIQUE
                    """)
        )
        for rr in r.erefs:
            rrv = rr.resolve()
            out.write(f"    ,{fmt.col(rrv.name + '_id')} UUID NOT NULL REFERENCES {fmt.obj(rrv.name)}(id)\n")
        out.write("    ,valid_from TIMESTAMPTZ DEFAULT NOW()\n")
        out.write("    ,recorded_at TIMESTAMPTZ DEFAULT NOW()\n")

        out.write("  ,PRIMARY KEY (\n")
        for rr in r.erefs:
            rrv = rr.resolve()
            out.write(f"    ,{fmt.col(rrv.name + '_id')}\n")
        out.write("    ,valid_from\n")
        out.write("    ,recorded_at\n")
        out.write("  )\n")

        out.write(")\n")

    out.write("\n\n-- ####### ATTRIBUTE SNAPSHOTS #######\n")
    for a in sast.reg_attribute_snapshots.values():
        e = a.entity.resolve()
        # TODO: psqtypes
        out.write(f"\nCREATE OR REPLACE FUNCTION {fmt.obj(a.name)}()\n")
        # TODO: RETURNS TABLE(....)
        out.write(f"AS $$\n")

        out.write(f"  SELECT\n")
        out.write(f"    {fmt.obj(e.name)}.id\n")
        for aa in a.attributes:
            out.write(f"    ,{fmt.obj(aa.name)}.value\n")

        out.write(f"  FROM {fmt.obj(e.name)}\n")
        for aa in a.attributes:
            out.write(f"  LEFT JOIN LATERAL (\n")
            out.write(f"    SELECT value\n")
            out.write(f"    FROM {fmt.obj(aa.name)}\n")
            out.write(f"    WHERE {fmt.obj(aa.name)}.entity_id = {fmt.obj(e.name)}.id\n")
            out.write(f"      AND {fmt.obj(aa.name)}.valid_from <= '{a.valid_at}'\n")
            out.write(f"      AND {fmt.obj(aa.name)}.recorded_at <= '{a.last_recorded_before}'\n")
            out.write(f"      AND NOT EXISTS (\n")
            out.write(f"          SELECT 1\n")
            out.write(f"          FROM {fmt.obj(aa.name)}\n")
            out.write(f"          WHERE {fmt.obj(aa.name)}.entity_id = {fmt.obj(e.name)}.id\n")
            out.write(f"            AND {fmt.obj(aa.name)}.valid_from > {fmt.obj(aa.name)}.valid_from\n")
            out.write(f"            AND {fmt.obj(aa.name)}.valid_from <= '{a.valid_at}'\n")
            out.write(f"            AND {fmt.obj(aa.name)}.recorded_at <= '{a.last_recorded_before}'\n")
            out.write(f"      )\n")
            out.write(f"    ORDER BY {fmt.obj(aa.name)}.valid_from DESC, {aa.name}.recorded_at DESC\n")
            out.write(f"    LIMIT 1\n")
            out.write(f"  ) ON true\n")
        out.write(f"ORDER BY {fmt.obj(e.name)}.id;\n")
        out.write(f"$$ LANGUAGE SQL;\n")


def _write_attribute_snapshots(sast: STree, fmt: PostgresNameFormatter, out: FileIO):
    out.write("\n\n-- ####### ATTRIBUTE SNAPSHOTS #######\n")
    out.write("-- TODO: not implemented\n")


def _write_relationship_snapshots(sast: STree, fmt: PostgresNameFormatter, out: FileIO):
    out.write("\n\n-- ####### RELATIONSHIP SNAPSHOTS #######\n")
    out.write("-- TODO: not implemented\n")


def _write_table_normalization(sast: STree, fmt: PostgresNameFormatter, out: FileIO):
    out.write("\n\n-- ####### TABLE NORMALIZATION #######\n")
    out.write("-- TODO: not implemented\n")
