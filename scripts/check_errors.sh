#!/bin/bash

ES="http://localhost:9200"
INDEX="nginx-logs"
THRESHOLD=2

echo "=============================="
echo " ELK Error Check - $(date '+%Y-%m-%d %H:%M:%S')"
echo "=============================="

# Get total error count
TOTAL=$(curl -s "$ES/$INDEX/_count" \
  -H "Content-Type: application/json" \
  -d '{"query": {"term": {"is_error": true}}}' \
  | jq '.count')

echo "Total errors: $TOTAL"

# Alert if above threshold
if [ "$TOTAL" -gt "$THRESHOLD" ]; then
  echo "!! ALERT: Error count $TOTAL exceeds threshold $THRESHOLD"
else
  echo "OK: Error count within threshold"
fi

echo ""
echo "Errors by endpoint:"
curl -s "$ES/$INDEX/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "size": 0,
    "query": {"term": {"is_error": true}},
    "aggs": {
      "by_endpoint": {
        "terms": {"field": "endpoint.keyword"}
      }
    }
  }' | jq -r '.aggregations.by_endpoint.buckets[] | "  \(.key): \(.doc_count) errors"'

echo "=============================="
