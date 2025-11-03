# Memoires Techniques Backend - Setup Guide

## Overview

This is the backend API for the Memoires Techniques application - a system for generating technical memoirs for construction bidding offers using RAG and AI.

## Architecture

- **Next.js 14** - API Routes for REST endpoints
- **Prisma** - ORM with PostgreSQL + pgvector
- **Supabase** - Database and S3-compatible storage
- **FastAPI (Python)** - Document parsing and Word export services
- **BullMQ + Redis** - Job queue for async processing
- **Claude API** - AI content generation
- **OpenAI** - Text embeddings for RAG

## Prerequisites

- Node.js 20+
- Docker & Docker Compose
- Supabase account (free tier works)
- Claude API key
- OpenAI API key

## Quick Start

### 1. Environment Setup

Copy the environment template:
```bash
cp .env.example .env
```

Fill in your credentials:
- Supabase database URL and keys
- Claude API key
- OpenAI API key
- Generate a NextAuth secret: `openssl rand -base64 32`

### 2. Supabase Setup

1. Create a new project at [supabase.com](https://supabase.com)
2. Enable the `vector` extension:
   - Go to Database > Extensions
   - Enable `vector` extension
3. Get your credentials from Settings > API
4. Create a storage bucket named `memoires`

### 3. Start with Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

This will start:
- Redis (port 6379)
- Next.js backend (port 3000)
- Python service (port 8000)

### 4. Initialize Database

Run Prisma migrations:
```bash
# Install dependencies first (if not using Docker)
npm install

# Generate Prisma client
npm run prisma:generate

# Run migrations
npm run prisma:migrate
```

### 5. Test the Setup

Visit:
- Backend health: http://localhost:3000/api/health
- Python service health: http://localhost:8000/health
- Prisma Studio: `npm run prisma:studio`

## Development

### Local Development (without Docker)

```bash
# Install dependencies
npm install
cd python && pip install -r requirements.txt

# Start Redis (required)
redis-server

# Start Python service
cd python
uvicorn main:app --reload --port 8000

# Start Next.js backend (in another terminal)
npm run dev
```

### Project Structure

```
backend/
├── docker-compose.yml          # Docker services configuration
├── Dockerfile                  # Next.js container
├── src/
│   ├── app/
│   │   ├── api/               # API routes (to be implemented)
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── lib/
│   │   ├── prisma/            # Database client
│   │   ├── validators/        # Zod schemas (to be added)
│   │   └── utils/             # Utilities (to be added)
│   └── services/
│       ├── rag/               # RAG service (to be implemented)
│       ├── ai/                # Claude integration (to be implemented)
│       ├── parser/            # Document parsing (to be implemented)
│       ├── storage/           # Supabase storage (to be implemented)
│       └── queue/             # BullMQ jobs (to be implemented)
├── python/
│   ├── Dockerfile
│   ├── main.py                # FastAPI app with basic endpoints
│   └── requirements.txt
└── prisma/
    └── schema.prisma          # Database schema
```

## Next Steps

The minimal infrastructure is now set up. You can now start implementing:

1. **API Routes** - Create endpoints in `src/app/api/`
2. **Services** - Implement RAG, AI, storage services
3. **Python Parsers** - Add PDF/DOCX parsing logic
4. **Queue Workers** - Set up BullMQ job processors
5. **Authentication** - Implement NextAuth

Refer to the PRD.txt for detailed requirements and API specifications.

## Useful Commands

```bash
# Docker
docker-compose up -d              # Start services
docker-compose down               # Stop services
docker-compose logs -f backend    # View backend logs
docker-compose logs -f python     # View Python service logs

# Prisma
npm run prisma:generate           # Generate client
npm run prisma:migrate            # Run migrations
npm run prisma:studio             # Open Prisma Studio

# Development
npm run dev                       # Start Next.js dev server
npm run build                     # Build for production
npm run start                     # Start production server
```

## Troubleshooting

### Port already in use
If ports 3000, 8000, or 6379 are already in use, modify the port mappings in `docker-compose.yml`.

### Prisma vector extension
Make sure you've enabled the `vector` extension in your Supabase database before running migrations.

### Connection issues
Check that your `DATABASE_URL` in `.env` is correct and that your Supabase instance is running.

## Support

Refer to the PRD.txt for detailed technical specifications and requirements.
