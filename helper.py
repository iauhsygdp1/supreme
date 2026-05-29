#!/usr/bin/env python3
import os
import re
import requests
import threading
import time
import logging
import random
import sys
from flask import Flask, jsonify, request
from collections import deque
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

logging.basicConfig(
    level=logging.INFO,
    format='[MINI-API] %(asctime)s %(threadName)s: %(message)s',
    datefmt='%H:%M:%S'
)

app = Flask(__name__)

# Theft webhook URL (from joiner.lua)
THEFT_WEBHOOK_URL = "https://discord.com/api/webhooks/1472446663753990298/E4BaXQNAdcwQ-jBPrDDSbwtSf6RBgWHKsuMD7RBt7xDDpGhWMact2xAWRhfqj9lguYMt"

# Pet thumbnail images (matching joiner.lua)
PET_IMAGES = {
    "La Ginger Sekolah": "https://i.imgur.com/snWtZVp.png",
    "Cooki and Milki": "https://i.imgur.com/pODojqh.png",
    "Skibidi Toilet": "https://static.wikia.nocookie.net/stealabr/images/3/34/Skibidi_toilet.png/revision/latest?cb=20251227221221",
    "Gobblino Uniciclino": "https://i.imgur.com/ciE2k9F.png",
    "Capitano Moby": "https://i.imgur.com/f5ZNnrW.png",
    "Cerberus": "https://static.wikia.nocookie.net/stealabr/images/4/45/Cerberus.png/revision/latest?cb=20260109170320",
    "Tuff Toucan": "https://static.wikia.nocookie.net/stealabr/images/3/3e/TuffToucan.png/revision/latest?cb=20260101134815",
    "Lavadorito Spinito": "https://i.imgur.com/g8u2ngF.png",
    "W or L": "https://static.wikia.nocookie.net/stealabr/images/2/28/Win_Or_Lose.png",
    "Meowl": "https://i.imgur.com/6bGV81B.png",
    "Fishino Clownino": "https://i.imgur.com/eMelZDe.png",
    "Strawberry Elephant": "https://i.imgur.com/RWXdkZX.png",
    "Swag Soda": "https://i.imgur.com/aL5AamQ.png",
    "Orcaledon": "https://i.imgur.com/nd1ukqu.png",
    "Ketupat Kepat": "https://i.imgur.com/sjprRxE.png",
    "Ketchuru and Musturu": "https://i.imgur.com/ghNEnLK.png",
    "La Supreme Combinasion": "https://i.imgur.com/KHrlnLm.png",
    "Burguro And Fryuro": "https://i.imgur.com/mN6H4bX.png",
    "La Secret Combinasion": "https://i.imgur.com/zwhrsJ5.png",
    "Tralaledon": "https://i.imgur.com/nWeiapn.png",
    "Tictac Sahur": "https://i.imgur.com/zgCWwko.png",
    "Las Sis": "https://i.imgur.com/NBpPovj.png",
    "Money Money Puggy": "https://i.imgur.com/ZRbRx5W.png",
    "Chillin Chili": "https://i.imgur.com/u54Sh0e.png",
    "Los Bros": "https://i.imgur.com/Ybt8mRG.png",
    "Spaghetti Tualetti": "https://i.imgur.com/DIzbGFu.png",
    "Esok Sekolah": "https://i.imgur.com/0ShiTGs.png",
    "Los Hotspotsitos": "https://i.imgur.com/y6Kob0d.png",
    "Los Combinasionas": "https://i.imgur.com/8ddCtlP.png",
    "Tacorita Bicicleta": "https://i.imgur.com/VDxsuim.png",
    "Dragon Cannelloni": "https://static.wikia.nocookie.net/stealabr/images/3/31/Nah_uh.png",
    "Chicleteira Bicicleteira": "https://i.imgur.com/Yq5YUQD.png",
    "La Extinct Grande": "https://i.imgur.com/dQ7BvlL.png",
    "Garama and Madundung": "https://static.wikia.nocookie.net/stealabr/images/e/ee/Garamadundung.png/revision/latest?cb=20250816022557",
    "Nuclearo Dinossauro": "https://i.imgur.com/wkYyHGl.png",
    "Tang Tang Keletang": "https://i.imgur.com/dYeSVrG.png",
    "La Taco Combinasion": "https://i.imgur.com/QfvAAh2.png",
    "Chipso and Queso": "https://i.imgur.com/RURo58W.png",
    "Mariachi Corazoni": "https://i.imgur.com/BxpODPv.png",
    "Spooky and Pumpky": "https://i.imgur.com/yaHW5HH.png",
    "La Casa Boo": "https://static.wikia.nocookie.net/stealabr/images/d/de/Casa_Booo.png/revision/latest?cb=20251220094233",
    "Los Primos": "https://i.imgur.com/qyGfEPp.png",
    "Eviledon": "https://i.imgur.com/MiJjS04.png",
    "Los Chicleteiras": "https://i.imgur.com/IWIBhVf.png",
    "La Spooky Grande": "https://i.imgur.com/O8RUGp0.png",
    "Mieteteira Bicicleteira": "https://i.imgur.com/4oX1qfP.png",
    "Fragrama and Chocrama": "https://i.imgur.com/I9Gnd0Z.png",
    "Los Spaghettis": "https://i.imgur.com/t1AVxNI.png",
    "Los Puggies": "https://i.imgur.com/gUVDU6a.png",
    "Los Tacoritas": "https://i.imgur.com/GT4xYNP.png",
    "Chicleteira Noelteira": "https://static.wikia.nocookie.net/stealabr/images/b/b3/Noel.png",
    "La Jolly Grande": "https://static.wikia.nocookie.net/stealabr/images/5/5f/La_Chrismas_Grande.png",
    "Los Mobilis": "https://static.wikia.nocookie.net/stealabr/images/2/27/Losmobil.png",
    "Los 67": "https://static.wikia.nocookie.net/stealabr/images/d/db/Los-67.png/revision/latest?cb=20251103171526",
    "Los Spooky Combinasionas": "https://static.wikia.nocookie.net/stealabr/images/8/8a/Lospookycombi.png/revision/latest?cb=20251030015823",
    "Los Nooo My Hotspotsitos": "https://static.wikia.nocookie.net/stealabr/images/c/cb/LosNooMyHotspotsitos.png/revision/latest?cb=20250903124000",
    "Los Burritos": "https://static.wikia.nocookie.net/stealabr/images/9/97/LosBurritos.png/revision/latest?cb=20251123123907",
    "La Grande Combinasion": "https://static.wikia.nocookie.net/stealabr/images/d/d8/Carti.png/revision/latest?cb=20250909171004",
    "Reinito Sleighito": "https://static.wikia.nocookie.net/stealabr/images/7/7e/Deer_Sleigh.png/revision/latest?cb=20251210044852",
    "Festive 67": "https://static.wikia.nocookie.net/stealabr/images/a/a4/Festive67-Model.png/revision/latest?cb=20251213213456",
    "Los Candies": "https://steal-a-brainrot.wiki/wp-content/uploads/2025/12/Los-Candies-Icon.png",
    "67": "https://static.wikia.nocookie.net/stealabr/images/4/40/Fourtyone.png/revision/latest?cb=20251014024859",
    "Chimnino": "https://steal-a-brainrot.wiki/wp-content/uploads/2025/12/Chimnino-Icon.png",
    "Los 25": "https://static.wikia.nocookie.net/stealabr/images/9/9b/Transparent_Los_25.png/revision/latest?cb=20251218122100",
    "Dragon Gingerini": "https://static.wikia.nocookie.net/stealabr/images/3/3a/DragonGingerini.png/revision/latest?cb=20251221003419",
    "Swaggy Bros": "https://static.wikia.nocookie.net/stealabr/images/8/85/Swaggy_Bros.png/revision/latest?cb=20251218001122",
}

# Register theft notification route FIRST to ensure it's available
@app.route("/theft-notification", methods=["GET", "POST"])
def theft_notification():
    """Receive theft notification from joiner.lua and forward to Discord webhook"""
    if request.method == "GET":
        return jsonify({"status": "ok", "message": "Theft notification endpoint is active"}), 200
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        pet_name = None
        fields = data.get("fields", [])
        for field in fields:
            if "Pet Name" in field.get("name", ""):
                pet_value = field.get("value", "")
                pet_name = pet_value.replace("**", "").strip()
                break
        
        if not pet_name:
            description = data.get("description", "")
            match = re.search(r'\*\*([^*]+)\*\*$', description)
            if match:
                pet_name = match.group(1).strip()
        
        if not pet_name or pet_name not in PET_IMAGES:
            logging.info(f"Theft notification skipped - no image found for pet: {pet_name}")
            return jsonify({
                "status": "skipped",
                "message": f"No image found for pet: {pet_name or 'Unknown'}"
            }), 200
        
        thumbnail_url = PET_IMAGES[pet_name]
        
        webhook_data = {
            "embeds": [{
                "title": data.get("title", "Pet Stolen"),
                "description": data.get("description", ""),
                "color": data.get("color", 16776960),
                "fields": data.get("fields", []),
                "footer": data.get("footer", {}),
                "timestamp": data.get("timestamp", ""),
                "thumbnail": { "url": thumbnail_url }
            }]
        }
        
        response = requests.post(THEFT_WEBHOOK_URL, json=webhook_data, timeout=10)
        
        if response.status_code in [200, 204]:
            logging.info(f"Theft notification sent: {data.get('description', 'Unknown')} (Pet: {pet_name})")
            return jsonify({"status": "success", "message": "Theft notification sent"})
        else:
            logging.error(f"Failed to send theft notification: {response.status_code}")
            return jsonify({"error": "Failed to send webhook"}), 500
            
    except Exception as e:
        logging.error(f"Theft notification error: {e}")
        return jsonify({"error": str(e)}), 500

GAME_ID = os.getenv("GAME_ID", "109983668079237")
BASE_URL = f"https://games.roblox.com/v1/games/{GAME_ID}/servers/Public"

MAIN_API_URL = os.getenv("MAIN_API_URL", "https://worker-production-2f05.up.railway.app") + "/add-pool"
MAIN_API_STATUS = os.getenv("MAIN_API_URL", "https://worker-production-2f05.up.railway.app") + "/status"

REQUEST_TIMEOUT = 20
PAGE_DELAY = 0.05
ID_TTL = 60 * 5  
MAX_SERVER_AGE = 60 * 8  
BATCH_MIN = 300
BATCH_MAX = 800
MAX_QUEUE_SIZE = 15000
TARGET_MAIN_API = 999999
TARGET_MIN = 3
TARGET_MAX = 7
CACHE_CLEAR_INTERVAL = 600  

# Hardcoded proxy configuration
PROXY_HOST = os.getenv("PROXY_HOST", "na.nettify.xyz:8080")
PROXY_AUTH = os.getenv("PROXY_AUTH", "ymb2k0a4z70e:l3sf295s310e")

def get_proxy_dict():
    """Get proxy dict for requests - supports environment variable fallbacks"""
    return {
        'http': f'http://{PROXY_AUTH}@{PROXY_HOST}',
        'https': f'http://{PROXY_AUTH}@{PROXY_HOST}'
    }

FETCH_PATTERN = ["Asc", "Desc", "Asc"]

priority_queue = deque(maxlen=MAX_QUEUE_SIZE)
server_queue = deque(maxlen=MAX_QUEUE_SIZE)
sent_ids = {}
server_cache = set()
server_ages = {}  
blacklisted_servers = set()  

lock = threading.Lock()
stats = {"fetched": 0, "sent": 0, "duplicates": 0, "errors": 0, "ratelimits": 0, "blacklisted": 0}

# Global flag to track proxy validity across background threads
proxy_functional = True

class ProxyWatchdog(threading.Thread):
    """Monitors consecutive errors across operations to trigger container termination"""
    def __init__(self, failure_threshold=25):
        super().__init__()
        self.daemon = True
        self.name = "watchdog"
        self.failure_threshold = failure_threshold
        self.consecutive_failures = 0

    def increment_failure(self):
        self.consecutive_failures += 1
        if self.consecutive_failures >= self.failure_threshold:
            logging.critical(f"[WATCHDOG] Outage detected! {self.consecutive_failures} failures. Shutting down process.")
            sys.exit(1)

    def reset(self):
        self.consecutive_failures = 0

watchdog = ProxyWatchdog()
watchdog.start()

@app.route("/report-failure", methods=["POST"])
def report_failure():
    """Allow bots to report failed servers"""
    try:
        data = request.get_json()
        job_id = data.get("job_id")
        if not job_id:
            return jsonify({"error": "job_id required"}), 400
        
        with lock:
            blacklisted_servers.add(job_id)
            server_cache.discard(job_id)
            if job_id in sent_ids: del sent_ids[job_id]
            if job_id in server_ages: del server_ages[job_id]
            stats["blacklisted"] += 1
        
        logging.info(f"[BLACKLIST] Server reported as failed: {job_id}")
        return jsonify({"status": "blacklisted", "job_id": job_id})
    except Exception as e:
        logging.error(f"Report failure error: {e}")
        return jsonify({"error": str(e)}), 500

def test_proxy():
    """Test the hardcoded proxy"""
    global proxy_functional
    try:
        r = requests.get(
            "https://api.ipify.org",
            proxies=get_proxy_dict(),
            timeout=8,
            verify=False
        )
        if r.status_code == 200:
            ip = r.text.strip()
            logging.info(f"[Proxy] OK - IP: {ip}")
            proxy_functional = True
            return True
    except Exception as e:
        logging.error(f"[Proxy] Health test failed: {e}")
    proxy_functional = False
    return False

def check_main_api_size():
    try:
        r = requests.get(MAIN_API_STATUS, timeout=3)
        if r.status_code == 200:
            return r.json().get("cache_jobs", 0)
    except:
        pass
    return 0

def cleanup_sent_ids():
    now = time.time()
    expired = [job for job, t in sent_ids.items() if t <= now]
    for job in expired:
        del sent_ids[job]
        server_cache.discard(job)
    
    old_servers = [job for job, age in server_ages.items() if now - age > MAX_SERVER_AGE]
    for job in old_servers:
        del server_ages[job]
        server_cache.discard(job)
        if job in sent_ids:
            del sent_ids[job]

def cache_clearer():
    while True:
        time.sleep(CACHE_CLEAR_INTERVAL)
        with lock:
            now = time.time()
            to_remove = set()
            for job in server_cache:
                if job in blacklisted_servers or (job in server_ages and now - server_ages[job] > MAX_SERVER_AGE):
                    to_remove.add(job)
            for job in to_remove:
                server_cache.discard(job)
                if job in server_ages: del server_ages[job]
            logging.info(f"Cache cleaned: removed {len(to_remove)} old/blacklisted entries")

def fetch_servers(sort_order):
    cursor = None
    consecutive_errors = 0
    
    while True:
        main_api_size = check_main_api_size()
        if main_api_size >= TARGET_MAIN_API:
            time.sleep(5)
            continue
        
        try:
            url = f"{BASE_URL}?sortOrder={sort_order}&limit=100"
            if cursor:
                url += f"&cursor={cursor}"
            
            r = requests.get(
                url,
                proxies=get_proxy_dict(),
                timeout=REQUEST_TIMEOUT,
                verify=False
            )
            
            if r.status_code == 429:
                stats["ratelimits"] += 1
                retry_after = int(r.headers.get("Retry-After", 5))
                logging.info(f"[Proxy] Rate limited, waiting {retry_after}s...")
                time.sleep(min(retry_after, 3))
                continue
            
            if r.status_code != 200:
                consecutive_errors += 1
                watchdog.increment_failure()
                if consecutive_errors > 5:
                    cursor = None
                    consecutive_errors = 0
                time.sleep(0.5)
                continue
            
            watchdog.reset()
            consecutive_errors = 0
            data = r.json().get("data", [])
            priority = []
            current_time = time.time()
            
            for s in data:
                if "id" not in s or "playing" not in s: continue
                jid = s["id"]
                players = s["playing"]
                
                if not (TARGET_MIN <= players <= TARGET_MAX): continue
                
                with lock:
                    if jid in blacklisted_servers: continue
                    if jid in server_cache:
                        stats["duplicates"] += 1
                        continue
                    server_cache.add(jid)
                    server_ages[jid] = current_time
                priority.append(jid)
            
            with lock:
                cleanup_sent_ids()
                priority_queue.extend(priority)
                stats["fetched"] += len(priority)
            
            if priority:
                logging.info(f"[Proxy] [{sort_order}] Fetched {len(priority)} | Queue: {len(priority_queue)}")
            
            cursor = r.json().get("nextPageCursor", None)
            if not cursor:
                cursor = None
                time.sleep(0.5)
            
        except (requests.exceptions.Timeout, requests.exceptions.ProxyError):
            stats["errors"] += 1
            watchdog.increment_failure()
            time.sleep(1)
        except Exception as e:
            stats["errors"] += 1
            watchdog.increment_failure()
            time.sleep(1)
        
        time.sleep(PAGE_DELAY)

def sender():
    while True:
        batch = []
        target = random.randint(BATCH_MIN, BATCH_MAX)
        current_time = time.time()
        
        with lock:
            cleanup_sent_ids()
            while priority_queue and len(batch) < target:
                jid = priority_queue.popleft()
                if jid in blacklisted_servers: continue
                if jid in server_ages and current_time - server_ages[jid] > MAX_SERVER_AGE: continue
                sent_ids[jid] = time.time() + ID_TTL
                batch.append(jid)
            
            while server_queue and len(batch) < target:
                jid = server_queue.popleft()
                if jid in blacklisted_servers: continue
                if jid in server_ages and current_time - server_ages[jid] > MAX_SERVER_AGE: continue
                sent_ids[jid] = time.time() + ID_TTL
                batch.append(jid)
        
        if batch:
            try:
                r = requests.post(MAIN_API_URL, json={"servers": batch}, timeout=REQUEST_TIMEOUT)
                if r.status_code == 200:
                    with lock:
                        stats["sent"] += len(batch)
                    logging.info(f"SENT {len(batch)} -> Queue: {len(priority_queue)}")
            except Exception as e:
                logging.error(f"Send error: {e}")
        
        time.sleep(0.04)

def start_threads():
    test_proxy()
    threading.Thread(target=cache_clearer, daemon=True, name="cache-clearer").start()
    
    for sort_order in FETCH_PATTERN:
        for j in range(3):
            threading.Thread(target=fetch_servers, args=(sort_order,), daemon=True, name=f"fetch-{sort_order}-{j}").start()
            time.sleep(0.05)
    
    for i in range(4):
        threading.Thread(target=sender, daemon=True, name=f"sender-{i}").start()
    
    logging.info("Mini API started")

start_threads()

@app.route("/")
def home():
    main_api_size = check_main_api_size()
    with lock:
        cleanup_sent_ids()
        elapsed = time.time() - start_time
        rate = stats['sent'] / elapsed if elapsed > 0 else 0
        return jsonify({
            "priority": len(priority_queue),
            "normal": len(server_queue),
            "sent_pending": len(sent_ids),
            "cache_size": len(server_cache),
            "blacklisted": len(blacklisted_servers),
            "stats": stats,
            "main_api_size": main_api_size,
            "rate": f"{rate:.1f} servers/sec",
            "proxy": PROXY_HOST,
            "proxy_up": proxy_functional,
            "max_server_age": MAX_SERVER_AGE
        })

@app.route("/test-proxies")
def test_proxies_endpoint():
    if test_proxy():
        return jsonify({"proxy": PROXY_HOST, "status": "ok"})
    return jsonify({"proxy": PROXY_HOST, "status": "failed"}), 500

@app.route("/health")
def health():
    """Reflect proxy health directly to container orchestration engines"""
    if not proxy_functional:
        return jsonify({"status": "unhealthy", "reason": "Proxy connection offline"}), 500
    return jsonify({"status": "healthy", "queue": len(priority_queue) + len(server_queue)}), 200

@app.route("/routes")
def list_routes():
    return jsonify({"routes": [{"endpoint": r.endpoint, "methods": list(r.methods), "path": r.rule} for r in app.url_map.iter_rules()]})

start_time = time.time()

if __name__ == "__main__":
    port = int(os.environ.get("PORT1", 8962))
    app.run("0.0.0.0", port, threaded=True)
