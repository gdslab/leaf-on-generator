# leaf-on-generator

## Running locally with Docker Compose

1. Copy `test_oct2_.h5` to the `backend/app/leaf_on_generator` directory.

Run the following commands from the root repo directory.

2. Build the `frontend` and `backend` images by running:

```bash
docker compose build
```

3. Start the containers in the background by running:

```bash
docker compose up -d
```

4. Access the application in your browser at `http://localhost:8001`.

5. Stop the containers by running:

```bash
docker compose down
```
