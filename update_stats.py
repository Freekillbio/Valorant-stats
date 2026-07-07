import os
import requests
import logging
import json

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Configuration: Loaded via environment variables
CONFIG = {
    "VAL_API_KEY": os.environ.get("VAL_API_KEY"),
    "VAL_REGION": os.environ.get("VAL_REGION", "eu"),
    "VAL_NAME": os.environ.get("VAL_NAME", "Freekill"),
    "VAL_TAG": os.environ.get("VAL_TAG", "omen"),
    "DISCORD_BOT_TOKEN": os.environ.get("DISCORD_BOT_TOKEN"),
    "DISCORD_USER_ID": os.environ.get("DISCORD_USER_ID"),
    "DISCORD_APP_ID": os.environ.get("DISCORD_APP_ID")
}

def safe_str(value, length=100):
    """Ensures strings are within Discord's API limits."""
    return str(value)[:length]

def fetch_live_rank_icon_url(rank_name: str) -> str:
    fallback = "https://media.valorant-api.com/competitivetiers/564d8e28-c226-3180-6285-e48a390db8b1/0/largeicon.png"
    try:
        resp = requests.get("https://valorant-api.com/v1/competitivetiers", timeout=10)
        if resp.status_code == 200:
            for tier_group in resp.json().get("data", []):
                for tier in tier_group.get("tiers", []):
                    if tier.get("tierName", "").lower() == rank_name.strip().lower():
                        return tier.get("largeIcon")
    except Exception as e:
        logger.error(f"Icon fetch error: {e}")
    return fallback

def update_discord_widget():
    base_url = "https://api.henrikdev.xyz/valorant"
    headers = {"Authorization": CONFIG["VAL_API_KEY"]} if CONFIG["VAL_API_KEY"] else {}
    
    try:
        # Fetch MMR
        mmr_resp = requests.get(f"{base_url}/v2/mmr/{CONFIG['VAL_REGION']}/{CONFIG['VAL_NAME']}/{CONFIG['VAL_TAG']}", headers=headers, timeout=10)
        if mmr_resp.status_code != 200:
            logger.warning(f"MMR API returned status code: {mmr_resp.status_code}. Using runtime cache.")
        
        mmr_payload = mmr_resp.json().get("data", {})
        current_data = mmr_payload.get("current_data", {})
        
        rank = current_data.get("currenttierpatched", "Silver 3")
        rr = str(current_data.get("ranking_in_tier", "0"))
        
        highest_rank_obj = mmr_payload.get("highest_rank", {})
        peak = highest_rank_obj.get("patched_tier", rank) if highest_rank_obj else rank
        
        acc_resp = requests.get(f"{base_url}/v1/account/{CONFIG['VAL_NAME']}/{CONFIG['VAL_TAG']}", headers=headers, timeout=10)
        level = str(acc_resp.json().get("data", {}).get("account_level", "0"))
        
    except Exception as e:
        logger.error(f"API failure: {e}")
        return

    # Payload Construction
    payload = {
        "data": {
            "dynamic": [
                {"type": 1, "name": "rank_name", "value": safe_str(rank)},
                {"type": 1, "name": "rank_rr", "value": safe_str(rr)},
                {"type": 1, "name": "rank_peak", "value": safe_str(peak)},
                {"type": 1, "name": "level", "value": safe_str(level)},
                {"type": 3, "name": "rank_icon", "value": {"url": safe_str(fetch_live_rank_icon_url(rank))}},
                {"type": 3, "name": "peak_icon", "value": {"url": safe_str(fetch_live_rank_icon_url(peak))}}
            ]
        }
    }
    
    # Log payload for debugging
    logger.info(f"DEBUG PAYLOAD: {json.dumps(payload, indent=2)}")
    
    url = f"https://discord.com/api/v9/applications/{CONFIG['DISCORD_APP_ID']}/users/{CONFIG['DISCORD_USER_ID']}/identities/0/profile"
    headers = {"Authorization": f"Bot {CONFIG['DISCORD_BOT_TOKEN']}", "Content-Type": "application/json"}
    
    response = requests.patch(url, headers=headers, json=payload, timeout=10)
    if response.status_code in [200, 204]:
        logger.info("Successfully synced to Discord!")
    else:
        logger.error(f"Discord API error {response.status_code}: {response.text}")

if __name__ == '__main__':
    update_discord_widget()
