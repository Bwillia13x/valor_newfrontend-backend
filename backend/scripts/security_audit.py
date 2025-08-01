#!/usr/bin/env python3
"""
Security Audit Script for Valor IVX
Checks for common security issues and vulnerabilities
"""

import os
import re
import sys
import json
from pathlib import Path
from typing import List, Dict, Any

class SecurityAuditor:
    """Security auditor for the Valor IVX codebase"""
    
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path)
        self.issues = []
        self.warnings = []
        
    def audit_secrets(self) -> List[Dict[str, Any]]:
        """Audit for hardcoded secrets"""
        issues = []
        
        # Patterns for secrets
        secret_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'key\s*=\s*["\'][^"\']+["\']',
            r'token\s*=\s*["\'][^"\']+["\']',
            r'api_key\s*=\s*["\'][^"\']+["\']',
        ]
        
        for pattern in secret_patterns:
            for file_path in self.root_path.rglob("*.py"):
                if "venv" in str(file_path) or "__pycache__" in str(file_path):
                    continue
                    
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        matches = re.finditer(pattern, content, re.IGNORECASE)
                        for match in matches:
                            issues.append({
                                'type': 'hardcoded_secret',
                                'file': str(file_path),
                                'line': content[:match.start()].count('\n') + 1,
                                'pattern': pattern,
                                'severity': 'high'
                            })
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
        
        return issues
    
    def audit_sql_injection(self) -> List[Dict[str, Any]]:
        """Audit for potential SQL injection vulnerabilities"""
        issues = []
        
        # Look for raw SQL queries with user input
        sql_patterns = [
            r'execute\s*\(\s*["\'][^"\']*%[^"\']*["\']',
            r'query\s*\(\s*["\'][^"\']*%[^"\']*["\']',
            r'raw\s*\(\s*["\'][^"\']*%[^"\']*["\']',
        ]
        
        for pattern in sql_patterns:
            for file_path in self.root_path.rglob("*.py"):
                if "venv" in str(file_path) or "__pycache__" in str(file_path):
                    continue
                    
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        matches = re.finditer(pattern, content, re.IGNORECASE)
                        for match in matches:
                            issues.append({
                                'type': 'sql_injection',
                                'file': str(file_path),
                                'line': content[:match.start()].count('\n') + 1,
                                'pattern': pattern,
                                'severity': 'high'
                            })
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
        
        return issues
    
    def audit_xss_vulnerabilities(self) -> List[Dict[str, Any]]:
        """Audit for XSS vulnerabilities in JavaScript"""
        issues = []
        
        # Look for innerHTML usage
        xss_patterns = [
            r'\.innerHTML\s*=',
            r'document\.write\s*\(',
            r'eval\s*\(',
        ]
        
        for pattern in xss_patterns:
            for file_path in self.root_path.rglob("*.js"):
                if "node_modules" in str(file_path):
                    continue
                    
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        matches = re.finditer(pattern, content, re.IGNORECASE)
                        for match in matches:
                            issues.append({
                                'type': 'xss_vulnerability',
                                'file': str(file_path),
                                'line': content[:match.start()].count('\n') + 1,
                                'pattern': pattern,
                                'severity': 'medium'
                            })
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
        
        return issues
    
    def audit_file_permissions(self) -> List[Dict[str, Any]]:
        """Audit file permissions"""
        issues = []
        
        # Check for world-writable files
        for file_path in self.root_path.rglob("*"):
            if file_path.is_file():
                try:
                    stat = file_path.stat()
                    if stat.st_mode & 0o002:  # World writable
                        issues.append({
                            'type': 'world_writable_file',
                            'file': str(file_path),
                            'severity': 'medium'
                        })
                except Exception as e:
                    print(f"Error checking permissions for {file_path}: {e}")
        
        return issues
    
    def audit_dependencies(self) -> List[Dict[str, Any]]:
        """Audit dependencies for known vulnerabilities"""
        issues = []
        
        # Check requirements files
        requirements_files = ['requirements.txt', 'requirements-simple.txt']
        
        for req_file in requirements_files:
            req_path = self.root_path / req_file
            if req_path.exists():
                try:
                    with open(req_path, 'r') as f:
                        content = f.read()
                        # Check for known vulnerable packages
                        vulnerable_packages = [
                            'django<2.2.0',
                            'flask<2.0.0',
                            'requests<2.25.0',
                        ]
                        
                        for package in vulnerable_packages:
                            if package in content:
                                issues.append({
                                    'type': 'vulnerable_dependency',
                                    'file': str(req_path),
                                    'package': package,
                                    'severity': 'high'
                                })
                except Exception as e:
                    print(f"Error reading {req_path}: {e}")
        
        return issues
    
    def audit_environment_variables(self) -> List[Dict[str, Any]]:
        """Audit environment variable usage"""
        issues = []
        
        # Check for missing environment variables in production
        env_files = ['.env.example', '.env.production']
        
        for env_file in env_files:
            env_path = self.root_path / env_file
            if env_path.exists():
                try:
                    with open(env_path, 'r') as f:
                        content = f.read()
                        if 'SECRET_KEY=' in content and 'change-me' in content:
                            issues.append({
                                'type': 'default_secret',
                                'file': str(env_path),
                                'severity': 'high'
                            })
                except Exception as e:
                    print(f"Error reading {env_path}: {e}")
        
        return issues
    
    def run_full_audit(self) -> Dict[str, Any]:
        """Run complete security audit"""
        print("🔍 Starting security audit...")
        
        audit_results = {
            'secrets': self.audit_secrets(),
            'sql_injection': self.audit_sql_injection(),
            'xss': self.audit_xss_vulnerabilities(),
            'file_permissions': self.audit_file_permissions(),
            'dependencies': self.audit_dependencies(),
            'environment': self.audit_environment_variables(),
        }
        
        # Count issues by severity
        total_issues = 0
        high_issues = 0
        medium_issues = 0
        low_issues = 0
        
        for category, issues in audit_results.items():
            for issue in issues:
                total_issues += 1
                if issue.get('severity') == 'high':
                    high_issues += 1
                elif issue.get('severity') == 'medium':
                    medium_issues += 1
                else:
                    low_issues += 1
        
        audit_results['summary'] = {
            'total_issues': total_issues,
            'high_issues': high_issues,
            'medium_issues': medium_issues,
            'low_issues': low_issues,
        }
        
        return audit_results
    
    def print_report(self, results: Dict[str, Any]):
        """Print audit report"""
        print("\n" + "="*60)
        print("🔒 SECURITY AUDIT REPORT")
        print("="*60)
        
        summary = results.get('summary', {})
        print(f"\n📊 SUMMARY:")
        print(f"   Total Issues: {summary.get('total_issues', 0)}")
        print(f"   High Severity: {summary.get('high_issues', 0)}")
        print(f"   Medium Severity: {summary.get('medium_issues', 0)}")
        print(f"   Low Severity: {summary.get('low_issues', 0)}")
        
        for category, issues in results.items():
            if category == 'summary':
                continue
                
            if issues:
                print(f"\n🚨 {category.upper()} ISSUES ({len(issues)}):")
                for issue in issues:
                    severity_icon = "🔴" if issue.get('severity') == 'high' else "🟡" if issue.get('severity') == 'medium' else "🟢"
                    print(f"   {severity_icon} {issue.get('file', 'Unknown file')}")
                    if 'line' in issue:
                        print(f"      Line: {issue['line']}")
                    if 'pattern' in issue:
                        print(f"      Pattern: {issue['pattern']}")
                    print()
        
        if summary.get('total_issues', 0) == 0:
            print("\n✅ No security issues found!")
        else:
            print(f"\n⚠️  Found {summary.get('total_issues', 0)} security issues that need attention.")

def main():
    """Main function"""
    auditor = SecurityAuditor()
    results = auditor.run_full_audit()
    auditor.print_report(results)
    
    # Exit with error code if high severity issues found
    if results.get('summary', {}).get('high_issues', 0) > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()