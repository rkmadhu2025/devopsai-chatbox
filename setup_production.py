#!/usr/bin/env python3
"""
Production Setup Script
=======================
Initializes database tables and verifies all components are working.

Run: python setup_production.py
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def print_header(text):
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

def print_status(name, status, detail=""):
    icon = "+" if status else "X"
    status_text = "OK" if status else "FAILED"
    print(f"  [{icon}] {name}: {status_text} {detail}")

def check_dependencies():
    """Check all required dependencies are installed."""
    print_header("Checking Dependencies")

    deps = {
        "psycopg2": "PostgreSQL sync driver",
        "asyncpg": "PostgreSQL async driver",
        "fitz": "PDF processing (PyMuPDF)",
        "pypdf": "PDF fallback",
        "pdfplumber": "PDF tables",
        "PIL": "Image processing (Pillow)",
        "chardet": "Text encoding detection",
        "anthropic": "Anthropic API client",
        "fastapi": "Web framework",
    }

    all_ok = True
    for module, description in deps.items():
        try:
            if module == "PIL":
                __import__("PIL")
            elif module == "fitz":
                __import__("fitz")
            else:
                __import__(module)
            print_status(description, True)
        except ImportError:
            print_status(description, False, "(optional)" if module in ["fitz", "pdfplumber"] else "")
            if module not in ["fitz", "pdfplumber", "asyncpg"]:
                all_ok = False

    return all_ok

def check_database():
    """Check database connection and create tables."""
    print_header("Database Connection")

    try:
        from database import DatabaseManager

        db = DatabaseManager()
        print(f"  Connection string: {db.config['host']}:{db.config['port']}/{db.config['database']}")

        # Try to connect
        if db.initialize_sync_pool():
            print_status("Connection pool", True)

            # Health check
            health = db.health_check()
            if health.get("status") == "healthy":
                print_status("Database health", True, health.get("version", "")[:50])
            else:
                print_status("Database health", False, health.get("error", ""))
                return False

            # Create tables
            print("\n  Creating tables...")
            if db.create_tables():
                print_status("Tables created", True)
            else:
                print_status("Tables creation", False)
                return False

            # Verify tables exist
            try:
                result = db.fetch_all("""
                    SELECT table_name FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name IN ('chat_history', 'file_loads', 'host_history', 'sessions')
                """)
                tables = [r['table_name'] for r in result]
                for table in ['chat_history', 'file_loads', 'host_history', 'sessions']:
                    print_status(f"Table '{table}'", table in tables)
            except Exception as e:
                print(f"  Warning: Could not verify tables: {e}")

            db.close()
            return True
        else:
            print_status("Connection pool", False, "Could not initialize")
            return False

    except ImportError as e:
        print_status("Database module", False, str(e))
        return False
    except Exception as e:
        print_status("Database", False, str(e))
        return False

def check_file_processor():
    """Check file processor is working."""
    print_header("File Processor")

    try:
        from file_loader import FileProcessor, PDFLoader, TextLoader, ImageLoader

        # Check PDF loader
        pdf = PDFLoader()
        print_status("PDF loader", pdf.is_available(), f"Libraries: {', '.join(pdf.get_available_libraries())}")

        # Check text loader
        text = TextLoader()
        print_status("Text loader", True)

        # Check image loader
        img = ImageLoader()
        print_status("Image loader", img.is_available())
        print_status("OCR available", img.is_ocr_available(), f"Backend: {img.ocr_backend or 'none'}")

        # Check file processor
        fp = FileProcessor()
        print_status("File processor", True, f"Upload dir: {fp.upload_dir}")

        # Ensure upload directory exists
        os.makedirs(fp.upload_dir, exist_ok=True)
        print_status("Upload directory", os.path.exists(fp.upload_dir))

        return True

    except ImportError as e:
        print_status("File loader module", False, str(e))
        return False
    except Exception as e:
        print_status("File processor", False, str(e))
        return False

def check_agents():
    """Check agents are configured."""
    print_header("Agent Configuration")

    try:
        from agents.devops_agents import DEVOPS_AGENT_CONFIGS, get_agents_by_category

        print_status("Agent configs loaded", True, f"{len(DEVOPS_AGENT_CONFIGS)} agents")

        categories = get_agents_by_category()
        for cat, agents in categories.items():
            print(f"    - {cat}: {len(agents)} agents")

        return True

    except Exception as e:
        print_status("Agents", False, str(e))
        return False

def check_api_config():
    """Check API configuration."""
    print_header("API Configuration")

    config_path = os.path.join(os.path.dirname(__file__), "config.json")

    if os.path.exists(config_path):
        print_status("config.json", True)

        import json
        with open(config_path, 'r') as f:
            config = json.load(f)

        api_key = config.get("anthropic", {}).get("api_key", "")
        if api_key and len(api_key) > 20:
            print_status("Anthropic API key", True, f"...{api_key[-8:]}")
        else:
            print_status("Anthropic API key", False, "Not configured or invalid")

        model = config.get("anthropic", {}).get("model", "unknown")
        print_status("Model", True, model)

        return bool(api_key)
    else:
        print_status("config.json", False, "File not found")
        return False

def run_test_insert():
    """Test database operations."""
    print_header("Testing Database Operations")

    try:
        from database import DatabaseManager, ChatRepository, HostRepository

        db = DatabaseManager()
        if not db.initialize_sync_pool():
            print_status("Database connection", False)
            return False

        # Test chat repository
        chat_repo = ChatRepository(db)
        test_session = "test_session_setup"

        msg_id = chat_repo.save_message(
            session_id=test_session,
            role="user",
            message="Test message from setup script",
            agent_id="general"
        )
        print_status("Chat insert", msg_id is not None, f"ID: {msg_id}")

        # Test host repository
        host_repo = HostRepository(db)
        host_id = host_repo.log_action(
            hostname="test-host",
            action="health_check",
            status="success",
            details={"source": "setup_script"}
        )
        print_status("Host log insert", host_id is not None, f"ID: {host_id}")

        # Cleanup test data
        chat_repo.delete_session(test_session)
        print_status("Cleanup", True)

        db.close()
        return True

    except Exception as e:
        print_status("Database operations", False, str(e))
        return False

def main():
    print("\n" + "=" * 60)
    print("  DEVOPS GENAI CHATBOT - PRODUCTION SETUP")
    print("=" * 60)

    results = {}

    # Run all checks
    results["dependencies"] = check_dependencies()
    results["database"] = check_database()
    results["file_processor"] = check_file_processor()
    results["agents"] = check_agents()
    results["api_config"] = check_api_config()

    # Test database operations if database is OK
    if results["database"]:
        results["db_operations"] = run_test_insert()

    # Summary
    print_header("Setup Summary")

    all_ok = all(results.values())

    for check, status in results.items():
        print_status(check.replace("_", " ").title(), status)

    if all_ok:
        print("\n  [+] All checks passed! Ready for production.")
        print("\n  Start the server with:")
        print("    python -m uvicorn chatbot.main:app --host 0.0.0.0 --port 8000")
        print("\n  Or for development:")
        print("    python -m uvicorn chatbot.main:app --reload --port 8000")
    else:
        print("\n  [!] Some checks failed. Please review the output above.")
        if not results.get("database"):
            print("\n  Note: Database connection failed. The application will")
            print("        use in-memory storage as fallback.")

    print("\n" + "=" * 60 + "\n")

    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())
