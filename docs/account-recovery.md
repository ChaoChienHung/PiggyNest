# Account recovery

## User flow

Email is the login identifier; username is the display name. A forgotten username does not prevent signing in, but the sign-in page offers a reminder. The user enters their registered email and receives the username at that address. The response is the same whether the account exists or not.

For a forgotten password, the user enters their email, receives an eight-digit code, and submits the code with a new password. The code expires after ten minutes, is usable once, and permits five incorrect attempts. A new request replaces the prior code. Requests for the same account are limited to one message per minute. The user signs in again after a successful reset; existing bearer tokens are invalidated by incrementing the account's token version.

The API never returns a username or reset code to the requester. It stores only an HMAC digest of the code, keyed by the server secret. The mail sender uses TLS SMTP, and credentials come from environment variables. If mail is not configured, the request endpoint returns 503 rather than pretending an email was sent. Mail delivery failures are logged by the server, without logging codes.

## Configuration and limits

Set `SMTP_HOST`, `SMTP_PORT` (default `465`), `SMTP_FROM`, and optionally `SMTP_USERNAME` and `SMTP_PASSWORD` in the backend environment. Use an SMTP server that supports implicit TLS. Set a stable, high-entropy `SECRET_KEY`; a server restart with a new key invalidates outstanding reset codes and login tokens. Keep these values out of Git. The local Bob and Ludwig email addresses cannot receive recovery mail unless a matching mailbox or test mail service is configured.

The application does not yet verify email ownership at registration. Recovery proves control of the mailbox at reset time; email verification should be added before treating the registered address as an established contact channel. Account-level cooldown and attempt limits are implemented; a deployment with multiple workers should also apply a shared IP-based rate limit at its gateway. Outbound mail delivery and abuse limits require deployment-level monitoring.

## Implementation areas

Start from the [repository guide](../README.md#repository-guide). The forms and routes are in [`frontend/`](../frontend/). Account, challenge, mail, and token checks are in [`backend/`](../backend/). Recovery state is stored in the local `data/` database; no codes are written to files.

The code and one-time use behavior follow the [OWASP Forgot Password Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html). Authentication response wording and token invalidation follow the [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html).
