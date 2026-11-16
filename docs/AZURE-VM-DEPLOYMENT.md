# Deploy Project Bridge on one Azure Ubuntu VM

This option runs Next.js, FastAPI, PostgreSQL, and Caddy on one VM. `compose.azure.yml` is the production configuration; the root `docker-compose.yml` is for local HTTP development. Caddy serves HTTPS and forwards requests to Next.js, which forwards `/api/v1/*` to FastAPI. Only Caddy exposes public ports. The database and API stay inside the Docker network.

## 1. Azure VM and domain

1. In Azure Portal, create a resource group and an **Ubuntu 24.04 LTS** VM. Start with about 2 vCPUs and 8 GiB RAM for container builds; monitor use and resize if needed. VM, disk, public IP, and outbound traffic may incur charges.
2. Use an SSH public key. Restrict inbound SSH (TCP 22) to your own IP address. Allow inbound TCP **80** and **443** in the VM's Network Security Group. Do not open 3000, 8000, or 5432.
3. Give the VM a **Standard, static public IP**. Point a domain name's A record to that IP. Google OAuth's production redirect URI needs a real HTTPS domain; a raw public IP is not suitable.
4. Wait for DNS to point at the VM before starting Caddy. Its automatic HTTPS needs the domain and ports 80/443 reachable from the internet.

## 2. Install Docker and copy the code

SSH into the VM as its non-root administrator. Install Git and follow [Docker's official Ubuntu Engine installation steps](https://docs.docker.com/engine/install/ubuntu/) to install Docker Engine, the Buildx plugin, and the Compose plugin. The convenience script is not needed. Commands below use `sudo docker` so adding your account to the Docker group is unnecessary.

```bash
sudo apt update
sudo apt install -y git
git clone https://github.com/Tanishk009-create/Project-Bridge.git
cd Project-Bridge
```

## 3. Configure private values

```bash
cp azure.env.example .env
chmod 600 .env
nano .env
```

Fill every required blank. `BRIDGE_DOMAIN` is only the hostname, for example `bridge.example.com`—no `https://`, path, or trailing slash. Generate three **different** random values for `DB_PASSWORD`, `JWT_SECRET_KEY`, and `NEXTAUTH_SECRET` with `openssl rand -hex 32` (run it three times). Put the Gemini key in `GEMINI_API_KEY`. Keep the `.env` file on the VM; never commit it or paste it into chat.

The production Compose file sends verification and recovery email through SMTP. Change the Gmail password previously shared in chat, enable 2-Step Verification, and make a **Google App Password**. Put the App Password in `SMTP_PASSWORD`; put the sending Gmail address in both `SMTP_USERNAME` and `SMTP_FROM`. Do not use the normal Gmail sign-in password. Azure permits authenticated SMTP relay on TCP 587; port 25 has subscription restrictions.

Google sign-in can be configured after the first deployment. Leave `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` blank until the OAuth client is created, then add both and restart the containers.

## 4. Start the application

From the cloned repository directory:

```bash
sudo docker compose -f compose.azure.yml up -d --build
```

Compose starts PostgreSQL, waits for database health, applies Alembic migrations, starts FastAPI and Next.js, and starts Caddy. Caddy obtains and renews HTTPS certificates for `BRIDGE_DOMAIN`. Open `https://your-domain` after startup. The public health route is `https://your-domain/api/v1/health/db`. If startup fails, inspect `sudo docker compose -f compose.azure.yml ps` and `sudo docker compose -f compose.azure.yml logs --tail=100`.

The Compose database volume persists across container rebuilds. A new VM or deleted volume will not contain old data. Existing local SQLite accounts and writing do not move automatically to PostgreSQL; migrate them separately if they matter.

## 5. Enable Google sign-in

In Google Cloud, configure the app's audience and create a **Web application** OAuth client. Register:

- Authorized JavaScript origin: `https://your-domain`
- Authorized redirect URI: `https://your-domain/api/auth/callback/google`

Copy the client ID and secret into the VM's `.env`. The same client ID is supplied to the backend by Compose; the secret goes only to Next.js. Recreate the containers with `sudo docker compose -f compose.azure.yml up -d --build`. The Google redirect URI must match exactly.

## 6. Maintain and back up

To deploy later GitHub updates, run `git pull --ff-only` from the repository directory followed by `sudo docker compose -f compose.azure.yml up -d --build`. Back up the database regularly and keep a copy outside the VM. For example, from the repository directory:

```bash
sudo docker compose -f compose.azure.yml exec -T db pg_dump -U bridge bridge | gzip > "$HOME/bridge-backup-$(date +%F).sql.gz"
```

VM disk snapshots are useful as an additional recovery option. Keep the OS and Docker packages updated, and monitor VM disk, memory, container logs, mail delivery, and domain renewal. Do not use `npm run dev` or the local HTTP Compose file on the public VM.

## Source documentation

- [Azure Linux VM quickstart](https://learn.microsoft.com/azure/virtual-machines/linux/quick-create-portal)
- [Azure static public IP](https://learn.microsoft.com/azure/virtual-network/ip-services/virtual-network-static-public-ip)
- [Azure SMTP guidance](https://learn.microsoft.com/troubleshoot/azure/virtual-network/troubleshoot-outbound-smtp-connectivity)
- [Caddy automatic HTTPS](https://caddyserver.com/docs/automatic-https)
- [Google OAuth redirect rules](https://developers.google.com/identity/protocols/oauth2/web-server)
