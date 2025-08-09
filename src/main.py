
from nordnet_client import NordnetClient
from datetime import datetime
from time import sleep
from poll_auth import poll_auth_status

if __name__ == "__main__":
    # ikke gi tokens og sånt direkte her, men heller starte init_auth som metode første gang man lager objektet?
    result = poll_auth_status() # Denne erstattes med api requests osv til fast-api

    client = NordnetClient(next_token=result.get("NEXT"), ntag=result.get("ntag")) # Generert ca. 8 --- kan legge til nnx_session_id selv om den ser ut il å være lik next_token
    # add more logging with the logging package. info, error etcc.

    i = 0
    while True:
        i += 1

        now = datetime.now()
        formatted = now.strftime("%Y-%m-%d %H:%M:%S")
        print(f"Iteration {i} - Trying to refresh token at {formatted}")

        client._refresh_bearer_token()

        sleep(300) # refresh every 5 min