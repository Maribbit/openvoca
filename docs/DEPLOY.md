# Deploying OpenVoca

How to run OpenVoca on a machine you own, reachable over a private network.
Written to be followed on the deployment machine, by a person or an agent.

The reasoning behind this layout is in [`docs/specs/private-deployment.md`](docs/specs/private-deployment.md).
This file is the procedure; that file is the contract.

## What this is not

No reverse proxy, no TLS, no containers, no image registry. The service listens
on a port and the private network provides transport security. If the service
ever needs to be reachable from the open internet, that is a separate design and
the authentication in `docs/specs/deployment.md` becomes a prerequisite — the
settings table holds your model provider's API key.

## Prerequisites

On the deployment machine:

| Requirement | Why |
|---|---|
| `git` | `deploy.py` exports revisions from a checkout |
| `uv` | installs the backend's Python dependencies |
| Node.js and `pnpm` | builds the interface |
| systemd | supervises the process |
| A DNS or VPN route | how your other devices reach the machine |

The private network is out of scope here. Tailscale and WireGuard both work; so
does a plain LAN, with the caveat that plain HTTP on a shared network is
readable by anyone on it.

## Layout

Two roots, and the separation is the whole point: an update replaces a code
directory, so a database stored inside one would be replaced with it.

```
/opt/openvoca/                        code, replaced by each deployment
  releases/<revision>/                one export per revision
  current -> releases/<revision>      what the service runs; the only switch
  revision.env                        revision and version the service reports

/var/lib/openvoca/                    data, never touched by a deployment
  openvoca.db
  snapshots/                          one SQLite snapshot per deployment
```

Overridable through the environment, read by `scripts/deploy.py`:

| Variable | Default |
|---|---|
| `OPENVOCA_ROOT` | `/opt/openvoca` |
| `OPENVOCA_DATA_DIR` | `/var/lib/openvoca` |
| `OPENVOCA_RESTART_CMD` | `systemctl restart openvoca` |

Changing `OPENVOCA_ROOT` or `OPENVOCA_DATA_DIR` means the unit file has to be
told too — it names both.

## First deployment

Run these on the deployment machine.

**1. Create the service account and the two roots.**

```bash
sudo useradd --system --home /opt/openvoca --shell /usr/sbin/nologin openvoca
sudo mkdir -p /opt/openvoca/releases /var/lib/openvoca/snapshots
sudo chown -R openvoca:openvoca /var/lib/openvoca
```

The service runs as `openvoca` and writes only to `/var/lib/openvoca`. The code
tree stays owned by whoever deploys, so the running service cannot modify the
code it is serving.

**2. Get a checkout.** This is the source revisions are exported from, not the
code that runs.

```bash
sudo git clone https://github.com/Maribbit/openvoca /srv/openvoca-src
```

**3. Install the unit.**

```bash
sudo cp /srv/openvoca-src/deploy/openvoca.service /etc/systemd/system/openvoca.service
sudo systemctl daemon-reload
sudo systemctl enable openvoca
```

`enable` without `--now`, because nothing has been deployed yet. The first
deployment starts it.

Optionally copy `deploy/openvoca.conf.example` to `/etc/openvoca/openvoca.conf`
to change the port. The service starts without that file.

**4. Deploy a revision.**

```bash
cd /srv/openvoca-src
sudo git fetch --tags
sudo python3 scripts/deploy.py v0.10.2
```

Pass the tag or commit you want. The script exports it, installs its
dependencies, builds its interface, snapshots the database, checks the new
revision against that snapshot, then switches and restarts.

The script itself needs only the Python standard library, so it runs under the
system interpreter. `uv` and `pnpm` are needed by the steps it performs, not by
the script.

**5. Confirm.**

```bash
curl -s http://localhost:8000/api/health
```

```json
{"status":"ok","message":"OpenVoca backend is running!","revision":"v0.10.2"}
```

`revision` is the answer to "is the new code actually live?" — it comes from the
environment the service manager loaded, not from the code.

Then open `http://<machine>:8000/` from a device on the private network and set
your model provider in Settings.

## Updating

```bash
cd /srv/openvoca-src
sudo git fetch --tags
sudo python3 scripts/deploy.py <new-revision>
```

That is the whole procedure. There is no separate rollback command: going back
is the same command with the previous revision.

```bash
sudo python3 scripts/deploy.py <previous-revision>
```

## What a deployment guarantees

- **The old revision keeps serving until the new one is proven.** Everything
  that can fail happens before the switch, so a failed deployment changes
  nothing. The script prints which revision is still serving and the exact
  command that returns to it.
- **Data survives.** Each deployment snapshots the database first, using
  SQLite's own backup mechanism. Replacing a code directory cannot touch
  `/var/lib/openvoca`.
- **The switch does not blink.** `current` is replaced with a rename, so there
  is no moment when it points at nothing.
- **A revision that cannot run will not be switched to.** The new revision's
  own startup check runs first, against a *copy* of the snapshot, so a revision
  that is about to be rejected has not written anything.

## When something goes wrong

### The service will not start

```bash
systemctl status openvoca
journalctl -u openvoca -n 50 --no-pager
```

The service logs the paths it resolved, in this order:

```
Data directory : /var/lib/openvoca
Database       : /var/lib/openvoca/openvoca.db
Frontend       : /opt/openvoca/current/frontend/dist
```

**If the paths are wrong**, the environment is wrong. Check
`/opt/openvoca/revision.env` and `/etc/openvoca/openvoca.conf`.
`OPENVOCA_DATA_DIR` pointing somewhere new does not lose data — it starts a new,
empty database and leaves the old one where it was.

**If it refuses to start with a schema message**, the database predates the
revision:

```
Database schema does not match the models this revision expects.
Refusing to start: queries would fail at runtime instead of at startup.

  table wordrecord is missing column(s): cooldown, seen_count
```

This is deliberate and it is why a failed deployment is safe: the previous
revision is still running. Deploy the revision that created the current schema,
or migrate the database. Rolling back is the normal answer.

**If it says `no interface build`**, the frontend build is missing from that
revision. Re-run the deployment.

**If the unit is in `failed` state**, the restart limit was reached. Fix the
cause, then `sudo systemctl reset-failed openvoca`.

### The service keeps restarting

Check the journal. Restarts stop after `StartLimitBurst` attempts in
`StartLimitIntervalSec` and the unit enters `failed`, so a loop in the logs is
bounded and the reason is at the start of it.

### The database is locked or looks wrong

```bash
ls -l /var/lib/openvoca/
```

The directory must be owned by `openvoca`, or the service cannot write. To
inspect the database without disturbing the service, copy a snapshot:

```bash
sqlite3 /var/lib/openvoca/snapshots/<newest>.db
```

Snapshots are complete and self-contained, unlike a copy of `openvoca.db` made
while the service is running.

### Recovering on another machine

Snapshots cover a lost machine only up to the last deployment. For anything
since then you need what the interface exports, and no single export is
complete:

| Piece | Covers | Gap |
|---|---|---|
| Vocabulary CSV | every word field | no settings at all |
| Settings JSON | preferences | excludes the provider key and custom headers |
| Provider key | model access | must be typed back in |

So a full restore is: deploy, import the vocabulary CSV, import the settings
JSON, then re-enter the provider API key. Do this before you need it.

## Changing the port

```bash
sudo cp /srv/openvoca-src/deploy/openvoca.conf.example /etc/openvoca/openvoca.conf
sudoedit /etc/openvoca/openvoca.conf     # uncomment and edit OPENVOCA_PORT
sudo systemctl restart openvoca
```
Do not edit `/etc/systemd/system/openvoca.service` for this: it is replaced when
the checkout is updated, and editing it loses the change silently.

## Removing

```bash
sudo systemctl disable --now openvoca
sudo rm /etc/systemd/system/openvoca.service
sudo rm -r /opt/openvoca
# /var/lib/openvoca is your data. Deleting it deletes the database.
```

## Uninstalling the assumption of a public network

Nothing in this deployment assumes the service is private except the absence of
authentication. If you expose the port, do the authentication work first.
