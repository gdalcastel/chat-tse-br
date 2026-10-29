IMAGE ?= chatse
PORT ?= 8000

.PHONY: run

run:
	docker build -t $(IMAGE) .
	-docker rm -f chatse >/dev/null 2>&1
	docker run --rm --name chatse -p $(PORT):8000 -e CHATSE_PORT=8000 $(IMAGE)
