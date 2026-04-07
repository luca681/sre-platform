#!/bin/bash

# ============================================
# Banking SRE - Morning Health Check
# Run at start of every shift
# ============================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

pass() { echo -e "${GREEN}[PASS]${NC} $*"; }
fail() { echo -e "${RED}[FAIL]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }

echo "============================================"
echo " Equity SRE - Morning Health Check"
echo " $(date '+%A %d %B %Y — %H:%M:%S')"
echo "============================================"
echo ""

# --- 1. SYSTEM RESOURCES ---
echo "[ System Resources ]"

DISK=$(df -h / | awk 'NR==2 {print $5}' | tr -d '%')
if [ "$DISK" -gt 85 ]; then
  fail "Disk usage critical: ${DISK}%"
elif [ "$DISK" -gt 70 ]; then
  warn "Disk usage high: ${DISK}%"
else
  pass "Disk usage OK: ${DISK}%"
fi

MEM=$(free | awk 'NR==2 {printf "%.0f", $3/$2*100}')
if [ "$MEM" -gt 90 ]; then
  fail "Memory critical: ${MEM}%"
elif [ "$MEM" -gt 75 ]; then
  warn "Memory high: ${MEM}%"
else
  pass "Memory OK: ${MEM}%"
fi

LOAD=$(cat /proc/loadavg | awk '{print $1}')
pass "Load average: ${LOAD}"
echo ""

# --- 2. SYSTEM SERVICES ---
echo "[ Critical Services ]"

for SERVICE in docker filebeat apache2; do
  if systemctl is-active --quiet $SERVICE; then
    pass "$SERVICE is running"
  else
    fail "$SERVICE is DOWN — run: sudo systemctl restart $SERVICE"
  fi
done
echo ""

# --- 3. DOCKER CONTAINERS ---
echo "[ ELK Stack Containers ]"

# Elasticsearch has a healthcheck — use health status
ES_STATUS=$(docker inspect --format='{{.State.Health.Status}}' elasticsearch 2>/dev/null)
if [ "$ES_STATUS" = "healthy" ]; then
  pass "elasticsearch is healthy"
else
  fail "elasticsearch is $ES_STATUS"
fi

# Kibana and Logstash have no healthcheck — check running state
for CONTAINER in kibana logstash; do
  RUNNING=$(docker inspect --format='{{.State.Running}}' $CONTAINER 2>/dev/null)
  if [ "$RUNNING" = "true" ]; then
    pass "$CONTAINER is running"
  else
    fail "$CONTAINER is DOWN — run: docker compose up -d $CONTAINER"
  fi
done
echo ""

# --- 4. ELASTICSEARCH CLUSTER ---
echo "[ Elasticsearch Cluster ]"

ES_HEALTH=$(curl -s http://localhost:9200/_cluster/health | jq -r '.status' 2>/dev/null)
ES_DOCS=$(curl -s http://localhost:9200/_cat/indices?h=docs.count | awk '{sum+=$1} END {print sum}')

if [ "$ES_HEALTH" = "green" ]; then
  pass "Cluster status: green"
elif [ "$ES_HEALTH" = "yellow" ]; then
  warn "Cluster status: yellow (single node — expected in dev)"
else
  fail "Cluster status: $ES_HEALTH — investigate immediately"
fi
pass "Total documents indexed: $ES_DOCS"
echo ""

# --- 5. SLO CHECK ---
echo "[ API Availability SLO ]"

ERROR_COUNT=$(curl -s http://localhost:9200/nginx-logs/_count \
  -H "Content-Type: application/json" \
  -d '{"query": {"term": {"is_error": true}}}' | jq '.count')

TOTAL_COUNT=$(curl -s http://localhost:9200/nginx-logs/_count | jq '.count')

if [ "$TOTAL_COUNT" -gt 0 ]; then
  AVAILABILITY=$(echo "scale=2; ($TOTAL_COUNT - $ERROR_COUNT) * 100 / $TOTAL_COUNT" | bc)
  if (( $(echo "$AVAILABILITY < 99" | bc -l) )); then
    fail "API availability: ${AVAILABILITY}% — SLO breach — target is 99%"
    fail "Errors: $ERROR_COUNT out of $TOTAL_COUNT requests"
    fail "ACTION REQUIRED: Run ~/sre-platform/scripts/check_errors.sh"
  else
    pass "API availability: ${AVAILABILITY}% — SLO target met"
  fi
fi
echo ""

echo "============================================"
echo " Check complete — $(date '+%H:%M:%S')"
echo "============================================"
