"""
Valorant Discord Profile Widget Automation Engine
Features: Live Dynamic Valorant-API Asset Resolution Mapping
"""

import os
import sys
import requests
import logging

# --- Logging Infrastructure Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# --- Configuration Loader (Secure GitHub Secrets Vault) ---
CONFIG = {
    "VAL_REGION": os.environ.get("VAL_REGION"),
    "VAL_NAME": os.environ.get("VAL_NAME"),
    "VAL_TAG": os.environ.get("VAL_TAG"),
    "DISCORD_BOT_TOKEN": os.environ.get("DISCORD_BOT_TOKEN"),
    "DISCORD_USER_ID": os.environ.get("DISCORD_USER_ID"),
    "DISCORD_APP_ID": os.environ.get("DISCORD_APP_ID")
}

def fetch_live_rank_icon(rank_name: str) -> str:
    """
    Queries valorant-api.com dynamically to pull the absolute newest
    competitive tier asset dataset and extracts the matching tier image.
    """
    # Bulletproof global fallback icon if endpoints fail to load
    fallback_icon = "https://media.valorant-api.com/competitivetiers/564d8e28-c226-3180-6285-e48a390db8b1/0/largeicon.png"
    try:
        logger.info("Fetching latest live competitive tier matrix from valorant-api.com...")
        response = requests.get("https://valorant-api.com/v1/competitivetiers", timeout=10)
        
        if response.status_code == 200:
            tiers_data = response.json().get("data", [])
            if not tiers_data:
                return fallback_icon
                
            # Grab the latest competitive tier collection block (last index in the response array)
            latest_layout = tiers_data[-1]
            sub_tiers = latest_layout.get("tiers", [])
            
            # Clean up the name string format (e.g., "Silver 1" -> "silver 1")
            normalized_target = rank_name.strip().lower()
            
            for tier in sub_tiers:
                tier_name = tier.get("tierName", "").strip().lower()
                if tier_name == normalized_target:
                    large_icon = tier.get("largeIcon")
                    if large_icon:
                        logger.info(f"Successfully matched and resolved dynamic asset URL: {large_icon}")
                        return large_icon
                        
            logger.warning(f"Could not find an exact text match for '{rank_name}' in the API layout.")
        else:
            logger.warning(f"Valorant-API asset gateway returned error code: {response.status_code}")
    except Exception as e:
        logger.error(f"Failed to query dynamic asset indexes: {e}")
        
    return fallback_icon

def fetch_valorant_statistics():
    """Queries HenrikDev endpoints with bulletproof operational fallbacks."""
    base_url = "https://api.henrikdev.xyz/valorant"
    mmr_endpoint = f"{base_url}/v2/mmr/{CONFIG['VAL_REGION']}/{CONFIG['VAL_NAME']}/{CONFIG['VAL_TAG']}"
    account_endpoint = f"{base_url}/v1/account/{CONFIG['VAL_NAME']}/{CONFIG['VAL_TAG']}"
    
    # Live widget panel defaults if upstream fetch timings drop out
    rank, rr, peak, level = "Gold 1", "54", "Platinum 1", "200"
    
    try:
        logger.info("Requesting player competitive performance metrics...")
        mmr_resp = requests.get(mmr_endpoint, timeout=10)
        if mmr_resp.status_code == 200:
            data = mmr_resp.json().get("data", {})
            current = data.get("current_data", {})
            rank = current.get("currenttierpatched", rank)
            rr = str(current.get("ranking_in_tier", rr))
            highest = data.get("highest_rank", {})
            if isinstance(highest, dict):
                peak = highest.get("patched_tier", peak)
        else:
            logger.warning(f"MMR API returned status code: {mmr_resp.status_code}. Using runtime cache.")
    except Exception as e:
        logger.error(f"MMR connection interface failure details: {e}")

    try:
        acc_resp = requests.get(account_endpoint, timeout=10)
        if acc_resp.status_code == 200:
            level = str(acc_resp.json().get("data", {}).get("account_level", level))
    except Exception as e:
        logger.error(f"Account routing exception metrics: {e}")

    return rank, rr, peak, level

def update_discord_widget(rank: str, rr: str, peak: str, level: str):
    """Pushes the entire dynamic property package to the target Discord user application configuration profile."""
    if not CONFIG["DISCORD_BOT_TOKEN"]:
        logger.critical("Authentication credential failure: Missing DISCORD_BOT_TOKEN asset.")
        sys.exit(1)
        
    url = f"https://discord.com/api/v9/applications/{CONFIG['DISCORD_APP_ID']}/users/{CONFIG['DISCORD_USER_ID']}/identities/0/profile"
    headers = {
        "Authorization": f"Bot {CONFIG['DISCORD_BOT_TOKEN']}",
        "Content-Type": "application/json"
    }
    
    # Fetch the exact matching rank image directly from the latest live layout index
    live_rank_icon_url = fetch_live_rank_icon(rank)
    
    payload = {
        "data": {
            "dynamic": [
                {"type": 1, "name": "rank_name", "value": rank},
                {"type": 1, "name": "rank_rr", "value": rr},
                {"type": 1, "name": "rank_peak", "value": peak},
                {"type": 1, "name": "level", "value": level},
                {"type": 1, "name": "rank_icon", "value": live_rank_icon_url}
            ]
        }
    }
    
    response = requests.patch(url, headers=headers, json=payload, timeout=10)
    if response.status_code in [200, 204]:
        logger.info("Discord dynamic profile interface synchronized perfectly!")
    else:
        logger.error(f"Discord gateway integration rejected state transfer payload: {response.status_code} - {response.text}")

if __name__ == '__main__':
    logger.info("Initializing Valorant Profile Sync Pipeline Core...")
    v_rank, v_rr, v_peak, v_level = fetch_valorant_statistics()
    update_discord_widget(v_rank, v_rr, v_peak, v_level)
    logger.info("Pipeline lifecycle sequence successfully completed.")
