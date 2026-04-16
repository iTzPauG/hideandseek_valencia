# 🕵️ Hide & Seek Valencia

Juego de escondite real en Valencia usando las paradas del metro. Dos equipos (cazadores y fugitivos) se turnan por rondas. Los cazadores usan preguntas para descubrir la parada escondite del fugitivo.

## Estructura del proyecto

```
hideandseek_valencia/
├── backend/          # FastAPI (Python 3.12)
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py       # SQLAlchemy async (Cloud SQL)
│   │   ├── firestore_client.py
│   │   ├── models.py         # User, GameHistory
│   │   ├── auth_utils.py     # JWT + bcrypt
│   │   └── routers/
│   │       ├── auth.py       # /auth/register, /auth/login
│   │       ├── games.py      # /games/create, /join, /start, GET
│   │       ├── players.py    # /players/location, /select-station, /ranking
│   │       ├── questions.py  # /questions/ask, /guess-station
│   │       ├── cards.py      # /cards/play
│   │       └── map.py        # /map/stations, /map/lines
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/         # React + Vite + Leaflet
│   ├── src/
│   │   ├── App.jsx
│   │   ├── store.js          # Zustand global state
│   │   ├── api.js            # Axios client
│   │   ├── pages/
│   │   │   ├── AuthPage.jsx  # Login / Registro
│   │   │   ├── LobbyPage.jsx # Crear / Unirse partida
│   │   │   └── GamePage.jsx  # Partida en curso
│   │   └── components/
│   │       ├── MapView.jsx   # Leaflet + metro lines
│   │       ├── QuestionsView.jsx
│   │       ├── CardsView.jsx
│   │       ├── RankingView.jsx
│   │       └── Timer.jsx
│   ├── Dockerfile
│   └── nginx.conf
├── terraform/        # Infraestructura GCP
│   ├── main.tf       # Cloud Run, Cloud SQL, Firestore, Artifact Registry
│   ├── variables.tf
│   └── outputs.tf
├── scripts/
│   ├── seed_firestore.py   # Paradas metro, cartas, preguntas, retos
│   └── migrate_db.py       # Crea tablas en Cloud SQL
└── docs/
    └── architecture.md
```

## Despliegue rápido

### Prerrequisitos
- `gcloud` autenticado con `pgaespdata@gmail.com`
- `terraform >= 1.7`
- `docker` corriendo localmente
- `python >= 3.12`

### 1. Configurar variables secretas

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Edita terraform.tfvars con tu contraseña de BD y JWT secret
```

### 2. Desplegar todo

```bash
cd terraform
terraform init
terraform apply
```

Esto hace en orden:
1. Crea Artifact Registry
2. Construye y sube imágenes Docker (backend + frontend)
3. Crea Cloud SQL PostgreSQL
4. Crea secretos en Secret Manager
5. Despliega Cloud Run backend y frontend
6. Crea Firestore y ejecuta el seed de datos

### 3. Migrar base de datos

```bash
# Obtén la URL de conexión del output de terraform
export DATABASE_URL="postgresql+asyncpg://appuser:PASSWORD@/hidenseek?host=/cloudsql/hidenseekpau:europe-west1:hidenseek-pg"
cd scripts && python migrate_db.py
```

### 4. Acceder al juego

```bash
terraform output frontend_url
```

## Desarrollo local

### Backend
```bash
cd backend
pip install -r requirements.txt
# Necesitas un PostgreSQL local y credenciales de GCP para Firestore
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost/hidenseek"
export SECRET_KEY="dev-secret"
uvicorn app.main:app --reload --port 8080
```

### Frontend
```bash
cd frontend
npm install --legacy-peer-deps
VITE_API_URL=http://localhost:8080 npm run dev
```

## Notas sobre ubicación en background

Ver [docs/architecture.md](docs/architecture.md#notas-sobre-background-location) para la explicación completa de las limitaciones de iOS/Android y la solución adoptada.
