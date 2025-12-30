# Project 2: AI Agent Architecture Explained

## 🎯 Framework: N8N Based Agentic AI Platform

**The AI agents in Project 2 are built on N8N**, which is a low code/no code workflow automation platform.

N8N serves as the **orchestration layer** that:
- Receives triggers (webhooks, scheduled tasks, events)
- Orchestrates workflows between different services
- Calls the FastAPI backend for analysis
- Sends notifications and alerts
- Enables non developers to create and modify agent workflows

## 🧠 The "Brain": Rule Based Cost Analyzer + Price Monitor

**The decision making "brain" is the [CostAnalyzer](backend/app/services/cost_analyzer.py)**, which uses **rule based AI logic** to make decisions. Here's how it works:

### **Decision Making Logic (Rule Based AI)**

The CostAnalyzer doesn't use an LLM for core decisions. Instead, it uses **intelligent rule based algorithms** that analyze patterns:

```python
# Example: Idle Resource Detection
def _find_idle_resources(self, records):
    """Rule-based detection: CPU < 5% = idle"""
    for record in records:
        cpu_util = record.usage_metrics.get('cpu_utilization', 0)
        if cpu_util < 5:  # Rule: Less than 5% = idle
            return "Terminate - resource is idle"
```

**The "brain" makes decisions based on:**
1. **Resource Utilization Patterns**: CPU, memory, network usage
2. **Cost Thresholds**: Resources costing above certain amounts
3. **Usage Metrics**: Hours of operation, request counts
4. **Price Comparisons**: Current vs historical pricing
5. **Pattern Recognition**: Grouping similar resources, identifying trends

### **Why Rule Based Instead of LLM?**

For cost optimization, **rule based logic is actually more reliable** than LLM based decisions because:
- **Deterministic**: Same input = same output (critical for financial decisions)
- **Explainable**: You can see exactly why a recommendation was made
- **Fast**: No API calls to LLM, instant results
- **Accurate**: Mathematical calculations are precise

## 🤖 Where the LLM Comes In: Enhanced Recommendations

**The LLM is used for generating human readable recommendations**, not for making the core decisions. Here's the flow:

### **Current Implementation (Rule Based Decisions + LLM Recommendations)**

```
1. CostAnalyzer (Rule Based Brain)
   ├── Analyzes cost data
   ├── Applies rules (CPU < 5% = idle)
   ├── Calculates savings
   └── Identifies opportunities

2. Recommendation Generation (Could use LLM)
   ├── Takes opportunity data
   ├── Generates human readable explanation
   ├── Provides action steps
   └── Explains ROI and impact
```

### **How LLM Would Enhance This (Future Enhancement)**

Currently, recommendations are generated with template based text. An LLM could enhance this by:

**1. Generating Contextual Recommendations**
```python
# Instead of: "Terminate idle resource"
# LLM generates: "Resource i-12345 has been idle for 90+ days with 
#  0% CPU utilization. This appears to be a test instance that was 
#  never cleaned up. Safe to terminate - will save $500/month."
```

**2. Providing Actionable Steps**
```python
# LLM generates step-by-step remediation:
recommendation = llm.generate_recommendation(opportunity)
# Returns:
# "1. Verify resource is not needed (check last access: 90+ days)
#  2. Create snapshot for backup
#  3. Terminate instance: aws ec2 terminate-instances --instance-ids i-xxx
#  4. Monitor for 7 days to ensure no impact"
```

**3. Explaining Complex Scenarios**
```python
# For complex multi-resource optimizations, LLM explains:
# "This optimization involves 5 related resources. Terminating the 
#  primary instance will automatically clean up 4 dependent resources,
#  resulting in $2,000/month savings. Risk: Low - resources are in 
#  development environment with no production traffic."
```

## 📊 Current Architecture

### **Decision Flow:**

```
┌─────────────────────────────────────────┐
│  N8N Workflow (Orchestration)          │
│  - Scheduled triggers                   │
│  - Webhook receivers                    │
│  - Workflow automation                  │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  FastAPI Backend                        │
│  - Receives analysis requests           │
│  - Orchestrates services                │
└──────────────┬──────────────────────────┘
               │
       ┌───────┴────────┐
       │                │
       ▼                ▼
┌──────────────┐  ┌──────────────┐
│ CostAnalyzer │  │ PriceMonitor │
│ (Rule Based) │  │ (Rule Based) │
│              │  │              │
│ • Idle       │  │ • Price      │
│   detection  │  │   scraping   │
│ • Over      │  │ • Change     │
│   provision  │  │   detection  │
│ • Storage    │  │ • Discount   │
│   analysis   │  │   detection  │
└──────┬───────┘  └──────┬───────┘
       │                 │
       └────────┬────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  Recommendation Generation               │
│  (Currently: Template based)            │
│  (Future: LLM enhanced)                 │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  Dashboard UI                           │
│  - Displays opportunities                │
│  - Shows recommendations                 │
│  - Human in the loop decisions           │
└─────────────────────────────────────────┘
```

## 🔄 Where LLM Could Be Integrated

### **Option 1: Recommendation Enhancement (Recommended)**

Add an LLM service that takes opportunity data and generates rich, contextual recommendations:

```python
class RecommendationGenerator:
    def __init__(self):
        self.llm_service = LLMService()  # OpenRouter
    
    def generate_recommendation(self, opportunity):
        """Use LLM to generate human-readable recommendation"""
        prompt = f"""
        Analyze this cost optimization opportunity and provide:
        1. Clear explanation of the issue
        2. Specific action steps
        3. Risk assessment
        4. Expected outcome
        
        Opportunity: {opportunity}
        """
        return self.llm_service.chat(prompt)
```

### **Option 2: RAG Enhanced Recommendations**

Use the existing [RAG service](backend/app/services/rag_cost_service.py) to find relevant best practices, then use LLM to generate recommendations:

```python
def generate_rag_enhanced_recommendation(self, opportunity):
    # 1. Find relevant best practices from RAG
    relevant_docs = rag_service.search_optimization_strategies(
        opportunity_type=opportunity['type'],
        cloud_provider=opportunity['cloud_provider']
    )
    
    # 2. Use LLM to generate recommendation with context
    prompt = f"""
    Based on these best practices and this opportunity, 
    generate a recommendation:
    
    Best Practices:
    {relevant_docs}
    
    Opportunity:
    {opportunity}
    """
    return llm_service.chat(prompt)
```

## 💡 Interview Answer

**"What framework are the AI agents built on?"**

> "The AI agents are built on **N8N**, which is a low code/no code workflow automation platform. N8N serves as the orchestration layer that receives triggers, calls our FastAPI backend for analysis, and sends notifications. This makes it easy for non-developers to create and modify agent workflows."

**"What is the brain that makes decisions?"**

> "The decision making brain is the **CostAnalyzer**, which uses **rule based AI logic**. It analyzes cost data using intelligent algorithms that detect patterns like idle resources (CPU < 5%), over provisioned instances, and price changes. I chose rule based logic for cost optimization because it's deterministic, explainable, and fast  critical for financial decisions where you need to understand exactly why a recommendation was made."

**"Where does the LLM come in?"**

> "Currently, the LLM would be used for **enhancing recommendations** rather than making core decisions. The CostAnalyzer makes the decisions using rule based logic, then an LLM service could generate human readable explanations, actionable steps, and contextual recommendations. There's also a RAG service that could retrieve relevant best practices from documentation, which the LLM could then use to generate more informed recommendations. This hybrid approach rule based decisions with LLM enhanced communication provides the best of both worlds: reliable, explainable decisions with natural language explanations."

## 🎯 Key Points

1. **Framework**: N8N (low code workflow automation)
2. **Brain**: CostAnalyzer (rule based AI logic)
3. **LLM Role**: Recommendation generation and explanation (not core decisions)
4. **Why Rule Based**: Deterministic, explainable, fast - critical for financial decisions
5. **Future Enhancement**: LLM could generate richer, more contextual recommendations

This architecture provides reliable, explainable cost optimization decisions while leveraging LLM capabilities for better communication and user experience.

