#!/usr/bin/env bash
# ==============================================================================
# provision-azure.sh
#
# Provisions the cheapest dev/test Azure infrastructure for the Flight Search
# Streamlit app:
#   - Resource group
#   - Linux App Service plan (B1 Basic) + Web App (Python)
#   - Azure Database for MySQL Flexible Server (Burstable B1ms)
#   - Firewall rule allowing Azure services to reach MySQL
#   - App settings (env vars) wired to match config.py
#
# MongoDB stays on Atlas — this script does NOT touch Mongo. See
# AZURE_DEPLOYMENT.md for the Atlas network-access step.
#
# Prerequisites:
#   - Azure CLI installed and logged in: `az login`
#   - mysql client installed locally (for the schema import step), OR use
#     Azure Cloud Shell which has it preinstalled.
#
# Usage:
#   1. Edit the variables in the "EDIT ME" block below.
#   2. bash provision-azure.sh
# ==============================================================================
set -euo pipefail

# ---------------------------- EDIT ME ----------------------------------------
RESOURCE_GROUP="flightsearch-rg"
LOCATION="centralindia"                      # e.g. centralindia, eastus, westeurope
APP_SERVICE_PLAN="flightsearch-plan"
WEBAPP_NAME="flightsearch-app-$RANDOM"        # must be globally unique across Azure
PYTHON_VERSION="PYTHON:3.12"

MYSQL_SERVER_NAME="flightsearch-mysql-$RANDOM" # must be globally unique across Azure
MYSQL_ADMIN_USER="flightadmin"
MYSQL_ADMIN_PASSWORD="ChangeMe_$(date +%s)!Aa" # CHANGE THIS to your own strong password
MYSQL_DB_NAME="flight_db"

SERPAPI_KEY="__PASTE_YOUR_SERPAPI_KEY__"
MONGO_URI="__PASTE_YOUR_MONGODB_ATLAS_URI__"   # mongodb+srv://user:pass@cluster.../
MONGO_DB_NAME="flight_cache"
MONGO_APP_DB_NAME="flight_app"
MONGO_CACHE_TTL_SECONDS="21600"
# -------------------------------------------------------------------------------

echo "== 1/6: Creating resource group: $RESOURCE_GROUP in $LOCATION =="
az group create \
  --name "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --output table

echo "== 2/6: Creating MySQL Flexible Server (Burstable B1ms, cheapest tier) =="
az mysql flexible-server create \
  --resource-group "$RESOURCE_GROUP" \
  --name "$MYSQL_SERVER_NAME" \
  --location "$LOCATION" \
  --admin-user "$MYSQL_ADMIN_USER" \
  --admin-password "$MYSQL_ADMIN_PASSWORD" \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --storage-size 20 \
  --version 8.0 \
  --database-name "$MYSQL_DB_NAME" \
  --public-access 0.0.0.0 \
  --yes \
  --output table

MYSQL_HOST="${MYSQL_SERVER_NAME}.mysql.database.azure.com"
echo "MySQL host: $MYSQL_HOST"

echo "== 3/6: Creating Linux App Service plan (B1 Basic) =="
az appservice plan create \
  --name "$APP_SERVICE_PLAN" \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --sku B1 \
  --is-linux \
  --output table

echo "== 4/6: Creating the Web App (Python runtime) =="
az webapp create \
  --resource-group "$RESOURCE_GROUP" \
  --plan "$APP_SERVICE_PLAN" \
  --name "$WEBAPP_NAME" \
  --runtime "$PYTHON_VERSION" \
  --output table

echo "== 5/6: Configuring startup command + app settings =="
az webapp config set \
  --resource-group "$RESOURCE_GROUP" \
  --name "$WEBAPP_NAME" \
  --startup-file "bash startup.sh" \
  --output table

az webapp config appsettings set \
  --resource-group "$RESOURCE_GROUP" \
  --name "$WEBAPP_NAME" \
  --settings \
    SCM_DO_BUILD_DURING_DEPLOYMENT=true \
    WEBSITES_PORT=8000 \
    DB_HOST="$MYSQL_HOST" \
    DB_USER="$MYSQL_ADMIN_USER" \
    DB_PASSWORD="$MYSQL_ADMIN_PASSWORD" \
    DB_NAME="$MYSQL_DB_NAME" \
    SERPAPI_KEY="$SERPAPI_KEY" \
    MONGO_URI="$MONGO_URI" \
    MONGO_DB_NAME="$MONGO_DB_NAME" \
    MONGO_APP_DB_NAME="$MONGO_APP_DB_NAME" \
    MONGO_CACHE_TTL_SECONDS="$MONGO_CACHE_TTL_SECONDS" \
  --output table

echo "== 6/6: Fetching outbound IPs (add these to MongoDB Atlas Network Access) =="
az webapp show \
  --resource-group "$RESOURCE_GROUP" \
  --name "$WEBAPP_NAME" \
  --query "possibleOutboundIpAddresses" \
  --output tsv

echo ""
echo "=============================================================================="
echo "Done. Save these values — you'll need them for the next steps:"
echo ""
echo "  Web App name:        $WEBAPP_NAME"
echo "  Web App URL:         https://${WEBAPP_NAME}.azurewebsites.net"
echo "  MySQL host:          $MYSQL_HOST"
echo "  MySQL admin user:    $MYSQL_ADMIN_USER"
echo "  MySQL admin password: (the value you set above — store it in a password manager)"
echo ""
echo "Next: import the schema (see AZURE_DEPLOYMENT.md Step 3), then:"
echo "  mysql -h $MYSQL_HOST -u $MYSQL_ADMIN_USER -p --ssl-mode=REQUIRED $MYSQL_DB_NAME < azure_migration/flight_db_dump.sql"
echo "=============================================================================="
