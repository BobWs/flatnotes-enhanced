# Running Multiple Flatnotes Enhanced Instances

This guide explains how to run two or more Flatnotes Enhanced instances on the
same server — for example, one for work notes and one for personal notes — and
access both from the same browser without interference.

---

## How It Works

Flatnotes Enhanced namespaces the browser session by origin. Each domain gets
its own isolated authentication token stored under a unique key, so switching
between two instances never causes session bleed, stale cache hits, or the
"note not found" errors that plague the original Flatnotes in this setup.

---

## Requirements

Before you start, make sure each instance has:

1. **Its own data volume** — never share `/data` between instances
2. **Its own database volume** — never share `.flatnotes/` between instances  
3. **A unique `FLATNOTES_SECRET_KEY`** — this is mandatory (see below)
4. **A unique `FLATNOTES_TOTP_KEY`** — required if using TOTP auth
5. **A unique domain or subdomain** — e.g. `notes.example.com` and `wnotes.example.com`

---

## Critical: Unique Secret Keys

**Every instance must have its own `FLATNOTES_SECRET_KEY`.** This is the single
most important configuration requirement for multi-instance setups.

If two instances share the same secret key, their JWT tokens are
cryptographically interchangeable. This causes subtle auth failures when
the browser's cookie from one instance is accepted by the other.

Generate a unique key for each instance:
```bash
openssl rand -hex 32
```

Run this command once per instance and use a different value for each.

If you use TOTP authentication, also generate a unique `FLATNOTES_TOTP_KEY`
for each instance:
```bash
openssl rand -base64 32
```

---

## Docker Compose Example

```yaml
version: '3.8'

services:

  flatnotes-personal:
    container_name: flatnotes-personal
    image: dockerbobw/flatnotes-enhanced:latest
    hostname: flatnotes-personal
    restart: unless-stopped
    ports:
      - "8091:8080"
    volumes:
      - /your/path/personal-notes:/data
      - /your/path/personal-db/.flatnotes:/data/.flatnotes
    environment:
      PUID: 1000
      PGID: 1000
      FLATNOTES_AUTH_TYPE: "totp"
      FLATNOTES_USERNAME: "your_username"
      FLATNOTES_PASSWORD: "your_password"
      FLATNOTES_TOTP_KEY: "unique_totp_key_for_personal"
      FLATNOTES_SECRET_KEY: "unique_secret_key_for_personal"
      FLATNOTES_SESSION_EXPIRY_DAYS: 30
      ENABLE_DATABASE: true
      DATABASE_PATH: /data/.flatnotes/flatnotes.db

  flatnotes-work:
    container_name: flatnotes-work
    image: dockerbobw/flatnotes-enhanced:latest
    hostname: flatnotes-work
    restart: unless-stopped
    ports:
      - "8092:8080"
    volumes:
      - /your/path/work-notes:/data
      - /your/path/work-db/.flatnotes:/data/.flatnotes
    environment:
      PUID: 1000
      PGID: 1000
      FLATNOTES_AUTH_TYPE: "totp"
      FLATNOTES_USERNAME: "your_username"
      FLATNOTES_PASSWORD: "your_password"
      FLATNOTES_TOTP_KEY: "a_different_totp_key_for_work"   # must be different
      FLATNOTES_SECRET_KEY: "a_different_secret_key_for_work" # must be different
      FLATNOTES_SESSION_EXPIRY_DAYS: 30
      ENABLE_DATABASE: true
      DATABASE_PATH: /data/.flatnotes/flatnotes.db
```

> **Important:** Give each service a unique `hostname`. Using the same hostname
> on both services causes confusing logs and can cause network conflicts.

---

## Reverse Proxy Configuration

Both instances must be served on their own domain or subdomain. Path-based
routing (e.g. `/personal` and `/work` on the same domain) is not supported.

### Nginx Proxy Manager

In NPM, create two separate proxy hosts:

| Proxy Host | Forward Hostname/IP | Forward Port |
|---|---|---|
| `notes.example.com` | `192.168.1.100` | `8091` |
| `wnotes.example.com` | `192.168.1.100` | `8092` |

**Do not add an Access List with a password** to these proxy hosts. NPM's
password-protected Access Lists use the `Authorization` header for their own
basic auth, which conflicts with Flatnotes' Bearer token authentication.

IP-based allow/deny rules (without a password) work fine and do not interfere.

**No custom Nginx configuration is needed.** NPM forwards the `Authorization`
header by default for proxy hosts without a password-protected Access List.

### Caddy

```caddy
notes.example.com {
    reverse_proxy localhost:8091
}

wnotes.example.com {
    reverse_proxy localhost:8092
}
```

### Nginx

```nginx
server {
    server_name notes.example.com;
    location / {
        proxy_pass http://localhost:8091;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Authorization $http_authorization;
    }
}

server {
    server_name wnotes.example.com;
    location / {
        proxy_pass http://localhost:8092;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Authorization $http_authorization;
    }
}
```

---

## After First Login

After upgrading from a pre-multi-instance build, the first login on each
instance will ask you to log in again. This is expected — the session key
format changed. It only happens once. All your notes and settings are intact.

---

## Pre-Login 401s in Logs

You will see 401 responses in the container logs on startup, before the user
logs in. These are normal — the app attempts to load settings and tags
immediately, and those requests are rejected because no session exists yet.
They stop as soon as the user logs in.

---

## Verifying Isolation

To confirm both instances are correctly isolated:

1. Log in to `notes.example.com` and open **DevTools → Application →
   Local Storage**. You should see a key starting with `token_` followed by
   a base64 string unique to that origin.
2. Open `wnotes.example.com` in the same browser. Its Local Storage key will
   be a different `token_` string.
3. Both instances can now be used simultaneously in the same browser with no
   interference.

---

## Frequently Asked Questions

**Can both instances use the same username and password?**  
Yes. Each instance authenticates against its own configuration independently.

**Can both instances use the same TOTP key?**  
Technically yes, but it means one authenticator entry unlocks both instances.
Using separate TOTP keys gives you true isolation — a compromised key only
affects one instance.

**What if I forget to use unique secret keys?**  
Tokens from one instance will be accepted by the other. You may see unexpected
auth behaviour, cross-instance session sharing, or intermittent 401 errors.
The fix is to add unique keys and restart both containers.

**Does this work with TOTP (two-factor authentication)?**  
Yes, fully supported. Each instance has its own TOTP secret and its own session
storage namespace.

**Can I run more than two instances?**  
Yes. Repeat the pattern for as many instances as you need. Each needs its own
port, domain, data volume, and secret key.

**What if both instances are on the same domain under different paths?**  
Not supported. The session isolation is based on origin (domain + port). Two
paths on the same domain share the same origin and cannot be isolated this way.
Use separate subdomains instead.
