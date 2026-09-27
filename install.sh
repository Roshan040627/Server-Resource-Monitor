#!/bin/bash

echo "Installing Server Resource Monitor..."

sudo mkdir -p /opt/server_resource_monitor

sudo cp -r ./* /opt/server_resource_monitor/

sudo pip3 install psutil

sudo cp server-resource-monitor.service /etc/systemd/system/

sudo systemctl daemon-reload

sudo systemctl enable server-resource-monitor

sudo systemctl start server-resource-monitor

echo "Installation completed."

echo "Checking service status..."

sudo systemctl status server-resource-monitor

