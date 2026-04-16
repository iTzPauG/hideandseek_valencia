# Hide & Seek Valencia — Arquitectura

## Visión general

Juego de escondite real en Valencia usando las paradas del metro. Dos equipos (cazadores y fugitivos) se turnan por rondas. Los cazadores usan preguntas para descubrir la parada escondite del fugitivo.

## Stack tecnológico

| Capa | Tecnología | Hosting |
|------|-----------|---------|
| Frontend | React + Vite + Leaflet | Cloud Run |
| Backend | FastAPI (Python 3.12) | Cloud Run |
| Base de datos relacional | Cloud SQL (PostgreSQL 15) | GCP |
| Base de datos documental | Firestore | GCP |
| Imágenes Docker | Artifact Registry | GCP |
| Infraestructura | Terraform | — |
| Secretos | Secret Manager | GCP |

## Diagrama de componentes

```
[Móvil jugador]
      │
      ▼
[Cloud Run: React Frontend]
      │  REST + WebSocket
      ▼
[Cloud Run: FastAPI Backend]
      ├──► [Cloud SQL: PostgreSQL]   ← usuarios, partidas, ranking
      └──► [Firestore]               ← estado partida, cartas, preguntas, mapa, ubicaciones
```

## Firestore — colecciones

| Colección | Descripción |
|-----------|-------------|
| `metro_stations` | Paradas del metro con coordenadas y líneas |
| `metro_lines` | Líneas con color oficial y lista de paradas |
| `cards` | Mazo completo de cartas (tiempo, poder, reto) |
| `questions` | Preguntas disponibles por categoría (radar, match, foto) |
| `challenges` | Retos con dificultad, recompensa y penalización |
| `games` | Estado de cada partida activa |
| `game_players` | Jugadores en una partida, rol, ubicación en tiempo real |

## Cloud SQL — tablas

| Tabla | Descripción |
|-------|-------------|
| `users` | Registro de usuarios (email, hash contraseña) |
| `game_history` | Historial de partidas con tiempo conseguido |

## Flujo de partida

1. Jugador A crea partida → recibe código de 6 caracteres
2. Jugador B introduce código → ambos en sala de espera
3. Jugador A pulsa "Empezar" → se sortea quién se esconde primero
4. **Fase escondite (30 min):** fugitivo usa metro, selecciona parada en mapa
5. **Fase búsqueda:** cazadores hacen preguntas, descartan mapa, seleccionan parada
6. Al acertar o agotar tiempo → siguiente ronda con roles invertidos
7. Al acabar todas las rondas → ganador por mayor tiempo escondido

## Notas sobre background location

El requisito de compartir ubicación con móvil suspendido es **parcialmente posible**:
- **iOS:** Background location requiere permiso "Always Allow" y la app debe estar en modo "significant location changes". No garantizado con pantalla apagada.
- **Android:** Se puede usar un Service en background, pero los fabricantes (Xiaomi, Samsung) matan procesos agresivamente.
- **Solución adoptada:** El frontend usa la Geolocation API con `watchPosition`. El backend recibe pings de ubicación cada 15s. Si el móvil se suspende, la última ubicación conocida se mantiene en Firestore hasta el siguiente ping. Se muestra un aviso en la UI pidiendo mantener la pantalla activa o usar modo "no molestar" en lugar de apagar pantalla.
