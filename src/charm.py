#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
# Copyright © 2020 Dominik Fleischmann dominik.fleischmann@canonical.com

"""Operator Charm main library."""
# Load modules from lib directory
import logging

import setuppath  # noqa:F401
from ops.charm import CharmBase
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus, MaintenanceStatus


class SquidK8SCharm(CharmBase):
    """Class reprisenting this Operator charm."""

    state = StoredState()

    def __init__(self, *args):
        """Initialize charm and configure states and events to observe."""
        super().__init__(*args)
        # -- standard hook observation
        self.framework.observe(self.on.install, self.on_install)
        self.framework.observe(self.on.start, self.on_start)
        self.framework.observe(self.on.config_changed, self.on_config_changed)
#        self.framework.observe(self.on.addconfig.action, self.on_addconfig_action)
        # -- initialize states --
        self.state.set_default(installed=False)
        self.state.set_default(configured=False)
        self.state.set_default(started=False)

    def make_pod_spec(self):
        config = self.framework.model.config
        ports = [{"name": "squid", "containerPort": config["port"], "protocol": "TCP"}]

        spec = {
            "containers": [{
                "name": self.framework.model.app.name,
                "image": config["image"],
                "ports": ports,
            }],
        }

        return spec

    def _apply_spec(self, spec):
        # Only apply the spec if this unit is a leader
        if self.framework.model.unit.is_leader():
            self.framework.model.pod.set_spec(spec)
            self.state.spec = spec

    def on_install(self, event):
        """Handle install state."""
        self.unit.status = MaintenanceStatus("Installing charm software")
        # Perform install tasks
        self.unit.status = MaintenanceStatus("Install complete")
        logging.info("Install of software complete")
        self.state.installed = True

    def on_config_changed(self, event):
        """Handle config changed."""

        if not self.state.installed:
            logging.warning("Config changed called before install complete, deferring event: {}.".format(event.handle))
            self._defer_once(event)

            return

        if self.state.started:
            # Stop if necessary for reconfig
            logging.info("Stopping for configuration, event handle: {}".format(event.handle))
        # Configure the software
        logging.info("Configuring")
        self.state.configured = True

    def on_start(self, event):
        """Handle start state."""

        if not self.state.configured:
            logging.warning("Start called before configuration complete, deferring event: {}".format(event.handle))
            self._defer_once(event)

            return
        self.unit.status = MaintenanceStatus("Applying pod spec")
        # Start software
        new_pod_spec = self.make_pod_spec()
        self._apply_spec(new_pod_spec)

        self.unit.status = ActiveStatus("Unit is ready")
        self.state.started = True
        logging.info("Started")

    def _defer_once(self, event):
        """Defer the given event, but only once."""
        notice_count = 0
        handle = str(event.handle)

        for event_path, _, _ in self.framework._storage.notices(None):
            if event_path.startswith(handle.split('[')[0]):
                notice_count += 1
                logging.debug("Found event: {} x {}".format(event_path, notice_count))

        if notice_count > 1:
            logging.debug("Not deferring {} notice count of {}".format(handle, notice_count))
        else:
            logging.debug("Deferring {} notice count of {}".format(handle, notice_count))
            event.defer()

    def on_addconfig_action(self, event):
        """Handle the example_action action."""
        event.log("Hello from the example action.")
        event.set_results({"success": "true"})


if __name__ == "__main__":
    from ops.main import main
    main(SquidK8SCharm)
