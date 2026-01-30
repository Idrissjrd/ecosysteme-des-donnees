import requests

# OPTION A: Standard Docker-for-Mac address
# This tells Docker: "Look at the computer hosting me"
RIVAL_API_URL = "http://host.docker.internal:16040/taille"

# OPTION B: If Option A fails, use your Mac's real IP address
# Run 'ipconfig getifaddr en0' in a terminal to find it (e.g., 192.168.1.15)
# RIVAL_API_URL = "http://192.168.1.15:16040/taille"

def get_vampire_size_from_api():
    """
    Fetches the vampire population size from the API.
    Returns: (size, is_connected)
    """
    try:
        # Timeout is short (1s) so the app doesn't freeze if offline
        response = requests.get(RIVAL_API_URL, timeout=1)
        
        if response.status_code == 200:
            data = response.json()
            # Success! Return the value AND True
            return float(data.get("taille", 0.0)), True
            
    except Exception as e:
        # If any error happens (timeout, refused), return 0 and False
        # print(f"Connection error: {e}") # Debug only
        pass

    # Fallback if offline
    return 0.0, False