import os
import pymysql 
import django
from django.conf import settings
pymysql.install_as_MySQLdb() 
# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PayrollManagement.settings')
django.setup()

def connect_db():
    """Connect to the MySQL database using settings from Django."""
    return pymysql.connect(
        host=settings.DATABASES['default']['HOST'],
        user=settings.DATABASES['default']['USER'],
        passwd=settings.DATABASES['default']['PASSWORD'],
        db=settings.DATABASES['default']['NAME'],
    )

def execute_sql_file(cursor, file_path):
    """Execute SQL commands from file."""
    print(f"Executing SQL file: {file_path}")
    with open(file_path, 'r') as f:
        sql_content = f.read()
        # Split on DELIMITER to handle multi-statement triggers properly
        if "DELIMITER" in sql_content:
            parts = sql_content.split("DELIMITER")
            # Skip the first empty part
            for part in parts[1:]:
                if not part.strip():
                    continue
                
                # Extract delimiter and the SQL code
                lines = part.strip().split("\n")
                delimiter = lines[0].strip()
                sql_code = "\n".join(lines[1:])
                
                # Execute the SQL code with proper delimiter
                if "$$" in delimiter:
                    # For $$ delimiter sections, execute all at once
                    sql_statements = sql_code.split("$$")
                    for stmt in sql_statements:
                        if stmt.strip():
                            cursor.execute(stmt.strip())
                else:
                    # For other delimiter sections like ;
                    statements = sql_code.split(delimiter)
                    for stmt in statements:
                        if stmt.strip():
                            cursor.execute(stmt.strip())
        else:
            # If no DELIMITER keyword, execute as regular SQL
            for statement in sql_content.split(';'):
                if statement.strip():
                    cursor.execute(statement.strip() + ';')

def setup_triggers_and_functions(cursor):
    """Set up all triggers and functions from PLSQL directory."""
    # Define the order of SQL files to execute
    sql_files = [
        "PLSQL/employee/FunctionForTaxSlab.sql",  # Function should be created before triggers using it
        "PLSQL/registration/reg_trigger.sql",
        "PLSQL/employee/allowanceChangeTrig.sql",
        "PLSQL/employee/jobIDChange_Trigger.sql",
        "PLSQL/hr/JobSalaryRangeChangeTrig.sql",
        "PLSQL/hr/leaveApprovalTrigger.sql",
    ]
    
    for sql_file in sql_files:
        file_path = os.path.join(os.getcwd(), sql_file)
        if os.path.exists(file_path):
            try:
                execute_sql_file(cursor, file_path)
            except Exception as e:
                print(f"Error executing {sql_file}: {e}")
        else:
            print(f"Warning: SQL file not found: {file_path}")

def setup_departments(cursor):
    """Set up departments with NULL managers."""
    print("Setting up departments...")

    # Reset auto-increment
    cursor.execute("ALTER TABLE payroll_department AUTO_INCREMENT = 1;")
    
    # Insert departments with NULL managers
    departments = [
        "HR",
        "Engineering",
        "Sales",
        "Marketing",
        "Finance",
        "Operations"
    ]
    
    for dept in departments:
        cursor.execute(
            "INSERT INTO payroll_department (department_name, manager_id) VALUES (%s, NULL);",
            [dept]
        )

def setup_jobs_and_salary_ranges(cursor):
    """Set up jobs and salary ranges."""
    print("Setting up jobs and salary ranges...")
    # Drop existing data if any
    cursor.execute("DELETE FROM payroll_jobsalaryrange;")
    cursor.execute("DELETE FROM payroll_job;")
    
    # Reset auto-increment
    cursor.execute("ALTER TABLE payroll_job AUTO_INCREMENT = 1;")
    
    # Job titles and corresponding salary ranges
    jobs_and_salaries = [
        ("HR Manager", 70000.00),
        ("Software Engineer", 60000.00),
        ("Data Analyst", 100000.50),
        ("Sales Executive", 150000.00),
        ("Marketing Specialist", 52000.00),
        ("Financial Analyst", 58000.00),
        ("Operations Manager", 65000.00)
    ]
    
    for job_title, salary_range in jobs_and_salaries:
        # Insert job
        cursor.execute(
            "INSERT INTO payroll_job (job_title) VALUES (%s);",
            [job_title]
        )
        job_id = cursor.lastrowid
        
        # Insert salary range for the job
        cursor.execute(
            "INSERT INTO payroll_jobsalaryrange (job_id, salary_range) VALUES (%s, %s);",
            [job_id, salary_range]
        )

def main():
    """Main setup function."""
    print("Starting database setup...")
    try:
        connection = connect_db()
        cursor = connection.cursor()
        
        # Create triggers and functions
        setup_triggers_and_functions(cursor)
        
        # Set up departments and jobs
        setup_departments(cursor)
        setup_jobs_and_salary_ranges(cursor)
        
        # Commit all changes
        connection.commit()
        print("Database setup completed successfully!")
        
    except Exception as e:
        print(f"Error setting up database: {e}")
        
    finally:
        if connection:
            connection.close()

if __name__ == "__main__":
    print("running setup_database.py")
    print("This script sets up the database for the Payroll Management System.")
    ch=input("RUN IT ONLY ONCE AFTER MIGRATION.ARE YOU SURE?(Y/N)")
    if ch.lower() == 'y':
        print("Running setup_database.py...")
        main()
    else:
        print("Exiting without running setup_database.py.")
        exit(0)
    