# squid-k8s Charm

## Overview

This is a Kuberentes Charm to deploy [Squid Cache](http://www.squid-cache.org/).

Sugested Actions for this charm:
* Pass custom squid.conf to the container
* Stop/Start/Restart the squid service
* Set ftp, http, https proxies

## Quickstart

If you don't have microk8s and juju installed executing the following commands:
```
sudo snap install juju --classic
sudo snap install microk8s --classic
juju bootstrap microk8s
juju add-model squid
```

Afterwards clone the repository and deploy the charm
```
git clone https://github.com/DomFleischmann/charm-squid-k8s.git
cd charm-squid-k8s
git submodule update --init
juju deploy .
```
Check if the charm is deployed correctly with `juju status`

## Contact
 - Author: Dominik Fleischmann <dominik.fleischmann@canonical.com>
 - Bug Tracker: [here](https://github.com/DomFleischmann/charm-squid-k8s)
