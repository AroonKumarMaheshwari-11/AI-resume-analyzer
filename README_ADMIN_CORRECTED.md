# Corrected Admin + Loading UI

This build fixes the previous admin/loading implementation:

- Public sidebar has no Admin entry.
- Streamlit developer toolbar is disabled with `client.toolbarMode = "minimal"` so Deploy/developer controls are not exposed.
- Initial boot animation is rendered by Streamlit itself and shown once per browser session using `st.session_state`; it no longer depends on injected JavaScript.
- Career/job links show a small CSS loading spinner on click and stop after the navigation transition.
- Admin is available only through the hidden `?admin=1` route and still requires authentication.
- First-run admin creation cannot be claimed by an unauthenticated visitor: it requires `ADMIN_SETUP_KEY` unless `ADMIN_USERNAME`/`ADMIN_PASSWORD` are already configured as secrets/environment variables.
- Passwords are stored as salted PBKDF2-HMAC-SHA256 hashes.
- Failed logins are rate-limited with a temporary lock.
- Password change requires the current password.
- Activity audit records app opens, resume uploads, analysis start/completion/failure, admin login/logout, password changes, and validation failures without storing resume contents.

## Local admin setup

Copy:

`.streamlit/secrets.toml.example`

to:

`.streamlit/secrets.toml`

and replace the values. Then:

```powershell
streamlit run app.py
```

Open:

`http://localhost:8501/?admin=1`

For a production deployment, use HTTPS, a persistent database, platform secrets, and a proper authentication/session layer.
