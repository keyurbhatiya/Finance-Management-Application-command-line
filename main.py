import sqlite3
import hashlib
import getpass
import os
import logging
from contextlib import contextmanager
from datetime import datetime

# Set up logging
logging.basicConfig(
    filename='finance_app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = None
    try:
        conn = sqlite3.connect("finance_app.db")
        yield conn
    except Exception as e:
        logging.error(f"Database error: {str(e)}")
        raise
    finally:
        if conn:
            conn.close()

def validate_date(date_str):
    """Validate date string format."""
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def hash_password(password):
    """Hash the password using a more secure method."""
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'),
                                 salt, 100000)
    return salt.decode('ascii') + ':' + pwdhash.hex()

def verify_password(stored_password, provided_password):
    """Verify the stored password against the provided password."""
    try:
        salt, stored_hash = stored_password.split(':')
        pwdhash = hashlib.pbkdf2_hmac('sha512', provided_password.encode('utf-8'),
                                     salt.encode('ascii'), 100000)
        return pwdhash.hex() == stored_hash
    except Exception:
        return False

def create_database():
    """Create the database and tables if they don't exist."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.executescript('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    type TEXT CHECK(type IN ('Income', 'Expense')) NOT NULL,
                    category TEXT NOT NULL,
                    amount DECIMAL(10,2) NOT NULL,
                    description TEXT,
                    date TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                );
                
                CREATE TABLE IF NOT EXISTS budgets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    category TEXT NOT NULL,
                    amount DECIMAL(10,2) NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id),
                    UNIQUE(user_id, category)
                );
                
                CREATE INDEX IF NOT EXISTS idx_transactions_user_date 
                ON transactions(user_id, date);
                
                CREATE INDEX IF NOT EXISTS idx_budgets_user 
                ON budgets(user_id);
            ''')
            logging.info("Database created/updated successfully")
    except Exception as e:
        logging.error(f"Failed to create database: {str(e)}")
        raise

def register_user():
    """Register a new user with improved security."""
    print("\n=== Register ===")
    username = input("Enter a username: ").strip()
    if not username:
        print("Username cannot be empty.")
        return

    password = getpass.getpass("Enter a password: ")
    confirm_password = getpass.getpass("Confirm password: ")

    if password != confirm_password:
        print("Passwords do not match. Please try again.")
        return

    if len(password) < 8:
        print("Password must be at least 8 characters long.")
        return

    hashed_password = hash_password(password)

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", 
                         (username, hashed_password))
            conn.commit()
            print("Registration successful! You can now log in.")
            logging.info(f"New user registered: {username}")
    except sqlite3.IntegrityError:
        print("Username already exists. Please choose a different one.")
    except Exception as e:
        logging.error(f"Registration error: {str(e)}")
        print("Registration failed. Please try again.")

def login_user():
    """Authenticate an existing user with secure password verification."""
    print("\n=== Login ===")
    username = input("Enter your username: ").strip()
    password = getpass.getpass("Enter your password: ")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, password FROM users WHERE username = ?", 
                         (username,))
            user = cursor.fetchone()

            if user and verify_password(user[1], password):
                print(f"Welcome back, {username}!")
                logging.info(f"User logged in: {username}")
                return user[0]  # Return user ID
            else:
                print("Invalid username or password. Please try again.")
                return None
    except Exception as e:
        logging.error(f"Login error: {str(e)}")
        print("Login failed. Please try again.")
        return None

def add_transaction(user_id):
    """Add a new income or expense transaction with validation."""
    print("\n=== Add Transaction ===")
    
    # Validate transaction type
    while True:
        type = input("Enter transaction type (Income/Expense): ").capitalize()
        if type in ["Income", "Expense"]:
            break
        print("Invalid transaction type. Please enter 'Income' or 'Expense'.")
    
    category = input("Enter category (e.g., Food, Rent, Salary): ").strip()
    if not category:
        print("Category cannot be empty.")
        return
    
    # Validate amount
    while True:
        try:
            amount = float(input("Enter amount: "))
            if amount <= 0:
                raise ValueError("Amount must be positive")
            break
        except ValueError as e:
            print(f"Invalid amount: {str(e)}")
    
    description = input("Enter description (optional): ")
    
    # Validate date
    while True:
        date = input("Enter date (YYYY-MM-DD): ")
        if validate_date(date):
            break
        print("Invalid date format. Please use YYYY-MM-DD format.")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO transactions 
                (user_id, type, category, amount, description, date)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, type, category, amount, description, date))
            conn.commit()
        print("Transaction added successfully!")
        logging.info(f"Transaction added for user {user_id}: {type} - {amount}")
    except Exception as e:
        logging.error(f"Failed to add transaction: {str(e)}")
        print("Failed to add transaction. Please try again.")

def view_transactions(user_id):
    """View all transactions for the logged-in user."""
    print("\n=== View Transactions ===")
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, type, category, amount, description, date 
                FROM transactions 
                WHERE user_id = ?
                ORDER BY date DESC
            ''', (user_id,))
            transactions = cursor.fetchall()

        if transactions:
            for transaction in transactions:
                print(f"ID: {transaction[0]} | Type: {transaction[1]} | "
                      f"Category: {transaction[2]} | Amount: {transaction[3]:.2f} | "
                      f"Description: {transaction[4]} | Date: {transaction[5]}")
        else:
            print("No transactions found.")
    except Exception as e:
        logging.error(f"Failed to view transactions: {str(e)}")
        print("Failed to retrieve transactions. Please try again.")

def update_transaction(user_id):
    """Update an existing transaction with validation."""
    print("\n=== Update Transaction ===")
    view_transactions(user_id)
    
    try:
        transaction_id = int(input("Enter the transaction ID to update: "))
    except ValueError:
        print("Invalid transaction ID.")
        return

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM transactions WHERE id = ? AND user_id = ?
            ''', (transaction_id, user_id))
            transaction = cursor.fetchone()

            if not transaction:
                print("Transaction not found.")
                return

            # Get and validate new values
            while True:
                type = input("Enter new transaction type (Income/Expense): ").capitalize()
                if type in ["Income", "Expense"]:
                    break
                print("Invalid transaction type.")

            category = input("Enter new category: ").strip()
            if not category:
                print("Category cannot be empty.")
                return

            while True:
                try:
                    amount = float(input("Enter new amount: "))
                    if amount <= 0:
                        raise ValueError("Amount must be positive")
                    break
                except ValueError:
                    print("Invalid amount.")

            description = input("Enter new description: ")

            while True:
                date = input("Enter new date (YYYY-MM-DD): ")
                if validate_date(date):
                    break
                print("Invalid date format. Please use YYYY-MM-DD format.")

            cursor.execute('''
                UPDATE transactions 
                SET type = ?, category = ?, amount = ?, description = ?, date = ? 
                WHERE id = ? AND user_id = ?
            ''', (type, category, amount, description, date, transaction_id, user_id))
            conn.commit()
            print("Transaction updated successfully!")
            logging.info(f"Transaction {transaction_id} updated for user {user_id}")
    except Exception as e:
        logging.error(f"Failed to update transaction: {str(e)}")
        print("Failed to update transaction. Please try again.")

def delete_transaction(user_id):
    """Delete an existing transaction with confirmation."""
    print("\n=== Delete Transaction ===")
    view_transactions(user_id)
    
    try:
        transaction_id = int(input("Enter the transaction ID to delete: "))
    except ValueError:
        print("Invalid transaction ID.")
        return

    confirm = input("Are you sure you want to delete this transaction? (y/n): ")
    if confirm.lower() != 'y':
        print("Deletion cancelled.")
        return

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM transactions WHERE id = ? AND user_id = ?
            ''', (transaction_id, user_id))
            if cursor.rowcount > 0:
                conn.commit()
                print("Transaction deleted successfully!")
                logging.info(f"Transaction {transaction_id} deleted for user {user_id}")
            else:
                print("Transaction not found.")
    except Exception as e:
        logging.error(f"Failed to delete transaction: {str(e)}")
        print("Failed to delete transaction. Please try again.")

def set_budget(user_id):
    """Set a budget for a specific category with validation."""
    print("\n=== Set Budget ===")
    category = input("Enter category for the budget: ").strip()
    if not category:
        print("Category cannot be empty.")
        return

    try:
        amount = float(input("Enter budget amount: "))
        if amount <= 0:
            print("Budget amount must be positive.")
            return

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO budgets (user_id, category, amount)
                VALUES (?, ?, ?)
            ''', (user_id, category, amount))
            conn.commit()
            print(f"Budget set for {category}: {amount:.2f}")
            logging.info(f"Budget set for user {user_id}: {category} - {amount}")
    except ValueError:
        print("Invalid amount.")
    except Exception as e:
        logging.error(f"Failed to set budget: {str(e)}")
        print("Failed to set budget. Please try again.")

def check_budget(user_id):
    """Check if any budget is exceeded with detailed reporting."""
    print("\n=== Check Budget ===")
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT b.category, b.amount, 
                       COALESCE(SUM(t.amount), 0) as spent
                FROM budgets b
                LEFT JOIN transactions t ON b.user_id = t.user_id 
                    AND b.category = t.category 
                    AND t.type = 'Expense'
                    AND t.date >= date('now', 'start of month')
                WHERE b.user_id = ?
                GROUP BY b.category, b.amount
            ''', (user_id,))
            results = cursor.fetchall()

            if not results:
                print("No budgets set. Please set a budget first.")
                return

            budget_exceeded = False
            for category, budget_amount, spent in results:
                if spent > budget_amount:
                    budget_exceeded = True
                    print(f"⚠️  Budget exceeded for {category}: "
                          f"Spent {spent:.2f}, Budget {budget_amount:.2f}")
                else:
                    print(f"✅ Within budget for {category}: "
                          f"Spent {spent:.2f}, Budget {budget_amount:.2f}")

            if not budget_exceeded:
                print("All budgets are within limits.")
    except Exception as e:
        logging.error(f"Failed to check budgets: {str(e)}")
        print("Failed to check budgets. Please try again.")

def generate_reports(user_id):
    """Generate financial reports with improved formatting."""
    print("\n=== Financial Reports ===")
    try:
        # Get and validate input
        while True:
            try:
                month = input("Enter month for report (MM): ")
                year = input("Enter year for report (YYYY): ")
                if validate_date(f"{year}-{month}-01"):
                    break
                print("Invalid month/year format.")
            except ValueError:
                print("Invalid date format.")

        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Monthly Report
            cursor.execute('''
                SELECT type, SUM(amount) FROM transactions
                WHERE user_id = ? AND date LIKE ?
                GROUP BY type
            ''', (user_id, f"{year}-{month}-%"))
            monthly_data = cursor.fetchall()

            # Calculate totals
            monthly_income = sum(amount for type, amount in monthly_data if type == "Income")
            monthly_expense = sum(amount for type, amount in monthly_data if type == "Expense")
            monthly_savings = monthly_income - monthly_expense

            print(f"\nMonthly Report ({year}-{month}):")
            print(f"Total Income:  ₹{monthly_income:,.2f}")
            print(f"Total Expense: ₹{monthly_expense:,.2f}")
            print(f"Savings:       ₹{monthly_savings:,.2f}")

            # Yearly Report
            cursor.execute('''
                SELECT type, SUM(amount) FROM transactions
                WHERESELECT type, SUM(amount) FROM transactions
                WHERE user_id = ? AND date LIKE ?
                GROUP BY type
            ''', (user_id, f"{year}-%"))
            yearly_data = cursor.fetchall()

            # Calculate yearly totals
            yearly_income = sum(amount for type, amount in yearly_data if type == "Income")
            yearly_expense = sum(amount for type, amount in yearly_data if type == "Expense")
            yearly_savings = yearly_income - yearly_expense

            print(f"\nYearly Report ({year}):")
            print(f"Total Income:  ₹{yearly_income:,.2f}")
            print(f"Total Expense: ₹{yearly_expense:,.2f}")
            print(f"Savings:       ₹{yearly_savings:,.2f}")

            # Category breakdown
            print("\nExpense Breakdown by Category:")
            cursor.execute('''
                SELECT category, SUM(amount) as total
                FROM transactions
                WHERE user_id = ? AND type = 'Expense' AND date LIKE ?
                GROUP BY category
                ORDER BY total DESC
            ''', (user_id, f"{year}-{month}-%"))
            
            categories = cursor.fetchall()
            for category, amount in categories:
                percentage = (amount / monthly_expense * 100) if monthly_expense > 0 else 0
                print(f"{category}: ₹{amount:,.2f} ({percentage:.1f}%)")

    except Exception as e:
        logging.error(f"Failed to generate reports: {str(e)}")
        print("Failed to generate reports. Please try again.")

def backup_data():
    """Backup the database with error handling."""
    try:
        import shutil
        from datetime import datetime
        
        # Create backup with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f'finance_backup_{timestamp}.db'
        
        shutil.copy('finance_app.db', backup_file)
        print(f"Backup completed successfully: {backup_file}")
        logging.info(f"Database backed up to {backup_file}")
    except Exception as e:
        logging.error(f"Backup failed: {str(e)}")
        print("Failed to create backup. Please try again.")

def restore_data():
    """Restore the database from backup with validation."""
    try:
        import shutil
        import glob
        
        # List available backups
        backups = glob.glob('finance_backup_*.db')
        if not backups:
            print("No backup files found.")
            return

        print("\nAvailable backups:")
        for i, backup in enumerate(backups, 1):
            print(f"{i}. {backup}")

        choice = input("\nEnter backup number to restore (or 'cancel'): ")
        if choice.lower() == 'cancel':
            return

        try:
            backup_file = backups[int(choice) - 1]
        except (ValueError, IndexError):
            print("Invalid selection.")
            return

        # Confirm before restoring
        confirm = input(f"Are you sure you want to restore from {backup_file}? "
                       f"Current data will be overwritten (y/n): ")
        if confirm.lower() != 'y':
            print("Restore cancelled.")
            return

        shutil.copy(backup_file, 'finance_app.db')
        print("Data restored successfully!")
        logging.info(f"Database restored from {backup_file}")
    except Exception as e:
        logging.error(f"Restore failed: {str(e)}")
        print("Failed to restore data. Please try again.")

def main():
    """Main function to handle user interaction with improved error handling."""
    try:
        create_database()
        user_id = None

        while True:
            try:
                print("\n=== Personal Finance Management Application ===")
                print("1. Register")
                print("2. Login")
                print("3. Backup Data")
                print("4. Restore Data")
                print("5. Exit")

                choice = input("Select an option (1-5): ")

                if choice == "1":
                    register_user()
                elif choice == "2":
                    user_id = login_user()
                    if user_id:
                        break
                elif choice == "3":
                    backup_data()
                elif choice == "4":
                    restore_data()
                elif choice == "5":
                    print("Goodbye!")
                    return
                else:
                    print("Invalid choice. Please try again.")

            except KeyboardInterrupt:
                print("\nOperation cancelled by user.")
            except Exception as e:
                logging.error(f"Main menu error: {str(e)}")
                print("An error occurred. Please try again.")

        while user_id:
            try:
                print("\n=== Finance Dashboard ===")
                print("1. Add Transaction")
                print("2. View Transactions")
                print("3. Update Transaction")
                print("4. Delete Transaction")
                print("5. Set Budget")
                print("6. Check Budget")
                print("7. Generate Reports")
                print("8. Backup Data")
                print("9. Restore Data")
                print("10. Logout")

                choice = input("Select an option (1-10): ")

                if choice == "1":
                    add_transaction(user_id)
                elif choice == "2":
                    view_transactions(user_id)
                elif choice == "3":
                    update_transaction(user_id)
                elif choice == "4":
                    delete_transaction(user_id)
                elif choice == "5":
                    set_budget(user_id)
                elif choice == "6":
                    check_budget(user_id)
                elif choice == "7":
                    generate_reports(user_id)
                elif choice == "8":
                    backup_data()
                elif choice == "9":
                    restore_data()
                elif choice == "10":
                    print("Logged out successfully!")
                    user_id = None
                else:
                    print("Invalid choice. Please try again.")

            except KeyboardInterrupt:
                print("\nOperation cancelled by user.")
            except Exception as e:
                logging.error(f"Dashboard error: {str(e)}")
                print("An error occurred. Please try again.")

    except Exception as e:
        logging.error(f"Application error: {str(e)}")
        print("A critical error occurred. Please check the logs.")

if __name__ == "__main__":
    main()