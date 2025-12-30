"""
Ingest security documentation into RAG pipeline
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.rag_security_service import SecurityRAGService
from loguru import logger


def create_sample_docs():
    """Create sample security documentation"""
    docs = []
    
    # CVE Remediation Guide
    docs.append({
        "content": """
CVE Remediation Best Practices:

1. Prioritize by CVSS score and exploitability
2. Critical vulnerabilities (CVSS 9.0+) should be patched within 24 hours
3. High severity (CVSS 7.0-8.9) should be patched within 7 days
4. Medium severity (CVSS 4.0-6.9) should be patched within 30 days
5. Low severity can be patched within 90 days or accepted as risk

Remediation Steps:
1. Identify affected components and versions
2. Check for available patches or updates
3. Test patches in staging environment
4. Apply patches during maintenance window
5. Verify remediation and monitor for regressions
6. Update security documentation

For Remote Code Execution vulnerabilities:
- Immediate patching required
- Consider temporary mitigation (WAF rules, network isolation)
- Monitor for exploitation attempts
- Verify no backdoors were installed
        """,
        "metadata": {
            "type": "remediation_guide",
            "category": "general",
            "source": "security_best_practices"
        }
    })
    
    # SQL Injection Remediation
    docs.append({
        "content": """
SQL Injection Vulnerability Remediation:

Immediate Actions:
1. Review application code for SQL injection vulnerabilities
2. Use parameterized queries or prepared statements
3. Implement input validation and sanitization
4. Apply least privilege principle to database users
5. Enable SQL injection protection in WAF

Code Examples:
- Use parameterized queries: SELECT * FROM users WHERE id = ?
- Avoid string concatenation in SQL queries
- Validate and sanitize all user inputs
- Use ORM frameworks that prevent SQL injection

Testing:
1. Perform penetration testing
2. Use automated SQL injection scanners
3. Review code with static analysis tools
4. Test with various input types
        """,
        "metadata": {
            "type": "remediation_guide",
            "category": "sql_injection",
            "source": "owasp_guidelines"
        }
    })
    
    # Authentication Bypass Remediation
    docs.append({
        "content": """
Authentication Bypass Vulnerability Remediation:

Critical Steps:
1. Review authentication mechanisms
2. Implement multi-factor authentication (MFA)
3. Use strong password policies
4. Implement account lockout after failed attempts
5. Review session management
6. Check for default credentials

Remediation:
1. Update authentication libraries to latest versions
2. Implement proper session management
3. Use secure token generation (JWT with proper signing)
4. Enable rate limiting on authentication endpoints
5. Monitor for brute force attempts
6. Implement CAPTCHA for repeated failures

Verification:
1. Test authentication bypass attempts
2. Verify MFA is working correctly
3. Check session timeout mechanisms
4. Review access logs for suspicious activity
        """,
        "metadata": {
            "type": "remediation_guide",
            "category": "authentication",
            "source": "security_framework"
        }
    })
    
    # Kubernetes Security
    docs.append({
        "content": """
Kubernetes Vulnerability Remediation:

Common Vulnerabilities:
1. Container escape vulnerabilities
2. Privilege escalation
3. Network policy misconfigurations
4. Secret management issues

Remediation Steps:
1. Update Kubernetes to latest patched version
2. Review and update container images
3. Implement network policies
4. Use RBAC for access control
5. Scan container images for vulnerabilities
6. Implement pod security policies
7. Use secrets management (Vault, etc.)

For CVE in Kubernetes components:
1. Check Kubernetes security advisories
2. Apply security patches immediately
3. Review affected components (kubelet, API server, etc.)
4. Test in non-production first
5. Update all cluster nodes
6. Verify cluster health after patching
        """,
        "metadata": {
            "type": "remediation_guide",
            "category": "kubernetes",
            "source": "kubernetes_security"
        }
    })
    
    return docs


def main():
    """Ingest security documentation"""
    logger.info("🚀 Ingesting security documentation...")
    
    try:
        rag_service = SecurityRAGService()
    except Exception as e:
        logger.error(f"❌ Failed to initialize RAG service: {e}")
        logger.error("Make sure ChromaDB is running: docker-compose up chromadb")
        return
    
    # Create sample docs
    docs = create_sample_docs()
    
    # Ingest each document
    total_chunks = 0
    for doc in docs:
        try:
            chunks = rag_service.ingest_document(
                content=doc["content"],
                metadata=doc["metadata"]
            )
            total_chunks += chunks
            logger.info(f"✅ Ingested: {doc['metadata'].get('source', 'unknown')}")
        except Exception as e:
            logger.error(f"❌ Failed to ingest document: {e}")
    
    logger.info(f"✅ Ingestion complete! Total chunks: {total_chunks}")
    logger.info("💡 Security RAG is ready for vulnerability management!")


if __name__ == "__main__":
    main()

