# leaf-on-generator

## Running locally with Docker Compose

1. Copy `test_oct2_.h5` to the `backend/app/ml` directory.

2. Copy `best_naip_unet_model.h5` to the `backend/app/ml` directory.

3. Rename `.backend.env.example` to `.backend.env`. Environment settings:
- `AOI_AREA_LIMIT` (integer): Specifies the maximum allowable user-drawn area in square meters.
- `CELERY_BROKER_URL` (string): Leave on default value.
- `CELERY_RESULT_BACKEND` (string): Leave on default value.
- `DB_FILE` (string): Path to sqlite3 database file. Leave on default value.
- `SECRET_KEY` (string): Change to your own unique, strong secret key.

4. Rename `.env.development.example` to `.env.development`. Environment settings:
- `VITE_AOI_AREA_LIMIT` (integer): Specifies the maximum allowable user-drawn area in square meters. Should match limit set on backend.
- `VITE_MAPBOX_ACCESS_TOKEN` (string): Mapbox access token for displaying basemap.

Run the following commands from the root repo directory.

5. Build the `frontend` and `backend` images by running:

```bash
docker compose build
```

6. Start the containers in the background by running:

```bash
docker compose up -d
```

7. Access the application in your browser at `http://localhost:8001`.

8. Stop the containers by running:

```bash
docker compose down
```
