# Onboarding a new Time Assistant tenant

1. **Create the tenant store repo** from the template:
   ```bash
   gh repo create <org>/<customer>-time-data --private \
     --template <org>/time-data-template
   git clone git@github.com:<org>/<customer>-time-data.git \
     ~/time-data/<customer>
   ```
2. **Provision config + register the tenant:**
   ```bash
   cd ~/.claude/skills/time-assistant
   python3 -m onboarding.provision \
     --tenant <customer> --name "<Name>" --tz <IANA tz> \
     --profile knowledge-worker --integrations timeular,oura \
     --store ~/time-data/<customer> \
     --repo <org>/<customer>-time-data
   ```
3. **Connect integrations.** Ask the customer for the fields listed in
   `integrations/registry.json` → `auth_fields` and pipe them in as JSON:
   ```bash
   echo '{"OURA_ACCESS_TOKEN": "…"}' | python3 onboarding/save_credentials.py
   ```
   They land in `<store>/.credentials.json` (mode `0600`), which the writer
   adds to the store's `.gitignore` first. Nothing is validated at store time —
   confirm by pulling data. `TIME_ASSISTANT_CRED_PROVIDER` is only needed to
   force a non-default source (`env` in CI, `bitwarden` for a vault-backed setup).
4. **Verify:**
   ```bash
   TIME_ASSISTANT_TENANT=<customer> python3 -c \
     "from engine.config import load_tenant_config; from engine.memory import resolve_store; \
      print(load_tenant_config(resolve_store()))"
   ```
5. **Seed classification rules.** Edit `<store>/rules.json` (starts empty) or let
   the assistant learn rules with the customer over the first week.
