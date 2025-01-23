# PRevent dockerfile

1. Build the app locally using the provided `Dockerfile`:

```bash
docker buildx build -t prevent .
```

2. Build and Push the image to your container registry (e.g. GCR):

```bash
PREVENT_PATH=<your.artifact.registry>
PREVENT_TAG=1.0

docker buildx build \
  --platform linux/arm64/v8,linux/amd64 \
  --push --pull \
  -t $PREVENT_PATH:$PREVENT_TAG \
  ../.
```

3. Run the container locally:

```bash
PREVENT_PATH=<your.artifact.registry>
PREVENT_TAG=1.0
docker run --rm -it $PREVENT_PATH:$PREVENT_TAG
```

4. Access the container locally:

```bash
PREVENT_PATH=<your.artifact.registry>
PREVENT_TAG=1.0
docker run --rm -it --entrypoint /bin/sh $PREVENT_PATH:$PREVENT_TAG
```
