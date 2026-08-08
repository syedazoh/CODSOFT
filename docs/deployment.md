# Deployment Runbook (AWS EC2)

There is no Terraform/IaC in this repo yet — this is a documented manual setup,
time-boxed for the FYP. Automating it with Terraform is a reasonable stretch
goal if time remains, but isn't required to demo a working deployment.

## One-time EC2 setup

1. Launch an EC2 instance — **t3.small or larger** (Mongo + Chroma + the backend's
   in-memory sentence-transformers model can OOM a t2.micro). Ubuntu 22.04 LTS is
   a safe default AMI.
2. Security group: allow inbound `22` (SSH, restrict to your IP), `80` (frontend),
   `8000` (backend API).
3. SSH in and install Docker + the Compose plugin:
   ```bash
   curl -fsSL https://get.docker.com | sh
   sudo usermod -aG docker $USER
   sudo apt-get install -y docker-compose-plugin
   ```
   Log out/in for the group change to apply.
4. Create a deploy directory and pull just the two files the host actually needs:
   ```bash
   mkdir -p ~/startup-simulator && cd ~/startup-simulator
   curl -o docker-compose.prod.yml https://raw.githubusercontent.com/<org>/<repo>/main/docker-compose.prod.yml
   ```
5. Create `.env` in that same directory (never committed — `.gitignore` already
   excludes `.env*`):
   ```
   GROQ_API_KEY=your-real-groq-key
   GROQ_MODEL=llama-3.3-70b-versatile
   MONGO_ROOT_USERNAME=admin
   MONGO_ROOT_PASSWORD=<generate a strong one>
   BACKEND_IMAGE=<account-id>.dkr.ecr.<region>.amazonaws.com/startup-simulator-backend:latest
   FRONTEND_IMAGE=<account-id>.dkr.ecr.<region>.amazonaws.com/startup-simulator-frontend:latest
   ```
   `chmod 600 .env`.
6. Authenticate Docker on the host to your ECR registry once (Jenkins re-auths on
   every deploy, but you'll want this for the first manual pull too):
   ```bash
   aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <account-id>.dkr.ecr.<region>.amazonaws.com
   ```
7. Create the ECR repositories (`startup-simulator-backend`, `startup-simulator-frontend`)
   if they don't exist yet.

## Deploying

Either via Jenkins (`Jenkinsfile` at repo root — see its header comment for the
required credentials/env vars), or manually from the EC2 host:

```bash
cd ~/startup-simulator
../CODSOFT/scripts/deploy.sh   # or copy scripts/deploy.sh alongside docker-compose.prod.yml
```

Verify:
```bash
curl http://localhost:8000/health
# -> {"status":"healthy","mongo":"connected"}
curl -I http://localhost/
# -> HTTP/1.1 200 OK
```

## Rollback

Images are tagged with the short git commit SHA in addition to `latest`. To roll
back, set `BACKEND_IMAGE`/`FRONTEND_IMAGE` in `.env` to the previous SHA tag and
re-run `docker compose -f docker-compose.prod.yml up -d`.

## Secrets

- `GROQ_API_KEY` and Mongo credentials live only in the EC2 host's `.env` (never
  committed) and in Jenkins' credential store for the pipeline's own AWS/SSH access.
- Never put real keys in `.env.example` files — see `backend/.env.example` for the
  placeholder pattern this repo follows.
