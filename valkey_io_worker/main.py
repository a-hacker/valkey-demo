import os
import time
import valkey
import csv
from dataclasses import dataclass, asdict, fields
import uuid

from polyfactory.factories import DataclassFactory

# Configuration
VALKEY_HOST = "valkey"
VALKEY_PORT = 6379
ROLE = os.getenv("ROLE", "writer")
WORKER_ID = os.getenv("WORKER_ID", "0")
OUTPUT_DIR = "/app/output"


@dataclass
class User:
    id: uuid.UUID
    name: str
    worker: str

class UserFactory(DataclassFactory[User]):
    worker = WORKER_ID

@dataclass
class Order:
    id: uuid.UUID
    item_name: str
    quantity: int
    price: float
    user_id: str
    worker: str

class OrderFactory(DataclassFactory[Order]):
    worker = WORKER_ID

TABLES = {"users": UserFactory, "orders": OrderFactory}


def connect_to_valkey() -> valkey.Valkey:
    """Connects to Valkey with retries."""
    while True:
        try:
            client = valkey.Valkey(host=VALKEY_HOST, port=VALKEY_PORT, decode_responses=True)
            client.ping()  # Test connection
            print(f"[{ROLE}] Connected to Valkey!")
            return client
        except valkey.ConnectionError:
            print(f"[{ROLE}] Waiting for Valkey to be ready...")
            time.sleep(2)

def dataclass_to_list(data_object):
    data_dict = asdict(data_object)
    return {key: str(value) for key, value in data_dict.items()}

def write_data(client: valkey.Valkey):
    """Writes sample data to Valkey."""
    for table, factory in TABLES.items():
        for i in range(5):
            record = dataclass_to_list(factory.build())
            row_key = f"{table}:{WORKER_ID}:{record['id']}"
            client.hset(row_key, mapping=record)  # Store row as a hash
            client.expire(row_key, time=120, lt=True)
            print(f"[{ROLE}] Wrote {row_key} -> {record}")
            time.sleep(1)


def stream_read_table(client: valkey.Valkey, table_name: str, factory: type[DataclassFactory]):
    """Fetches all rows for a given table and writes them to a CSV row-by-row."""
    table_keys = client.keys(f"{table_name}:*")
    output_file = f"{OUTPUT_DIR}/{table_name}.csv"

    header = [field.name for field in fields(factory.__model__)]

    def to_row(raw_data: dict[str, str], model):
        return [raw_data[field.name] for field in fields(model)]

    with open(output_file, mode="w", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(header)

        for key in table_keys:
            row_data = client.hgetall(key)  # Get full row
            writer.writerow(to_row(row_data, factory.__model__))
            print(f"[reader] Wrote row: {row_data} to {output_file}")


def read_data(client: valkey.Valkey):
    """Reads tables one at a time and streams them to separate CSVs."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for table_name, factory in TABLES.items():
        print(f"[reader] Processing table: {table_name}")
        stream_read_table(client, table_name, factory)


def main():
    client = connect_to_valkey()

    if ROLE == "writer":
        write_data(client)
    elif ROLE == "reader":
        read_data(client)


if __name__ == "__main__":
    main()