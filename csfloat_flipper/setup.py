#!/usr/bin/env python3
"""
Setup script for CSFloat Auto-Flipper
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check Python version"""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8+ is required")
        sys.exit(1)
    print(f"✓ Python {sys.version.split()[0]} detected")

def install_dependencies():
    """Install required dependencies"""
    print("\nInstalling dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
    print("✓ Dependencies installed")

def setup_environment():
    """Setup environment file"""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        print("\nCreating .env file...")
        import shutil
        shutil.copy(env_example, env_file)
        print("✓ .env file created")
        print("\n⚠️  Please edit .env and add your CSFLOAT_API_KEY")
    elif env_file.exists():
        print("✓ .env file already exists")

def setup_directories():
    """Create required directories"""
    directories = ["logs", "data", "models"]
    for dir_name in directories:
        Path(dir_name).mkdir(exist_ok=True)
    print("✓ Directories created")

def check_services():
    """Check required services"""
    print("\nChecking services...")
    
    # Check MongoDB
    try:
        import pymongo
        client = pymongo.MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=1000)
        client.server_info()
        print("✓ MongoDB is running")
    except:
        print("⚠️  MongoDB is not running. Please start MongoDB")
        
    # Check Redis
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✓ Redis is running")
    except:
        print("⚠️  Redis is not running. Please start Redis")

def main():
    """Main setup function"""
    print("CSFloat Auto-Flipper Setup")
    print("=" * 50)
    
    check_python_version()
    install_dependencies()
    setup_environment()
    setup_directories()
    check_services()
    
    print("\n" + "=" * 50)
    print("Setup complete!")
    print("\nNext steps:")
    print("1. Edit .env file and add your CSFLOAT_API_KEY")
    print("2. Start MongoDB and Redis if not running")
    print("3. Run: python main.py")
    print("\nOptional:")
    print("- Configure trading parameters in config.py")
    print("- Monitor dashboard at http://localhost:9090/dashboard")

if __name__ == "__main__":
    main()