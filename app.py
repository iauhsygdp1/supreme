#!/usr/bin/env python3

from flask import Flask, jsonify, request
import threading
import time
from collections import deque
import logging
import os
import sys

app = Flask(__name__)

CACHE_LIMIT = int(os.getenv("CACHE_LIMIT", 250)) # Kept synced to your 250 log specification
CACHE_ENTRY_TTL = int(os.getenv("CACHE_ENTRY_TTL", 5400))
CACHE_CLEAR_INTERVAL = int(os.getenv("CACHE_CLEAR_INTERVAL", 1800))
BOT_TIMEOUT = int(os.getenv("BOT_TIMEOUT", 300))  # 5 minutes

server_cache = deque()
cache_set = set()
jobs_assigned = 0
total_received = 0
visited_servers = {}
visit_stats = {"total_visits": 0, "unique_servers": 0, "repeat_visits": 0}

active_bots = {}  
bot_lock = threading.Lock()
lock = threading.Lock()

logging.basicConfig(
    level=logging.INFO,
    format='[MAIN-API] %(asctime)s %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)

# =====================================================================
# 🐕 INTERNAL WATCHDOG SYSTEM
# =====================================================================
class MainStateWatchdog(threading.Thread):
    def __init__(self, check_interval=15, max_stale_seconds=45):
        super().__init__()
        self.daemon = True
        self.name = "state-watchdog"
        self.check_interval = check_interval
        self.max_stale_seconds = max_stale_seconds
        self.last_pulse = time.time()

    def pulse(self):
        """Register transaction heartbeat"""
        self.last_pulse = time.time()

    def run(self):
        logging.info("[WATCHDOG] Core server system monitoring active.")
        while True:
            time.sleep(self.check_interval)
            stale = time.time() - self.last_pulse
            if stale > self.max_stale_seconds:
                logging.critical(f"[WATCHDOG] CRITICAL: Transaction loops are entirely frozen ({int(stale)}s stale)! Exiting container.")
                sys.exit(1)

watchdog = MainStateWatchdog()
watchdog.start()
# =====================================================================

def _now():
    return time.time()

def get_bot_id():
    bot_id = request.headers.get('X-Bot-Name')
    if not bot_id:
        bot_id = request.args.get('bot_id')
    if not bot_id:
        try:
            data = request.get_json(silent=True)
            if data:
                bot_id = data.get('bot_id')
        except:
            pass
    return bot_id

def track_bot(bot_id):
    if not bot_id:
        return
    with bot_lock:
        now = _now()
        if bot_id in active_bots:
            active_bots[bot_id]["last_seen"] = now
            active_bots[bot_id]["requests"] += 1
        else:
            active_bots[bot_id] = {
                "last_seen": now,
                "first_seen": now,
                "requests": 1
            }

def get_active_bot_count():
    with bot_lock:
        now = _now()
        return sum(1 for bot in active_bots.values() if now - bot["last_seen"] < BOT_TIMEOUT)

def cleanup_inactive_bots():
    with bot_lock:
        now = _now()
        inactive = [bid for bid, bot in active_bots.items() if now - bot["last_seen"] >= BOT_TIMEOUT]
        for bid in inactive:
            del active_bots[bid]

def cleanup_expired():
    global server_cache, cache_set
    now = _now()
    while server_cache and server_cache[0]["expires_at"] <= now:
        expired_job = server_cache.popleft()
        cache_set.discard(expired_job["id"])

@app.route("/", methods=["GET"])
@app.route("/status", methods=["GET"])
def status():
    """Outputs the specific cluster metric format you requested"""
    watchdog.pulse()
    with lock:
        cleanup_expired()
    cleanup_inactive_bots()
    
    # Check if the watchdog itself has crashed or fallen behind
    is_healthy = "healthy" if (time.time() - watchdog.last_pulse < 30) else "unhealthy"
    
    payload = {
        "active_bots": get_active_bot_count(),
        "cache_jobs": len(cache_set),
        "cache_limit": CACHE_LIMIT,
        "health": is_healthy,
        "jobs_assigned": jobs_assigned,
        "total_received": total_received,
        "visit_tracking": {
            "repeat_rate": visit_stats["repeat_visits"],
            "total_visits": visit_stats["total_visits"],
            "unique_servers": visit_stats["unique_servers"]
        }
    }
    
    return jsonify(payload), 200 if is_healthy == "healthy" else 500

@app.route("/add-pool", methods=["POST"])
def add_pool():
    global total_received
    watchdog.pulse()
    data = request.get_json()
    if not data or "servers" not in data:
        return jsonify({"error": "Missing servers list"}), 400
        
    bot_id = get_bot_id()
    track_bot(bot_id)
    
    added_count = 0
    now = _now()
    expires_at = now + CACHE_ENTRY_TTL
    
    with lock:
        cleanup_expired()
        for s_id in data["servers"]:
            total_received += 1
            if s_id not in cache_set:
                if len(cache_set) >= CACHE_LIMIT:
                    # Drop oldest elements if cache limit is met
                    if server_cache:
                        oldest = server_cache.popleft()
                        cache_set.discard(oldest["id"])
                
                server_cache.append({"id": s_id, "expires_at": expires_at})
                cache_set.add(s_id)
                added_count += 1
                
    return jsonify({"status": "success", "added": added_count, "total_cache": len(cache_set)}), 200

@app.route("/get-job", methods=["GET", "POST"])
def get_job():
    global jobs_assigned
    watchdog.pulse()
    bot_id = get_bot_id()
    track_bot(bot_id)
    
    with lock:
        cleanup_expired()
        if not cache_set:
            return jsonify({"job_id": None, "message": "No jobs available"}), 200
            
        # Assign job tracking logic
        job_id = list(cache_set)[0] 
        jobs_assigned += 1
        return jsonify({"job_id": job_id}), 200

def periodic_cleanup():
    while True:
        time.sleep(10)
        with lock:
            cleanup_expired()
        cleanup_inactive_bots()

def cache_clear_30min():
    while True:
        time.sleep(CACHE_CLEAR_INTERVAL)
        with lock:
            old_size = len(server_cache)
            server_cache.clear()
            cache_set.clear()
            logging.info(f"30-minute cache clear: removed {old_size} servers")

def stats_logger():
    while True:
        time.sleep(60)
        with lock:
            elapsed = time.time() - start_time
            rate = jobs_assigned / elapsed if elapsed > 0 else 0
            active_bots_count = get_active_bot_count()
            logging.info(
                f"STATS - Cache: {len(server_cache)}, "
                f"Assigned: {jobs_assigned}, "
                f"Received: {total_received}, "
                f"Rate: {rate:.1f} jobs/sec, "
                f"Active Bots: {active_bots_count}"
            )

threading.Thread(target=periodic_cleanup, daemon=True).start()
threading.Thread(target=cache_clear_30min, daemon=True).start()
threading.Thread(target=stats_logger, daemon=True).start()

start_time = time.time()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8963))
    app.run("0.0.0.0", port, threaded=True)
