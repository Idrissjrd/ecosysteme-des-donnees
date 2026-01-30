import requests


VAMPIRE_GROUP_IP = "192.168.1.45"  
VAMPIRE_PORT = "16040"             

# Construct the full URL
RIVAL_API_URL = f"http://{VAMPIRE_GROUP_IP}:{VAMPIRE_PORT}/taille"

def get_vampire_size_from_api(fallback_value=0.0):
    """
    Fetches the vampire population size from the Group E API.
    Returns: (size, is_connected)
    """
    try:
        response = requests.get(RIVAL_API_URL, timeout=2)
        
        if response.status_code == 200:
            data = response.json()
            # Success! Return the value AND True
            return float(data.get("taille", 0.0)), True
            
    except Exception as e:
        pass

    return float(fallback_value), False