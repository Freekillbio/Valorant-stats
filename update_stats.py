import os
import requests

# --- CONFIGURATION (Loaded safely via GitHub Secrets) ---
VAL_API_KEY = os.environ.get("VAL_API_KEY")
VAL_REGION = os.environ.get("VAL_REGION")       
VAL_NAME = os.environ.get("VAL_NAME")    
VAL_TAG = os.environ.get("VAL_TAG")          

DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
DISCORD_USER_ID = os.environ.get("DISCORD_USER_ID")       
DISCORD_APP_ID = os.environ.get("DISCORD_APP_ID") 
# -----------------------------------------------------

def get_valorant_data():
    headers = {"Authorization": VAL_API_KEY}
    mmr_url = f"https://api.henrikdev.xyz/valorant/v2/mmr/{VAL_REGION}/{VAL_NAME}/{VAL_TAG}"
    account_url = f"https://api.henrikdev.xyz/valorant/v1/account/{VAL_NAME}/{VAL_TAG}"
    
    rank, rr, peak, level = None, None, None, None
    try:
        mmr_resp = requests.get(mmr_url, headers=headers)
        if mmr_resp.status_code == 200:
            mmr_payload = mmr_resp.json().get("data", {})
            current_data = mmr_payload.get("current_data", {})
            rank = current_data.get("currenttierpatched", "Unknown")
            rr = str(current_data.get("ranking_in_tier", "0"))
            
            highest_rank_obj = mmr_payload.get("highest_rank", {})
            if highest_rank_obj and isinstance(highest_rank_obj, dict):
                peak = highest_rank_obj.get("patched_tier", rank)
            else:
                peak = rank 
            
        acc_resp = requests.get(account_url, headers=headers)
        if acc_resp.status_code == 200:
            level = str(acc_resp.json().get("data", {}).get("account_level", "0"))
            
        return rank, rr, peak, level
    except Exception as e:
        print(f"Error reading endpoints: {e}")
        return None, None, None, None

def update_discord_stats_grid(rank_name, rank_rr, rank_peak, level):
    url = f"https://discord.com/api/v9/applications/{DISCORD_APP_ID}/users/{DISCORD_USER_ID}/identities/0/profile"
    headers = {
        "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "DiscordBot (https://github.com/discord/discord-api-docs, 1.0.0)"
    }
    payload = {
        "username": f"{VAL_NAME}#{VAL_TAG}",
        "data": {
            "primary": {"rank_name": rank_name},
            "dynamic": [
                {"type": 1, "name": "rank_rr", "value": rank_rr},
                {"type": 1, "name": "rank_peak", "value": rank_peak},
                {"type": 1, "name": "level", "value": level}
            ]
        }
    }
    try:
        response = requests.patch(url, headers=headers, json=payload)
        if response.status_code in [200, 204]:
            print(f"Successfully updated profile widget to {rank_name}!")
        else:
            print(f"Discord API rejected payload with status code: {response.status_code}")
    except Exception as e:
        print(f"Discord connection failed: {e}")

if __name__ == '__main__':
    if not VAL_API_KEY or not DISCORD_BOT_TOKEN:
        print("Error: Missing hidden Environment Secrets on GitHub.")
    else:
        v_rank, v_rr, v_peak, v_level = get_valorant_data()
        if v_rank:
            update_discord_stats_grid(v_rank, v_rr, v_peak, v_level)
        else:
            print("Failed to pull live stats from Valorant API.")
