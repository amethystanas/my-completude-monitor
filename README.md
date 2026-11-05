# Completude monitor

Checks Completude every 5 minutes for new tutoring offers near you and emails you when one appears. Runs for free on GitHub Actions.

## 1. Find your search settings

1. Log in at https://professeur.completude.com in Chrome or Firefox.
2. Open the developer tools (F12) and go to the **Network** tab.
3. Open the page where you search for students on the map.
4. In the Network list, click the request named **`search`** (URL ends with `cap/search`) and open its **Payload** / **Request** tab.
5. Copy these values into `config.py`:
   - `SessionRecherche.IdAdresse` → `ID_ADRESSE`
   - the four `MapBox` coordinates → `MAP_BOX`
   - the other `SessionRecherche` fields → `SESSION_RECHERCHE`

## 2. Get a Gmail app password

Your normal Gmail password won't work for this.
1. Turn on 2-Step Verification on your Google account.
2. Go to https://myaccount.google.com/apppasswords and create an app password.
3. Copy the 16-character code.

## 3. Test locally (optional)

```bash
pip install -r requirements.txt
cp .env.example .env      # then fill in .env
python monitor.py
```

The first run records the offers that already exist without emailing you. To test the email, delete `seen_offers.json`, set `SILENT_FIRST_RUN = False`, and run it again.

## 4. Put it on GitHub

1. Create a new repository and push these files.
2. Go to **Settings → Secrets and variables → Actions → New repository secret** and add:
   `COMPLETUDE_USERNAME`, `COMPLETUDE_PASSWORD`, `SMTP_USERNAME`, `SMTP_APP_PASSWORD`, `EMAIL_TO`
3. Open the **Actions** tab, enable workflows, then run **Completude Monitor → Run workflow** once to check that it works.

## Notes

- Your passwords stay in GitHub Secrets. The login token stays in memory and is never committed.
- In a **public** repo, Actions minutes are free and unlimited. In a **private** repo you get about 2,000 minutes a month, which won't cover a check every 5 minutes. To stay within that, change the cron to `'*/30 * * * *'`.
- `config.py` (the map box) gives your rough area. If that bothers you, use a private repo.
- GitHub often runs scheduled jobs a few minutes late. That's normal.
