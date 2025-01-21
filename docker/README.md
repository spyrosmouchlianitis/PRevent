# pr-event Dockerfile

### To build image:

```bash
docker build -t pr-event .
```

### To build and push image to our GCR (with buildx):

```bash
PR_EVENT_TAG=1.0
docker buildx build \
  --platform linux/arm64/v8,linux/amd64 \
  --push --pull \
  -t us-docker.pkg.dev/apiiro/public-images/pr-event:$PR_EVENT_TAG \
  .
```

### To run docker container:

```bash
PR_EVENT_TAG=1.0

docker run --rm -it us-docker.pkg.dev/apiiro/public-images/pr-event:$PR_EVENT_TAG

# Enter to shell
docker run --rm -it --entrypoint /bin/sh us-docker.pkg.dev/apiiro/public-images/pr-event:$PR_EVENT_TAG
```

### To observe existing images: [us-docker.pkg.dev/apiiro/public-images/pr-event]()
