# Sign-in moves to auth.rvanegas.co

Decided 2026-11-08 (rvanegas-site
`planning/task/one-sign-in-for-every-project-at-auth-rvanegas-co.md`, which
is the design): noesis's OAuth server becomes a
service of its own, `auth.rvanegas.co`, issuing signed JWT access tokens.

dianoia's part, in Phase 1: `src/api/auth.py` verifies a person's token
against auth's JWKS (issuer, audience, expiry, `client_id` in what is now
`NOESIS_CLIENT_IDS`, renamed `AUTH_CLIENT_IDS`) instead of asking noesis's
`/me`, and the minute's cache goes with it. noesis's own `NOESIS_TOKEN` is
unchanged.
