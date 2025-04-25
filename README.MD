# PayrollManagement System

A comprehensive web-based payroll management solution built with Django, designed to streamline employee compensation, attendance tracking, leave management, and financial reporting for organizations.

## 📋 Features

### Multi-User Role System
- **Employee Portal**: Self-service dashboard for personal payroll information
- **HR Portal**: Comprehensive management of all payroll and employee data
- **Authentication**: Secure login using Django's authentication system with custom user model
- **Implementation**: Role-based access control with dedicated views for each user type

### Employee Management
- Complete employee profile management with personal and professional details
- Department and job role assignment system
- Manager designation within organizational structure
- **Implementation**: SQL triggers initialize employee records with default values upon creation

### Payroll Processing
- **Automated Salary Calculation**:
  - Base salary management based on job roles
  - Configurable allowances (HRA: 40% of base, DA: 10% of base, TA: fixed ₹3200)
  - Overtime compensation (hourly rate = base salary/160 × 2)
  - Bonus processing with manual adjustments
  - **Implementation**: Database triggers update allowances and taxes automatically

- **Deduction Management**:
  - Progressive tax calculations using `calculate_tax()` MySQL function
  - EPF (Employee Provident Fund) at 12% of base salary
  - Professional tax (fixed at ₹200)
  - Other customizable deductions

### Attendance & Leave Management
- **Attendance Tracking**:
  - Daily work hours recording
  - Overtime logging and approval workflow
  - **Implementation**: Overtime hours automatically affect salary calculations

- **Leave Management**:
  - Multiple leave types (Vacation, Sick, Others)
  - Leave request submission and approval workflow
  - Leave balance tracking
  - **Implementation**: `after_leave_approval` trigger updates attendance records

### Financial Processing
- Salary disbursement with multiple payment modes
- Transaction tracking with unique reference numbers
- Bank account integration for payroll processing
- **Implementation**: `generate_bank_account()` function creates unique transaction IDs

### Comprehensive Reporting
- **Payroll Reports**: Detailed salary breakdowns by department
- **Attendance Reports**: Work hours and overtime analytics
- **Leave Reports**: Leave utilization and balance statistics
- **Tax Reports**: Tax deduction summaries by employee and department
- Export options in multiple formats (PDF, Excel, CSV)

### HR Analytics Dashboard
- Department headcount visualization
- Salary distribution metrics with min/max/average analysis
- Financial breakdown with interactive charts
- Recent joiners tracking

## 🛠️ Technology Stack

- **Backend**:
  - Django 5.1 (Python web framework)
  - Custom middleware for role-based security

- **Database**:
  - MySQL 8.0 with custom PL/SQL functions and triggers
  - Complex data relationships with foreign key constraints

- **Frontend**:
  - HTML/CSS with chart.js for data visualisation.

- **Additional Libraries**:
  - django-widget-tweaks: Enhanced form rendering
  - django-extensions: Development tools
  - pymysql: MySQL database connector
  - reportlab: PDF generation

## 📁 File Structure

```
PayrollManagement/
├── PayrollManagement/           # Project settings
│   ├── settings.py              # Django settings
│   ├── urls.py                  # Main URL routing
│   └── wsgi.py                  # WSGI configuration
├── accounts/                    # User authentication
│   ├── models.py                # CustomUser model
│   ├── views.py                 # Login/logout views
│   └── templates/               # Authentication templates
├── employee/                    # Employee module
│   ├── views.py                 # Employee views
│   ├── urls.py                  # Employee URL patterns
│   └── templates/               # Employee templates
│       ├── dashboard.html       # Employee dashboard
│       ├── profile.html         # Profile management
│       ├── salary.html          # Salary details view
│       ├── transaction_history.html  # Payment history
│       ├── request_leave.html   # Leave request form
│       ├── leave_balance.html   # Leave balance tracking
│       ├── attendance_details.html  # Attendance records
│       └── clock_overtime.html  # Overtime logging
├── hr/                          # HR module
│   ├── views.py                 # HR functionality
│   ├── urls.py                  # HR URL patterns
│   └── templates/               # HR templates
│       ├── dashboard.html       # HR dashboard
│       ├── assign_employee.html # Role assignment
│       ├── update_payscales.html # Salary management
│       ├── manage_employee.html # Employee management
│       ├── approve_leaves.html  # Leave approval
│       ├── salary_disbursement.html # Process payments
│       ├── payment_history.html # Payment records
│       ├── generate_reports.html # Report generation
│       ├── metrics_dashboard.html # HR analytics
│       ├── attendance_details.html # Track attendance
│       └── profile.html         # HR profile
├── payroll/                     # Core payroll models
│   ├── models.py                # Database models
│   └── migrations/              # Database migrations
├── templates/                   # Global templates
│   └── base.html                # Base template
├── PLSQL/                       # Database triggers and functions
│   ├── registration/            # User registration triggers
│   ├── employee/                # Employee-related triggers
│   │   ├── FunctionForTaxSlab.sql  # Tax calculation
│   │   ├── allowanceChangeTrig.sql # Allowance updates
│   │   └── jobIDChange_Trigger.sql # Job change triggers
│   └── hr/                      # HR-related triggers
│       ├── JobSalaryRangeChangeTrig.sql # Salary updates
│       └── leaveApprovalTrigger.sql     # Leave approval
├── setup_database.py            # Database initialization script
├── config.env                   # Environment configuration (not in version control)
├── manage.py                    # Django command-line utility
└── requirements.txt             # Python dependencies
```

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8+
- MySQL 8.0+
- pip (Python package manager)

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/PayrollManagement.git
   cd PayrollManagement
   ```

2. **Set up a virtual environment**
   ```bash
   python -m venv env
   source env/bin/activate  # On Windows: env\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create a config.env file with your environment variables**
   Create a file named config.env in the project root with the following contents:
   ```
   # Django Settings
   SECRET_KEY=your-generated-secret-key
   DEBUG=True

   # Database Settings
   DB_ENGINE=django.db.backends.mysql
   DB_NAME=payroll_db
   DB_USER=your_username
   DB_PASSWORD=your_password
   DB_HOST=localhost
   DB_PORT=3306
   ```

   To generate a new SECRET_KEY, run the following command in your Python shell:
   ```python
   from django.core.management.utils import get_random_secret_key
   print(get_random_secret_key())
   ```

5. **Update settings.py to use environment variables**
   Ensure your settings.py uses the python-decouple package to read from config.env:
   ```python
   from decouple import config
   
   SECRET_KEY = config('SECRET_KEY')
   DEBUG = config('DEBUG', default=False, cast=bool)
   
   DATABASES = {
       'default': {
           'ENGINE': config('DB_ENGINE'),
           'NAME': config('DB_NAME'),
           'USER': config('DB_USER'),
           'PASSWORD': config('DB_PASSWORD'),
           'HOST': config('DB_HOST'),
           'PORT': config('DB_PORT'),
       }
   }
   ```

6. **Run database migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

7. **Initialize database with triggers and initial data**
   ```bash
   python setup_database.py
   ```

8. **Create a superuser**
   ```bash
   python manage.py createsuperuser
   ```

9. **Start the development server**
   ```bash
   python manage.py runserver
   ```

## 👥 User Roles and Access

### Employee
- View personal salary details with complete breakdown
- Clock overtime hours
- Submit and track leave requests
- Monitor attendance records
- View transaction history with payment details

### HR
- Manage employees (add, update, assign roles and departments)
- Update pay scales for job positions
- Process salary disbursements
- Approve or reject leave requests
- Generate various reports (payroll, attendance, leave, tax)
- Access analytics dashboard with financial metrics

## 🗄️ Database Structure

The system employs a relational database with interconnected tables:

### Core Tables
- **Employee**: Personal and professional details
- **Department**: Organizational structure
- **Job & JobSalaryRange**: Positions and compensation

### Financial Tables
- **Payroll**: Core table linking employees to compensation
- **Bonus & Deduction**: Additional payments and withholdings
- **Payment & PaymentDetail**: Transaction records

### Time Management
- **Attendance**: Daily work hours and overtime
- **Leave**: Request status and history

### Technical Implementation
- **Triggers**: Automate calculations and maintain data consistency
- **Functions**: Handle complex logic like tax calculations
- **Foreign Keys**: Enforce data integrity between tables

---
