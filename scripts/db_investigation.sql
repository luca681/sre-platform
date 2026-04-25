-- ============================================================
-- Banking SRE — Database Incident Investigation Queries
-- Usage: psql -U sre_analyst -d equity_bank -f db_investigation.sql
-- ============================================================

-- 1. Transaction failure rate
SELECT 
    status,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM transactions
GROUP BY status
ORDER BY count DESC;

-- 2. Failed transactions with error messages
SELECT 
    account_number,
    transaction_type,
    amount,
    error_message,
    created_at
FROM transactions
WHERE status = 'failed'
ORDER BY created_at DESC;

-- 3. Slow API calls above 500ms
SELECT 
    endpoint,
    method,
    status_code,
    response_ms,
    ip_address,
    created_at
FROM api_logs
WHERE response_ms > 500
ORDER BY response_ms DESC;

-- 4. API availability by endpoint
SELECT
    endpoint,
    COUNT(*) as total_requests,
    SUM(CASE WHEN status_code >= 500 THEN 1 ELSE 0 END) as errors,
    ROUND(
        (COUNT(*) - SUM(CASE WHEN status_code >= 500 THEN 1 ELSE 0 END)) 
        * 100.0 / COUNT(*), 2
    ) as availability_pct
FROM api_logs
GROUP BY endpoint
ORDER BY availability_pct ASC;

-- 5. Customers with failed transactions
SELECT 
    c.full_name,
    c.account_number,
    c.balance,
    COUNT(t.id) as total_transactions,
    SUM(CASE WHEN t.status = 'failed' THEN 1 ELSE 0 END) as failed_transactions
FROM customers c
LEFT JOIN transactions t ON c.account_number = t.account_number
GROUP BY c.id, c.full_name, c.account_number, c.balance
HAVING SUM(CASE WHEN t.status = 'failed' THEN 1 ELSE 0 END) > 0
ORDER BY failed_transactions DESC;
