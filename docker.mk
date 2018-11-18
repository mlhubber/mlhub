d_build:
	docker build --rm --force-rm -t $(APP) .

d_rebuild:

	docker build --no-cache --rm --force-rm -t $(APP) .

# See https://dzone.com/articles/docker-x11-client-via-ssh

d_run:
	xhost +
	docker run -it --rm --network=host --env="DISPLAY" -v ~/.Xauthority:/root/.Xauthority:rw $(APP)

d_tag:
	docker tag $(APP) kayon/$(APP)

d_push: tag
	docker login docker.io -u kayon -p $(shell cat docker.pwd)
	docker push kayon/$(APP)

d_pull:
	docker pull kayon/$(APP)

d_exited:
	docker ps -a | grep Exited

clean.ps:
	docker ps -a | grep Exited | awk '{print $$1}' | xargs docker rm

clean.images:
	docker images | egrep "(weeks|months) ago" | awk '{print $$3}' | xargs docker rmi

realclean::
	rm -rf /var/lib/docker

d_list:
	docker ps -a
