### **Testing and Documentation Plan**

---

#### **Unit Testing**

Unit testing ensures that individual components of your Finance Dashboard work as expected. Here's how you can write tests for key functionalities:

---



##### **Setup**
Create a file named `test_finance_dashboard.py` and include unit tests for key functions such as `add_transaction`, `set_budget`, `check_budget`, etc.

---

##### **Example Unit Tests**

```python
import unittest
import sqlite3
from finance_dashboard import add_transaction, set_budget, check_budget

class TestFinanceDashboard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Setup test database
        cls.conn = sqlite3.connect(":memory:")
        cls.cursor = cls.conn.cursor()
        # Create tables
        cls.cursor.execute('''
            CREATE TABLE transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                category TEXT,
                amount REAL,
                type TEXT,
                timestamp TEXT
            )
        ''')
        cls.cursor.execute('''
            CREATE TABLE budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                category TEXT,
                amount REAL
            )
        ''')

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def test_add_transaction(self):
        # Add a test transaction
        user_id = 1
        add_transaction(user_id, "Food", 500, "Expense", self.cursor, self.conn)
        self.cursor.execute("SELECT * FROM transactions WHERE user_id = ?", (user_id,))
        transactions = self.cursor.fetchall()
        self.assertEqual(len(transactions), 1)
        self.assertEqual(transactions[0][2], "Food")

    def test_set_budget(self):
        # Set a test budget
        user_id = 1
        set_budget(user_id, "Rent", 4000, self.cursor, self.conn)
        self.cursor.execute("SELECT * FROM budgets WHERE user_id = ?", (user_id,))
        budgets = self.cursor.fetchall()
        self.assertEqual(len(budgets), 1)
        self.assertEqual(budgets[0][2], "Rent")
        self.assertEqual(budgets[0][3], 4000)

    def test_check_budget(self):
        # Set a budget and add transactions to test check_budget
        user_id = 1
        set_budget(user_id, "Groceries", 3000, self.cursor, self.conn)
        add_transaction(user_id, "Groceries", 1500, "Expense", self.cursor, self.conn)
        add_transaction(user_id, "Groceries", 2000, "Expense", self.cursor, self.conn)

        # Call check_budget and validate
        result = check_budget(user_id, self.cursor)
        self.assertIn("⚠️ Budget exceeded for Groceries", result)

if __name__ == "__main__":
    unittest.main()
```

---

##### **Run Tests**

```bash
python -m unittest test_finance_dashboard.py
```



### **Finance Dashboard User Manual**

#### **1. Overview**  
The Finance Dashboard is a command-line Python application that allows users to manage their finances effectively. Key features include adding transactions, setting and checking budgets, and generating reports.

---

#### **2. Installation**

**Requirements**:
- Python 3.7+
- SQLite (built-in with Python)
- Required libraries: `sqlite3`

**Steps**:
1. Clone the repository:
   ```bash
   git clone https://github.com/keyurbhatiya/Finance-Management-Application-command-line.git
   cd 
   ```
2. Install dependencies:
   No external dependencies are required. Python's built-in `sqlite3` is used.

3. Run the application:
   ```bash
   python main.py
   ```

---

#### **3. Usage**

##### **3.1 Launching the Application**
- Run the application using:
  ```bash
  python main.py
  ```
- You will see the main dashboard with menu options.

##### **3.2 Key Features**

- **Add Transaction**:  
  Select option `1`. Enter details for the transaction, including category, amount, and type (`Income` or `Expense`).

- **Set Budget**:  
  Select option `5`. Specify the category and the budget amount. Budgets are saved for tracking expenses.

- **Check Budget**:  
  Select option `6`. View a comparison of your expenses and budgets. Alerts are shown for exceeded budgets.

- **Generate Reports**:  
  Select option `7`. A summary of all transactions and budget statuses is displayed.

- **Logout**:  
  Select option `8` to exit the application.

---

#### **4. Troubleshooting**

- **Error: "Invalid Choice"**  
  Ensure you select a valid menu option (1-8).

- **Database Issues**  
  If the application fails to fetch or save data, ensure the `finance_app.db` file exists and has the correct schema. Reinitialize the database if needed.

- **Budget Not Updating**  
  Verify that the `set_budget` and `check_budget` functions are working correctly. Check the database tables for accuracy.

---

#### **5. Additional Information**

**Database Schema**:

1. **Transactions Table**:
   | Column Name | Type    | Description                   |
   |-------------|---------|-------------------------------|
   | id          | INTEGER | Auto-increment primary key    |
   | user_id     | INTEGER | User ID                      |
   | category    | TEXT    | Category of transaction       |
   | amount      | REAL    | Transaction amount            |
   | type        | TEXT    | 'Income' or 'Expense'         |
   | timestamp   | TEXT    | Date and time of transaction  |

2. **Budgets Table**:
   | Column Name | Type    | Description                   |
   |-------------|---------|-------------------------------|
   | id          | INTEGER | Auto-increment primary key    |
   | user_id     | INTEGER | User ID                      |
   | category    | TEXT    | Budget category               |
   | amount      | REAL    | Budget amount                 |

---
