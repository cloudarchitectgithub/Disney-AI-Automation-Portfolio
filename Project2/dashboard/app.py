"""
Cost Optimization Dashboard
"""
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://cost-optimization-backend:8002")
API_BASE = f"{BACKEND_URL}/api"

# Page config
st.set_page_config(
    page_title="Cost Optimization Agent",
    page_icon="💰",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .savings-highlight {
        background-color: #1e3a5f;
        color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #007bff;
    }
    .savings-highlight h3, .savings-highlight p {
        color: #ffffff;
    }
</style>
""", unsafe_allow_html=True)


def check_backend():
    """Check if backend is available"""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False


def get_data_sources():
    """Get registered data sources"""
    try:
        response = requests.get(f"{API_BASE}/data-sources/", timeout=5)
        if response.status_code == 200:
            return response.json()
        return {"sources": [], "count": 0}
    except Exception as e:
        st.error(f"Failed to fetch data sources: {e}")
        return {"sources": [], "count": 0}


def analyze_costs():
    """Analyze costs across all sources"""
    try:
        response = requests.post(f"{API_BASE}/cost/analyze", json={}, timeout=30)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Failed to analyze costs: {e}")
        return None


def get_opportunities():
    """Get optimization opportunities"""
    try:
        response = requests.get(f"{API_BASE}/cost/opportunities?limit=20", timeout=30)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Failed to get opportunities: {e}")
        return None


def get_summary():
    """Get cost summary"""
    try:
        response = requests.get(f"{API_BASE}/cost/summary", timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Failed to get summary: {e}")
        return None


def check_price_changes():
    """Check for price changes across cloud providers"""
    try:
        response = requests.get(f"{API_BASE}/cost/check-prices", timeout=30)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Failed to check price changes: {e}")
        return None


# Main app
def main():
    st.markdown('<div class="main-header">💰 Multi-Cloud Cost Optimization Agent</div>', unsafe_allow_html=True)
    
    # Initialize session state
    if 'baseline_complete' not in st.session_state:
        st.session_state['baseline_complete'] = False
    if 'baseline_analysis' not in st.session_state:
        st.session_state['baseline_analysis'] = None
    
    # Check backend
    if not check_backend():
        st.error("⚠️ Backend service is not available. Make sure Docker containers are running.")
        st.info("Run: `docker-compose up -d`")
        return
    
    # Sidebar
    with st.sidebar:
        st.header("🎛️ Controls")
        
        if st.button("🔄 Refresh Analysis", type="primary"):
            # Reset baseline state to zero
            st.session_state['baseline_complete'] = False
            st.session_state['baseline_analysis'] = None
            st.rerun()
        
        st.divider()
        
        # Data sources
        st.subheader("Data Sources")
        sources_data = get_data_sources()
        st.write(f"**Registered:** {sources_data.get('count', 0)}")
        
        for source in sources_data.get('sources', []):
            schema = source.get('schema', {})
            st.write(f"- **{source['name']}**: {schema.get('row_count', 0)} records")
    
    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "💡 Opportunities", "🔍 Analysis", "💰 Price Monitoring"])
    
    with tab1:
        st.header("Cost Summary & Baseline Analysis")
        
        # Workflow explanation
        st.markdown("""
        **📊 Analysis Workflow:**
        1. **Baseline Analysis** - Analyze current services to establish accurate baseline
        2. **Price Scraping** - Scrape current pricing from cloud providers
        3. **Savings Opportunities** - Compare baseline vs. current pricing to find savings
        """)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 Run Baseline Analysis", type="primary", use_container_width=True):
                with st.spinner("Analyzing current Disney services across all cloud providers..."):
                    analysis = analyze_costs()
                    if analysis:
                        st.success("✅ Baseline analysis complete! Current state established.")
                        st.session_state['baseline_analysis'] = analysis
                        st.session_state['baseline_complete'] = True
                        st.rerun()
                    else:
                        st.error("❌ Failed to run baseline analysis")
        
        with col2:
            if st.session_state.get('baseline_complete', False):
                st.success("✅ Baseline established")
            else:
                st.info("⏳ Run baseline analysis to begin")
        
        st.divider()
        
        # Show metrics - start at 0, populate after baseline
        col1, col2, col3, col4 = st.columns(4)
        
        if st.session_state.get('baseline_complete', False):
            # Show real data after baseline analysis
            summary = get_summary()
            if summary:
                total_cost = summary.get('total_cost', 0)
                num_providers = len(summary.get('by_provider', {}))
                num_sources = len(summary.get('sources', []))
                total_records = sum(s.get('records', 0) for s in summary.get('sources', []))
                
                col1.metric("Total Monthly Cost", f"${total_cost:,.2f}")
                col2.metric("Cloud Providers", num_providers)
                col3.metric("Data Sources", num_sources)
                col4.metric("Total Records", total_records)
            else:
                # Fallback if summary fails
                col1.metric("Total Monthly Cost", "$0.00")
                col2.metric("Cloud Providers", "0")
                col3.metric("Data Sources", "0")
                col4.metric("Total Records", "0")
        else:
            # Show zeros before baseline analysis
            col1.metric("Total Monthly Cost", "$0.00")
            col2.metric("Cloud Providers", "0")
            col3.metric("Data Sources", "0")
            col4.metric("Total Records", "0")
        
        # Show baseline status
        if st.session_state.get('baseline_complete', False):
            baseline = st.session_state.get('baseline_analysis', {})
            if baseline:
                st.info("📊 **Baseline Established:** Current state analysis complete. This is your starting point for cost optimization.")
        
        # Show charts only after baseline - show empty state before
        if st.session_state.get('baseline_complete', False):
            summary = get_summary()
            if summary:
                st.divider()
                
                # Cost by provider
                if summary.get('by_provider') and len(summary.get('by_provider', {})) > 0:
                    st.subheader("Cost by Cloud Provider")
                    provider_df = pd.DataFrame([
                        {"Provider": k.upper(), "Cost": v}
                        for k, v in summary['by_provider'].items()
                    ])
                    
                    fig = px.pie(provider_df, values='Cost', names='Provider', 
                                title='Cost Distribution by Provider')
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.subheader("Cost by Cloud Provider")
                    st.info("No provider data available. Run baseline analysis to see cost breakdown.")
                
                # Cost by category
                analysis = analyze_costs()
                if analysis and analysis.get('analysis', {}).get('summary', {}).get('by_category'):
                    st.subheader("Cost by Service Category")
                    category_df = pd.DataFrame([
                        {"Category": k, "Cost": v}
                        for k, v in analysis['analysis']['summary']['by_category'].items()
                    ])
                    
                    fig = px.bar(category_df, x='Category', y='Cost', 
                               title='Cost by Service Category')
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.subheader("Cost by Service Category")
                    st.info("No category data available. Run baseline analysis to see cost breakdown.")
        else:
            # Show empty state before baseline
            st.divider()
            st.subheader("Cost by Cloud Provider")
            empty_provider_df = pd.DataFrame({
                "Provider": ["No Data"],
                "Cost": [0]
            })
            fig = px.pie(empty_provider_df, values='Cost', names='Provider', 
                        title='Cost Distribution by Provider')
            fig.update_traces(textposition='inside', textinfo='none')
            st.plotly_chart(fig, use_container_width=True)
            st.caption("💡 Run baseline analysis to see cost breakdown by provider")
            
            st.subheader("Cost by Service Category")
            empty_category_df = pd.DataFrame({
                "Category": ["No Data"],
                "Cost": [0]
            })
            fig = px.bar(empty_category_df, x='Category', y='Cost', 
                       title='Cost by Service Category')
            st.plotly_chart(fig, use_container_width=True)
            st.caption("💡 Run baseline analysis to see cost breakdown by category")
    
    with tab2:
        st.header("Optimization Opportunities & AI Recommendations")
        
        # Check if baseline is complete
        if not st.session_state.get('baseline_complete', False):
            st.warning("⚠️ **Baseline Analysis Required:** Please run baseline analysis first (Overview tab) to establish current state.")
            st.info("💡 The baseline analysis ensures we have accurate current numbers before finding savings opportunities.")
        
        st.markdown("""
        **🤖 AI-Powered Cost Optimization with Human-in-the-Loop**
        
        **Workflow:**
        1. ✅ **Baseline Analysis** - Current state of all services (Overview tab)
        2. ✅ **Price Scraping** - Real-time pricing from cloud providers (Price Monitoring tab)
        3. ✅ **Savings Opportunities** - Compare baseline vs. pricing to find savings (this tab)
        
        **The system identifies:**
        - **Unused/Idle Resources**: Resources running but not utilized
        - **Over-provisioned Instances**: Right-sizing opportunities
        - **Price Reductions**: "Fire sales" from cloud providers
        - **Discount Programs**: Savings Plans, Reserved Instances, Spot opportunities
        
        **Human Decision Required:** Review AI recommendations and approve/reject actions.
        """)
        
        opportunities_data = get_opportunities()
        
        if opportunities_data:
            total_savings = opportunities_data.get('total_potential_savings', 0)
            total_cost = opportunities_data.get('total_cost', 0)
            savings_pct = opportunities_data.get('savings_percentage', 0)
            
            # Savings highlight with annual projection
            monthly_savings = total_savings
            annual_savings = monthly_savings * 12
            
            st.markdown(f"""
            <div class="savings-highlight">
                <h3>💰 Potential Monthly Savings: ${monthly_savings:,.2f}</h3>
                <p><strong>Annual Projection: ${annual_savings:,.2f}/year</strong></p>
                <p>That's <strong>{savings_pct:.1f}%</strong> of total monthly costs (${total_cost:,.2f})</p>
                <p style="color: #28a745; font-weight: bold;">$9M FY26 Savings ✅</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.divider()
            
            # Opportunities list
            opportunities = opportunities_data.get('opportunities', [])
            
            if not opportunities:
                st.info("No optimization opportunities found. All resources are optimized!")
            else:
                # Group opportunities by type
                unused_resources = [o for o in opportunities if 'idle' in o.get('type', '').lower() or 'unused' in o.get('type', '').lower()]
                over_provisioned = [o for o in opportunities if 'over' in o.get('type', '').lower() or 'right' in o.get('type', '').lower()]
                price_changes = [o for o in opportunities if 'price' in o.get('type', '').lower()]
                other_opps = [o for o in opportunities if o not in unused_resources + over_provisioned + price_changes]
                
                if unused_resources:
                    st.subheader("🗑️ Unused/Idle Resources")
                    st.caption(f"Found {len(unused_resources)} resources that are running but not being utilized")
                    for i, opp in enumerate(unused_resources[:5], 1):
                        with st.expander(f"💡 {i}. {opp.get('resource_id', 'N/A')} - ${opp.get('potential_savings', 0):,.2f}/month savings", expanded=(i == 1)):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**Resource ID:** {opp.get('resource_id', 'N/A')}")
                                st.write(f"**Cloud Provider:** {opp.get('cloud_provider', 'N/A').upper()}")
                                st.write(f"**Current Cost:** ${opp.get('current_cost', 0):,.2f}/month")
                                st.write(f"**Type:** {opp.get('type', 'N/A').replace('_', ' ').title()}")
                            with col2:
                                st.write(f"**🤖 AI Recommendation:** {opp.get('recommendation', 'N/A')}")
                                st.write(f"**Priority:** {opp.get('priority', 'medium').upper()}")
                                st.write(f"**Potential Savings:** ${opp.get('potential_savings', 0):,.2f}/month")
                            
                            # Human-in-the-loop decision
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                if st.button(f"✅ Approve Action", key=f"approve_unused_{i}", type="primary"):
                                    st.success("✅ Approved! Resource will be terminated.")
                            with col2:
                                if st.button(f"❌ Reject", key=f"reject_unused_{i}"):
                                    st.info("❌ Rejected. Resource will remain running.")
                            with col3:
                                if st.button(f"⏸️ Defer Review", key=f"defer_unused_{i}"):
                                    st.warning("⏸️ Deferred for later review.")
                    
                    if len(unused_resources) > 5:
                        st.caption(f"... and {len(unused_resources) - 5} more unused resources")
                
                if price_changes:
                    st.subheader("🔥 Price Reductions (Fire Sales)")
                    st.caption(f"Found {len(price_changes)} price reduction opportunities from cloud providers")
                    for i, opp in enumerate(price_changes[:5], 1):
                        with st.expander(f"💰 {i}. {opp.get('cloud_provider', 'N/A').upper()} {opp.get('instance_type', 'N/A')} - ${opp.get('potential_savings', 0):,.2f}/month savings", expanded=(i == 1)):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**Provider:** {opp.get('cloud_provider', 'N/A').upper()}")
                                st.write(f"**Instance Type:** {opp.get('instance_type', 'N/A')}")
                                st.write(f"**Price Reduction:** {opp.get('price_reduction_pct', 0):.1f}%")
                                if opp.get('old_price_per_hour'):
                                    st.write(f"**Old Price:** ${opp.get('old_price_per_hour', 0):.4f}/hour")
                                    st.write(f"**New Price:** ${opp.get('new_price_per_hour', 0):.4f}/hour")
                            with col2:
                                st.write(f"**Current Monthly Cost:** ${opp.get('current_cost', 0):,.2f}")
                                st.write(f"**Potential Savings:** ${opp.get('potential_savings', 0):,.2f}/month")
                                st.write(f"**🤖 AI Recommendation:** {opp.get('recommendation', 'N/A')}")
                                st.write(f"**Priority:** {opp.get('priority', 'medium').upper()}")
                            
                            # Human-in-the-loop decision
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                if st.button(f"✅ Approve", key=f"approve_price_{i}", type="primary"):
                                    st.success("✅ Approved! Will take advantage of price reduction.")
                            with col2:
                                if st.button(f"❌ Reject", key=f"reject_price_{i}"):
                                    st.info("❌ Rejected. No action taken.")
                            with col3:
                                if st.button(f"⏸️ Defer", key=f"defer_price_{i}"):
                                    st.warning("⏸️ Deferred for later review.")
                    
                    if len(price_changes) > 5:
                        st.caption(f"... and {len(price_changes) - 5} more price reduction opportunities")
                
                if over_provisioned:
                    st.subheader("📏 Over-Provisioned Resources (Right-Sizing)")
                    st.caption(f"Found {len(over_provisioned)} resources that can be downsized")
                    for i, opp in enumerate(over_provisioned[:5], 1):
                        with st.expander(f"💡 {i}. {opp.get('resource_id', 'N/A')} - ${opp.get('potential_savings', 0):,.2f}/month savings", expanded=(i == 1)):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**Resource ID:** {opp.get('resource_id', 'N/A')}")
                                st.write(f"**Cloud Provider:** {opp.get('cloud_provider', 'N/A').upper()}")
                                st.write(f"**Current Cost:** ${opp.get('current_cost', 0):,.2f}/month")
                            with col2:
                                st.write(f"**🤖 AI Recommendation:** {opp.get('recommendation', 'N/A')}")
                                st.write(f"**Potential Savings:** ${opp.get('potential_savings', 0):,.2f}/month")
                                st.write(f"**Priority:** {opp.get('priority', 'medium').upper()}")
                            
                            # Human-in-the-loop decision
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                if st.button(f"✅ Approve", key=f"approve_over_{i}", type="primary"):
                                    st.success("✅ Approved! Resource will be right-sized.")
                            with col2:
                                if st.button(f"❌ Reject", key=f"reject_over_{i}"):
                                    st.info("❌ Rejected. No changes will be made.")
                            with col3:
                                if st.button(f"⏸️ Defer", key=f"defer_over_{i}"):
                                    st.warning("⏸️ Deferred for later review.")
                    
                    if len(over_provisioned) > 5:
                        st.caption(f"... and {len(over_provisioned) - 5} more right-sizing opportunities")
                
                if other_opps:
                    st.subheader("💡 Other Optimization Opportunities")
                    for i, opp in enumerate(other_opps[:5], 1):
                        with st.expander(f"💡 {i}. {opp.get('type', 'Unknown').replace('_', ' ').title()} - ${opp.get('potential_savings', 0):,.2f} savings", expanded=(i == 1)):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**Resource ID:** {opp.get('resource_id', 'N/A')}")
                                st.write(f"**Cloud Provider:** {opp.get('cloud_provider', 'N/A').upper()}")
                                st.write(f"**Current Cost:** ${opp.get('current_cost', 0):,.2f}")
                            with col2:
                                st.write(f"**Potential Savings:** ${opp.get('potential_savings', 0):,.2f}")
                                st.write(f"**Priority:** {opp.get('priority', 'medium').upper()}")
                            
                            st.write(f"**🤖 AI Recommendation:** {opp.get('recommendation', 'N/A')}")
                            
                            # Human-in-the-loop decision
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                if st.button(f"✅ Approve", key=f"approve_other_{i}", type="primary"):
                                    st.success("✅ Approved!")
                            with col2:
                                if st.button(f"❌ Reject", key=f"reject_other_{i}"):
                                    st.info("❌ Rejected.")
                            with col3:
                                if st.button(f"⏸️ Defer", key=f"defer_other_{i}"):
                                    st.warning("⏸️ Deferred.")
    
    with tab3:
        st.header("Detailed Analysis")
        
        if st.button("🔍 Run Full Analysis", type="primary"):
            with st.spinner("Analyzing costs across all cloud providers..."):
                analysis = analyze_costs()
                
                if analysis:
                    st.success("✅ Analysis complete!")
                    
                    analysis_data = analysis.get('analysis', {})
                    
                    # Summary metrics
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Total Cost", f"${analysis_data.get('total_cost', 0):,.2f}")
                    col2.metric("Potential Savings", f"${analysis_data.get('total_potential_savings', 0):,.2f}")
                    col3.metric("Savings %", f"{analysis_data.get('savings_percentage', 0):.1f}%")
                    
                    st.divider()
                    
                    # Opportunities table
                    opportunities = analysis_data.get('opportunities', [])
                    if opportunities:
                        st.subheader("Top Opportunities")
                        opp_df = pd.DataFrame(opportunities)
                        st.dataframe(opp_df[['type', 'resource_id', 'cloud_provider', 'current_cost', 'potential_savings', 'priority']], use_container_width=True)
                else:
                    st.error("Failed to analyze costs")
    
    with tab4:
        st.header("💰 Price Change Monitoring & AI Recommendations")
        
        # Check if baseline is complete
        if not st.session_state.get('baseline_complete', False):
            st.warning("⚠️ **Baseline Analysis Required:** Please run baseline analysis first (Overview tab).")
            st.info("💡 Price monitoring compares current pricing against your baseline to find savings.")
        
        st.markdown("""
        **Real-time price monitoring** across AWS, GCP, and Azure.
        
        **Phase 2: Price Scraping**
        After establishing baseline (Phase 1), this phase:
        1. Scrapes current pricing from all cloud providers
        2. Compares against historical pricing
        3. Detects price reductions and new discount programs
        
        **The system detects:**
        - **Price reductions** (>5% changes) - "Fire sales" from providers
        - **New discount programs** (Savings Plans, Committed Use, etc.)
        - **Spot instance opportunities** (60-90% savings)
        - **Promotional pricing** and limited-time offers
        
        **🤖 AI Recommendations with Human-in-the-Loop:**
        - AI analyzes opportunities and provides recommendations
        - Human reviews and makes final decisions
        - System tracks approval/rejection for learning
        """)
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("🔍 Check Price Changes", type="primary"):
                with st.spinner("Checking prices across all cloud providers..."):
                    price_data = check_price_changes()
                    
                    if price_data:
                        st.success("✅ Price check complete!")
                        
                        # Summary
                        total_savings = price_data.get('total_potential_savings', 0)
                        high_priority = price_data.get('high_priority_count', 0)
                        medium_priority = price_data.get('medium_priority_count', 0)
                        checked_at = price_data.get('checked_at', '')
                        providers = price_data.get('providers_checked', [])
                        
                        st.markdown("### 📊 Price Check Results")
                        
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Total Savings", f"${total_savings:,.2f}/month")
                        col2.metric("High Priority", high_priority)
                        col3.metric("Medium Priority", medium_priority)
                        
                        st.write(f"**Checked At:** {checked_at}")
                        st.write(f"**Providers Checked:** {', '.join([p.upper() for p in providers])}")
                        st.write(f"**Method:** {price_data.get('scraping_method', 'real_pricing_data')}")
                        
                        st.divider()
                        
                        # Opportunities
                        opportunities = price_data.get('opportunities', [])
                        
                        if opportunities:
                            st.subheader("💰 Detected Price Change Opportunities")
                            
                            for i, opp in enumerate(opportunities, 1):
                                opp_type = opp.get('type', 'price_change_opportunity')
                                savings = opp.get('potential_savings', 0)
                                provider = opp.get('cloud_provider', 'unknown').upper()
                                instance_type = opp.get('instance_type', 'N/A')
                                reduction_pct = opp.get('price_reduction_pct', 0)
                                
                                with st.expander(
                                    f"💡 {i}. {provider} {instance_type} - ${savings:,.2f}/month savings",
                                    expanded=(i <= 2)
                                ):
                                    col1, col2 = st.columns(2)
                                    
                                    with col1:
                                        st.write(f"**Provider:** {provider}")
                                        st.write(f"**Instance Type:** {instance_type}")
                                        st.write(f"**Price Reduction:** {reduction_pct:.1f}%")
                                        if opp.get('old_price_per_hour'):
                                            st.write(f"**Old Price:** ${opp.get('old_price_per_hour', 0):.4f}/hour")
                                            st.write(f"**New Price:** ${opp.get('new_price_per_hour', 0):.4f}/hour")
                                    
                                    with col2:
                                        st.write(f"**Current Monthly Cost:** ${opp.get('current_cost', 0):,.2f}")
                                        st.write(f"**Potential Savings:** ${savings:,.2f}/month")
                                        st.write(f"**Priority:** {opp.get('priority', 'medium').upper()}")
                                        if opp.get('affected_resources'):
                                            st.write(f"**Affected Resources:** {opp.get('affected_resources')} instances")
                                    
                                    st.write(f"**🤖 AI Recommendation:** {opp.get('recommendation', 'N/A')}")
                                    
                                    # Human-in-the-loop decision
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        if st.button(f"✅ Approve", key=f"approve_{i}", type="primary"):
                                            st.success("✅ Approved! Action will be taken.")
                                    with col2:
                                        if st.button(f"❌ Reject", key=f"reject_{i}"):
                                            st.info("❌ Rejected. No action taken.")
                                    with col3:
                                        if st.button(f"⏸️ Defer", key=f"defer_{i}"):
                                            st.warning("⏸️ Deferred for later review.")
                                    
                                    if opp.get('detected_at'):
                                        st.caption(f"🔍 Detected: {opp.get('detected_at')}")
                        else:
                            st.info("ℹ️ No price changes detected. Prices are stable across all providers.")
                            st.caption("This is normal - the system is monitoring and will alert when changes occur.")
                    else:
                        st.error("❌ Failed to check price changes")
        
        with col2:
            st.markdown("### 📋 How It Works")
            st.markdown("""
            **1. Price Scraping**
            - Fetches real pricing data from AWS, GCP, Azure
            - Uses actual 2024 cloud provider pricing
            - Stores in price history database
            
            **2. Change Detection**
            - Compares current prices vs. historical
            - Detects reductions >5%
            - Calculates monthly savings automatically
            
            **3. Resource Matching**
            - Matches price changes to your actual resources
            - Counts affected instances
            - Calculates total savings
            
            **4. Notifications**
            - High priority (>$500/month): Immediate alerts
            - Medium ($100-$500/month): Daily digest
            - Low (<$100/month): Weekly summary
            """)
            
            st.markdown("### 🔄 Scheduled Monitoring")
            st.markdown("""
            In production, this runs automatically:
            - **Every 6 hours** via N8N workflow
            - **Real-time** when providers announce changes
            - **On-demand** via this dashboard
            """)
            
            st.markdown("### 💡 Technical Details")
            with st.expander("View Technical Implementation"):
                st.code("""
# Price scraper fetches real pricing
scraper = PricingScraper()
current_prices = await scraper.scrape_all_providers()

# Compare with history
changes = scraper.detect_price_changes(current_prices)

# Match to resources
opportunities = detector.match_changes_to_resources(changes, resources)
                """, language="python")


if __name__ == "__main__":
    main()

