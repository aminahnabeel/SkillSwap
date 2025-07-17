"""
SQL Server to MySQL Query Converter Helper
This script helps identify and convert SQL Server specific queries to MySQL compatible ones.
"""

def convert_sql_server_to_mysql():
    """
    Guide for converting SQL Server queries to MySQL in your Flask application
    """
    
    conversions = {
        "Date Functions": {
            "GETDATE()": "NOW()",
            "DATEADD(day, 1, GETDATE())": "DATE_ADD(NOW(), INTERVAL 1 DAY)",
            "DATEADD(hour, 1, GETDATE())": "DATE_ADD(NOW(), INTERVAL 1 HOUR)",
            "DATEDIFF(day, date1, date2)": "DATEDIFF(date2, date1)",
        },
        
        "Identity/Auto-increment": {
            "SELECT @@IDENTITY": "SELECT LAST_INSERT_ID()",
            "SELECT SCOPE_IDENTITY()": "SELECT LAST_INSERT_ID()",
        },
        
        "Limiting Results": {
            "SELECT TOP 10 *": "SELECT * LIMIT 10",
            "SELECT TOP 1 *": "SELECT * LIMIT 1",
        },
        
        "String Functions": {
            "ISNULL(column, 'default')": "IFNULL(column, 'default')",
            "LEN(column)": "LENGTH(column)",
            "CHARINDEX('text', column)": "LOCATE('text', column)",
        },
        
        "Conditional Logic": {
            "CASE WHEN condition THEN value ELSE other END": "Same syntax in MySQL",
            "COALESCE(col1, col2, 'default')": "Same syntax in MySQL",
        },
        
        "Boolean Values": {
            "1 (TRUE)": "TRUE or 1",
            "0 (FALSE)": "FALSE or 0",
        }
    }
    
    return conversions

def find_sql_server_queries_in_app():
    """
    List of SQL Server specific queries found in your app.py that need conversion
    """
    
    queries_to_convert = [
        {
            "line": "Various locations",
            "original": "GETDATE()",
            "converted": "NOW()",
            "context": "Date insertion and updates"
        },
        {
            "line": "~885",
            "original": "SELECT @@IDENTITY AS ID",
            "converted": "SELECT LAST_INSERT_ID() AS ID",
            "context": "Getting last inserted message ID"
        },
        {
            "line": "Various locations",
            "original": "SELECT TOP 1",
            "converted": "SELECT ... LIMIT 1",
            "context": "Limiting query results"
        },
        {
            "line": "~597",
            "original": "ORDER BY CreatedDate DESC",
            "converted": "Same syntax - no change needed",
            "context": "Ordering results"
        }
    ]
    
    return queries_to_convert

def update_app_for_mysql():
    """
    Instructions for updating your app.py file for MySQL compatibility
    """
    
    instructions = """
    Manual Updates Required in app.py:
    
    1. Replace all instances of GETDATE() with NOW()
    2. Replace SELECT @@IDENTITY with SELECT LAST_INSERT_ID()
    3. Replace SELECT TOP n with SELECT ... LIMIT n
    4. Update any ISNULL functions to IFNULL
    5. Ensure all boolean values use TRUE/FALSE or 1/0
    
    Example changes:
    
    # Old SQL Server query:
    cursor.execute("INSERT INTO Users (...) VALUES (..., GETDATE())")
    cursor.execute("SELECT @@IDENTITY AS ID")
    
    # New MySQL query:
    cursor.execute("INSERT INTO Users (...) VALUES (..., NOW())")
    cursor.execute("SELECT LAST_INSERT_ID() AS ID")
    
    # Old SQL Server query:
    cursor.execute("SELECT TOP 1 * FROM Users ORDER BY UserID DESC")
    
    # New MySQL query:
    cursor.execute("SELECT * FROM Users ORDER BY UserID DESC LIMIT 1")
    """
    
    return instructions

if __name__ == "__main__":
    print("SQL Server to MySQL Conversion Guide")
    print("=" * 50)
    
    conversions = convert_sql_server_to_mysql()
    for category, items in conversions.items():
        print(f"\n{category}:")
        for old, new in items.items():
            print(f"  {old} → {new}")
    
    print("\n" + "=" * 50)
    print("Queries to Convert in Your App:")
    print("=" * 50)
    
    queries = find_sql_server_queries_in_app()
    for i, query in enumerate(queries, 1):
        print(f"{i}. Line {query['line']}")
        print(f"   Original: {query['original']}")
        print(f"   Convert to: {query['converted']}")
        print(f"   Context: {query['context']}")
        print()
    
    print(update_app_for_mysql())
