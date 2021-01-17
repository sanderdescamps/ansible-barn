#!/usr/bin/env python3

import click
import random
import json
import yaml


TECHNOLOGIES = ['acl', 'ad', 'algorithm', 'amp', 'amq', 'analog', 'ap', 'api', 'app', 'aws', 'backup', 'bchain', 'bin',
                'bit', 'bite', 'bkmrk', 'blog', 'bmp', 'boot', 'bot', 'bug', 'build', 'bus', 'byte', 'captcha', 'cast', 'cd',
                'cert', 'client', 'cloud', 'cmd', 'codec', 'compile', 'compress', 'config', 'core', 'crm', 'cron', 'cyber',
                'dashboard', 'data', 'db', 'dc', 'dcim', 'debug', 'del', 'desk', 'dev', 'dig', 'disk', 'dns', 'doc', 'docker',
                'domain', 'dos', 'dot', 'download', 'elk', 'encode', 'encrypt', 'etcd', 'file', 'find', 'firm', 'flash',
                'format', 'frame', 'fw', 'gcp', 'git', 'gluster', 'gnu', 'hack', 'hash', 'home', 'html', 'icon', 'inbox',
                'int', 'ipam', 'java', 'jdk', 'jre', 'js', 'junk', 'kde', 'kernel', 'key', 'lamp', 'lic', 'link', 'linux',
                'lnk', 'mac', 'macro', 'mail', 'main', 'malware', 'mariadb', 'master', 'mav', 'media', 'mem', 'mgt',
                'miner', 'mirror', 'model', 'mongo', 'msql', 'mx', 'mysql', 'net', 'nfs', 'nginx', 'node', 'ocr',
                'option', 'os', 'output', 'passwd', 'path', 'pltfrm', 'portal', 'print', 'privacy', 'prog', 'prom', 'psql',
                'python', 'rabbitmq', 'raft', 'redis', 'ruby', 'sap', 'sas', 'scanner', 'se', 'sec', 'shell', 'sierra',
                'slave', 'smb', 'spam', 'spool', 'stor', 'storage', 'syslog', 'table', 'tag', 'terminal', 'time', 'unix',
                'url', 'user', 'vault', 'virt', 'wamp', 'web', 'widget', 'wiki', 'window', 'wordpress', 'worker', 'worm',
                'www', 'xml', 'zip']


def _generate_nodes(count, number_unique_hosts=None, prefix="", suffix=""):
    number_unique_hosts = int(
        0.5*count) if not number_unique_hosts else number_unique_hosts
    keyword_list = None
    if number_unique_hosts < len(TECHNOLOGIES):
        keyword_list = random.sample(TECHNOLOGIES, number_unique_hosts)
    else:
        keyword_list = TECHNOLOGIES
        number_unique_hosts = len(TECHNOLOGIES)
    keyword_queue = dict(zip(keyword_list, [1]*number_unique_hosts))
    for i in range(count-number_unique_hosts):
        keyword_queue[random.choice(list(keyword_queue.keys()))] += 1

    hostlist = []
    grouplist = {}
    for keyword, number in keyword_queue.items():
        for i in range(1, number+1):
            hostname = "{}{}{:02d}{}".format(prefix, keyword, i, suffix)
            hostlist.append(hostname)
            join_groups = ["{}_servers".format(keyword)]
            join_groups.append("all_servers")
            if i % 2 == 0:
                join_groups.append("even_servers")
            else:
                join_groups.append("odd_servers")
            if number == 1:
                join_groups.append("single_node_servers")

            for group in join_groups:
                if group not in grouplist:
                    grouplist[group] = []

                grouplist[group] += [hostname]

    return hostlist, grouplist


@click.command()
@click.option('--number', '-n', help='Number of test hosts', type=click.INT, default=100)
@click.option('--prefix', '-p', help='Hostname prefix', type=click.STRING, default="")
@click.option('--suffix', '-s', help='Hostname suffix', type=click.STRING, default="")
@click.argument("destination",type=click.Path())
def main(destination, **kwargs):
    hostlist, grouplist = _generate_nodes(kwargs.get(
        "number", 100), prefix=kwargs.get("prefix"), suffix=kwargs.get("suffix"))
    barn_data = dict(hosts=[],groups=[])
    for host in hostlist:
        barn_data["hosts"].append(dict(
            name=host,
            vars=dict()
        ))
    for group,hosts in grouplist.items():
        barn_data["groups"].append(dict(
            name=group,
            vars=dict(),
            hosts=hosts
        ))
    with open(destination,'w') as file:
        yaml.dump(barn_data, file, indent=2, sort_keys=False)

    click.echo("File generated: {}".format(destination))



if __name__ == '__main__':
    main()
