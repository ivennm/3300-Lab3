"""User Server (US) - HTTP server on port 8080.

GET /fibonacci?hostname=fibonacci.com&fs_port=K&number=X&as_ip=Y&as_port=Z

1. Returns 400 if any parameter is missing.
2. Asks the Authoritative Server (UDP) for the IP address of `hostname`.
3. Requests http://<ip>:<fs_port>/fibonacci?number=X from the Fibonacci Server
   and returns its result (200 on success).
"""
import socket

import requests
from flask import Flask, jsonify, request

app = Flask(__name__)
PARAMS = ["hostname", "fs_port", "number", "as_ip", "as_port"]


def dns_query(hostname, as_ip, as_port):
    """Send a TYPE=A query to the AS and return the IP address (or None)."""
    message = f"TYPE=A\nNAME={hostname}\n"
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(3)
    try:
        sock.sendto(message.encode(), (as_ip, as_port))
        reply, _ = sock.recvfrom(2048)
    finally:
        sock.close()

    fields = {}
    for token in reply.decode().split():
        if "=" in token:
            key, value = token.split("=", 1)
            fields[key.upper()] = value
    return fields.get("VALUE")


@app.route("/fibonacci", methods=["GET"])
def fibonacci():
    args = {p: request.args.get(p) for p in PARAMS}
    missing = [p for p, v in args.items() if not v]
    if missing:
        return jsonify(error=f"missing parameter(s): {', '.join(missing)}"), 400

    try:
        as_port = int(args["as_port"])
        fs_port = int(args["fs_port"])
    except ValueError:
        return jsonify(error="as_port and fs_port must be integers"), 400

    try:
        fs_ip = dns_query(args["hostname"], args["as_ip"], as_port)
    except OSError as e:
        return jsonify(error=f"could not reach authoritative server: {e}"), 500
    if not fs_ip:
        return jsonify(error=f"hostname {args['hostname']} not found"), 404

    try:
        resp = requests.get(
            f"http://{fs_ip}:{fs_port}/fibonacci",
            params={"number": args["number"]},
            timeout=5,
        )
    except requests.RequestException as e:
        return jsonify(error=f"could not reach fibonacci server: {e}"), 500

    return resp.content, resp.status_code, {"Content-Type": "application/json"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
