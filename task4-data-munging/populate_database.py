"""
Populate shipment_database.db from the shipping spreadsheets.

Spreadsheet 0: one row per shipment line, already self contained.
Spreadsheet 1: one row per single unit of a product; rows sharing a
               shipment_identifier belong to the same shipment.
Spreadsheet 2: origin and destination for each shipment in spreadsheet 1.

Database schema:
    product  (id, name UNIQUE)
    shipment (id, product_id -> product, quantity, origin, destination)

Usage:
    python populate_database.py
"""

import csv
import sqlite3
import sys
from collections import Counter
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATABASE_PATH = BASE_DIR / "shipment_database.db"


def read_rows(filename):
    """Return every row of a CSV file as a dict keyed by column name."""
    with open(DATA_DIR / filename, newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def get_product_id(cursor, product_cache, product_name):
    """Return the id for a product, inserting it the first time it is seen."""
    if product_name not in product_cache:
        cursor.execute("INSERT OR IGNORE INTO product (name) VALUES (?)", (product_name,))
        cursor.execute("SELECT id FROM product WHERE name = ?", (product_name,))
        product_cache[product_name] = cursor.fetchone()[0]
    return product_cache[product_name]


def build_shipment_rows():
    """Combine all spreadsheets into (product_name, quantity, origin, destination) tuples."""
    rows = []

    # Spreadsheet 0: each row is already a complete shipment line.
    for row in read_rows("shipping_data_0.csv"):
        rows.append((
            row["product"],
            int(row["product_quantity"]),
            row["origin_warehouse"],
            row["destination_store"],
        ))

    # Spreadsheet 2: look up origin and destination by shipment identifier.
    locations = {
        row["shipment_identifier"]: (row["origin_warehouse"], row["destination_store"])
        for row in read_rows("shipping_data_2.csv")
    }

    # Spreadsheet 1: each row is one unit, so count rows per (shipment, product)
    # to get the quantity of that product in the shipment.
    quantities = Counter(
        (row["shipment_identifier"], row["product"])
        for row in read_rows("shipping_data_1.csv")
    )

    for (shipment_id, product_name), quantity in quantities.items():
        if shipment_id not in locations:
            raise ValueError(f"Shipment {shipment_id} has no origin/destination in spreadsheet 2")
        origin, destination = locations[shipment_id]
        rows.append((product_name, quantity, origin, destination))

    return rows


def main():
    shipment_rows = build_shipment_rows()

    connection = sqlite3.connect(DATABASE_PATH)
    try:
        cursor = connection.cursor()

        # Guard against running twice and duplicating every shipment.
        cursor.execute("SELECT COUNT(*) FROM shipment")
        if cursor.fetchone()[0] > 0:
            sys.exit("The shipment table already has data; aborting to avoid duplicates.")

        # One transaction: either every row is inserted or none are.
        with connection:
            product_cache = {}
            cursor.executemany(
                "INSERT INTO shipment (product_id, quantity, origin, destination) "
                "VALUES (?, ?, ?, ?)",
                [
                    (get_product_id(cursor, product_cache, name), quantity, origin, destination)
                    for name, quantity, origin, destination in shipment_rows
                ],
            )

        print(f"Inserted {len(product_cache)} products and {len(shipment_rows)} shipment rows.")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
