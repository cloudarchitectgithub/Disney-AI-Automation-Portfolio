"""
Vulnerability Management Dashboard
"""
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime
import os

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://vulnerability-backend:8003")
API_BASE = f"{BACKEND_URL}/api"

# Page config
st.set_page_config(
    page_title="Vulnerability Management Agent",
    page_icon="🔒",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #dc3545;
        margin-bottom: 1rem;
    }
    .critical { background-color: #f8d7da; border-left: 4px solid #dc3545; padding: 1rem; margin: 0.5rem 0; }
    .high { background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 1rem; margin: 0.5rem 0; }
    .medium { background-color: #d1ecf1; border-left: 4px solid #17a2b8; padding: 1rem; margin: 0.5rem 0; }
    .low { background-color: #d4edda; border-left: 4px solid #28a745; padding: 1rem; margin: 0.5rem 0; }
</style>
""", unsafe_allow_html=True)


def check_backend():
    """Check if backend is available"""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False


def get_vulnerabilities(status=None, severity=None, team=None):
    """Fetch vulnerabilities"""
    try:
        params = {}
        if status:
            params["status"] = status
        if severity:
            params["severity"] = severity
        if team:
            params["team"] = team
        
        response = requests.get(f"{API_BASE}/vulnerabilities/", params=params, timeout=5)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Failed to fetch vulnerabilities: {e}")
        return []


def create_vulnerability(cve_data):
    """Create a new vulnerability"""
    try:
        response = requests.post(f"{API_BASE}/vulnerabilities/", json=cve_data, timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Failed to create vulnerability: {e}")
        return None


def triage_vulnerability(vuln_id):
    """Triage a vulnerability"""
    try:
        response = requests.post(f"{API_BASE}/vulnerabilities/{vuln_id}/triage", timeout=30)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Failed to triage vulnerability: {e}")
        return None


def assign_ownership(vuln_id):
    """Assign ownership"""
    try:
        response = requests.post(f"{API_BASE}/vulnerabilities/{vuln_id}/assign", timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Failed to assign ownership: {e}")
        return None


def get_sla_compliance():
    """Get SLA compliance stats"""
    try:
        response = requests.get(f"{API_BASE}/vulnerabilities/stats/sla-compliance", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Failed to get SLA stats: {e}")
        return None


# Main app
def main():
    st.markdown('<div class="main-header">🔒 Vulnerability Management Agent</div>', unsafe_allow_html=True)
    
    # Check backend
    if not check_backend():
        st.error("⚠️ Backend service is not available. Make sure Docker containers are running.")
        st.info("Run: `docker-compose up -d vulnerability-backend`")
        return
    
    # Sidebar
    with st.sidebar:
        st.header("🎛️ Controls")
        
        if st.button("🔄 Refresh", type="primary"):
            st.rerun()
        
        st.divider()
        
        st.subheader("Create Test Vulnerability")
        if st.button("🔒 Create Test CVE"):
            test_cve = {
                "cve_id": f"CVE-2024-{st.session_state.get('cve_counter', 1000)}",
                "title": "Remote Code Execution in API Service",
                "description": "A remote code execution vulnerability has been discovered in the API service. Proof of concept exploit is available.",
                "cvss_score": 8.5,
                "affected_components": ["api-service", "backend"],
                "source": "scanner"
            }
            vuln = create_vulnerability(test_cve)
            if vuln:
                st.success(f"✅ Created: {vuln['cve_id']}")
                st.session_state['cve_counter'] = st.session_state.get('cve_counter', 1000) + 1
                st.rerun()
        
        st.divider()
        
        # Filters
        st.subheader("Filters")
        filter_status = st.selectbox("Status", ["All", "detected", "triaged", "assigned", "in_progress", "remediated"])
        filter_severity = st.selectbox("Severity", ["All", "CRITICAL", "HIGH", "MEDIUM", "LOW"])
    
    # Main tabs
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "🔍 Vulnerabilities", "📈 SLA Compliance"])
    
    with tab1:
        st.header("Vulnerability Overview")
        
        # Get vulnerabilities
        vulns = get_vulnerabilities()
        
        if not vulns:
            st.info("No vulnerabilities found. Use sidebar to create a test CVE.")
        else:
            # Metrics
            col1, col2, col3, col4 = st.columns(4)
            
            total = len(vulns)
            critical = len([v for v in vulns if v['severity'] == 'CRITICAL'])
            high = len([v for v in vulns if v['severity'] == 'HIGH'])
            open_vulns = len([v for v in vulns if v['status'] not in ['remediated', 'accepted', 'false_positive']])
            
            col1.metric("Total Vulnerabilities", total)
            col2.metric("Critical", critical, delta=f"{critical} require immediate attention")
            col3.metric("High Severity", high)
            col4.metric("Open", open_vulns)
            
            st.divider()
            
            # Severity distribution
            st.subheader("Vulnerabilities by Severity")
            severity_counts = pd.DataFrame([
                {"Severity": "CRITICAL", "Count": len([v for v in vulns if v['severity'] == 'CRITICAL'])},
                {"Severity": "HIGH", "Count": len([v for v in vulns if v['severity'] == 'HIGH'])},
                {"Severity": "MEDIUM", "Count": len([v for v in vulns if v['severity'] == 'MEDIUM'])},
                {"Severity": "LOW", "Count": len([v for v in vulns if v['severity'] == 'LOW'])},
            ])
            
            fig = px.bar(severity_counts, x='Severity', y='Count', 
                        color='Severity',
                        color_discrete_map={
                            'CRITICAL': '#dc3545',
                            'HIGH': '#ffc107',
                            'MEDIUM': '#17a2b8',
                            'LOW': '#28a745'
                        })
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.header("Vulnerability Management")
        
        # Get filtered vulnerabilities
        status_filter = None if filter_status == "All" else filter_status
        severity_filter = None if filter_severity == "All" else severity_filter
        
        vulns = get_vulnerabilities(status=status_filter, severity=severity_filter)
        
        if not vulns:
            st.info("No vulnerabilities match the filters.")
        else:
            # Vulnerability list
            for vuln in vulns[:20]:  # Show top 20
                severity_class = vuln['severity'].lower()
                
                with st.expander(f"🔒 {vuln['cve_id']} - {vuln['title']} ({vuln['severity']})", expanded=(vuln['severity'] == 'CRITICAL')):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Priority Score:** {vuln.get('priority_score', 0):.1f}/100")
                        st.write(f"**CVSS Score:** {vuln['cvss_score']}")
                        st.write(f"**Status:** {vuln['status']}")
                        st.write(f"**Affected Components:** {', '.join(vuln.get('affected_components', []))}")
                        
                        # Show ownership information
                        if vuln.get('assigned_team'):
                            st.success(f"**✅ Assigned Team:** {vuln['assigned_team']}")
                            if vuln.get('assigned_to'):
                                st.write(f"**Assigned To:** {vuln['assigned_to']}")
                        elif vuln.get('recommended_team'):
                            st.warning(f"**🤖 Recommended Team:** {vuln['recommended_team']} (needs assignment)")
                            if vuln.get('recommended_owner'):
                                st.write(f"**Recommended Owner:** {vuln['recommended_owner']}")
                        else:
                            st.info("**👤 Ownership:** Not yet determined")
                    
                    with col2:
                        if vuln['status'] == 'detected':
                            if st.button(f"🤖 AI Triage", key=f"triage_{vuln['id']}"):
                                with st.spinner("Triaging with AI..."):
                                    result = triage_vulnerability(vuln['id'])
                                    if result:
                                        st.success("✅ Triaged!")
                                        st.rerun()
                        
                        if vuln['status'] == 'triaged' and not vuln.get('assigned_team'):
                            if vuln.get('recommended_team'):
                                st.info(f"💡 AI recommends: **{vuln['recommended_team']}** team")
                            if st.button(f"👤 Assign Ownership", key=f"assign_{vuln['id']}", type="primary"):
                                with st.spinner("Assigning ownership..."):
                                    result = assign_ownership(vuln['id'])
                                    if result:
                                        st.success(f"✅ Assigned to {result['assigned_team']} team")
                                        st.rerun()
                    
                    st.write(f"**Description:** {vuln['description']}")
    
    with tab3:
        st.header("SLA Compliance")
        
        sla_stats = get_sla_compliance()
        
        if sla_stats:
            col1, col2, col3 = st.columns(3)
            
            col1.metric("Total Vulnerabilities", sla_stats.get('total_vulnerabilities', 0))
            col2.metric("Within SLA", sla_stats.get('within_sla', 0))
            col3.metric("Overdue", sla_stats.get('overdue', 0), delta=f"{sla_stats.get('overdue', 0)} need attention")
            
            compliance_rate = sla_stats.get('compliance_rate', 0)
            st.metric("SLA Compliance Rate", f"{compliance_rate:.1f}%")
            
            # Compliance chart
            compliance_df = pd.DataFrame([
                {"Status": "Within SLA", "Count": sla_stats.get('within_sla', 0)},
                {"Status": "Overdue", "Count": sla_stats.get('overdue', 0)}
            ])
            
            fig = px.pie(compliance_df, values='Count', names='Status',
                        title='SLA Compliance Status')
            st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()

