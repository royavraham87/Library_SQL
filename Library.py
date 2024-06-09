from enum import Enum
import sqlite3
from datetime import datetime, timedelta

# Connect to SQLite database
conn = sqlite3.connect('library.db')
cursor = conn.cursor()

# Create tables
cursor.execute('''CREATE TABLE IF NOT EXISTS Books (
                    ID INTEGER PRIMARY KEY,
                    Name TEXT,
                    Author TEXT,
                    YearPublished INTEGER,
                    LoanType INTEGER,
                    Status TEXT)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS Customers (
                    ID INTEGER PRIMARY KEY,
                    Name TEXT,
                    City TEXT,
                    Age INTEGER)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS Loans (
                    CustID INTEGER,
                    BookID INTEGER,
                    LoanDate TEXT,
                    ReturnDate TEXT,
                    FOREIGN KEY(CustID) REFERENCES Customers(ID),
                    FOREIGN KEY(BookID) REFERENCES Books(ID))''')

cursor.execute('''CREATE TABLE IF NOT EXISTS LateLoans (
                    CustID INTEGER,
                    CustName TEXT,
                    BookName TEXT,
                    ExpectedReturnDate TEXT,
                    ActualReturnDate TEXT,
                    FOREIGN KEY(CustID) REFERENCES Customers(ID))''')

conn.commit()

class AdminActions(Enum):
    ADD_CUSTOMER = 1
    ADD_BOOK = 2
    DISPLAY_ALL_BOOKS = 3
    DISPLAY_ALL_CUSTOMERS = 4
    DISPLAY_ALL_LOANS = 5
    DISPLAY_LATE_LOANS = 6
    FIND_BOOK_BY_NAME = 7
    FIND_CUSTOMER_BY_NAME = 8
    REMOVE_BOOK = 9
    REMOVE_CUSTOMER = 10

class CustomerActions(Enum):
    LOAN_BOOK = 1
    RETURN_BOOK = 2
    DISPLAY_ALL_BOOKS = 3
    FIND_BOOK_BY_NAME = 4

def add_customer(name, city, age):
    cursor.execute('''INSERT INTO Customers (Name, City, Age) VALUES (?, ?, ?)''', (name, city, age))
    conn.commit()
    print("Customer added successfully.")

def add_book(name, author, year_published, loan_type):
    cursor.execute('''INSERT INTO Books (Name, Author, YearPublished, LoanType, Status) VALUES (?, ?, ?, ?, ?)''', 
                   (name, author, year_published, loan_type, 'available'))
    conn.commit()
    print("Book added successfully.")

def display_all_books():
    cursor.execute('''SELECT * FROM Books''')
    books = cursor.fetchall()
    if books:
        for row in books:
            print(row)
    else:
        print("No books found.")

def display_all_customers():
    cursor.execute('''SELECT * FROM Customers''')
    customers = cursor.fetchall()
    if customers:
        for row in customers:
            print(row)
    else:
        print("No customers found.")

def display_all_loans():
    cursor.execute('''SELECT Loans.CustID, Customers.Name, Loans.BookID, Books.Name, Loans.LoanDate, Loans.ReturnDate, Books.LoanType
                      FROM Loans
                      JOIN Customers ON Loans.CustID = Customers.ID
                      JOIN Books ON Loans.BookID = Books.ID''')
    loans = cursor.fetchall()
    if loans:
        for loan in loans:
            loan_type_str = {1: '2 days', 2: '5 days', 3: '10 days', 4: '5 minutes'}.get(loan[6], 'Unknown')
            print(f"Customer: {loan[1]}, Book: {loan[3]}, Loan Date: {loan[4]}, Loan Type: {loan_type_str}, Return Date: {loan[5]}")
    else:
        print("No loans found.")

def display_late_loans():
    cursor.execute('''SELECT * FROM LateLoans''')
    late_loans = cursor.fetchall()
    if late_loans:
        for row in late_loans:
            print(row)
    else:
        print("No late loans found.")

def find_book_by_name(name):
    cursor.execute('''SELECT * FROM Books WHERE Name LIKE ?''', ('%' + name + '%',))
    books = cursor.fetchall()
    if books:
        for row in books:
            print(row)
    else:
        print("No books found with that name.")

def find_customer_by_name(name):
    cursor.execute('''SELECT * FROM Customers WHERE Name LIKE ?''', ('%' + name + '%',))
    customers = cursor.fetchall()
    if customers:
        for row in customers:
            print(row)
    else:
        print("No customers found with that name.")

def remove_book(book_id):
    cursor.execute('''SELECT Status, Name FROM Books WHERE ID = ?''', (book_id,))
    book_info = cursor.fetchone()
    if not book_info:
        print("Error: Book not found.")
        return
    if book_info[0] == 'loaned':
        print("Error: Book is currently loaned out and cannot be removed.")
        return
    book_name = book_info[1]
    confirm = input(f"Are you sure you want to delete the book '{book_name}'? (y/n): ").lower()
    if confirm == 'y':
        cursor.execute('''DELETE FROM Books WHERE ID = ?''', (book_id,))
        conn.commit()
        print("Book removed successfully.")
    else:
        print("Book deletion cancelled.")

def remove_customer(customer_id):
    cursor.execute('''SELECT Name FROM Customers WHERE ID = ?''', (customer_id,))
    customer_info = cursor.fetchone()
    if not customer_info:
        print("Error: Customer not found.")
        return

    customer_name = customer_info[0]

    cursor.execute('''SELECT * FROM Loans WHERE CustID = ?''', (customer_id,))
    if cursor.fetchone():
        print("Error: Customer is currently loaning a book and cannot be removed.")
        return

    confirm = input(f"Are you sure you want to delete the customer '{customer_name}'? (y/n): ").lower()
    if confirm == 'y':
        cursor.execute('''DELETE FROM Customers WHERE ID = ?''', (customer_id,))
        conn.commit()
        print("Customer removed successfully.")
    else:
        print("Customer deletion cancelled.")

def loan_book(cust_id, book_id):
    cursor.execute('''SELECT Status, LoanType, Name FROM Books WHERE ID = ?''', (book_id,))
    book_info = cursor.fetchone()
    if not book_info:
        print("Error: Book not found.")
        return
    if book_info[0] == 'loaned':
        print("Error: Book is already loaned.")
        return
    loan_type = book_info[1]
    book_name = book_info[2]
    today = datetime.today().date()
    return_date = today + timedelta(days=2 if loan_type == 1 else 5 if loan_type == 2 else 10 if loan_type == 3 else 0)
    if loan_type == 4:  # 5 minutes
        return_date = (datetime.now() + timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')
    else:
        return_date = (today + timedelta(days=2 if loan_type == 1 else 5 if loan_type == 2 else 10)).strftime('%Y-%m-%d')
    cursor.execute('''INSERT INTO Loans (CustID, BookID, LoanDate, ReturnDate) VALUES (?, ?, ?, ?)''', 
                   (cust_id, book_id, today.strftime('%Y-%m-%d'), return_date))
    cursor.execute('''UPDATE Books SET Status = 'loaned' WHERE ID = ?''', (book_id,))
    conn.commit()
    print(f"Book '{book_name}' should be returned by {return_date}.")

def return_book(cust_id, book_id):
    cursor.execute('''SELECT ReturnDate, BookID FROM Loans WHERE CustID = ? AND BookID = ?''', (cust_id, book_id))
    loan_info = cursor.fetchone()
    if not loan_info:
        print("Error: Loan not found.")
        return

    return_date = loan_info[0]
    today = datetime.today()

    cursor.execute('''DELETE FROM Loans WHERE CustID = ? AND BookID = ?''', (cust_id, book_id))
    cursor.execute('''UPDATE Books SET Status = 'available' WHERE ID = ?''', (book_id,))
    conn.commit()

    if today <= datetime.strptime(return_date, '%Y-%m-%d %H:%M:%S' if ' ' in return_date else '%Y-%m-%d'):
        print(f"The book was returned on time.")
    else:
        cursor.execute('''SELECT Name FROM Customers WHERE ID = ?''', (cust_id,))
        customer_name = cursor.fetchone()[0]
        cursor.execute('''SELECT Name FROM Books WHERE ID = ?''', (book_id,))
        book_name = cursor.fetchone()[0]
        cursor.execute('''INSERT INTO LateLoans (CustID, CustName, BookName, ExpectedReturnDate, ActualReturnDate)
                          VALUES (?, ?, ?, ?, ?)''', (cust_id, customer_name, book_name, return_date, today.strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        print(f"The book '{book_name}' was returned late.")

def admin_menu():
    while True:
        for action in AdminActions:
            print(f"{action.value}. {action.name.replace('_', ' ').title()}")
        choice = int(input("Choose an action (or type 0 to go back): "))
        if choice == 0:
            break
        elif choice == AdminActions.ADD_CUSTOMER.value:
            name = input("Enter customer name: ")
            city = input("Enter customer city: ")
            age = int(input("Enter customer age: "))
            add_customer(name, city, age)
        elif choice == AdminActions.ADD_BOOK.value:
            name = input("Enter book name: ")
            author = input("Enter author name: ")
            year_published = int(input("Enter year published: "))
            loan_type = int(input("Enter loan type (1 for 2 days, 2 for 5 days, 3 for 10 days, 4 for 5 minutes): "))
            add_book(name, author, year_published, loan_type)
        elif choice == AdminActions.DISPLAY_ALL_BOOKS.value:
            display_all_books()
        elif choice == AdminActions.DISPLAY_ALL_CUSTOMERS.value:
            display_all_customers()
        elif choice == AdminActions.DISPLAY_ALL_LOANS.value:
            display_all_loans()
        elif choice == AdminActions.DISPLAY_LATE_LOANS.value:
            display_late_loans()
        elif choice == AdminActions.FIND_BOOK_BY_NAME.value:
            name = input("Enter book name: ")
            find_book_by_name(name)
        elif choice == AdminActions.FIND_CUSTOMER_BY_NAME.value:
            name = input("Enter customer name: ")
            find_customer_by_name(name)
        elif choice == AdminActions.REMOVE_BOOK.value:
            display_all_books()
            book_id = int(input("Enter book ID: "))
            cursor.execute('''SELECT ID FROM Books WHERE ID = ?''', (book_id,))
            if cursor.fetchone():
                remove_book(book_id)
            else:
                print("Error: Invalid book ID.")
        elif choice == AdminActions.REMOVE_CUSTOMER.value:
            display_all_customers()
            customer_id = int(input("Enter customer ID: "))
            cursor.execute('''SELECT ID FROM Customers WHERE ID = ?''', (customer_id,))
            if cursor.fetchone():
                remove_customer(customer_id)
            else:
                print("Error: Invalid customer ID.")
        else:
            print("Invalid choice. Please try again.")

def customer_menu():
    cursor.execute('''SELECT * FROM Customers''')
    customers = cursor.fetchall()
    if customers:
        for row in customers:
            print(row)
        cust_id = int(input("Enter your customer ID: "))
        cursor.execute('''SELECT Name FROM Customers WHERE ID = ?''', (cust_id,))
        customer_name = cursor.fetchone()
        if customer_name:
            print(f"Welcome Mr. {customer_name[0]}")
            while True:
                for action in CustomerActions:
                    print(f"{action.value}. {action.name.replace('_', ' ').title()}")
                choice = int(input("Choose an action (or type 0 to go back): "))
                if choice == 0:
                    break
                elif choice == CustomerActions.LOAN_BOOK.value:
                    display_all_books()
                    book_id = int(input("Enter the ID of the book you want to borrow: "))
                    loan_book(cust_id, book_id)
                elif choice == CustomerActions.RETURN_BOOK.value:
                    cursor.execute('''SELECT Books.ID, Books.Name 
                                      FROM Books 
                                      JOIN Loans ON Books.ID = Loans.BookID 
                                      WHERE Loans.CustID = ?''', (cust_id,))
                    borrowed_books = cursor.fetchall()
                    if borrowed_books:
                        for row in borrowed_books:
                            print(row)
                        book_id = int(input("Enter the ID of the book you want to return: "))
                        return_book(cust_id, book_id)
                    else:
                        print("You have no borrowed books.")
                elif choice == CustomerActions.DISPLAY_ALL_BOOKS.value:
                    display_all_books()
                elif choice == CustomerActions.FIND_BOOK_BY_NAME.value:
                    name = input("Enter book name: ")
                    find_book_by_name(name)
                else:
                    print("Invalid choice. Please try again.")
        else:
            print("Invalid customer ID.")
    else:
        print("No customers found.")

def main():
    while True:
        user_type = input("Choose 1-Admin, 2-Customer, or type 'exit' to exit: ").lower()
        if user_type == 'exit':
            break
        elif user_type == '1':
            admin_menu()
        elif user_type == '2':
            customer_menu()
        else:
            print("Invalid choice. Please enter '1', '2', or 'exit'.")

if __name__ == "__main__":
    main()

# Close the database connection when the program is done
conn.close()
