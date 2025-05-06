# inspect_db.py

from utils.db import test_connection, print_schema

def main():
    # 1) verify connection to the database
    test_connection()

    # 2) dump all tables and columns to the console
    print_schema()

if __name__ == "__main__":
    main()
