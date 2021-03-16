
ansible role for docker deployment of generic container applications

[![GitHub Workflow Status](https://img.shields.io/github/workflow/status/bodsch/ansible-container/CI)][ci]
[![GitHub issues](https://img.shields.io/github/issues/bodsch/ansible-container)][issues]
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/bodsch/ansible-container)][releases]

[ci]: https://github.com/bodsch/ansible-container/actions
[issues]: https://github.com/bodsch/ansible-container/issues?q=is%3Aopen+is%3Aissue
[releases]: https://github.com/bodsch/ansible-container/releases


Als Registry kann eine private Registry eingesetzt werden.

## usage

### Konfiguration der Registry

```
container_registry:
  host: ''
  username: ''
  password: ''

```

### Konfiguration der Container

```
container:
  - name: workflow-server
    image: "{{ container_registry.aws_ecr }}/workflow-server:{{ coremedia_version }}"
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

Alle `environments` Einträge werden auf dem Zielsystem in eine seperate environments Datei persistiert.

Z.B. unter `/etc/ccontainer/${CONTAINER_NAME}/environment.env`


## tests

Lokale Tests werden in einem docker container ausgeführt.

Hier ist zu beachten, dass dieser einen eigenen docker-daemon zur Verfügung stellen muss (*docker-in-docker*).

```
$ tox -e py39-ansible29 -- molecule converge -s default
```

## filter_plugins

Information eines `docker pull`s über das `docker_container` Modul wird durch ein Filter Plugin
bereinigt und gibt anschließend nur noch relevante Informationen zurück.

- container
- created
- interne Id
- image prüfsumme

```
"content-management-server": {
    "container": "750859870390.dkr.ecr.eu-central-1.amazonaws.com/content-server:latest",
    "created": "2020-09-10T07:01:24.482766886Z",
    "id": "baaa15ee39248ecf2552133ea84c8abe02b6323ee04c2792de73117fa2b8dffb",
    "image": "sha256:e791a446e2c1ed9e5f65c0edb1ca488466caecb648a77331701111f0d9b454b7"
},
"workflow-server": {
    "container": "750859870390.dkr.ecr.eu-central-1.amazonaws.com/workflow-server:latest",
    "created": "2020-09-10T07:01:19.379408285Z",
    "id": "b1028d8c0ee9c8090fb17031435b6ce6f93aafde22e973977a1ae2cc6ce2ea6c",
    "image": "sha256:4dc04a576c0237b506a8e2b3fb015019b43d314b1eee11dcde06fef5b09bbdf4"
}
```
