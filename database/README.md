# CRM Database Setup

## Prerequisites
- Docker
- Docker Compose (optional)

## Quick Start

Run the setup script from the backend directory:
```bash
./database/setup.sh
```

This will:
1. Start a PostgreSQL container
2. Create the `crm_dev` database
3. Create the schema (tables, enums, indexes)

## Connection Details
- **Host**: localhost
- **Port**: 5432
- **Database**: crm_dev
- **User**: postgres
- **Password**: postgres

## Schema Reference
See `schema.sql` for the complete SQL schema.
