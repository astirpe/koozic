This folder provides a basic Docker configuration using Docker-compose in order to run a fully
functional KooZic installation. It includes:
- Ubuntu 18.04
- KooZic 2.0.0
- FFmpeg 4.1
- PostgreSQL from Docker hub

# Set up containers

1. Install Docker following the
[official instructions](https://docs.docker.com/engine/installation/)
2. Build:
```
docker-compose build
```
3. Configure:
Edit `docker-compose.yml` and replace `/music` by the music folder you want to share.
4. Run:
```
docker-compose up -d
```

KooZic should now be available at [http://localhost:8069](http://localhost:8069).
Don't forget to add `/mnt/host` in the Folders section.
