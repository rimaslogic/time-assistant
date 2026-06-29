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
3. **Connect integrations.** For each integration in the config, store its
   `auth_fields` (see `integrations/registry.json`) wherever the tenant's
   credential provider expects them:
   - `env` provider → export the vars before running.
   - `bitwarden` provider → `bw` vault items named exactly as the auth fields.
   - `keychain` provider → `security add-generic-password -s <FIELD> -a $USER -w`.
   Set `TIME_ASSISTANT_CRED_PROVIDER` accordingly.
4. **Verify:**
   ```bash
   TIME_ASSISTANT_TENANT=<customer> python3 -c \
     "from engine.config import load_tenant_config; from engine.memory import resolve_store; \
      print(load_tenant_config(resolve_store()))"
   ```
5. **Seed classification rules.** Edit `<store>/rules.json` (starts empty) or let
   the assistant learn rules with the customer over the first week.
