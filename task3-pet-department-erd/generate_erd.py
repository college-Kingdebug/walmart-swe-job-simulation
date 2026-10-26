# Draws the diagram with Graphviz (the "dot" command must be installed).
# Run: python3 generate_erd.py
def table(name, cols, head="#CFE0F5"):
    t = '<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3" COLOR="#2B3A55">'
    t += f'<TR><TD COLSPAN="3" BGCOLOR="{head}"><B>{name}</B></TD></TR>'
    for key, col, typ in cols:
        k = f'<B>{key}</B>' if key else ' '
        c = f'<U>{col}</U>' if 'PK' in key else col
        t += (f'<TR><TD ALIGN="LEFT" BGCOLOR="white"><FONT POINT-SIZE="8" COLOR="#7A4B00">{k}</FONT></TD>'
              f'<TD ALIGN="LEFT" BGCOLOR="white" PORT="{col}">{c}</TD>'
              f'<TD ALIGN="LEFT" BGCOLOR="white"><FONT COLOR="#555555">{typ}</FONT></TD></TR>')
    return t + '</TABLE>>'

core, sub, sales, ship, link = "#CFE0F5", "#FCEBD2", "#DDF0DF", "#EADCF5", "#EDEDED"
T = {
 "manufacturer": table("manufacturer", [("PK","manufacturer_id","INT"),("","name","VARCHAR(100)")], core),
 "animal": table("animal", [("PK","animal_id","INT"),("","name","VARCHAR(50)")], core),
 "product": table("product", [("PK","product_id","INT"),("","name","VARCHAR(150)"),
     ("FK","manufacturer_id","INT"),("","product_type","ENUM('FOOD','TOY','APPAREL')")], core),
 "product_animal": table("product_animal", [("PK, FK","product_id","INT"),("PK, FK","animal_id","INT")], link),
 "pet_food": table("pet_food", [("PK, FK","product_id","INT"),("","weight","DECIMAL(8,2)"),
     ("","flavor","VARCHAR(50)"),("","target_health_condition","VARCHAR(100)")], sub),
 "pet_toy": table("pet_toy", [("PK, FK","product_id","INT"),("","material","VARCHAR(50)"),("","durability","VARCHAR(50)")], sub),
 "pet_apparel": table("pet_apparel", [("PK, FK","product_id","INT"),("","color","VARCHAR(30)"),
     ("","size","VARCHAR(10)"),("","care_instructions","TEXT")], sub),
 "customer": table("customer", [("PK","customer_id","INT"),("","name","VARCHAR(100)"),("UQ","email","VARCHAR(255)")], sales),
 "customer_transaction": table("customer_transaction", [("PK","transaction_id","INT"),("FK","customer_id","INT"),("","transaction_date","DATE")], sales),
 "transaction_item": table("transaction_item", [("PK, FK","transaction_id","INT"),("PK, FK","product_id","INT"),("","quantity","INT")], sales),
 "location": table("location", [("PK","location_id","INT"),("","name","VARCHAR(100)"),("","zip_code","VARCHAR(10)")], ship),
 "shipment": table("shipment", [("PK","shipment_id","INT"),("FK","origin_location_id","INT"),("FK","destination_location_id","INT")], ship),
 "shipment_item": table("shipment_item", [("PK, FK","shipment_id","INT"),("PK, FK","product_id","INT"),("","quantity","INT")], ship),
}
ONE, ZMANY, OMANY, ZONE = "teetee", "crowodot", "crowtee", "teeodot"
def rel(parent, pport, child, cport, parent_end, child_end, label=""):
    lab = f', label="{label}"' if label else ""
    return f'{parent} -> {child} [dir=both, arrowtail={parent_end}, arrowhead={child_end}{lab}];'

R = [
 rel("manufacturer","manufacturer_id","product","manufacturer_id", ONE, ZMANY, "makes"),
 rel("product","product_id","product_animal","product_id", ONE, OMANY, "for"),
 rel("animal","animal_id","product_animal","animal_id", ONE, ZMANY),
 rel("product","product_id","pet_food","product_id", ONE, ZONE, "is a"),
 rel("product","product_id","pet_toy","product_id", ONE, ZONE, "is a"),
 rel("product","product_id","pet_apparel","product_id", ONE, ZONE, "is a"),
 rel("customer","customer_id","customer_transaction","customer_id", ONE, ZMANY, "makes"),
 rel("customer_transaction","transaction_id","transaction_item","transaction_id", ONE, OMANY, "contains"),
 rel("product","product_id","transaction_item","product_id", ONE, ZMANY),
 rel("location","location_id","shipment","origin_location_id", ONE, ZMANY, "origin"),
 rel("location","location_id","shipment","destination_location_id", ONE, ZMANY, "destination"),
 rel("shipment","shipment_id","shipment_item","shipment_id", ONE, OMANY, "contains"),
 rel("product","product_id","shipment_item","product_id", ONE, ZMANY),
]
legend = ('<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3" COLOR="#999999">'
 '<TR><TD COLSPAN="2" BGCOLOR="#F4F4F4"><B>Legend (crow\'s foot)</B></TD></TR>'
 '<TR><TD ALIGN="LEFT">-||</TD><TD ALIGN="LEFT">exactly one</TD></TR>'
 '<TR><TD ALIGN="LEFT">-o|</TD><TD ALIGN="LEFT">zero or one</TD></TR>'
 '<TR><TD ALIGN="LEFT">-|&lt;</TD><TD ALIGN="LEFT">one or many</TD></TR>'
 '<TR><TD ALIGN="LEFT">-o&lt;</TD><TD ALIGN="LEFT">zero or many</TD></TR>'
 '<TR><TD ALIGN="LEFT"><B>PK / FK / UQ</B></TD><TD ALIGN="LEFT">primary / foreign / unique key</TD></TR>'
 '<TR><TD ALIGN="LEFT" BGCOLOR="#CFE0F5">   </TD><TD ALIGN="LEFT">product catalog</TD></TR>'
 '<TR><TD ALIGN="LEFT" BGCOLOR="#FCEBD2">   </TD><TD ALIGN="LEFT">product subtypes</TD></TR>'
 '<TR><TD ALIGN="LEFT" BGCOLOR="#DDF0DF">   </TD><TD ALIGN="LEFT">customers and sales</TD></TR>'
 '<TR><TD ALIGN="LEFT" BGCOLOR="#EADCF5">   </TD><TD ALIGN="LEFT">locations and shipments</TD></TR>'
 '<TR><TD ALIGN="LEFT" BGCOLOR="#EDEDED">   </TD><TD ALIGN="LEFT">junction table</TD></TR></TABLE>>')
out = ['digraph ERD {',
 'graph [rankdir=LR, fontname="Helvetica", nodesep=0.4, ranksep=1.3, pad=0.3, splines=spline, labelloc=t, fontsize=18,',
 ' label=<<B>Walmart Pet Department: Centralized Database ERD</B><BR/><FONT POINT-SIZE="11">Normalized to 3NF  |  Crow\'s foot notation</FONT>>];',
 'node [shape=plaintext, fontname="Helvetica", fontsize=10];',
 'edge [fontname="Helvetica", fontsize=8, color="#2B3A55", arrowsize=0.9];']
for k,v in T.items(): out.append(f'{k} [label={v}];')
out.append(f'legend [label={legend}];')
out += R
out.append('{rank=same; manufacturer; animal; customer; location; legend;}')
out.append('{rank=same; product; customer_transaction; shipment;}')
out.append('}')
open("erd.dot","w").write("\n".join(out))

import subprocess
subprocess.run(["dot", "-Tpng", "-Gdpi=110", "erd.dot", "-o", "erd.png"], check=True)
