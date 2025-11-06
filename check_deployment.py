#!/usr/bin/env python3
"""
Pre-deployment checklist script
Verifies all required files and configurations are in place
"""
import os
import sys
from pathlib import Path

def check_file_exists(filepath, description):
    """Check if a file exists"""
    if Path(filepath).exists():
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description} MISSING: {filepath}")
        return False

def check_env_example():
    """Check if .env.example exists with required variables"""
    env_example = Path("backend/.env.example")
    if not env_example.exists():
        print("❌ backend/.env.example not found")
        return False
    
    required_vars = [
        "DATABASE_URL",
        "OPENAI_API_KEY",
        "SMTP_USER",
        "SMTP_PASSWORD",
        "SECRET_KEY"
    ]
    
    content = env_example.read_text()
    missing = [var for var in required_vars if var not in content]
    
    if missing:
        print(f"❌ Missing variables in .env.example: {', '.join(missing)}")
        return False
    else:
        print("✅ .env.example has all required variables")
        return True

def main():
    print("🔍 Running Pre-Deployment Checklist...\n")
    
    checks = []
    
    # Check root configuration
    print("📋 Root Configuration Files:")
    checks.append(check_file_exists("render.yaml", "Render Blueprint"))
    checks.append(check_file_exists("DEPLOY_RENDER.md", "Deployment Guide"))
    
    # Check backend files
    print("\n📦 Backend Files:")
    checks.append(check_file_exists("backend/requirements.txt", "Python Dependencies"))
    checks.append(check_file_exists("backend/build.py", "Database Build Script"))
    checks.append(check_file_exists("backend/.gitignore", "Backend .gitignore"))
    checks.append(check_file_exists("backend/app/main.py", "FastAPI Main"))
    checks.append(check_file_exists("backend/app/config.py", "Config Settings"))
    
    # Check frontend files
    print("\n🎨 Frontend Files:")
    checks.append(check_file_exists("frontend/package.json", "Package.json"))
    checks.append(check_file_exists("frontend/.env.production", "Production Env"))
    checks.append(check_file_exists("frontend/vite.config.ts", "Vite Config"))
    
    # Check environment example
    print("\n🔐 Environment Configuration:")
    checks.append(check_env_example())
    
    # Summary
    print("\n" + "="*50)
    passed = sum(checks)
    total = len(checks)
    
    if passed == total:
        print(f"✅ ALL CHECKS PASSED ({passed}/{total})")
        print("\n🚀 Ready for deployment!")
        print("\nNext steps:")
        print("1. Push code to GitHub")
        print("2. Go to Render Dashboard")
        print("3. Create Blueprint from your repository")
        print("4. Add environment variables")
        print("5. Deploy!")
        return 0
    else:
        print(f"❌ CHECKS FAILED ({total-passed}/{total} issues)")
        print("\n⚠️  Please fix the issues above before deploying")
        return 1

if __name__ == "__main__":
    sys.exit(main())
