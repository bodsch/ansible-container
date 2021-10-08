
# Ansible Role:  `container`


ansible role for docker deployment of generic container applications

[![GitHub Workflow Status](https://img.shields.io/github/workflow/status/bodsch/ansible-container/CI)][ci]
[![GitHub issues](https://img.shields.io/github/issues/bodsch/ansible-container)][issues]
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/bodsch/ansible-container)][releases]

[ci]: https://github.com/bodsch/ansible-container/actions
[issues]: https://github.com/bodsch/ansible-container/issues?q=is%3Aopen+is%3Aissue
[releases]: https://github.com/bodsch/ansible-container/releases


## usage

### container registry

A private registry can be used as the registry.

```yaml
container_registry:
  host: ''
  username: ''
  password: ''
```

## container configuration


```yaml
container:
  - name: workflow
    image: "{{ container_registry }}/workflow:{{ container_tag }}"
    pull: true
    state: started
    restart_policy: always
    dns_servers:
      - "{{ ansible_default_ipv4.address }}"
      networks_cli_compatible: true
      networks:
        - name: coremedia
      capabilities:
        - SYS_ADMIN
      volumes:
        - heapdumps:/coremedia/heapdumps
      published_ports:
        - 40380:8080
        - 40381:8081
        - 40383:40383
        - 40305:5005
      environments:
        DEBUG_ENTRYPOINT: "false"
        # ...
        HEAP_DUMP_FILENAME: workflow-server-heapdump
      properties:
        publisher.maxRecursionDepth: 600
```
## environments

All `environments` entries are persisted to a separate environments file on the target system.

E.g. under `/opt/container/${CONTAINER_NAME}/container.env`

The target directory for persistence can be customized via `container_env_directory`.

## properties

All `properties` entries are persisted to a separate properties file on the target system.

E.g. under `/opt/container/${CONTAINER_NAME}/${CONTAINER_NAME}.properties`

## custom fileds for volumes

The idea behind the cutom_fields is to define corresponding rights in addition to the optional creation of the directories.

**For example:**

One can persist the data directory in the host system for a solr container and also assign the correct rights to this directory.

However, since it is also possible to mount files or sockets in the container via volumes, it is possible here to prevent the creation of a directory using `ignore`.

The following variables can be used:

- `owner`
- `group`
- `mode`
- `ignore`

### Example

```yaml

    volumes:
      - /run/docker.sock:/run/docker.sock:ro
      - /tmp/nginx:/tmp/nginx:ro
      - /dev/foo:/dev/foo:ro
      - testing1:/var/tmp/testing1|{owner="1000",group="1000",mode="0755"}
      - testing2:/var/tmp/testing2|{owner="800",group="999",mode="0700"}
      - testing3:/var/tmp/testing3:rw|{owner="999",group="1000"}
      - testing4:/var/tmp/testing4|{owner="1001",mode="0700"}
      - testing5:/var/tmp/testing5|{owner="1001",mode="0700",ignore=True}
```


## tests

Local tests are executed in a docker container.

Note that this container must provide its own docker daemon (*docker-in-docker*).

```bash
tox -e py39-ansible29 -- molecule converge -s default
```

## filter_plugins

Information of a `docker pull` via the `docker_container` module is cleaned by a filter plugin
and returns only relevant information.

- container
- created
- interne Id
- image prüfsumme

```yaml
"content-management-server": {
    "container": "xxx.dkr.ecr.eu-central-1.amazonaws.com/content-server:latest",
    "created": "2020-09-10T07:01:24.482766886Z",
    "id": "baaa15ee39248ecf2552133ea84c8abe02b6323ee04c2792de73117fa2b8dffb",
    "image": "sha256:e791a446e2c1ed9e5f65c0edb1ca488466caecb648a77331701111f0d9b454b7"
},
"workflow-server": {
    "container": "xxx.dkr.ecr.eu-central-1.amazonaws.com/workflow-server:latest",
    "created": "2020-09-10T07:01:19.379408285Z",
    "id": "b1028d8c0ee9c8090fb17031435b6ce6f93aafde22e973977a1ae2cc6ce2ea6c",
    "image": "sha256:4dc04a576c0237b506a8e2b3fb015019b43d314b1eee11dcde06fef5b09bbdf4"
}
```

## Author and License

- Bodo Schulz

## License

[Apache](LICENSE)

`FREE SOFTWARE, HELL YEAH!`
