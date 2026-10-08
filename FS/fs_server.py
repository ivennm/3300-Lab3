"""Fibonacci Server (FS) - HTTP server on port 9090.

PUT /register            body: {"hostname", "ip", "as_ip", "as_port"}
                         Registers hostname -> ip with the AS over UDP, returns 201.
GET /fibonacci?number=X  Returns the Fibonacci number for X (200), or 400 if X
                         is not a non-negative integer.
"""
import socket

from flask import Flask, jsonify, request

app = Flask(__name__)
TTL = 10


def fibonacci(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


@app.route("/register", methods=["PUT"])
def register():
    body = request.get_json(silent=True)
    required = ["hostname", "ip", "as_ip", "as_port"]
    if not body or any(k not in body for k in required):
        return jsonify(error="body must contain hostname, ip, as_ip, as_port"), 400

    try:
        as_port = int(body["as_port"])
    except (TypeError, ValueError):
        return jsonify(error="as_port must be an integer"), 400

    message = f"TYPE=A\nNAME={body['hostname']} VALUE={body['ip']} TTL={TTL}\n"
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(3)
    try:
        sock.sendto(message.encode(), (body["as_ip"], as_port))
        reply, _ = sock.recvfrom(2048)
    except OSError as e:
        return jsonify(error=f"could not reach authoritative server: {e}"), 500
    finally:
        sock.close()

    if "ERROR" in reply.decode():
        return jsonify(error=reply.decode()), 500
    return jsonify(message="registered", record=message), 201


@app.route("/fibonacci", methods=["GET"])
def get_fibonacci():
    number = request.args.get("number")
    try:
        n = int(number)
        if n < 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify(error="number must be a non-negative integer"), 400
    return jsonify(number=n, fibonacci=fibonacci(n)), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9090)
