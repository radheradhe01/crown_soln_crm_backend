-- Database Schema Reference
-- This file contains the SQL schema for reference and manual execution

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

