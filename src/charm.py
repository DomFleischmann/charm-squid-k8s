#! /usr/bin/env python3

import logging

# import subprocess

from ops.charm import CharmBase
from ops.main import main
from ops.model import ActiveStatus, MaintenanceStatus, BlockedStatus
from opslib.squid.cluster import SquidCluster
from oci_image import OCIImageResource, OCIImageResourceError

logger = logging.getLogger(__name__)

EXPORTER_CONTAINER = {
    "name": "exporter",
    "image": "prom/node-exporter",
    "ports": [
        {
            "containerPort": 9100,
            "name": "exporter-http",
            "protocol": "TCP",
        }
    ],
}


class SquidCharm(CharmBase):
    """Class reprisenting this Operator charm."""

    def __init__(self, *args):
        """Initialize charm and configure states and events to observe."""
        super().__init__(*args)
        self.image = OCIImageResource(self, "image")

        self.framework.observe(self.on.config_changed, self.configure_pod)
        self.framework.observe(self.on["add_url"].action, self._on_add_url_action)
        self.framework.observe(self.on["delete_url"].action, self._on_delete_url_action)

        self.framework.observe(
            self.on["prometheus-target"].relation_joined,
            self._publish_prometheus_target_info,
        )

        self.cluster = SquidCluster(self, "cluster")
        self.framework.observe(self.on["cluster"].relation_changed, self.configure_pod)

    def _publish_prometheus_target_info(self, event):
        event.relation.data[self.unit]["host"] = self.app.name
        event.relation.data[self.unit]["port"] = str(9100)

    def _on_add_url_action(self, event):
        self.cluster.add_url(event.params["url"])

    def _on_delete_url_action(self, event):
        self.cluster.delete_url(event.params["url"])

    def configure_pod(self, event):
        if not self.unit.is_leader():
            self.unit.status = ActiveStatus()
            return
        try:
            self.unit.status = MaintenanceStatus("Fetching image information")
            image_info = self.image.fetch()

            # if not self.cluster.is_ready():
            #     self.unit.status = BlockedStatus("cluster not ready")
            #     event.defer()
            #     return

            self.unit.status = MaintenanceStatus("Applying pod spec")
            containers = [
                {
                    "name": self.framework.model.app.name,
                    "imageDetails": image_info,
                    "ports": [
                        {
                            "name": "squid",
                            "containerPort": 3128,
                            "protocol": "TCP",
                        }
                    ],
                    "volumeConfig": [
                        {
                            "name": "config",
                            "mountPath": "/etc/squid",
                            "files": [
                                {
                                    "path": "squid.conf",
                                    "content": self.cluster.squid_config,
                                }
                            ],
                        }
                    ],
                }
            ]
            if self.config.get("enable-exporter"):
                containers.append(EXPORTER_CONTAINER)

            self.model.pod.set_spec({"version": 3, "containers": containers})

            self.unit.status = ActiveStatus()
            self.app.status = ActiveStatus()

        except OCIImageResourceError:
            self.unit.status = BlockedStatus("Error fetching image information")
            return


if __name__ == "__main__":
    main(SquidCharm)
