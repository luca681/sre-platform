# SRE Learning Progress — Thanos Oloo
Target role: SRE Engineer — Equity Group Holdings

## Week 1 — Completed
### Day 1
- Deployed full ELK stack via Docker Compose
- Ingested structured JSON logs simulating banking API
- Built Kibana dashboard: pie chart, bar chart, error metric
- Wrote Elasticsearch queries: range queries, aggregations
- Built bash monitoring script with threshold alerting
- Automated monitoring with cron

### Day 2
- Linux processes: ps, top, kill
- Linux permissions: chmod, chown, ls -la
- systemd: systemctl status, start, stop, enable
- journalctl: querying and filtering system logs
- Log triage: distinguishing real errors from noise
- Filebeat: installed, configured, shipping real logs
- Real pipeline: 35,000+ syslog entries in Elasticsearch

### Day 3
- Morning health check script — shift start procedure
- Incident INC-001: full investigation and report
- Kibana data views for syslog and apache-error
- Logstash grok parser for Apache logs
- Fixed pipeline: Filebeat → Logstash → Elasticsearch
- SLO dashboard: availability, response time, error rate

### Day 4
- Python virtual environment setup
- Auto-healing daemon: disk, memory, service, ES checks
- systemd service: daemon runs on boot, auto-restarts
- Proven crash recovery with new PID after kill
- Terraform: init, plan, apply, destroy workflow
- Docker provider: created Nginx container from code
- .gitignore fixed, repo cleaned

## Interview questions practiced: 12
## Weak areas to keep improving:
- Add specific commands to every answer
- Connect technical answers to banking business impact
- Structure incident response using the 6-step framework

## Week 2 — Starting now
Focus: Python automation, Ansible, Azure basics, IaC depth
