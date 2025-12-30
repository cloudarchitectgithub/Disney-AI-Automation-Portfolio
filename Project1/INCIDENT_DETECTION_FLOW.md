# Incident Detection & Triggering Flow

## 🎯 How the System Knows When Something is Down

### The Complete Flow: From Detection to Triage

```
Monitoring System → Alert → N8N Webhook → FastAPI → RAG + LLM → Triage Result
```

---

## 📡 Step 1: Incident Detection (Real-World Monitoring)

### How Systems Detect Problems

In production at Disney, incidents are detected by **monitoring and observability tools**:

#### **1. Infrastructure Monitoring**
- **Prometheus/Grafana**: Monitors Kubernetes pods, nodes, CPU, memory
- **Datadog/New Relic**: Application performance monitoring (APM)
- **CloudWatch (AWS)**: Cloud resource monitoring
- **Custom Metrics**: Business specific metrics (transaction rates, error rates)

#### **2. Application Monitoring**
- **Error Tracking**: Sentry, Rollbar catch application exceptions
- **Log Aggregation**: ELK Stack, Splunk analyze logs for patterns
- **Health Checks**: Kubernetes liveness/readiness probes
- **Synthetic Monitoring**: Pingdom, UptimeRobot test endpoints

#### **3. Alert Rules**
These tools have **alerting rules** that trigger when thresholds are exceeded:

**Example Alert Rules:**
```yaml
# Prometheus Alert Rule
- alert: PodCrashLoop
  expr: rate(kube_pod_container_status_restarts_total[5m]) > 3
  for: 2m
  annotations:
    summary: "Pod {{ $labels.pod }} is in crash loop"
    description: "Pod has restarted {{ $value }} times in 5 minutes"

# Datadog Alert
- name: High Error Rate
  query: sum(last_5m):sum:http.errors{*} > 100
  message: "Error rate exceeded threshold"
```

---

## 🔔 Step 2: Alert Generation

When a monitoring system detects an issue, it generates an **alert**:

### Alert Format (Example)
```json
{
  "alert_id": "alert-12345",
  "title": "Kubernetes Pod Crash Loop",
  "description": "Pod 'api-service-abc123' in namespace 'production' has restarted 15 times in the last 5 minutes",
  "severity": "high",
  "service": "api-service",
  "environment": "production",
  "timestamp": "2024-01-15T10:30:00Z",
  "source": "prometheus",
  "labels": {
    "namespace": "production",
    "pod": "api-service-abc123",
    "container": "api"
  },
  "metrics": {
    "restart_count": 15,
    "time_window": "5m"
  }
}
```

---

## 🌐 Step 3: Alert Routing to N8N

### Integration Options

#### **Option A: Direct Webhook (Current Implementation)**
Monitoring systems send alerts directly to N8N webhook:

```
PagerDuty → N8N Webhook → Workflow
Datadog → N8N Webhook → Workflow
Prometheus Alertmanager → N8N Webhook → Workflow
```

**N8N Webhook URL:**
```
http://n8n-server:5678/webhook/incident-alert
```

#### **Option B: Via Alert Manager (Production Pattern)**
```
Monitoring Tools → Alertmanager → N8N Webhook → Workflow
```

**Alertmanager Configuration:**
```yaml
# alertmanager.yml
route:
  routes:
    - match:
        severity: critical
      receiver: 'n8n-critical'
    - match:
        severity: high
      receiver: 'n8n-high'

receivers:
  - name: 'n8n-critical'
    webhook_configs:
      - url: 'http://n8n-server:5678/webhook/incident-alert'
        send_resolved: false
```

#### **Option C: Via PagerDuty (Common at Disney)**
```
Monitoring → PagerDuty → PagerDuty Webhook → N8N → Workflow
```

**PagerDuty Webhook Integration:**
- PagerDuty sends incident webhooks to N8N
- N8N receives structured incident data
- Workflow processes and routes to triage system

---

## ⚙️ Step 4: N8N Workflow Processing

### Current N8N Workflow (What Happens)

**Node 1: Webhook Trigger**
- Receives POST request from monitoring system
- Extracts incident data from request body
- Validates required fields (title, description, severity)

**Node 2: Create Incident**
- Calls FastAPI: `POST /api/incidents/`
- Creates incident record in system
- Returns incident ID

**Node 3: AI Triage**
- Calls FastAPI: `POST /api/incidents/{id}/triage`
- Triggers RAG + LLM analysis
- Gets triage result (severity, root cause, actions)

**Node 4: Respond/Route**
- Returns triage result to caller
- OR routes to Slack/Teams
- OR creates Jira ticket
- OR pages on-call engineer

### N8N Workflow Code (Simplified)
```json
{
  "nodes": [
    {
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "parameters": {
        "path": "incident-alert",
        "httpMethod": "POST"
      }
    },
    {
      "name": "Create Incident",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "http://python-backend:8001/api/incidents/",
        "method": "POST",
        "body": {
          "title": "={{ $json.body.title }}",
          "description": "={{ $json.body.description }}",
          "severity": "={{ $json.body.severity }}"
        }
      }
    },
    {
      "name": "AI Triage",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "=http://python-backend:8001/api/incidents/{{ $json.id }}/triage",
        "method": "POST"
      }
    }
  ]
}
```

---

## 🧠 Step 5: FastAPI Backend Processing

### Incident Creation (`POST /api/incidents/`)

```python
# What happens:
1. Receives incident data from N8N
2. Creates incident record with status=DETECTED
3. Assigns incident ID
4. Stores in database (currently in-memory, production would use PostgreSQL)
5. Returns incident object
```

### AI Triage (`POST /api/incidents/{id}/triage`)

```python
# What happens:
1. Retrieves incident from database
2. Builds search query: "{incident.description} {incident.service}"
3. RAG Service searches ChromaDB for relevant docs (top 5)
4. LLM Service receives:
   - Incident description
   - Affected service
   - Relevant documentation context
5. LLM analyzes and returns:
   - Severity (P0/P1/P2/P3)
   - Root cause category
   - Likely explanation
   - Recommended actions
6. Updates incident with triage results
7. Returns triage result
```

---

## 📊 Complete Flow Diagram

```
┌─────────────────┐
│  Monitoring     │  Prometheus, Datadog, PagerDuty
│  System         │  detects issue (pod crash, high CPU, etc.)
└────────┬────────┘
         │ Alert (JSON)
         ▼
┌─────────────────┐
│  N8N Webhook    │  Receives alert via HTTP POST
│  /incident-alert│  Extracts: title, description, severity, service
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  N8N Workflow   │  1. Create Incident (POST /api/incidents/)
│                 │  2. AI Triage (POST /api/incidents/{id}/triage)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  FastAPI        │  Creates incident record
│  Backend        │  Status: DETECTED
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  RAG Service    │  Searches documentation:
│  (ChromaDB)     │  - Query: "{description} {service}"
│                 │  - Returns: Top 5 relevant docs
└────────┬────────┘
         │ Relevant docs
         ▼
┌─────────────────┐
│  LLM Service    │  Analyzes with context:
│  (OpenRouter)   │  - Incident description
│                 │  - Relevant documentation
│                 │  - Returns: Severity, root cause, actions
└────────┬────────┘
         │ Triage result
         ▼
┌─────────────────┐
│  Update         │  Incident status: TRIAGED
│  Incident       │  Severity, root_cause, recommended_actions
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  N8N Routes     │  - Send to Slack
│  Result         │  - Create Jira ticket
│                 │  - Page on-call engineer
└─────────────────┘
```

---

## 🔍 Real-World Examples

### Example 1: Kubernetes Pod Crash

**1. Detection:**
```yaml
# Prometheus detects:
kube_pod_container_status_restarts_total{pod="api-service-abc123"} = 15
```

**2. Alert Generated:**
```json
{
  "title": "Pod Crash Loop Detected",
  "description": "Pod api-service-abc123 has restarted 15 times in 5 minutes",
  "severity": "high",
  "service": "api-service",
  "labels": {
    "namespace": "production",
    "pod": "api-service-abc123"
  }
}
```

**3. Sent to N8N:**
```bash
curl -X POST http://n8n:5678/webhook/incident-alert \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Pod Crash Loop Detected",
    "description": "Pod api-service-abc123 has restarted 15 times in 5 minutes",
    "severity": "high",
    "service": "api-service"
  }'
```

**4. RAG Retrieves:**
- Kubernetes troubleshooting docs
- Pod crash loop resolution guides
- Memory/CPU troubleshooting

**5. LLM Analyzes:**
- Severity: P1 (High)
- Root Cause: "Likely OutOfMemoryError or dependency failure"
- Actions: ["Check pod logs", "Review resource limits", "Check database connectivity"]

---

### Example 2: Database Connection Pool Exhausted

**1. Detection:**
```yaml
# Datadog monitors:
database.connection_pool.active > 95% of max
```

**2. Alert:**
```json
{
  "title": "Database Connection Pool Exhausted",
  "description": "Connection pool at 95% capacity, multiple timeout errors",
  "severity": "medium",
  "service": "database"
}
```

**3. RAG Retrieves:**
- Database connection troubleshooting
- Connection pool configuration guides
- Performance optimization docs

**4. LLM Analyzes:**
- Severity: P2 (Medium)
- Root Cause: "Application not releasing connections properly"
- Actions: ["Review connection lifecycle", "Check for connection leaks", "Increase pool size temporarily"]

---

## 🛠️ Integration Points

### How to Connect Real Monitoring Systems

#### **1. Prometheus Alertmanager → N8N**
```yaml
# alertmanager.yml
receivers:
  - name: 'n8n-incident-triage'
    webhook_configs:
      - url: 'http://n8n-server:5678/webhook/incident-alert'
        http_config:
          bearer_token: 'your-token'
```

#### **2. PagerDuty → N8N**
- Enable PagerDuty Webhooks
- Configure webhook URL: `http://n8n-server:5678/webhook/incident-alert`
- Map PagerDuty fields to incident format

#### **3. Datadog → N8N**
- Use Datadog Webhooks integration
- Configure webhook URL
- Map Datadog alert fields

#### **4. Custom Integration**
Any system that can send HTTP POST can trigger:
```python
import requests

alert = {
    "title": "Custom Alert",
    "description": "Something is wrong",
    "severity": "high",
    "service": "my-service"
}

response = requests.post(
    "http://n8n-server:5678/webhook/incident-alert",
    json=alert
)
```

---

## 🎯 Key Points for Interview

### **"How does the system know when something is down?"**

**Your Answer:**
"The system doesn't detect incidents itself - it receives alerts from monitoring systems. Here's the flow:

1. **Monitoring Layer**: Prometheus, Datadog, or PagerDuty continuously monitor infrastructure and applications. They have alert rules (e.g., 'pod restarts > 3 times in 5 minutes').

2. **Alert Generation**: When a threshold is exceeded, the monitoring system generates an alert with details (title, description, severity, affected service).

3. **Webhook Integration**: The alert is sent to N8N via HTTP webhook. N8N acts as the orchestration layer - it's flexible and can integrate with any monitoring system.

4. **Automated Triage**: N8N workflow automatically:
   - Creates an incident record
   - Triggers AI triage (RAG + LLM)
   - Routes the result to the appropriate team

The beauty of this architecture is that it's **monitoring-agnostic** - whether Disney uses PagerDuty, Datadog, or custom monitoring, they all send alerts to the same N8N webhook, and the system handles them uniformly."

---

### **"What if the monitoring system is down?"**

**Your Answer:**
"Great question. The system has several safeguards:

1. **Health Checks**: The FastAPI backend has health endpoints that monitoring systems can check
2. **Graceful Degradation**: If RAG fails, the LLM still works with general knowledge
3. **Manual Triggers**: Engineers can manually create incidents via the dashboard or API
4. **Alerting on the Alerting System**: We'd monitor N8N itself and alert if the webhook is unreachable

In production, I'd add:
- Dead letter queue for failed alerts
- Retry logic with exponential backoff
- Circuit breakers to prevent cascading failures
- Monitoring of the triage system itself"

---

### **"How do you handle alert noise or false positives?"**

**Your Answer:**
"Several strategies:

1. **Severity Filtering**: Only route high/critical alerts to AI triage initially
2. **Confidence Scoring**: LLM returns confidence scores - low confidence alerts can be flagged for manual review
3. **Deduplication**: Group similar alerts (same service, same error) into one incident
4. **Learning Loop**: Track which alerts lead to actual incidents vs false positives, use that to improve filtering

The RAG system helps here too - if retrieved docs don't match the alert, it might indicate a false positive."

---

## 📝 Summary

**Incident Detection Flow:**
1. Monitoring system detects issue → Generates alert
2. Alert sent to N8N webhook → Workflow triggered
3. N8N creates incident → Calls FastAPI
4. FastAPI triggers RAG search → Retrieves relevant docs
5. LLM analyzes with context → Returns triage result
6. Result routed to team → Engineer takes action

**Key Architecture Benefits:**
- ✅ Monitoring-agnostic (works with any alerting system)
- ✅ Automated triage reduces MTTI
- ✅ Context-aware recommendations via RAG
- ✅ Flexible routing via N8N workflows

