# Draws the diagram with Graphviz (the "dot" command must be installed).
# Run: python3 generate_diagram.py
def cls(name, stereo=None, attrs=(), methods=(), italic=False, color="#FFFFFF", head="#E8EEF7"):
    t = '<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="4" COLOR="#2B3A55">'
    title = f"<I>{name}</I>" if italic else name
    st = f'<FONT POINT-SIZE="10">«{stereo}»</FONT><BR/>' if stereo else ""
    t += f'<TR><TD BGCOLOR="{head}" ALIGN="CENTER">{st}<B>{title}</B></TD></TR>'
    def sec(rows):
        s = '<TR><TD BGCOLOR="%s" ALIGN="LEFT" BALIGN="LEFT" SIDES="T">' % color
        s += ("<BR/>".join(rows) if rows else " ") + "</TD></TR>"
        return s
    t += sec(list(attrs)) + sec(list(methods)) + "</TABLE>>"
    return t

def esc(s): return s.replace("<","&lt;").replace(">","&gt;")

nodes = {
 "DataProcessor": cls("DataProcessor", attrs=[
     "- modeRegistry: ModeRegistry",
     "- databaseRegistry: DatabaseRegistry",
     "- currentMode: ProcessingMode",
     "- currentDatabase: DatabaseConnection"],
   methods=[
     "+ DataProcessor(modes: ModeRegistry, databases: DatabaseRegistry)",
     "+ configure(mode: ModeIdentifier, database: DatabaseIdentifier): void",
     "+ process(dataPoint: DataPoint): void"], head="#CFE0F5"),
 "ModeRegistry": cls("ModeRegistry", attrs=[esc("- modes: Map<ModeIdentifier, ProcessingMode>")],
   methods=["+ register(id: ModeIdentifier, mode: ProcessingMode): void",
            "+ get(id: ModeIdentifier): ProcessingMode"]),
 "DatabaseRegistry": cls("DatabaseRegistry", attrs=[esc("- databases: Map<DatabaseIdentifier, DatabaseConnection>")],
   methods=["+ register(id: DatabaseIdentifier, db: DatabaseConnection): void",
            "+ get(id: DatabaseIdentifier): DatabaseConnection"]),
 "ProcessingMode": cls("ProcessingMode", "interface", italic=True,
   methods=["<I>+ process(dataPoint: DataPoint,</I>", "<I>        database: DatabaseConnection): void</I>"], head="#FCEBD2"),
 "DumpMode": cls("DumpMode", methods=["+ process(dataPoint: DataPoint,", "        database: DatabaseConnection): void"], head="#FEF5E7"),
 "PassthroughMode": cls("PassthroughMode", methods=["+ process(dataPoint: DataPoint,", "        database: DatabaseConnection): void"], head="#FEF5E7"),
 "ValidateMode": cls("ValidateMode", methods=["+ process(dataPoint: DataPoint,", "        database: DatabaseConnection): void"], head="#FEF5E7"),
 "DatabaseConnection": cls("DatabaseConnection", "interface", italic=True, methods=[
     "<I>+ connect(): void</I>", "<I>+ disconnect(): void</I>",
     "<I>+ insert(dataPoint: DataPoint): void</I>",
     "<I>+ validate(dataPoint: DataPoint): boolean</I>"], head="#DDF0DF"),
}
for db in ["PostgresDatabase","RedisDatabase","ElasticDatabase"]:
    nodes[db] = cls(db, methods=["+ connect(): void","+ disconnect(): void",
        "+ insert(dataPoint: DataPoint): void","+ validate(dataPoint: DataPoint): boolean"], head="#EEF8EF")
nodes["ModeIdentifier"] = cls("ModeIdentifier","enumeration", attrs=["DUMP","PASSTHROUGH","VALIDATE"], head="#EDEDED")
nodes["DatabaseIdentifier"] = cls("DatabaseIdentifier","enumeration", attrs=["POSTGRES","REDIS","ELASTIC"], head="#EDEDED")
nodes["DataPoint"] = cls("DataPoint", attrs=["(existing class)"], head="#EDEDED")

notes = {
 "nConfigure": "configure(mode, database):\\l  newDb = databaseRegistry.get(database)\\l  if newDb != currentDatabase:\\l    currentDatabase.disconnect()\\l    newDb.connect()\\l  currentMode = modeRegistry.get(mode)\\l  currentDatabase = newDb\\l\\lprocess(dataPoint):\\l  currentMode.process(dataPoint, currentDatabase)\\l",
 "nModes": "DumpMode: does nothing (drops data)\\lPassthroughMode: database.insert(dataPoint)\\lValidateMode: if database.validate(dataPoint)\\l                then database.insert(dataPoint)\\l",
}

out = ['digraph UML {',
 'graph [rankdir=TB, fontname="Helvetica", nodesep=0.45, ranksep=0.75, pad=0.3, splines=spline,',
 '       label=<<B>Walmart Data Processing Pipeline: Reconfigurable Data Processor</B><BR/><FONT POINT-SIZE="11">UML Class Diagram  |  Strategy pattern for modes and databases, registries for extension, constructor injection</FONT>>, labelloc=t, fontsize=18];',
 'node [shape=plaintext, fontname="Helvetica", fontsize=10];',
 'edge [fontname="Helvetica", fontsize=9, color="#2B3A55"];']
for k,v in nodes.items(): out.append(f'{k} [label={v}];')
for k,v in notes.items():
    out.append(f'{k} [shape=note, style=filled, fillcolor="#FFFBE0", color="#B8A64A", fontname="Courier", fontsize=9, label="{v}"];')

# ranks
out.append('{rank=same; ModeRegistry; DataProcessor; DatabaseRegistry;}')
out.append('{rank=same; ProcessingMode; DatabaseConnection; nConfigure; DataPoint;}')
out.append('ProcessingMode [ordering=out];')
out.append('{rank=same; nModes; DumpMode; PassthroughMode; ValidateMode; PostgresDatabase; RedisDatabase; ElasticDatabase;}')
out.append('{rank=same; ModeIdentifier; DatabaseIdentifier;}')

E = []
E.append('ProcessingMode -> nModes [style=dotted, arrowhead=none, color="#B8A64A"]')
# associations: processor uses registries (aggregation, injected)
E.append('DataProcessor -> ModeRegistry [arrowhead=vee, arrowtail=odiamond, dir=both, headlabel="1", taillabel="1"]')
E.append('DataProcessor -> DatabaseRegistry [arrowhead=vee, arrowtail=odiamond, dir=both, headlabel="1", taillabel="1"]')
# current strategies
E.append('DataProcessor -> ProcessingMode [arrowhead=vee, label="currentMode", headlabel="1"]')
E.append('DataProcessor -> DatabaseConnection [arrowhead=vee, label="currentDatabase", headlabel="1"]')
# registries hold many
E.append('ModeRegistry -> ProcessingMode [arrowhead=vee, arrowtail=odiamond, dir=both, headlabel="1..*", taillabel="1"]')
E.append('DatabaseRegistry -> DatabaseConnection [arrowhead=vee, arrowtail=odiamond, dir=both, headlabel="1..*", taillabel="1"]')
# realizations
for m in ["DumpMode","PassthroughMode","ValidateMode"]:
    E.append(f'ProcessingMode -> {m} [style=dashed, dir=back, arrowtail=empty, arrowhead=none]')
for d in ["PostgresDatabase","RedisDatabase","ElasticDatabase"]:
    E.append(f'DatabaseConnection -> {d} [style=dashed, dir=back, arrowtail=empty, arrowhead=none]')
# mode uses DB
E.append('ProcessingMode -> DatabaseConnection [style=dashed, arrowhead=vee, label="«uses»"]')
# dependencies to enums / DataPoint
E.append('ModeRegistry -> ModeIdentifier [style=dashed, arrowhead=vee, label="«keyed by»"]')
E.append('DatabaseRegistry -> DatabaseIdentifier [style=dashed, arrowhead=vee, label="«keyed by»"]')
E.append('DataProcessor -> DataPoint [style=dashed, arrowhead=vee, label="«uses»"]')
# notes
E.append('DataProcessor -> nConfigure [style=dotted, arrowhead=none, color="#B8A64A"]')

out += E + ['}']
open("uml.dot","w").write("\n".join(out))

import subprocess
subprocess.run(["dot", "-Tpng", "-Gdpi=110", "uml.dot", "-o", "class_diagram.png"], check=True)
