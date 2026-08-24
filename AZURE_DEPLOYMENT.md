# Deploying Flight Search to Azure

This guide takes your Streamlit flight search app (MySQL for data, MongoDB Atlas for SerpAPI caching, SerpAPI for live flight data) from "runs on localhost" to a live URL on Azure, with GitHub Actions auto-deploying every time you push to `main`.

## Architecture

- **Azure App Service (Linux, B1 Basic)** — hosts the Streamlit app, listening on port 8000 via `startup.sh`.
- **Azure Database for MySQL Flexible Server (Burstable B1ms)** — replaces your local MySQL for `airports`, `flights`, and `searches`.
- **MongoDB Atlas** — stays exactly where it is. Only its Network Access list changes, to allow the App Service's outbound IPs in.
- **SerpAPI** — unchanged, just needs its key set as an Azure app setting instead of a local `.env` file.
- **GitHub Actions** — builds and redeploys the app to App Service on every push to `main`.

Nothing in your application code needs to change — `config.py` already reads everything from environment variables, and Azure App Service injects app settings as environment variables automatically.

## Prerequisites

1. An Azure subscription ([free trial](https://azure.microsoft.com/free/) works fine for this).
2. [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli) installed, then run `az login`.
3. A GitHub account, with this project pushed to a GitHub repository (see Step 1 if it isn't yet).
4. Your existing MongoDB Atlas connection string and SerpAPI key (from your local `.env`).
5. A `mysql` command-line client installed locally, for the one-time schema import — or use [Azure Cloud Shell](https://shell.azure.com), which has it preinstalled.

## Step 1 — Push the project to GitHub

If this project isn't already a Git repository:

```bash
cd flightSearch_app
git init
git add .
git commit -m "Initial commit"
```

Check `.gitignore` includes `.env` before committing — you don't want your local secrets in the repo (the app settings on Azure will hold the real values instead).

Create an empty repository on GitHub, then:

```bash
git remote add origin https://github.com/<your-username>/<your-repo>.git
git branch -M main
git push -u origin main
```

## Step 2 — Provision Azure resources

Two files are included alongside this guide:

- `deploy/provision-azure.sh` — Azure CLI script that creates everything.
- `.github/workflows/azure-deploy.yml` — the CI/CD workflow.

Open `deploy/provision-azure.sh` and edit the block marked `EDIT ME` near the top:

- `LOCATION` — pick an Azure region close to you (e.g. `centralindia`, `eastus`).
- `MYSQL_ADMIN_PASSWORD` — set your own strong password (the script generates a placeholder one, but choose your own and store it in a password manager).
- `SERPAPI_KEY` — paste your SerpAPI key.
- `MONGO_URI` — paste your MongoDB Atlas connection string.

Then run it:

```bash
bash deploy/provision-azure.sh
```

This creates, in order: a resource group, a MySQL Flexible Server (Burstable B1ms — the cheapest paid tier), a Linux App Service plan (B1), the Web App itself, and sets all the app settings your `config.py` expects (`DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `SERPAPI_KEY`, `MONGO_URI`, `MONGO_DB_NAME`, `MONGO_APP_DB_NAME`, `MONGO_CACHE_TTL_SECONDS`). It finishes by printing the Web App name, its URL, the MySQL host, and the App Service's outbound IP addresses — copy all of these down.

Takes 5–10 minutes, mostly waiting on the MySQL server to provision.

## Step 3 — Import your MySQL schema and data

Using the MySQL host and admin credentials the script printed:

```bash
mysql -h <MYSQL_HOST> -u <MYSQL_ADMIN_USER> -p --ssl-mode=REQUIRED flight_db < azure_migration/flight_db_dump.sql
```

You'll be prompted for the password. If `mysql` isn't installed locally, open [Azure Cloud Shell](https://shell.azure.com) (it has the client preinstalled), upload `flight_db_dump.sql` there with the upload button, and run the same command.

Azure MySQL Flexible Server requires TLS by default; `--ssl-mode=REQUIRED` handles that from the CLI. Your app's `mysql-connector-python` connection in `db/connection.py` negotiates TLS automatically — no code change needed. If you ever see an SSL-related connection error from the app itself, the fix is adding `ssl_disabled=False` (default) or downloading Azure's CA bundle and passing `ssl_ca=<path>` in `DB_CONFIG`.

## Step 4 — Allow Azure to reach MongoDB Atlas

App Service on the B1 plan has a small, fixed set of possible outbound IPs (printed at the end of Step 2). In [Atlas](https://cloud.mongodb.com) → your project → **Network Access** → **Add IP Address**, add each of those IPs.

If you'd rather not manage a list (fine for a dev/test project, not recommended for production), add `0.0.0.0/0` once instead — this allows connections from anywhere, so make sure your Atlas database user has a strong, unique password.

## Step 5 — Connect GitHub Actions to Azure

Get the Web App's publish profile:

```bash
az webapp deployment list-publishing-profiles \
  --resource-group flightsearch-rg \
  --name <WEBAPP_NAME> \
  --xml
```

Copy the entire XML output. In your GitHub repo: **Settings → Secrets and variables → Actions → New repository secret**, name it `AZURE_WEBAPP_PUBLISH_PROFILE`, and paste the XML as the value.

Then open `.github/workflows/azure-deploy.yml` and set `AZURE_WEBAPP_NAME` to the exact Web App name from Step 2.

## Step 6 — Deploy

```bash
git add .github deploy AZURE_DEPLOYMENT.md
git commit -m "Add Azure deployment pipeline"
git push
```

The push triggers the workflow (check the **Actions** tab on GitHub). It checks out the code, then hands it to Azure, which runs its own build (`pip install -r requirements.txt` via Oryx, since `SCM_DO_BUILD_DURING_DEPLOYMENT=true` was set in Step 2) and starts the app with `bash startup.sh`.

First deploy takes a few minutes. Once it finishes, visit:

```
https://<WEBAPP_NAME>.azurewebsites.net
```

## Verifying and troubleshooting

Stream live logs if something isn't working:

```bash
az webapp log config --resource-group flightsearch-rg --name <WEBAPP_NAME> --docker-container-logging filesystem
az webapp log tail --resource-group flightsearch-rg --name <WEBAPP_NAME>
```

Common issues:

- **"Application Error" / blank page** — almost always a startup command or port mismatch. Confirm `WEBSITES_PORT=8000` is set (`az webapp config appsettings list`) and that the startup command is exactly `bash startup.sh`.
- **Database connection errors in the logs** — double-check `DB_HOST`/`DB_USER`/`DB_PASSWORD` app settings match what Step 2 set, and that the MySQL server's firewall allows Azure services (the `--public-access 0.0.0.0` flag in the script already does this).
- **MongoDB caching silently not working** — check that the Atlas IP allowlist includes the App Service's outbound IPs from Step 4; `get_mongo_client()` in `db/mongo.py` swallows connection errors and returns `None`, so the app keeps working without cache rather than crashing, but caching/mirroring will be silently disabled.
- **Deploy succeeds but old code still running** — App Service can take a minute to restart after a deploy; also confirm the workflow's `AZURE_WEBAPP_NAME` matches exactly (Web App names are case-sensitive in the URL but the resource lookup is not — a typo is the usual cause).
- **Slow first request after idle** — Basic (B1) tier doesn't sleep the way Free (F1) does, but it also isn't warmed automatically; if this matters, enable "Always On" in the Web App's Configuration → General settings (`az webapp config set --always-on true`).

## Cost (approximate — confirm with the [Azure pricing calculator](https://azure.microsoft.com/pricing/calculator/) for your region)

| Resource | Tier | Approx. monthly cost |
|---|---|---|
| App Service Plan | Linux B1 Basic | ~$13 |
| MySQL Flexible Server | Burstable B1ms, 20 GB | ~$12–15 |
| MongoDB Atlas | unchanged (your existing tier) | $0 extra |
| SerpAPI | unchanged (your existing plan) | $0 extra |

Total new spend is roughly **$25–30/month**. Two ways to cut it further:

- Swap the App Service plan to Free (F1) — no cost, but capped at 60 CPU-minutes/day, no "Always On", and the app will sleep between visits. Fine for a personal demo, not for anything you want responsive on demand.
- Stop (not delete) resources when not in use: `az webapp stop` / `az mysql flexible-server stop` pause billing for compute while keeping the data.

## Tearing it all down

Everything this guide creates lives in one resource group, so cleanup is one command:

```bash
az group delete --name flightsearch-rg --yes --no-wait
```

This deletes the App Service, its plan, and the MySQL server together. It does not touch MongoDB Atlas or your SerpAPI account.
