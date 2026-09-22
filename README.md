# Spotify Sorter

Ett kommandoradsverktyg som sorterar dina egna Spotify-spellistor efter artist eller releasedatum, eller slumpar ordningen. Originalet kan sorteras om utan att först tömmas, alternativt kan verktyget skapa en privat kopia.

## Förutsättningar

- Python 3.9 eller senare
- Ett Spotify-konto
- En app i [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)

## Installation

Klona repot och gå till projektmappen:

```bash
git clone https://github.com/GUBJ1/spotify-sorter.git
cd spotify-sorter
```

Skapa sedan en virtuell Python-miljö och installera beroendena med instruktionerna för terminalen du använder.

### Windows – Git Bash

```bash
py -m venv .venv
source .venv/Scripts/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

### Windows – PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

### macOS och Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

När miljön är aktiverad brukar terminalprompten börja med `(.venv)`. Du kan även kontrollera vilken Python som används:

```bash
python -c "import sys; print(sys.executable)"
```

Sökvägen som skrivs ut ska innehålla projektets `.venv`-mapp.

## Spotify-konfiguration

1. Öppna `.env` och ersätt `your_spotify_client_id` och `your_spotify_client_secret` med uppgifterna från din Spotify-app.
2. Lägg till `http://127.0.0.1:8888/callback` som Redirect URI i Spotify Developer Dashboard. Adressen måste exakt matcha `REDIRECT_URI` i `.env`.
3. Spara både Spotify-appens inställningar och `.env`.

Hemligheter i `.env` ska aldrig checkas in i Git. Filen ignoreras redan av repots `.gitignore`.

## Kör programmet

Med den virtuella miljön aktiverad:

```bash
python spotify_sorter.py
```

Första gången öppnas Spotifys inloggning och du får godkänna appens behörigheter.

## Tester

```bash
python -m unittest -v
```

## Vanligt fel i Git Bash

Kommandot `.\.venv\Scripts\Activate.ps1` är PowerShell-syntax och fungerar inte i Git Bash. Använd i stället:

```bash
source .venv/Scripts/activate
```
