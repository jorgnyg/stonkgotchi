from typing import Dict, List, Optional, Union
import requests
from datetime import datetime
import json

class NordnetClient:
    def __init__(self, next_token: str, ntag: str):
        self.base_urls = {
            "api": "https://api.prod.nntech.io", #
            "auth": "https://www.nordnet.no"  # https://www.nordnet.no/api/2/authentication/jwt/refresh
        }
        self.next_token = next_token
        self.ntag = ntag
        self._bearer_token = None
    
    def init_auth():
        # 1. på en måte åpne nordnet login siden
        # 2. prøve å fange responsen når man scanner qr-koden
        # 3. prøve å fange next_token (fra cookie) og ntag (fra login response?)
        # optional: fange qr koden som svg og vise den et annet sted/på eink display
        pass

    def _login(self):
        # https://www.nordnet.no/api/2/login
        cookies = {"NEXT": self.next_token, "NNX_SESSION_ID": self.next_token} 
        res = self._make_request("GET", "/api/2/login", base_url_key="auth", headers=self._get_auth_headers(), cookies=cookies)
        print(res)
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get headers specifically for authentication requests."""
        return {
            "Accept": "*/*",
            "Client-Id": "NEXT",
            "Content-Type": "application/json",
            "Ntag": self.ntag,
            "Origin": "https://www.nordnet.no",
            "Referer": "https://www.nordnet.no",
            "Priority": "u=1, i",
            "Sec-Ch-Ua": "\"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"138\", \"Microsoft Edge\";v=\"138\"",
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": "\"Windows\"",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0"
        }

    def _refresh_bearer_token(self):
        # Simulate token refresh
        print("Refreshing access token to aquire new bearer token")
        
        # Use auth-specific headers and cookies for token refresh
        cookies = {"NEXT": self.next_token, "NNX_SESSION_ID": self.next_token} # flytte til egen _get_api_cookies elns
        headers = self._get_auth_headers()
        res = self._make_request(
            "POST", 
            "/api/2/authentication/jwt/refresh", 
            base_url_key="auth",
            cookies=cookies,
            headers=headers
        )

        def log_result(res):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] {res}\n"

            with open("auth_log.txt", "a", encoding="utf-8") as f:
                f.write(log_entry)

            print("📝 Log entry added to auth_log.txt")

        log_result(res)
        self._bearer_token = res.get("jwt")
    
    def _get_api_headers(self) -> Dict[str, str]:
        """Get headers specifically for API requests."""
        return {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9,en-GB;q=0.8",
            "Authorization": f"Bearer {self._bearer_token}",
            "Origin": "https://www.nordnet.no",
            "Priority": "u=1, i",
            "Referer": "https://www.nordnet.no/"
        }

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        cookies: Optional[Dict] = None,
        base_url_key: str = "api",
        headers: Optional[Dict[str, str]] = None
    ) -> Dict:
        """
        Make an authenticated request to the API.
       
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Optional query parameters
            cookies: Optional cookies
            base_url_key: Which base URL to use ('api' or 'auth')
            headers: Optional custom headers
           
        Returns:
            Dict: Response data
        """
        base_url = self.base_urls.get(base_url_key, self.base_urls["api"])
        url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"

        try:
            response = requests.request(
                method=method.upper(),
                url=url,
                headers=headers,
                params=params,
                cookies=cookies
            )
            response.raise_for_status()
            return response.json()
           
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"API request failed: {str(e)}")

    def get_historical_returns(self):
        # Uses default 'api' base URL
        endpoint = "/holdings/historical-returns/v1/own-capital/graph?accids=1&fromDate=2025-08-01&toDate=2025-08-02&startFromZero=false"
        self._refresh_bearer_token()

        headers = self._get_api_headers()
        response = self._make_request("GET", endpoint, headers=headers)
        print(response)
        return response
    

if __name__ == "__main__":
    client = NordnetClient(next_token="cc848b60-9026-461b-bd06-d40bcab3bdb5", ntag="f5186571-3825-44bd-8133-983467f9cb8a")

    client.get_historical_returns()