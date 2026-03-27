# CareMinder Backend

## Base URL
Production:
`https://careminder-backend.onrender.com`

## Main Endpoints
- `GET /health`
- `GET /docs`
- `POST /api/v1/biomarkers/ingest`
- `GET /api/v1/biomarkers`
- `GET /api/v1/biomarkers/latest`
- `POST /api/v1/thresholds`
- `GET /api/v1/alerts`
- `POST /api/v1/devices/register`
- `POST /api/v1/devices/ingest-json`
- `GET /api/v1/me`
- `GET /api/v1/biomarkers/mine`
- `GET /api/v1/biomarkers/latest/mine`
- `GET /api/v1/provider/patients`
- `GET /api/v1/provider/patient/{user_id}/biomarkers`
- `GET /api/v1/provider/patient/{user_id}/alerts`
- `POST /api/v1/provider/clinical-notes`
- `GET /api/v1/provider/patient/{user_id}/notes`
- `POST /api/v1/summaries/generate`
- `GET /api/v1/summaries/latest`
- `GET /api/v1/summaries`
- `POST /api/v1/reports/generate`
- `GET /api/v1/reports`

## Auth
Use:
`Authorization: <supabase_access_token>` // can generate the token by adjusting id and password of user or provider in get_token.py under scripts folder in repo 

## Environment Variables
- SUPABASE_URL
- SUPABASE_ANON_KEY
- SUPABASE_SERVICE_ROLE_KEY
- OPENAI_API_KEY
- PASSWORD_RESET_REDIRECT_URL
- WITHINGS_API_BASE
- WITHINGS_REDIRECT_URI
- WITHINGS_CLIENT_SECRET
- WITHINGS_CLIENT_ID
- OPENWEATHER_API_KEY

