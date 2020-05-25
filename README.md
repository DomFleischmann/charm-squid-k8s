# squid-k8s Charm

## Overview

This is a Kuberentes Charm to deploy [Squid Cache](http://www.squid-cache.org/).

Sugested Actions for this charm:
* Set allowed URLs
  Possible way to run action: `juju run-action squid/0 addurl url=google.com`
* Stop/Start/Restart the squid service - done
  Run like this: `juju run-action squid/0 restart`
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

To test the `addurl` action open another terminal and type the following command:
`export https_proxy=http://<squid-ip>:3128`

Where squid-ip is the Squid App Address shown in `juju status`

Now when executing `curl https://www.google.com` squid will block access to the url

Execute the `addurl` action:
`juju run-action squid/0 addurl url=google.com`

Now when executing `curl https://www.google.com` it will give you the google output.

## Contact
 - Author: Dominik Fleischmann <dominik.fleischmann@canonical.com>
 - Bug Tracker: [here](https://github.com/charmed-osm/charm-squid-k8s)
