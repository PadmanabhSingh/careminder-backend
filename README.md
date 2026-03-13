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
`Authorization: Bearer <supabase_access_token>`

## Environment Variables
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`

