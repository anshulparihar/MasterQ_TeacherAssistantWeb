# MasterQ - AI Question Generation Platform 🚀

MasterQ is a production-grade AI-powered platform allowing educators and administrators to automatically generate highly contextual Question Papers and interact with a retrieval-augmented (RAG) Chatbot.

It relies on **Google Gemini 2.5 Pro** for generation, and **PostgreSQL (pgvector)** + **MinIO** for rapid semantic document retrieval.

## System Prerequisites
- Docker & Docker Compose
- `make` utility
- A valid Google Gemini API Key

## 🛠️ Step-by-Step Setup Guide

This deployment uses a fully orchestrated Docker Compose topology.

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd MasterQ
```

### 2. Configure Environment Variables
You must set up your environment variables before booting the cluster.
```bash
cp .env.example .env
```
Open the `.env` file in your text editor and **insert your Google Gemini API Key** under `GEMINI_API_KEY`.

### 3. Boot the Infrastructure
Run the following command to download the docker images, build the custom backend/frontend containers, and start the cluster:
```bash
make up
```
*(Note: This might take a few minutes the first time as it downloads PostgreSQL, Redis, MinIO, Node, and Python images).*

### 4. Run Database Migrations
Once the containers are up and running, you need to construct the PostgreSQL schema (which automatically enables the `pgvector` extension).
```bash
make migrate
```

### 5. Seed Initial Data
Populate the database with the default curriculum configurations (Subjects and Exam Types).
```bash
make seed
```

### 6. Create the Admin User
To access the Admin Panel and configure the global knowledge base, you must create a master admin account.
```bash
make create-admin
```
*Follow the interactive prompt to enter an email and password.*

### 7. Access the Application
The Nginx reverse proxy routes all traffic seamlessly:
- **Frontend**: Navigate your browser to `http://localhost`
- **Backend API Docs**: Navigate to `http://localhost/api/docs`

### 8. Final Workflow Steps
1. Log in to `http://localhost` using the admin credentials you just created.
2. Navigate to the **Admin Panel** to upload baseline global documents.
3. Test the generation engine on the **Dashboard**!

---

## Developer Commands Reference
All commands are wrapped cleanly in the `Makefile`.
- `make logs` - Tail the logs of the entire cluster.
- `make down` - Stop and remove all containers safely.
- `make shell` - Drop into a bash terminal inside the FastAPI backend.
