"""
Generate mock CVE/vulnerability data for demo purposes
"""
import json
from datetime import datetime, timedelta
from pathlib import Path
import random


def generate_mock_cves(output_path: str, num_cves: int = 20):
    """Generate mock CVE data"""
    cves = []
    
    # Sample vulnerability types
    vuln_types = [
        "Remote Code Execution",
        "SQL Injection",
        "Cross-Site Scripting (XSS)",
        "Authentication Bypass",
        "Privilege Escalation",
        "Denial of Service",
        "Information Disclosure",
        "Path Traversal"
    ]
    
    # Sample affected components
    components = [
        ["api-service", "backend"],
        ["kubernetes-cluster", "infrastructure"],
        ["postgres-database", "database"],
        ["auth-service", "security"],
        ["frontend-app", "frontend"],
        ["monitoring-stack", "observability"],
        ["ci-cd-pipeline", "devops"],
        ["data-pipeline", "data"]
    ]
    
    # Sample exploitability levels
    exploitability_levels = [
        ("active_exploits", "Actively exploited in the wild"),
        ("poc_available", "Proof of concept available"),
        ("theoretical", "Theoretical exploit possible"),
        ("none", "No known exploits")
    ]
    
    base_year = 2024
    
    for i in range(num_cves):
        cve_year = base_year - random.randint(0, 2)
        cve_num = random.randint(1000, 9999)
        cve_id = f"CVE-{cve_year}-{cve_num}"
        
        vuln_type = random.choice(vuln_types)
        affected = random.choice(components)
        exploitability, exploit_desc = random.choice(exploitability_levels)
        
        # Generate CVSS score based on exploitability
        if exploitability == "active_exploits":
            cvss_score = random.uniform(8.0, 10.0)
        elif exploitability == "poc_available":
            cvss_score = random.uniform(6.0, 9.0)
        elif exploitability == "theoretical":
            cvss_score = random.uniform(4.0, 7.0)
        else:
            cvss_score = random.uniform(2.0, 5.0)
        
        cve = {
            "cve_id": cve_id,
            "title": f"{vuln_type} in {affected[0]}",
            "description": f"{vuln_type} vulnerability discovered in {affected[0]}. {exploit_desc}. This vulnerability could allow an attacker to compromise the affected system.",
            "cvss_score": round(cvss_score, 1),
            "affected_components": affected,
            "detected_at": (datetime.utcnow() - timedelta(days=random.randint(0, 30))).isoformat(),
            "source": random.choice(["scanner", "manual", "security-advisory"]),
            "metadata": {
                "exploitability": exploitability,
                "vulnerability_type": vuln_type
            }
        }
        
        cves.append(cve)
    
    # Save to JSON file
    with open(output_path, 'w') as f:
        json.dump(cves, f, indent=2)
    
    print(f"✅ Generated {num_cves} mock CVEs: {output_path}")


def main():
    """Generate mock CVE data"""
    data_dir = Path(__file__).parent.parent.parent / "data" / "vulnerabilities"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = data_dir / "mock_cves.json"
    generate_mock_cves(str(output_file), 20)
    
    print("✅ Mock CVE data generation complete!")


if __name__ == "__main__":
    main()

