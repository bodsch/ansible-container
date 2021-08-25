
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

### container configuration


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
```

All `environments` entries are persisted to a separate environments file on the target system.

E.g. under `/opt/container/${CONTAINER_NAME}/environment.env`

The target directory for persistence can be customized via `container_env_directory`.


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
