import os
import requests
import logging
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Configuration
CONFIG = {
    "VAL_API_KEY": os.environ.get("VAL_API_KEY"),
    "VAL_REGION": os.environ.get("VAL_REGION", "eu"),
    "VAL_NAME": os.environ.get("VAL_NAME", "Freekill"),
    "VAL_TAG": os.environ.get("VAL_TAG", "omen"),
    "DISCORD_BOT_TOKEN": os.environ.get("DISCORD_BOT_TOKEN"),
    "DISCORD_USER_ID": os.environ.get("DISCORD_USER_ID"),
    "DISCORD_APP_ID": os.environ.get("DISCORD_APP_ID")
}

def fetch_live_rank_icon_url(rank_name: str) -> str:
    # Use a shorter fallback path if possible
    fallback = "https://media.valorant-api.com/competitivetiers/564d8e28-c226-3180-6285-e48a390db8b1/0/largeicon.png"
    try:
        resp = requests.get("https://valorant-api.com/v1/competitivetiers", timeout=10)
        if resp.status_code == 200:
            for tier_group in resp.json().get("data", []):
                for tier in tier_group.get("tiers", []):
                    if tier.get("tierName", "").lower() == rank_name.strip().lower():
                        return tier.get("largeIcon")
    except: pass
    return fallback

def update_discord_widget():
    base_url = "https://api.henrikdev.xyz/valorant"
    headers = {"Authorization": CONFIG["VAL_API_KEY"]} if CONFIG["VAL_API_KEY"] else {}
    
    try:
        mmr_resp = requests.get(f"{base_url}/v2/mmr/{CONFIG['VAL_REGION']}/{CONFIG['VAL_NAME']}/{CONFIG['VAL_TAG']}", headers=headers, timeout=10)
        data = mmr_resp.json().get("data", {})
        rank = data.get("current_data", {}).get("currenttierpatched", "Silver 3")
        rr = str(data.get("current_data", {}).get("ranking_in_tier", "0"))
        peak = data.get("highest_rank", {}).get("patched_tier", rank)
        level = "198" # Static if API fails
    except Exception as e:
        logger.error(f"API Error: {e}")
        return

    # Payload: We keep the values very short to satisfy Discord 100 char limit
    # We remove "url": prefix inside the object if the widget supports direct string
    payload = {
        "data": {
            "dynamic": [
                {"type": 1, "name": "rank_name", "value": rank[:50]},
                {"type": 1, "name": "rank_rr", "value": rr[:50]},
                {"type": 1, "name": "rank_peak", "value": peak[:50]},
                {"type": 1, "name": "level", "value": level[:50]},
                {"type": 3, "name": "rank_icon", "value": {"url": fetch_live_rank_icon_url(rank)[:80]}},
                {"type": 3, "name": "peak_icon", "value": {"url": fetch_live_rank_icon_url(peak)[:80]}}
            ]
        }
    }
    
    url = f"https://discord.com/api/v9/applications/{CONFIG['DISCORD_APP_ID']}/users/{CONFIG['DISCORD_USER_ID']}/identities/0/profile"
    headers = {"Authorization": f"Bot {CONFIG['DISCORD_BOT_TOKEN']}", "Content-Type": "application/json"}
    
    response = requests.patch(url, headers=headers, json=payload, timeout=10)
    if response.status_code in [200, 204]:
        logger.info("Sync Successful!")
    else:
        logger.error(f"Error {response.status_code}: {response.text}")

if __name__ == '__main__':
    update_discord_widget()
