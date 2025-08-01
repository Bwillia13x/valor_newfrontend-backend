#!/usr/bin/env python3
"""
Migration check script for CI/CD
Ensures enterprise models have proper migrations
"""

import os
import sys
from pathlib import Path

def check_migrations():
    """Check that migrations are properly configured"""
    
    # Check if alembic directory exists
    alembic_dir = Path("alembic")
    if not alembic_dir.exists():
        print("❌ Alembic directory not found. Run 'alembic init alembic'")
        return False
    
    # Check if versions directory exists and has migration files
    versions_dir = alembic_dir / "versions"
    if not versions_dir.exists():
        print("❌ Alembic versions directory not found")
        return False
    
    migration_files = list(versions_dir.glob("*.py"))
    if not migration_files:
        print("❌ No migration files found in alembic/versions/")
        return False
    
    print(f"✅ Found {len(migration_files)} migration file(s)")
    
    # Check if env.py imports EnterpriseBase
    env_py = alembic_dir / "env.py"
    if not env_py.exists():
        print("❌ alembic/env.py not found")
        return False
    
    with open(env_py, 'r') as f:
        content = f.read()
        if "EnterpriseBase" not in content:
            print("❌ alembic/env.py does not import EnterpriseBase")
            return False
    
    print("✅ alembic/env.py properly configured")
    
    # Check if enterprise models file exists
    models_file = Path("models/enterprise_models.py")
    if not models_file.exists():
        print("❌ models/enterprise_models.py not found")
        return False
    print("✅ Enterprise models file exists")
    
    # Check if database configuration file exists
    db_file = Path("db_enterprise.py")
    if not db_file.exists():
        print("❌ db_enterprise.py not found")
        return False
    print("✅ Database configuration file exists")
    
    return True

def main():
    """Main function"""
    print("🔍 Checking Valor IVX migrations...")
    
    # Change to backend directory if needed
    if not Path("alembic").exists() and Path("backend/alembic").exists():
        os.chdir("backend")
    
    success = check_migrations()
    
    if success:
        print("✅ Migration check passed")
        sys.exit(0)
    else:
        print("❌ Migration check failed")
        sys.exit(1)

if __name__ == "__main__":
    main()