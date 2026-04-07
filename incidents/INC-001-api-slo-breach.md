# INC-001 — API Availability SLO Breach

**Date:** 2026-04-06  
**Detected by:** Morning health check script  
**Severity:** P2  
**Status:** Investigating  
**Owner:** Thanos Oloo  

## Summary
Payment API availability dropped to 84% against a 99% SLO target.
8 errors detected out of 50 total requests.

## Timeline
| Time | Event |
|------|-------|
| 23:52 | Morning health check detected SLO breach |
| 23:52 | Incident opened |

## Error breakdown
| Endpoint | Errors |
|----------|--------|
| /api/login | 3 |
| /api/transfer | 2 |
| /api/balance | 1 |
| /api/users | 1 |
| /health | 1 |

## Impact
- Payment transfers affected: 2 failures
- Login failures: 3 — users unable to access accounts
- Estimated customers affected: unknown

## Investigation steps
- [ ] Check Elasticsearch for error patterns
- [ ] Check application logs for root cause
- [ ] Check system resources at time of errors
- [ ] Identify if errors are from a single IP (possible attack)

## Resolution
Pending investigation

## Root cause
Pending

## Prevention
Pending post-mortem

## Investigation findings
**Error source analysis:**
| IP | Count | Type | Assessment |
|----|-------|------|------------|
| 10.0.0.1 | 4 | Internal | Misconfigured internal service |
| 192.168.1.50 | 2 | Internal | Misconfigured internal service |
| 102.0.0.5 | 1 | External | Isolated incident |
| 197.232.4.2 | 1 | External (KE) | Isolated incident |

**Conclusion:** No attack detected. 75% of errors originate from internal 
network. Root cause likely a misconfigured internal batch job or test 
environment hitting the payment API incorrectly.

**Next steps:**
- Identify owner of 10.0.0.1 and 192.168.1.50
- Review what requests those IPs are making
- Fix or reconfigure the internal service

## Root cause identified
Internal service at 10.0.0.1 is making API calls with incorrect HTTP methods:
- Using PUT on /api/login (should be POST)
- Using DELETE on /api/transfer (should be POST)

This indicates a misconfigured API client — likely a recent deployment
with incorrect method configuration.

High response times (1278-1390ms) on all errors suggest server-side
processing before failure — not a network issue.

## Resolution
1. Contact owner of 10.0.0.1 to identify the service
2. Fix HTTP methods in their API client configuration
3. Redeploy the corrected service
4. Monitor error rate for 30 minutes after fix
5. Close incident when availability returns above 99%

## Status: Resolved — pending redeployment by service owner
## Resolved at: $(date '+%Y-%m-%d %H:%M')
