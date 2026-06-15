#!/bin/bash

# GreatReads VM Migration Script
# This script migrates data from the remote VM to the local environment

set -e  # Exit on any error

echo "🚀 Starting GreatReads VM migration..."

# Configuration
REMOTE_USER="brandon"
REMOTE_HOST="5.78.41.92"
REMOTE_PROJECT_DIR="/home/brandon/projects/GreatReads"
LOCAL_PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOCAL_DATA_DIR="$LOCAL_PROJECT_DIR/data"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}📋 Migration Configuration:${NC}"
echo "  Remote: $REMOTE_USER@$REMOTE_HOST:$REMOTE_PROJECT_DIR"
echo "  Local:  $LOCAL_PROJECT_DIR"
echo ""

# Create local data directory if it doesn't exist
echo -e "${GREEN}📁 Creating local data directory...${NC}"
mkdir -p "$LOCAL_DATA_DIR"
mkdir -p "$LOCAL_DATA_DIR/covers"

# Step 1: Migrate the database
echo -e "${GREEN}📊 Migrating database...${NC}"
scp "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PROJECT_DIR/src/greatreads.db" "$LOCAL_DATA_DIR/greatreads.db"
echo -e "${GREEN}✅ Database migrated${NC}"

# Step 2: Migrate book covers
echo -e "${GREEN}🖼️  Migrating book covers...${NC}"
if ssh "$REMOTE_USER@$REMOTE_HOST" "[ -d $REMOTE_PROJECT_DIR/src/greatreads/static/covers ]"; then
    scp -r "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PROJECT_DIR/src/greatreads/static/covers/*" "$LOCAL_DATA_DIR/covers/" 2>/dev/null || echo "No covers found or directory empty"
    echo -e "${GREEN}✅ Book covers migrated${NC}"
else
    echo -e "${YELLOW}⚠️  No covers directory found on remote VM${NC}"
fi

# Step 3: Check for any .env file
echo -e "${GREEN}🔐 Checking for environment variables...${NC}"
if ssh "$REMOTE_USER@$REMOTE_HOST" "[ -f $REMOTE_PROJECT_DIR/.env ]"; then
    echo -e "${YELLOW}⚠️  .env file found on remote VM${NC}"
    echo -e "${YELLOW}   Please manually review and copy any necessary environment variables${NC}"
    echo -e "${YELLOW}   Remote .env location: $REMOTE_USER@$REMOTE_HOST:$REMOTE_PROJECT_DIR/.env${NC}"
else
    echo -e "${GREEN}✅ No .env file found on remote VM${NC}"
fi

# Step 4: Summary
echo ""
echo -e "${GREEN}✅ Migration complete!${NC}"
echo ""
echo -e "${YELLOW}📋 Next steps:${NC}"
echo "  1. Review the migrated data in: $LOCAL_DATA_DIR"
echo "  2. Create a .env file from .env.template if needed"
echo "  3. Build and test the Docker container locally"
echo "  4. Deploy to production when ready"
echo ""
echo -e "${YELLOW}💡 To build and run locally:${NC}"
echo "  docker-compose up --build"
echo ""

