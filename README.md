# SRE Platform

A hands-on Site Reliability Engineering lab built on Ubuntu 24.04.
Targeting the SRE Engineer role at Equity Group Holdings.

## Stack
| Tool | Purpose |
|------|---------|
| Elasticsearch | Log storage and search |
| Kibana | Dashboards and visualisation |
| Logstash | Log processing pipeline |
| Docker Compose | Container orchestration |
| Python | Log generation and automation |
| Bash | Monitoring and alert scripts |

## Quick start
```bash
cd elk && docker compose up -d
```

## Services
| Service | URL |
|---------|-----|
| Kibana | http://localhost:5601 |
| Elasticsearch | http://localhost:9200 |

## Projects
- `elk/` — Full ELK stack with Nginx log analysis
- `scripts/` — Automated error monitoring with cron scheduling

## Week 1 — ELK Engineering and Log Analytics
- Deployed full ELK stack via Docker Compose
- Ingested structured JSON logs simulating a banking API
- Built Kibana dashboard: HTTP status breakdown, requests per endpoint, total error count
- Wrote Elasticsearch queries for incident investigation (range queries, aggregations)
- Built a bash monitoring script that alerts when error threshold is breached
- Automated monitoring with cron — runs every minute
