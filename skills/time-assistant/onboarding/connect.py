"""Which credential fields each provider needs, and where the user gets them.

Capture and storage live in onboarding/save_credentials.py. Nothing here
touches the network: credentials are stored exactly as pasted, and a wrong
value surfaces later as an adapter error."""

PROVIDER_FIELDS = {
    "oura": ["OURA_ACCESS_TOKEN"],
    "timeular": ["EARLY_API_KEY", "EARLY_API_SECRET"],
    "toggl": ["TOGGL_API_TOKEN"],
    "strava": ["STRAVA_CLIENT_ID", "STRAVA_CLIENT_SECRET", "STRAVA_REFRESH_TOKEN"],
}

PROVIDER_PAGES = {
    "oura": "https://cloud.ouraring.com/personal-access-tokens",
    "timeular": "https://profile.timeular.com/#/app/account/developerTools",
    # Toggl → Profile → API Token. Paste the classic 32-char api_token; a
    # toggl_sk_… service-account token is not exchanged for you any more.
    "toggl": "https://track.toggl.com/profile",
    "strava": "https://www.strava.com/settings/api",
}
