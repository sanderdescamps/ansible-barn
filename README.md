# Ansible-barn
Ansible-barn or Barn in short is a central variable server for Ansible. Barn was designed to provide an single location for all variables. Variables can be updated via ansible-task, api, file import and in the future also via cli. 

## Installation

### Client (Ansible)

Install Barn plugins as user (no sudo!!)

**!!Barn has not been tested on Ansible 2.10!!**

    bash ./ansible-plugins/install.sh

### Barn-server

Clone the repo

Start the barn server with docker compose

    cd ./barn-server/
    docker-compose up -d

## Inventory

### Using Barn inventory

With config file

    ansible all -i barn.yaml -m setup

With default config (see bellow)

    ansible all -i @barn -m setup

### Using @barn as inventory

#### Default connection file

The inventory plugin will search for the connection info in following files. 

* /etc/barn/barn.yml (/etc/barn/barn.yaml)
* ~/.barn.yml (~/.barn.yaml)

**Example barn.yml**

    ---
    plugin: barn
    barn_user: sdescamps
    barn_password: testpassword
    barn_url: https://127.0.0.1:443
    validate_certs: false
    fetch_variables: false


    ---
    plugin: barn
    barn_user: sdescamps
    barn_password: testpassword
    barn_host: 127.0.0.1            #barn_host is deprecated in favor of barn_url
    barn_port: 5000                 #barn_port is deprecated in favor of barn_url
    fetch_variables: false

    ---
    plugin: barn
    barn_user: sdescamps
    barn_password: testpassword
    barn_hostname: 127.0.0.1        #barn_hostname is deprecated in favor of barn_url
    barn_port: 5000
    fetch_variables: false

#### Default connection file

add `barn` in the [inventory-enabled](https://docs.ansible.com/ansible/latest/reference_appendices/config.html#inventory-enabled) list in the file 

    [inventory]
    enable_plugins = barn, host_list, script, auto, yaml, ini, toml

### Generate Ansible inventory file

Write the full inventory to a json-file. The json-file can directly be read by Ansible. No authentication required. 

    curl -s http://127.0.0.1:5000/inventory_file > test_inventory.json

### Ansible without DNS server with Barn

Usually you put the fqdn in the inventory file and a DNS server provides an IP address which Ansible uses to connect to the server. But there are cases where you can't rely on DNS. Therefore in Ansible you can define the `ansible_host` variable with the IP address in the inventory file. This is also possible with Barn. The variables stored in Barn will be injected in the root of the Ansible facts of the host (if `fetch_variables=True`). If you define `ansible_host` as a variable in Barn, Ansible will use that IP to connect to the host. 

## Ansible tasks

### barn_read

    - name: Read info from Barn
      barn_read:
        barn_host: "127.0.0.1"
        barn_user: "admin"
        barn_password: "admin"
        barn_port: 5000
        exclude: test
        load_to_facts: False
      register: output_barn_read

### barn_write

    - name: Add host to Barn
      barn_write:
        barn_host: "127.0.0.1"
        barn_user: "admin"
        barn_password: "admin"
        barn_port: 5000
        state: present
        vars: 
          custom_variable: with_custom_value
          host_ip: 10.6.51.32
          environment: development
          installed_packages:
            - "nano"
            - "vim"
            - "tcpdump"

## Upload data

Browse to [http://127.0.0.1:5000/upload](http://127.0.0.1:5000/upload)

    #Upload a file
    groups:
    - name: dns_servers
      child_groups: []
      hosts: []
      vars: {}
    - name: all_servers
      child_groups:
      - dns_servers
      hosts: []
      vars: {}
    hosts:
    - name: srvdns01.myhomecloud.be
      vars:
        creationdate: vandaag
        deploytime: today
        env_environment: development
        tags:
        - tag1
        - tag3
        test: testvariable
    - name: srvdns02.myhomecloud.be
      vars: {}

## API documentation

    https://127.0.0.1:5000/swagger/


## Roadmap

Barn is still under development. Version 1.0 is the first version which is publicly released. Version 1.0 should not be considered stable nor production ready. In the future new features will be added and issues will be fixed. Bellow a list of some of the features which will be added in the future. 

* Test Barn on Ansible 2.10 (Barn v1.1)
* Extend base features 
* BarnCLI
* Review token authentication and permissions assignment
* Variable encryption
* Improve documentation
* ...


## A word from the author

I'm a Linux system engineer and work as a consultant at Axxes. I started Barn as a personal weekend project. I'm not a great programmer but I know how to write code. For me, this project is a wonderful learning experiance. If you have any ideas, suggestions or feedback please reach out to me and let me know. I'm curious about what other people think about this project. 

