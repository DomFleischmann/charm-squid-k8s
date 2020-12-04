#! /usr/bin/env python3

import logging
import subprocess

from ops.main import main
from ops.charm import CharmBase
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus, MaintenanceStatus, BlockedStatus

from oci_image import OCIImageResource, OCIImageResourceError

from jinja2 import Template

SQUID_CONF = "/etc/squid/squid.conf"

logger = logging.getLogger(__name__)


class SquidK8SCharm(CharmBase):
    """Class reprisenting this Operator charm."""

    _stored = StoredState()

    def __init__(self, *args):
        """Initialize charm and configure states and events to observe."""
        super().__init__(*args)
        self._stored.set_default(pod_spec=None, allowedurls=set())

        self.framework.observe(self.on.start, self.configure_pod)
        self.framework.observe(self.on.config_changed, self.configure_pod)
        self.framework.observe(self.on.addurl_action, self.on_addurl_action)
        self.framework.observe(self.on.deleteurl_action, self.on_deleteurl_action)

        self.image = OCIImageResource(self, "image")

    def _update_allowed_urls(self, add: str = None, delete: str = None):
        if add:
            self._stored.allowedurls.add(add)
        if delete and delete in self._stored.allowedurls:
            self._stored.allowedurls.remove(delete)

    def _update_squid_config(self, add: str = None, delete: str = None):
        self._update_allowed_urls(add=add, delete=delete)
        squid_config_text = self._get_squid_config_file_text()
        if squid_config_text:
            with open(SQUID_CONF, "w") as f:
                f.write(squid_config_text)
            subprocess.Popen(
                "sleep 1 && kill -HUP `cat /var/run/squid.pid`", shell=True
            )

    def on_addurl_action(self, event):
        url = event.params["url"]
        self._update_squid_config(add=url)

    def on_deleteurl_action(self, event):
        """Handle the deleteurl action."""
        url = event.params["url"]
        self._update_squid_config(delete=url)

    def _get_squid_config_file_text(self):
        squid_config_text = None
        allowed_urls_text = ""
        for url in self._stored.allowedurls:
            allowed_urls_text += f"acl allowedurls dstdomain .{url}\n"
        allowed_urls_text += "http_access allow allowedurls\n"
        with open("template/squid.conf") as template:
            squid_config_text = Template(template.read()).render(
                allowed_urls=allowed_urls_text
            )
        return squid_config_text

    def configure_pod(self, event):
        if not self.unit.is_leader():
            self.unit.status = ActiveStatus("ready")
            return
        self.unit.status = MaintenanceStatus("Applying pod spec")

        # Fetch image information
        try:
            self.unit.status = MaintenanceStatus("Fetching image information")
            image_info = self.image.fetch()
        except OCIImageResourceError:
            self.unit.status = BlockedStatus("Error fetching image information")
            return

        pod_spec = self._make_pod_spec(image_info)

        if self._stored.pod_spec != pod_spec:
            self.model.pod.set_spec(pod_spec)
            self._stored.pod_spec = pod_spec
        self.unit.status = ActiveStatus("ready")

    def _make_pod_spec(self, image_info):
        config = self.config
        ports = [{"name": "squid", "containerPort": config["port"], "protocol": "TCP"}]

        spec = {
            "version": 3,
            "containers": [
                {
                    "name": self.framework.model.app.name,
                    "imageDetails": image_info,
                    "ports": ports,
                }
            ],
        }
        return spec


if __name__ == "__main__":
    main(SquidK8SCharm)
