# main.py

# This is the file from where we start our application
# It simply creates the app and runs it

from app import create_app

# Create app using factory function
app = create_app()


# This condition ensures the app runs only when this file is executed directly
if __name__ == "__main__":
    
    # Create database tables if they don't exist
    from app import db

    with app.app_context():
        db.create_all()

    # Run the Flask app
    app.run(debug=True)