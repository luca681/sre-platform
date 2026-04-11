#!/usr/bin/env python3
"""
Banking SRE - Auto-Healing Daemon
===================================
Monitors system health every 60 seconds and automatically
fixes common problems:
  - High disk usage  → cleans old logs
  - High memory      → identifies and reports memory hogs
  - Dead services    → restarts them automatically
  - Elasticsearch    → checks cluster health

All events are logged to Elasticsearch for Kibana dashboards.
"""

# ── Imports ──────────────────────────────────────────────────────────────────

import time           # for sleep() — pausing between checks
import logging        # Python's built-in logging system
import subprocess     # for running shell commands from Python
import socket         # for getting the hostname of this machine
import psutil         # for reading CPU, memory, disk, processes
from datetime import datetime, timezone   # for timestamps
from elasticsearch import Elasticsearch  # for sending events to ES

# ── Configuration ─────────────────────────────────────────────────────────────
# These are the thresholds that trigger alerts and auto-healing actions.
# In a real bank these would come from a config file, not be hardcoded.

CONFIG = {
    "es_host":          "http://localhost:9200",  # Elasticsearch address
    "es_index":         "sre-events",             # index to store our events
    "check_interval":   60,                        # seconds between checks
    "disk_warn":        70,                        # % disk — warn
    "disk_critical":    85,                        # % disk — auto-clean
    "memory_warn":      75,                        # % memory — warn
    "memory_critical":  90,                        # % memory — alert
    "services": [                                  # services to monitor
        "docker",
        "filebeat",
        "apache2"
    ]
}

# ── Logging setup ─────────────────────────────────────────────────────────────
# This configures Python's logging module to:
# - Print to the terminal with timestamps
# - Show INFO level and above (INFO, WARNING, ERROR, CRITICAL)
# The format string defines how each log line looks:
# 2026-04-11 12:00:00  INFO  auto_heal  Starting daemon...

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger("auto_heal")

# ── Elasticsearch client ───────────────────────────────────────────────────────
# Creates a connection to Elasticsearch.
# We use basic_auth=None and verify_certs=False because our local
# Elasticsearch has security disabled (xpack.security.enabled=false
# in docker-compose.yml).

es = Elasticsearch(
    CONFIG["es_host"],
    verify_certs=False,
    ssl_show_warn=False
)

# ── Helper: send event to Elasticsearch ───────────────────────────────────────
# Every time something happens — a warning, a fix, a failure — we send
# a structured event to Elasticsearch. This is what feeds your Kibana
# dashboard and gives you a history of everything the daemon did.

def send_event(level: str, check: str, message: str, action: str = "none"):
    """
    Send a structured event to Elasticsearch.

    Parameters:
        level   : "info" | "warning" | "critical"
        check   : what was being checked e.g. "disk" "memory" "service"
        message : human readable description of what happened
        action  : what the daemon did about it e.g. "restarted apache2"
    """
    doc = {
        # datetime.now(timezone.utc) gives current UTC time.
        # .isoformat() converts it to a string like "2026-04-11T09:00:00+00:00"
        # Elasticsearch understands this format natively as a timestamp.
        "timestamp": datetime.now(timezone.utc).isoformat(),

        # socket.gethostname() returns the machine's hostname — "Oloo" in your case.
        # In a bank with hundreds of servers this tells you WHICH server sent the event.
        "host":      socket.gethostname(),

        "level":     level,    # severity of the event
        "check":     check,    # which check produced this event
        "message":   message,  # what happened
        "action":    action,   # what was done about it
    }
    try:
        # es.index() sends the document to Elasticsearch.
        # index=  tells ES which index to store it in.
        # document= is the actual data to store.
        es.index(index=CONFIG["es_index"], document=doc)
    except Exception as e:
        # If Elasticsearch is down we don't want the daemon to crash.
        # We just log the error and continue — the daemon must keep running.
        log.error("Failed to send event to Elasticsearch: %s", e)

# ── Check 1: Disk usage ────────────────────────────────────────────────────────

def check_disk():
    """
    Check disk usage on the root partition.
    - Above 85%: delete old log files automatically
    - Above 70%: warn but take no action
    """
    # psutil.disk_usage("/") returns a named tuple with:
    # .total, .used, .free, .percent
    # We only need .percent — the percentage used.
    usage = psutil.disk_usage("/")
    pct   = usage.percent

    if pct > CONFIG["disk_critical"]:
        msg = f"Disk critical: {pct}% used on /"
        log.critical(msg)

        # Auto-healing action: clean old journal logs.
        # subprocess.run() executes a shell command from Python.
        # capture_output=True captures stdout and stderr so we can log them.
        # text=True returns strings instead of bytes.
        result = subprocess.run(
            ["journalctl", "--vacuum-time=3d"],
            capture_output=True,
            text=True
        )
        action = "cleaned journal logs older than 3 days"
        log.info("Auto-heal: %s", action)
        send_event("critical", "disk", msg, action)

    elif pct > CONFIG["disk_warn"]:
        msg = f"Disk warning: {pct}% used on /"
        log.warning(msg)
        send_event("warning", "disk", msg, "none — monitoring")

    else:
        log.info("Disk OK: %.1f%% used", pct)
        send_event("info", "disk", f"Disk OK: {pct}% used", "none")

# ── Check 2: Memory usage ──────────────────────────────────────────────────────

def check_memory():
    """
    Check RAM usage.
    - Above 90%: find the top memory consuming process and report it
    - Above 75%: warn
    """
    # psutil.virtual_memory() returns memory stats.
    # .percent is the percentage of RAM currently in use.
    mem = psutil.virtual_memory()
    pct = mem.percent

    if pct > CONFIG["memory_critical"]:
        # Find the process using the most memory.
        # psutil.process_iter() loops through every running process.
        # We ask for the "name" and "memory_percent" of each process.
        # max() finds the one with the highest memory_percent.
        top_proc = max(
            psutil.process_iter(["name", "memory_percent"]),
            key=lambda p: p.info["memory_percent"]
        )
        msg = (
            f"Memory critical: {pct}% used. "
            f"Top process: {top_proc.info['name']} "
            f"({top_proc.info['memory_percent']:.1f}%)"
        )
        log.critical(msg)
        send_event("critical", "memory", msg, "reported top process — manual intervention needed")

    elif pct > CONFIG["memory_warn"]:
        msg = f"Memory warning: {pct}% used"
        log.warning(msg)
        send_event("warning", "memory", msg, "none — monitoring")

    else:
        log.info("Memory OK: %.1f%% used", pct)
        send_event("info", "memory", f"Memory OK: {pct}% used", "none")

# ── Check 3: Service health ────────────────────────────────────────────────────

def check_services():
    """
    Check each critical service is running.
    If a service is down — restart it automatically.
    """
    for service in CONFIG["services"]:
        # subprocess.run() runs "systemctl is-active <service>"
        # This command exits with code 0 if the service is active,
        # or code 1-3 if it's inactive/failed.
        # capture_output=True suppresses the output from appearing in terminal.
        result = subprocess.run(
            ["systemctl", "is-active", service],
            capture_output=True,
            text=True
        )

        # result.returncode is the exit code of the command.
        # 0 means success (service is active).
        # Anything else means the service is not running.
        if result.returncode != 0:
            msg = f"Service DOWN: {service}"
            log.critical(msg)

            # Auto-healing: restart the service.
            # We use sudo because restarting services requires root.
            restart = subprocess.run(
                ["sudo", "systemctl", "restart", service],
                capture_output=True,
                text=True
            )

            if restart.returncode == 0:
                action = f"restarted {service} successfully"
                log.info("Auto-heal: %s", action)
            else:
                action = f"failed to restart {service}: {restart.stderr}"
                log.error("Auto-heal FAILED: %s", action)

            send_event("critical", "service", msg, action)

        else:
            log.info("Service OK: %s", service)
            send_event("info", "service", f"Service OK: {service}", "none")

# ── Check 4: Elasticsearch cluster health ─────────────────────────────────────

def check_elasticsearch():
    """
    Check Elasticsearch cluster health via its API.
    Green = all good
    Yellow = working but degraded (normal on single node)
    Red = data loss risk — critical alert
    """
    try:
        # es.cluster.health() calls the Elasticsearch cluster health API.
        # It returns a dictionary with fields like "status", "number_of_nodes" etc.
        health = es.cluster.health()
        status = health["status"]

        if status == "green":
            log.info("Elasticsearch: green")
            send_event("info", "elasticsearch", "Cluster status: green", "none")

        elif status == "yellow":
            # Yellow is expected on a single-node cluster because
            # Elasticsearch wants to store replica shards on a second node
            # but there is no second node. Not dangerous here.
            log.warning("Elasticsearch: yellow (expected on single node)")
            send_event("warning", "elasticsearch", "Cluster status: yellow", "expected on single node")

        else:
            msg = f"Elasticsearch: RED — data loss risk!"
            log.critical(msg)
            send_event("critical", "elasticsearch", msg, "immediate investigation required")

    except Exception as e:
        msg = f"Cannot connect to Elasticsearch: {e}"
        log.critical(msg)
        send_event("critical", "elasticsearch", msg, "check if container is running")

# ── Main loop ─────────────────────────────────────────────────────────────────

def run():
    """
    Main daemon loop.
    Runs all checks every 60 seconds forever.
    """
    log.info("Auto-heal daemon starting on host: %s", socket.gethostname())
    log.info("Checking every %d seconds", CONFIG["check_interval"])
    log.info("Sending events to: %s/%s", CONFIG["es_host"], CONFIG["es_index"])

    # This while True loop runs forever — that's what makes it a daemon.
    # It only stops if you press Ctrl+C or kill the process.
    while True:
        log.info("─── Running health checks ───")

        # Run all four checks in sequence.
        # Each check is independent — if one fails the others still run.
        try:
            check_disk()
        except Exception as e:
            log.error("Disk check failed: %s", e)

        try:
            check_memory()
        except Exception as e:
            log.error("Memory check failed: %s", e)

        try:
            check_services()
        except Exception as e:
            log.error("Service check failed: %s", e)

        try:
            check_elasticsearch()
        except Exception as e:
            log.error("Elasticsearch check failed: %s", e)

        log.info("─── Checks complete. Sleeping %ds ───\n", CONFIG["check_interval"])

        # time.sleep() pauses the script for 60 seconds.
        # During this time the script is idle — using zero CPU.
        time.sleep(CONFIG["check_interval"])

# ── Entry point ───────────────────────────────────────────────────────────────
# This is standard Python — the block below only runs when you execute
# this file directly (python3 auto_heal.py).
# It does NOT run if another script imports this file as a module.

if __name__ == "__main__":
    run()
