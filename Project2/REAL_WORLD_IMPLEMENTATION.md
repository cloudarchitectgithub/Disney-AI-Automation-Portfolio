# Real-World Implementation: How Disney Would Scan Current Costs

## 🎯 The Question: How Does Disney Actually Get Their Current Cost Data?

In the real world, Disney would use **cloud provider APIs** and **billing exports** to get their actual spending data. Here's how it works:

---

## 📊 Real-World Data Sources

### **1. AWS (Amazon Web Services)**

**Method 1: AWS Cost Explorer API**
```python
import boto3

# Connect to AWS Cost Explorer
ce_client = boto3.client('ce', region_name='us-east-1')

# Get current month's costs
response = ce_client.get_cost_and_usage(
    TimePeriod={
        'Start': '2024-12-01',
        'End': '2024-12-31'
    },
    Granularity='MONTHLY',
    Metrics=['UnblendedCost'],
    GroupBy=[
        {'Type': 'DIMENSION', 'Key': 'SERVICE'},
        {'Type': 'DIMENSION', 'Key': 'INSTANCE_TYPE'}
    ]
)

# Returns actual Disney AWS spending data
```

**Method 2: AWS Cost and Usage Reports (CUR)**
- Disney exports detailed billing reports to S3
- System reads CSV files from S3 bucket
- Contains line item detail of every charge

**Method 3: AWS Billing API**
```python
# Get billing data for specific services
billing_client = boto3.client('billingconductor')
response = billing_client.list_billing_groups()
```

---

### **2. GCP (Google Cloud Platform)**

**Method 1: GCP Billing API**
```python
from google.cloud import billing_v1

# Connect to GCP Billing
client = billing_v1.CloudBillingClient()

# Get billing account
billing_account = client.get_billing_account(
    name=f"billingAccounts/{DISNEY_BILLING_ACCOUNT_ID}"
)

# Get cost data
from google.cloud.billing import budget_v1
budget_client = budget_v1.BudgetServiceClient()

# Query actual spending
response = budget_client.list_budgets(
    parent=f"billingAccounts/{DISNEY_BILLING_ACCOUNT_ID}"
)
```

**Method 2: GCP BigQuery Billing Export**
- Disney exports billing data to BigQuery
- System queries BigQuery for cost data
- Real time or near real time cost information

**Method 3: GCP Cost Management API**
```python
from google.cloud import billing_v1

# Get detailed cost breakdown
cost_client = billing_v1.CloudBillingClient()
```

---

### **3. Azure**

**Method 1: Azure Cost Management API**
```python
from azure.identity import DefaultAzureCredential
from azure.mgmt.costmanagement import CostManagementClient

# Authenticate with Azure
credential = DefaultAzureCredential()
client = CostManagementClient(credential, subscription_id=DISNEY_SUBSCRIPTION_ID)

# Query cost data
query_definition = {
    "type": "ActualCost",
    "timeframe": "MonthToDate",
    "dataset": {
        "granularity": "Daily",
        "aggregation": {
            "totalCost": {"name": "PreTaxCost", "function": "Sum"}
        }
    }
}

# Get actual Disney Azure costs
response = client.query.usage(
    scope=f"/subscriptions/{DISNEY_SUBSCRIPTION_ID}",
    parameters=query_definition
)
```

**Method 2: Azure Cost Management Exports**
- Disney sets up automated exports to storage account
- System reads from Azure Blob Storage
- CSV/JSON files with detailed billing

---

## 🔧 How Our System Handles This (Schema Agnostic Layer)

### **The Magic: Our Data Source Abstraction**

Our system uses a **schema agnostic data access layer** that handles all these different formats:

```python
# In production, we'd have:

class AWSDataSource(DataSource):
    """Connects to AWS Cost Explorer API"""
    def __init__(self, aws_access_key, aws_secret_key, region):
        self.ce_client = boto3.client('ce', 
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=region
        )
    
    def query(self, query_params):
        # Query AWS Cost Explorer API
        response = self.ce_client.get_cost_and_usage(...)
        # Normalize to our unified format
        return self._normalize_aws_data(response)

class GCPDataSource(DataSource):
    """Connects to GCP Billing API"""
    def __init__(self, gcp_project_id, billing_account_id):
        self.billing_client = billing_v1.CloudBillingClient()
        self.project_id = gcp_project_id
        self.billing_account = billing_account_id
    
    def query(self, query_params):
        # Query GCP Billing API
        response = self.billing_client.get_billing_account(...)
        # Normalize to our unified format
        return self._normalize_gcp_data(response)

class AzureDataSource(DataSource):
    """Connects to Azure Cost Management API"""
    def __init__(self, subscription_id, tenant_id, client_id, client_secret):
        credential = ClientSecretCredential(tenant_id, client_id, client_secret)
        self.cost_client = CostManagementClient(credential, subscription_id)
    
    def query(self, query_params):
        # Query Azure Cost Management API
        response = self.cost_client.query.usage(...)
        # Normalize to our unified format
        return self._normalize_azure_data(response)
```

---

## 🔄 Real World Workflow

### **Step 1: Initial Setup (One Time)**

1. **Disney provides credentials:**
   - AWS: Access keys with Cost Explorer permissions
   - GCP: Service account with billing viewer role
   - Azure: Service principal with cost reader permissions

2. **System registers data sources:**
```python
# Register AWS
aws_source = AWSDataSource(
    aws_access_key=DISNEY_AWS_KEY,
    aws_secret_key=DISNEY_AWS_SECRET,
    region='us-east-1'
)
data_registry.register("aws", aws_source)

# Register GCP
gcp_source = GCPDataSource(
    gcp_project_id=DISNEY_GCP_PROJECT,
    billing_account_id=DISNEY_BILLING_ACCOUNT
)
data_registry.register("gcp", gcp_source)

# Register Azure
azure_source = AzureDataSource(
    subscription_id=DISNEY_AZURE_SUB,
    tenant_id=DISNEY_TENANT_ID,
    client_id=DISNEY_CLIENT_ID,
    client_secret=DISNEY_CLIENT_SECRET
)
data_registry.register("azure", azure_source)
```

### **Step 2: Baseline Analysis (When User Clicks Button)**

```python
# What happens when "Run Baseline Analysis" is clicked:

1. System queries each provider's API:
   - AWS: Calls Cost Explorer API for current month
   - GCP: Calls Billing API for current month
   - Azure: Calls Cost Management API for current month

2. Data is normalized:
   - Each provider returns different format
   - Our normalizer converts to unified format:
     {
       "resource_id": "...",
       "cloud_provider": "aws",
       "cost_usd": 1234.56,
       "service_category": "compute",
       "usage_metrics": {...}
     }

3. Analysis is performed:
   - Calculate total costs
   - Group by provider
   - Group by service category
   - Identify resource types

4. Baseline is stored:
   - Current state saved to database
   - This becomes the "starting point"
   - All future comparisons use this baseline
```

---

## 🏗️ Production Architecture

### **How It Would Actually Work:**

```
┌─────────────────────────────────────────────────────────┐
│  Disney's Cloud Accounts                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │   AWS    │  │   GCP    │  │  Azure   │            │
│  │ Accounts │  │ Projects │  │   Subs   │            │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘            │
└───────┼─────────────┼──────────────┼───────────────────┘
        │             │              │
        │ API Calls   │ API Calls    │ API Calls
        ▼             ▼              ▼
┌─────────────────────────────────────────────────────────┐
│  Our Cost Optimization Agent                           │
│                                                          │
│  ┌──────────────────────────────────────────────┐      │
│  │  Schema-Agnostic Data Access Layer           │      │
│  │  • AWSDataSource (Cost Explorer API)        │      │
│  │  • GCPDataSource (Billing API)              │      │
│  │  • AzureDataSource (Cost Management API)     │      │
│  └──────────────────────────────────────────────┘      │
│                        │                                │
│                        ▼                                │
│  ┌──────────────────────────────────────────────┐      │
│  │  Cost Normalizer                              │      │
│  │  Converts all formats to unified structure    │      │
│  └──────────────────────────────────────────────┘      │
│                        │                                │
│                        ▼                                │
│  ┌──────────────────────────────────────────────┐      │
│  │  Cost Analyzer                                │      │
│  │  • Baseline Analysis                          │      │
│  │  • Opportunity Detection                      │      │
│  │  • Savings Calculations                      │      │
│  └──────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────┘
```

---

## 🔐 Security & Authentication

### **How Disney Would Secure This:**

1. **Service Accounts / IAM Roles:**
   - AWS: IAM role with Cost Explorer read only permissions
   - GCP: Service account with Billing Viewer role
   - Azure: Service principal with Cost Reader role

2. **Secrets Management:**
   - Credentials stored in AWS Secrets Manager / Azure Key Vault
   - Never hardcoded in application
   - Rotated regularly

3. **Network Security:**
   - API calls over HTTPS
   - VPC endpoints for AWS
   - Private Google Access for GCP

---

## 📋 Interview Talking Points

### **When Asked: "How would Disney actually get their cost data?"**

**Answer:**

"In production, Disney would connect to cloud provider APIs:

1. **AWS**: We'd use the Cost Explorer API or read from Cost and Usage Reports (CUR) exported to S3. The system would authenticate using IAM roles with read only billing permissions.

2. **GCP**: We'd use the Cloud Billing API or query BigQuery if Disney exports billing data there. Authentication via service accounts with billing viewer permissions.

3. **Azure**: We'd use the Cost Management API, authenticating with service principals that have cost reader access.

Our schema-agnostic data access layer abstracts away the differences between these APIs. Each provider returns data in different formats, but our normalizer converts everything to a unified structure. This is what makes the system work across all three providers seamlessly.

When the user clicks 'Run Baseline Analysis', the system:
- Queries each provider's API for current month's costs
- Normalizes the data to our unified format
- Performs analysis to establish the baseline
- Stores this as the starting point for all future comparisons

This baseline then becomes the reference point for finding savings opportunities."

---

## 🎯 Key Technical Points

1. **Real APIs**: Uses actual cloud provider billing APIs
2. **Schema Agnostic**: Handles different data formats automatically
3. **Unified Format**: Normalizes everything to one structure
4. **Secure**: Uses service accounts/IAM roles, not hardcoded credentials
5. **Real Time**: Can query current costs on demand
6. **Scalable**: Works with any number of accounts/projects/subscriptions

---

## 💡 Demo vs. Production

**What We're Showing (Demo):**
- Mock CSV files simulating billing data
- Simulates what the APIs would return

**What Production Would Use:**
- Real API calls to AWS Cost Explorer, GCP Billing, Azure Cost Management
- Actual Disney credentials (stored securely)
- Real time cost data from their accounts

**The Architecture is the Same:**
- Schema agnostic layer handles both
- Same normalization process
- Same analysis logic
- Just different data sources

---

This is how it would work in the real world at Disney! 🎯

