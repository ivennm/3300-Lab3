"""Authoritative Server (AS).

Listens on UDP port 53533 and handles two kinds of messages:

1. Registration (from FS) - contains a VALUE field:
       TYPE=A
       NAME=fibonacci.com VALUE=172.18.0.2 TTL=10
   The record is saved to a JSON file so it persists.

2. DNS query (from US) - contains only TYPE and NAME:
       TYPE=A
       NAME=fibonacci.com
   The server answers with the stored record:
       TYPE=A
       NAME=fibonacci.com VALUE=172.18.0.2 TTL=10
"""
import json
import os
import socket

HOST = "0.0.0.0"
PORT = 53533
DB_FILE = os.environ.get("AS_DB_FILE", "dns_records.json")


def parse_message(data):
    """Turn 'KEY=value' pairs (separated by spaces or newlines) into a dict."""
    fields = {}
    for token in data.split():
        if "=" in token:
            key, value = token.split("=", 1)
            fields[key.strip().upper()] = value.strip()
    return fields


def load_records():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE) as f:
        return json.load(f)


def save_record(name, rtype, value, ttl):
    records = load_records()
    records[f"{name}|{rtype}"] = {"NAME": name, "TYPE": rtype, "VALUE": value, "TTL": ttl}
    with open(DB_FILE, "w") as f:
        json.dump(records, f, indent=2)


def format_record(rtype, name, value, ttl):
    return f"TYPE={rtype}\nNAME={name} VALUE={value} TTL={ttl}\n"


def handle(message):
    fields = parse_message(message)
    rtype = fields.get("TYPE")
    name = fields.get("NAME")
    if not rtype or not name:
        return "ERROR=bad request\n"

    if "VALUE" in fields:  # registration request
        ttl = fields.get("TTL", "10")
        save_record(name, rtype, fields["VALUE"], ttl)
        print(f"[AS] Registered {name} -> {fields['VALUE']} (TYPE={rtype}, TTL={ttl})", flush=True)
        return format_record(rtype, name, fields["VALUE"], ttl)

    # DNS query
    record = load_records().get(f"{name}|{rtype}")
    if record is None:
        print(f"[AS] Query for unknown name {name}", flush=True)
        return f"TYPE={rtype}\nNAME={name} ERROR=not found\n"
    print(f"[AS] Query {name} -> {record['VALUE']}", flush=True)
    return format_record(rtype, name, record["VALUE"], record["TTL"])


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((HOST, PORT))
    print(f"[AS] Listening on UDP {HOST}:{PORT}", flush=True)
    while True:
        data, addr = sock.recvfrom(2048)
        response = handle(data.decode())
        sock.sendto(response.encode(), addr)


if __name__ == "__main__":
    main()
