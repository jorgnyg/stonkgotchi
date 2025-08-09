
from nordnet_client import NordnetClient
from datetime import datetime
from time import sleep
from poll_auth import poll_auth_status
from display import draw_kaomoji

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

        result = client.get_historical_returns()

            # Extract DAY_1 values
        day_1 = next((p for p in result['periodReturns'] if p['period'] == 'DAY_1'), None)

        if day_1:
            monetary_value = day_1['monetaryReturn']['value']
            percentage_return = day_1['percentageReturn']
            print(f"DAY_1 Monetary Value: {monetary_value} NOK")
            print(f"DAY_1 Percentage Return: {percentage_return}%")
        else:
            print("DAY_1 data not found.")
            continue
    
        draw_kaomoji(percentage_return)
        
        sleep(10) # refresh every 5 min