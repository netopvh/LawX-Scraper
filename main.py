import app_code_120
import sys
def main():
    # Import and run app_code_120 as if it was run directly
    
    # Save original __name__ value
    original_name = app_code_120.__name__
    
    # Temporarily modify __name__ to simulate direct execution
    app_code_120.__name__ = "__main__"
    
    # Run the main logic from app_code_120
    try:
        if hasattr(app_code_120, 'main'):
            app_code_120.main()
        else:
            # Execute the file directly if no main() function exists
            exec(open('app_code_120.py').read())
    finally:
        # Restore original __name__
        app_code_120.__name__ = original_name


if __name__ == "__main__":
    main()
