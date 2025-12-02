#!/bin/bash

set -e  # Exit on error

echo "🗄️  Starting PostgreSQL Database Setup..."

# Configuration
CONTAINER_NAME="crm_postgres"
VOLUME_NAME="client-checker_postgres_data"
DB_NAME="crm_dev"
DB_USER="postgres"
DB_PASSWORD="postgres"
DB_PORT="5432"

# Step 1: Stop and remove existing container if it exists
echo "📦 Checking for existing container..."
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "   Stopping existing container..."
    docker stop ${CONTAINER_NAME} > /dev/null 2>&1 || true
    echo "   Removing existing container..."
    docker rm ${CONTAINER_NAME} > /dev/null 2>&1 || true
fi

# Step 2: Remove existing volume if it exists
echo "💾 Checking for existing volume..."
if docker volume ls --format '{{.Name}}' | grep -q "^${VOLUME_NAME}$"; then
    echo "   Removing existing volume..."
    docker volume rm ${VOLUME_NAME} > /dev/null 2>&1 || true
fi

# Step 3: Create and start PostgreSQL container
echo "🚀 Creating new PostgreSQL container..."
docker run -d \
    --name ${CONTAINER_NAME} \
    -e POSTGRES_USER=${DB_USER} \
    -e POSTGRES_PASSWORD=${DB_PASSWORD} \
    -e POSTGRES_DB=postgres \
    -p ${DB_PORT}:5432 \
    -v ${VOLUME_NAME}:/var/lib/postgresql/data \
    postgres:15-alpine \
    > /dev/null

# Step 4: Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if docker exec ${CONTAINER_NAME} pg_isready -U ${DB_USER} > /dev/null 2>&1; then
        echo "   ✅ PostgreSQL is ready!"
        break
    fi
    attempt=$((attempt + 1))
    sleep 1
done

if [ $attempt -eq $max_attempts ]; then
    echo "   ❌ PostgreSQL failed to start"
    exit 1
fi

# Step 5: Create database
echo "📊 Creating database '${DB_NAME}'..."
docker exec ${CONTAINER_NAME} psql -U ${DB_USER} -c "CREATE DATABASE ${DB_NAME};" 2>/dev/null || \
    docker exec ${CONTAINER_NAME} psql -U ${DB_USER} -c "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}';" | grep -q 1 && \
    echo "   Database already exists, skipping..."

# Step 6: Create schema (tables, enums, indexes)
echo "🏗️  Creating database schema..."
docker exec -i ${CONTAINER_NAME} psql -U ${DB_USER} -d ${DB_NAME} << 'SQL'
-- Drop existing objects if they exist (for clean setup)
DROP TABLE IF EXISTS "Lead" CASCADE;
DROP TABLE IF EXISTS "User" CASCADE;
DROP TYPE IF EXISTS "PipelineStatus" CASCADE;
DROP TYPE IF EXISTS "Role" CASCADE;

-- Create Enums
CREATE TYPE "Role" AS ENUM ('ADMIN', 'EMPLOYEE');
CREATE TYPE "PipelineStatus" AS ENUM (
    'Unassigned', 
    'Email_Sent', 
    'Client_Replied', 
    'Plan_Sent', 
    'Rate_Finalized', 
    'Docs_Signed', 
    'Testing', 
    'Approved', 
    'Rejected'
);

-- Create User table
CREATE TABLE "User" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "email" TEXT NOT NULL UNIQUE,
    "password" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "role" "Role" NOT NULL DEFAULT 'EMPLOYEE',
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create Lead table
CREATE TABLE "Lead" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "frn" TEXT NOT NULL UNIQUE,
    "company_name" TEXT NOT NULL,
    "contact_email" TEXT,
    "contact_phone" TEXT,
    "service_type" TEXT,
    "website" TEXT,
    "notes" TEXT,
    "pipelineStatus" "PipelineStatus" NOT NULL DEFAULT 'Unassigned',
    "history" TEXT[] DEFAULT ARRAY[]::TEXT[],
    "assignedEmployeeId" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "Lead_assignedEmployeeId_fkey" FOREIGN KEY ("assignedEmployeeId") 
        REFERENCES "User"("id") ON DELETE SET NULL ON UPDATE CASCADE
);

-- Create Indexes
CREATE INDEX "User_email_idx" ON "User"("email");
CREATE INDEX "Lead_assignedEmployeeId_idx" ON "Lead"("assignedEmployeeId");
CREATE INDEX "Lead_pipelineStatus_idx" ON "Lead"("pipelineStatus");
CREATE INDEX "Lead_frn_idx" ON "Lead"("frn");

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE crm_dev TO postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;
SQL

# Step 7: Verify setup
echo "✅ Verifying database setup..."
TABLES=$(docker exec ${CONTAINER_NAME} psql -U ${DB_USER} -d ${DB_NAME} -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';" | tr -d ' ')

if [ "$TABLES" -ge "2" ]; then
    echo "   ✅ Database setup complete!"
    echo "   📋 Tables created: $TABLES"
    docker exec ${CONTAINER_NAME} psql -U ${DB_USER} -d ${DB_NAME} -c "\dt" 2>/dev/null
else
    echo "   ❌ Database setup incomplete"
    exit 1
fi

# Step 8: Display connection info
echo ""
echo "🎉 Database setup complete!"
echo ""
echo "📝 Connection Details:"
echo "   Host: localhost"
echo "   Port: ${DB_PORT}"
echo "   Database: ${DB_NAME}"
echo "   User: ${DB_USER}"
echo "   Password: ${DB_PASSWORD}"
echo ""
echo "🔗 Connection String:"
echo "   postgresql://${DB_USER}:${DB_PASSWORD}@localhost:${DB_PORT}/${DB_NAME}?schema=public"
echo ""
echo "📊 Container Status:"
docker ps --filter "name=${CONTAINER_NAME}" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""

