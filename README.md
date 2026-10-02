# WhatsApp Dental Automation

A complete, rule-based WhatsApp Cloud API backend for a dental clinic portfolio demo. It receives Meta webhooks, remembers each customer's state, captures appointment requests, stores message history, supports human handoff, and includes a credential-free local demo API. It never presents a request as a confirmed appointment.

## Architecture

```text
Customer → Meta WhatsApp Cloud API → FastAPI webhook → message parser
         → persistent conversation state → deterministic automation router
         → Supabase/PostgreSQL → WhatsApp service → Customer
```

The application uses Supabase when `SUPABASE_URL` and `SUPABASE_KEY` are set. With neither configured, it uses a persistent local SQLite database, which makes the portfolio demo immediately runnable. WhatsApp sends are suppressed when `DEMO_MODE=true`.

The stack is Python 3.11+, FastAPI, Pydantic, HTTPX, Supabase/PostgreSQL, aiosqlite for local demo persistence, python-dotenv, Uvicorn, and pytest.

## Project structure

```text
app/
  api/                 health, webhook, demo, and protected admin routes
  core/                environment, logging, and clinic configuration
  database/            local persistence and Supabase client
  models/              API models, enums, and domain types
  repositories/        local and Supabase persistence implementations
  services/            automation, WhatsApp, follow-up, and future AI interface
  utils/                phone normalization and webhook parsing
  main.py               application composition
database/schema.sql     Supabase/PostgreSQL schema
tests/                  API/workflow tests and Meta payload fixtures
.env.example
Dockerfile
requirements.txt
```

## Local setup

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env   # Windows; use cp on macOS/Linux
uvicorn app.main:app --reload
```

Open `http://localhost:8000/docs` for Swagger. Useful checks:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/
```

## Environment configuration

Copy `.env.example` to `.env`. Never commit `.env` or expose `SUPABASE_KEY` to a browser.

- `DEMO_MODE=true`: enables `/demo/message` and prevents real Meta sends.
- `SUPABASE_URL`, `SUPABASE_KEY`: switch persistence from local SQLite to Supabase.
- `WHATSAPP_ACCESS_TOKEN`: Meta access token.
- `WHATSAPP_PHONE_NUMBER_ID`: found under WhatsApp > API Setup in the Meta app.
- `WHATSAPP_VERIFY_TOKEN`: a secret string you choose and enter in both Meta and `.env`.
- `WHATSAPP_API_VERSION`: Graph API version, including the `v` prefix.
- `META_APP_SECRET`: from Meta App Settings > Basic; used for webhook HMAC validation.
- `ADMIN_API_KEY`: required in the `X-API-Key` header for every `/admin` route.
- `REQUIRE_WEBHOOK_SIGNATURE=true`: require `X-Hub-Signature-256` during development. Production always requires it.
- `LOCAL_DATABASE_PATH`: local demo SQLite file path.

## Supabase

1. Create a Supabase project.
2. Open SQL Editor, paste [database/schema.sql](database/schema.sql), and run it.
3. Copy the project URL and a server-side key into `.env` as `SUPABASE_URL` and `SUPABASE_KEY`.
4. Restart the app. It now selects the Supabase repository automatically.

The schema provides unique constraints for phone numbers, incoming WhatsApp message IDs, and appointment request keys. Those constraints are the final concurrency-safe idempotency layer. Keep the Supabase key server-side and configure appropriate RLS policies if using a non-service key.

## Demo without WhatsApp

Keep `DEMO_MODE=true`, then send successive requests with the same phone:

```bash
curl -X POST http://localhost:8000/demo/message -H "Content-Type: application/json" -d "{\"phone\":\"+919999999999\",\"message\":\"Hi\"}"
```

Continue with `1`, `Yogita`, `2`, `Tomorrow`, `3`, and `1`. The final appointment contains Yogita, Teeth Whitening, Tomorrow, 12:00 PM, and status `requested`. Inspect it with:

```bash
curl http://localhost:8000/admin/appointments -H "X-API-Key: change-me"
```

Other admin routes are `/admin/leads`, `/admin/conversations`, `/admin/messages`, `/admin/stats`, `/admin/conversations/{phone}`, and POST resume/reset routes under the same conversation URL.

## Meta WhatsApp Cloud API

1. Create an app at Meta for Developers and add the WhatsApp product.
2. In WhatsApp > API Setup, copy the temporary access token and Phone Number ID. A permanent system-user token is preferable for deployment.
3. Meta's test number is supported. Under API Setup, add and verify your own phone as an allowed recipient; test sends only work to recipients listed there.
4. Set `DEMO_MODE=false`, add the token, Phone Number ID, API version, app secret, and your chosen verification token to `.env`.
5. Subscribe the webhook to the WhatsApp `messages` field.

Webhook verification calls `GET /webhook` with `hub.mode`, `hub.verify_token`, and `hub.challenge`. The app compares the token and returns the challenge as plain text. Event delivery uses `POST /webhook`; production verifies the raw request with the Meta app secret and `X-Hub-Signature-256` HMAC-SHA256 header.

### Expose a local webhook

```bash
ngrok http 8000
```

In Meta's webhook configuration, set the callback URL to `https://YOUR-SUBDOMAIN.ngrok.app/webhook` and enter the same verify token used in `.env`. Meta requires public HTTPS. Send a WhatsApp message to the test number and inspect app logs plus `/admin/messages`.

Status/read callbacks and unrelated events are acknowledged without failing. Text, button replies, and list replies are normalized. Media gets a text-only fallback. The Meta client has timeouts and never logs tokens.

## Tests

```bash
python -m pytest -q
```

Tests use isolated local databases and do not contact Meta. Fixtures include text and interactive webhook payloads. A manual fixture call is also possible:

```bash
curl -X POST http://localhost:8000/webhook -H "Content-Type: application/json" --data-binary @tests/fixtures/incoming_text.json
```

## Docker and deployment

```bash
docker build -t whatsapp-automation .
docker run --env-file .env -p 8000:8000 whatsapp-automation
```

On Render, Railway, or similar hosting, connect the repository, set the environment variables in the provider dashboard, and use:

```text
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Use Supabase in deployed environments because container-local SQLite may be ephemeral. Set `ENVIRONMENT=production`, `DEMO_MODE=false`, a strong admin key, the Meta app secret, and the live WhatsApp credentials. Configure Meta's callback as `https://YOUR-DOMAIN/webhook`.

### Free Render portfolio deployment

This repository includes `render.yaml` for a free Render web service. In Render, choose **New > Blueprint**, connect this GitHub repository, verify that the service plan is **Free**, and apply the Blueprint. Render generates the admin key rather than storing it in Git. The initial deployment intentionally keeps `DEMO_MODE=true`, so it works without Meta credentials and makes no WhatsApp API calls.

Free Render services sleep after inactivity and use an ephemeral filesystem. The local demo database can therefore reset after sleep, restart, or redeployment. Add free Supabase credentials in Render when persistent data is required. Switching on real WhatsApp delivery also requires setting the Meta secrets and changing `DEMO_MODE` to `false`.

## Customization and future AI

Clinic name, contact details, hours, treatments, and time slots live only in [app/core/clinic_config.py](app/core/clinic_config.py). Change that module to adapt the workflow to a salon, property agency, school, restaurant, or professional service.

The `AIService` interface is intentionally unimplemented. A later OpenAI or LangGraph adapter can classify free-form intent and draft safe replies while the deterministic workflow continues to own validation and actions:

```text
WhatsApp → FastAPI → Intent Router ─┬→ Deterministic Workflow → validated tools
                                    └→ AI Service → LLM/RAG → business context
```

An LLM must not directly confirm appointments, arbitrarily edit records, or make unrestricted API calls. It should identify an intent; validated backend functions perform the action. Message history already provides future AI context.

## Demo-only boundaries

- Local SQLite is a convenience fallback; Supabase/PostgreSQL is intended for deployment.
- Dates remain the customer's original text and available times are illustrative, not connected to a live clinic calendar.
- Appointment status starts as `requested`; staff confirmation happens separately.
- Human handoff marks the conversation for staff but does not include a staff inbox UI.
- Follow-up querying and generic template sending exist, but no marketing or automatic outreach is enabled. Outside WhatsApp's customer-service window, business-initiated messages generally require approved templates and must follow Meta policies.
- This project does not diagnose dental conditions. Safety routing encourages professional or emergency care where appropriate.
