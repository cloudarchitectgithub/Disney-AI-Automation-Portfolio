"""
Streamlit Dashboard for SRE Incident Triage Agent
"""
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import json
import os

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://python-backend:8001")
API_BASE = f"{BACKEND_URL}/api"

# Page config
st.set_page_config(
    page_title="SRE Incident Triage Agent",
    page_icon="🚨",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
    }
    .main .block-container {
        background-color: #0e1117;
        color: #ffffff;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff;
    }
    p, div, span {
        color: #ffffff;
    }
    .stMarkdown {
        color: #ffffff;
    }
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #ffffff;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #1e3a5f;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        color: #ffffff;
    }
    .incident-card {
        border-left: 4px solid #1f77b4;
        padding: 1rem;
        margin: 1rem 0;
        background-color: #1e3a5f;
        color: #ffffff;
    }
    .severity-p0 { border-left-color: #ff0000; }
    .severity-p1 { border-left-color: #ff8800; }
    .severity-p2 { border-left-color: #ffbb00; }
    .severity-p3 { border-left-color: #00aa00; }
</style>
""", unsafe_allow_html=True)


def check_backend_health():
    """Check if backend is available"""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False


def get_incidents():
    """Fetch all incidents"""
    try:
        response = requests.get(f"{API_BASE}/incidents/", timeout=5)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Failed to fetch incidents: {e}")
        return []


def trigger_test_incident(severity="high", service="kubernetes"):
    """Trigger a test incident"""
    try:
        response = requests.post(
            f"{API_BASE}/incidents/trigger",
            params={"severity": severity, "service": service},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Failed to trigger incident: {e}")
        return None


def triage_incident(incident_id):
    """Triage an incident using AI"""
    try:
        response = requests.post(
            f"{API_BASE}/incidents/{incident_id}/triage",
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Failed to triage incident: {e}")
        return None


def get_resolution(incident_id):
    """Get resolution suggestion for an incident"""
    try:
        response = requests.post(
            f"{API_BASE}/incidents/{incident_id}/resolve",
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Failed to get resolution: {e}")
        return None


# Main app
def main():
    # Header
    st.markdown('<div class="main-header">🚨 SRE Incident Triage Agent</div>', unsafe_allow_html=True)
    
    # Check backend health
    if not check_backend_health():
        st.error("⚠️ Backend service is not available. Make sure Docker containers are running.")
        st.info("Run: `docker-compose up -d`")
        return
    
    # Sidebar
    with st.sidebar:
        st.header("🎛️ Controls")
        
        st.subheader("Trigger Test Incident")
        severity = st.selectbox("Severity", ["high", "medium", "low"], key="severity")
        service = st.text_input("Service", value="kubernetes", key="service")
        
        if st.button("🚨 Trigger Incident", type="primary"):
            with st.spinner("Triggering incident..."):
                incident = trigger_test_incident(severity, service)
                if incident:
                    st.success(f"✅ Incident created: {incident['id']}")
                    st.rerun()
        
        st.divider()
        
        st.subheader("System Status")
        try:
            health = requests.get(f"{BACKEND_URL}/health/detailed", timeout=2).json()
            st.json(health)
        except:
            st.warning("Unable to fetch system status")
    
    # Main content
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "🔍 Incidents", "📚 RAG Stats"])
    
    with tab1:
        st.header("Incident Overview")
        
        incidents = get_incidents()
        
        if not incidents:
            st.info("No incidents yet. Use the sidebar to trigger a test incident.")
        else:
            # Metrics
            col1, col2, col3, col4 = st.columns(4)
            
            total = len(incidents)
            open_incidents = len([i for i in incidents if i['status'] not in ['resolved', 'closed']])
            p0_p1 = len([i for i in incidents if i['severity'] in ['P0', 'P1']])
            resolved = len([i for i in incidents if i['status'] == 'resolved'])
            
            col1.metric("Total Incidents", total)
            col2.metric("Open Incidents", open_incidents)
            col3.metric("Critical (P0/P1)", p0_p1)
            col4.metric("Resolved", resolved)
            
            st.divider()
            
            # Recent incidents
            st.subheader("Recent Incidents")
            for incident in incidents[:10]:
                severity_class = f"severity-{incident['severity'].lower()}"
                st.markdown(f"""
                <div class="incident-card {severity_class}">
                    <h4>{incident['title']} <span style="color: #666;">({incident['severity']})</span></h4>
                    <p>{incident['description'][:200]}...</p>
                    <small>Status: {incident['status']} | Service: {incident.get('service', 'Unknown')}</small>
                </div>
                """, unsafe_allow_html=True)
    
    with tab2:
        st.header("Incident Management")
        
        incidents = get_incidents()
        
        if not incidents:
            st.info("No incidents to display.")
        else:
            # Incident selector
            incident_options = {f"{i['title']} ({i['severity']})": i['id'] for i in incidents}
            selected = st.selectbox("Select Incident", list(incident_options.keys()))
            incident_id = incident_options[selected]
            
            incident = next(i for i in incidents if i['id'] == incident_id)
            
            # Display incident details
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Incident Details")
                st.write(f"**ID:** {incident['id']}")
                st.write(f"**Title:** {incident['title']}")
                st.write(f"**Severity:** {incident['severity']}")
                st.write(f"**Status:** {incident['status']}")
                st.write(f"**Service:** {incident.get('service', 'Unknown')}")
                st.write(f"**Detected:** {incident['detected_at']}")
                
                if incident.get('root_cause'):
                    st.write(f"**Root Cause:** {incident['root_cause']}")
            
            with col2:
                st.subheader("Actions")
                
                if incident['status'] == 'detected':
                    if st.button("🤖 AI Triage", type="primary"):
                        with st.spinner("Analyzing incident with AI..."):
                            triage_result = triage_incident(incident_id)
                            if triage_result:
                                st.success("✅ Incident triaged!")
                                st.json(triage_result)
                                st.rerun()
                
                if incident['status'] in ['triaged', 'assigned']:
                    if st.button("💡 Get Resolution", type="primary"):
                        with st.spinner("Generating resolution suggestions..."):
                            resolution = get_resolution(incident_id)
                            if resolution:
                                st.success("✅ Resolution generated!")
                                st.subheader("Resolution Strategy")
                                st.write(resolution.get('suggestion', ''))
                                
                                st.subheader("Steps")
                                for i, step in enumerate(resolution.get('steps', []), 1):
                                    st.write(f"{i}. {step}")
                                
                                st.subheader("Relevant Documentation")
                                for doc in resolution.get('relevant_documentation', [])[:3]:
                                    with st.expander(doc.get('metadata', {}).get('source', 'Document')):
                                        st.write(doc.get('content', '')[:500])
            
            # Full description
            st.subheader("Full Description")
            st.write(incident['description'])
    
    with tab3:
        st.header("RAG System Statistics")
        
        try:
            stats = requests.get(f"{API_BASE}/rag/stats", timeout=5).json()
            st.json(stats)
            
            st.metric("Total Document Chunks", stats.get('total_chunks', 0))
        except Exception as e:
            st.error(f"Failed to fetch RAG stats: {e}")


if __name__ == "__main__":
    main()

