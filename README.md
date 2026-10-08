# dns_app – Lab 3, Problem 2

| Server | Folder | Port | Protocol |
|---|---|---|---|
| Authoritative Server | `AS/` | 53533 | UDP |
| Fibonacci Server | `FS/` | 9090 | HTTP |
| User Server | `US/` | 8080 | HTTP |

## Run with Docker

```bash
# 1. Build the images (run from inside dns_app/)
docker build -t as:latest AS
docker build -t fs:latest FS
docker build -t us:latest US

# 2. Create a network and start the containers
docker network create dnsnet
docker run -d --network dnsnet --name as -p 53533:53533/udp as:latest
docker run -d --network dnsnet --name fs -p 9090:9090 fs:latest
docker run -d --network dnsnet --name us -p 8080:8080 us:latest

# 3. Find each container's IP on the network
docker inspect dnsnet
```

## Test

Replace `FS_IP` and `AS_IP` with the addresses from `docker inspect dnsnet`.

```bash
# Register fibonacci.com with the AS (expect 201)
curl -i -X PUT http://localhost:9090/register \
  -H "Content-Type: application/json" \
  -d '{"hostname":"fibonacci.com","ip":"FS_IP","as_ip":"AS_IP","as_port":"53533"}'

# Ask the US for Fibonacci(10) (expect 200, fibonacci = 55)
curl -i "http://localhost:8080/fibonacci?hostname=fibonacci.com&fs_port=9090&number=10&as_ip=AS_IP&as_port=53533"

# Bad number (expect 400)
curl -i "http://localhost:8080/fibonacci?hostname=fibonacci.com&fs_port=9090&number=abc&as_ip=AS_IP&as_port=53533"

# Missing parameter (expect 400)
curl -i "http://localhost:8080/fibonacci?hostname=fibonacci.com&number=10"
```

## Message formats (UDP to AS)

Registration (FS → AS):
```
TYPE=A
NAME=fibonacci.com VALUE=172.18.0.3 TTL=10
```
Query (US → AS):
```
TYPE=A
NAME=fibonacci.com
```
Response (AS → US):
```
TYPE=A
NAME=fibonacci.com VALUE=172.18.0.3 TTL=10
```
The AS stores records in `dns_records.json`.
