# N8N Workflows

This directory contains N8N workflow configurations for the SRE Incident Triage Agent.

## ⚠️ Important: N8N is Already Set Up!

**You don't need to install N8N separately!** It's already configured in `docker-compose.yml` and runs in a Docker container.

**Just access it at:** http://localhost:5678
- Username: `admin`
- Password: `disney2024`

## Quick Start

1. **Start services**: `make up` or `docker-compose up -d`
2. **Access N8N**: http://localhost:5678
3. **Login**: admin / disney2024
4. **Create workflows** in the UI (or import from files)

## Workflow Ideas

### 1. Incident Triage Workflow
- **Trigger**: Webhook from incident detection system
- **Steps**:
  1. Receive incident webhook
  2. Call backend API to create incident
  3. Trigger AI triage endpoint
  4. Send notification to SRE team
  5. Update incident status

### 2. Resolution Assistant Workflow
- **Trigger**: Manual trigger or scheduled check
- **Steps**:
  1. Get unresolved incidents
  2. For each incident, call resolution API
  3. Format and send suggestions to assigned engineer
  4. Log actions

### 3. Daily Incident Report
- **Trigger**: Scheduled (daily at 9 AM)
- **Steps**:
  1. Query all incidents from last 24 hours
  2. Generate summary statistics
  3. Send report to team

## Importing Workflows

1. Access N8N UI: http://localhost:5678
2. Click "Workflows" → "Import from File"
3. Select workflow JSON file
4. Configure webhook URLs and API endpoints
5. Activate workflow

## Webhook URLs

- **Backend API**: http://python-backend:8001/api/incidents/
- **Triage Endpoint**: http://python-backend:8001/api/incidents/{id}/triage
- **Resolution Endpoint**: http://python-backend:8001/api/incidents/{id}/resolve

## Example Webhook Configuration

When creating workflows, use these internal Docker service names:
- `http://python-backend:8001` (internal)
- `http://localhost:8001` (external/from host)

## Cost Savings

By running N8N locally in Docker instead of cloud-hosted:
- **N8N Cloud**: $20-50/month
- **Local Docker**: $0
- **Savings**: $240-600/year

