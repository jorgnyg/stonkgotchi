Kjøre docker container med api på rpi-stor  
Kjøre request fra rpi-liten til rpi-stor 
Rendre svg paths til display (qr kode)   
Refreshe qr kode på display så lenge den endrer seg  
Når login er ok, bruk token videre i requests

Issue: QR-kode hos nordnet endrer seg hyppig. Kan bli delay mellom polling og visning osv. 

docker build -t fastapi-playwright-scraper .

docker run -p 8000:8000 fastapi-playwright-scraper

curl http://192.168.1.152:8000/get-auth-status