import json
import random
import time
from datetime import datetime
import urllib.request

ES_URL = "http://localhost:9200"
INDEX   = "nginx-logs"

ENDPOINTS = ["/api/login", "/api/transfer", "/api/balance", "/api/users", "/health"]
IPS       = ["41.90.64.1", "197.232.4.2", "102.0.0.5", "10.0.0.1", "192.168.1.50"]
METHODS   = ["GET", "POST", "PUT", "DELETE"]
STATUSES  = [200]*70 + [201]*10 + [404]*10 + [500]*7 + [503]*3  # weighted

def send_doc(doc):
    data = json.dumps(doc).encode()
    req  = urllib.request.Request(
        f"{ES_URL}/{INDEX}/_doc",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    urllib.request.urlopen(req)

def make_log():
    status = random.choice(STATUSES)
    return {
        "timestamp":    datetime.utcnow().isoformat(),
        "ip":           random.choice(IPS),
        "method":       random.choice(METHODS),
        "endpoint":     random.choice(ENDPOINTS),
        "status":       status,
        "response_ms":  random.randint(10, 2000),
        "bytes":        random.randint(200, 5000),
        "is_error":     status >= 400
    }

print("Sending 50 log entries to Elasticsearch...")
for i in range(50):
    doc = make_log()
    send_doc(doc)
    print(f"  [{i+1:02d}/50] {doc['method']:6} {doc['endpoint']:20} → {doc['status']}")
    time.sleep(0.1)

print("\nDone. Open Kibana → Discover to see your logs.")
