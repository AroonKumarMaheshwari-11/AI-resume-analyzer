# AI Resume Analyzer — Secure Admin Console

## User-facing page
- The public sidebar contains **no Admin entry**.
- Streamlit's developer toolbar/menu is disabled with `client.toolbarMode = "minimal"`, so the **Deploy** control is not exposed to normal users.
- The public page has a boot animation and a separate navigation loading overlay.

## Open the private admin console
Use the hidden admin route:

`http://localhost:8501/?admin=1`

The route is not linked anywhere in the public UI. It still requires username + password authentication.

## Secure first-run initialization

There is intentionally **no public "create admin" button without protection**. On first run, create:

`.streamlit/secrets.toml`

from the included example and set:

```toml
ADMIN_USERNAME = "your_admin_username"
ADMIN_PASSWORD = "your_long_unique_password"
ADMIN_SETUP_KEY = "a-random-24-plus-character-bootstrap-key"
```

The setup key is required to bootstrap the local admin credential file. After setup, the password is stored only as a salted PBKDF2-HMAC-SHA256 hash (310,000 iterations).

Restart Streamlit and open `?admin=1`. Enter the setup key once, choose the admin username/password, then log in normally.

**Never commit `secrets.toml`, `admin_auth.json`, or activity logs.**

## Admin security
- Username + password authentication
- Salted PBKDF2-HMAC-SHA256 password hashing
- Constant-time password comparison
- Five failed login attempts trigger a temporary lock
- 30-minute rolling authenticated session
- Secure logout
- Password changes require the current password
- Admin setup requires a separate bootstrap key
- No plaintext password is written to activity logs
- Public UI does not expose the admin route
- Developer/Deploy toolbar is disabled for normal users

## Activity dashboard
The dashboard records safe audit events such as:
- `app_opened`
- `analysis_started`
- `analysis_completed`
- `analysis_failed`
- `admin_setup_failed`
- `admin_account_created`
- `admin_login`
- `admin_login_failed`
- `password_changed`
- `password_change_failed`
- `admin_logout`

Resume text itself is not stored in the audit log. Analysis events store limited metadata such as filename, file size, ATS score, detected-skill counts, career category, and timestamps.

## Production note
For a real public deployment, use HTTPS, a proper persistent database (SQLite/PostgreSQL), a secret manager, rate limiting/WAF, and an external session/authentication layer. The local JSONL audit file is suitable for this standalone project but is not a replacement for a production audit database.
