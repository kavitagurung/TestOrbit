# Teams integration guide

Create a one-way Microsoft Teams Workflows webhook. Store the URL only as `TEAMS_WEBHOOK_URL` in the backend environment. Use the payload builder; never log the URL or require broad Graph/MCP permissions for notification delivery.

## Slack alternative

For simpler channel delivery, configure a Slack Incoming Webhook as `SLACK_WEBHOOK_URL` in the Render backend environment. TestOrbit accepts only HTTPS Slack webhook hosts and posts a compact Block Kit notification; the URL is never sent to the browser or committed.
