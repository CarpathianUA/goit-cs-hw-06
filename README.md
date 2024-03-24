## Demo HTTP and Socket servers in Python

### Run

```bash
docker-compose up -d --build
```

### Test

In a browser go to http://localhost:3000/message and fill a form with your name and message.

### Verify app startup

```bash
docker-compose logs app
```

### Verify database

```bash
docker run --rm -it mongo:7.0.6 mongosh "mongodb://host.docker.internal:27017/homework" --eval "db.messages.find({}).pretty()"
```

### Cleanup

```bash
docker-compose down -v
```
