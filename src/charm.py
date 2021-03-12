#! /usr/bin/env python3

import logging

# import subprocess

from ops.charm import CharmBase
from ops.main import main
from ops.model import ActiveStatus, MaintenanceStatus, BlockedStatus
from opslib.squid.cluster import SquidCluster
from oci_image import OCIImageResource, OCIImageResourceError

logger = logging.getLogger(__name__)

class SquidCharm(CharmBase):
    """Class reprisenting this Operator charm."""

    def __init__(self, *args):
        """Initialize charm and configure states and events to observe."""
        super().__init__(*args)
        self.image = OCIImageResource(self, "image")

        self.framework.observe(self.on.config_changed, self.configure_pod)

        self.cluster = SquidCluster(self, "cluster")
        self.framework.observe(self.on["cluster"].relation_changed, self.configure_pod)


    def configure_pod(self, event):
        if not self.unit.is_leader():
            self.unit.status = ActiveStatus()
            return
        try:
            self.unit.status = MaintenanceStatus("Fetching image information")
            image_info = self.image.fetch()

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

            self.model.pod.set_spec({"version": 3, "containers": containers})

            self.unit.status = ActiveStatus()
            self.app.status = ActiveStatus()

        except OCIImageResourceError:
            self.unit.status = BlockedStatus("Error fetching image information")
            return


if __name__ == "__main__":
    main(SquidCharm)
