# Log Pipeline

## Data sources
| Source | Path | Index |
|--------|------|-------|
| System logs | /var/log/syslog | syslog-YYYY.MM.DD |
| Apache errors | /var/log/apache2/error.log | apache-error-YYYY.MM.DD |
| Fake API logs | Python script | nginx-logs |

## How it works
1. Filebeat watches log files and ships new lines to Elasticsearch
2. Elasticsearch indexes and stores every log as a JSON document
3. Kibana reads from Elasticsearch to build dashboards

## Useful commands
```bash
# Check Filebeat status
sudo systemctl status filebeat

# Check all indexes and document counts
curl -s http://localhost:9200/_cat/indices?v

# Tail Filebeat logs for troubleshooting
sudo journalctl -u filebeat -f
```
