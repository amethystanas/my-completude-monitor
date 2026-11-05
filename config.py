# -----------------------------------------------------------------------------
# Search settings — NOT secrets. Passwords go in GitHub Secrets / .env only.
# Fill these in from YOUR own request (see README, "Find your search settings").
# -----------------------------------------------------------------------------

# Your address ID on Completude (from the "IdAdresse" field of the search request)
ID_ADRESSE = 2215582  # <-- replace

# The map area to search (from the "MapBox" field of the search request)
MAP_BOX = {
    "IdSessionRecherche": 0,
    "NordOuestLatitude": 45.27550163853575,   # <-- replace
    "NordOuestLongitude": -1.2194923218221776,  # <-- replace
    "SudEstLatitude": 44.37718636146425,      # <-- replace
    "SudEstLongitude": 0.04708432182217781,     # <-- replace
}

# Search filters (from the "SessionRecherche" field of the search request)
SESSION_RECHERCHE = {
    "Id": 0,
    "AvecChat": True,
    "AvecChien": True,
    "AvecVehicule": False,
    "DispoSemaine": True,
    "DispoVacance": True,
    "DispoWeekEnd": True,
}

# Only email offers at most this far from your address (km)
DISTANCE_THRESHOLD_KM = 6.0

# On the very first run, record existing offers without emailing them all
SILENT_FIRST_RUN = True

# Email server (Gmail by default)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465

# State file (committed back to the repo by the workflow)
STATE_FILE = "seen_offers.json"
