#!/bin/sh
# Wait until the provisioner has loaded the dashboard into Grafana's database,
# then set it as the home dashboard for the org via the API.
# This affects all users including anonymous sessions.

echo "Waiting for Kapampangan dashboard to be provisioned..."
until curl -sf "http://admin:admin@grafana:3000/api/dashboards/uid/kapampangan-main" > /dev/null; do
  sleep 2
done

echo "Dashboard found. Setting as org home dashboard..."
curl -s -X PUT "http://admin:admin@grafana:3000/api/org/preferences" \
  -H "Content-Type: application/json" \
  -d '{"homeDashboardUID":"kapampangan-main"}'

echo "Done."
