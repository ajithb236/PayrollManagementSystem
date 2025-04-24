1. Query 1
Description: Insert a new employee record into the payroll_employee table

INSERT INTO payroll_Employee (user_id, name, contact, email, date_joined) 
VALUES (%s, %s, %s, %s, %s)

2. Query 2
Description: Update the last login timestamp for a user in the accounts_customuser table

UPDATE accounts_customuser 
SET last_login = NOW() 
WHERE id = %s

3. Query 3
Description: Fetch employee details along with job and department information

SELECT e.employee_id, e.name, e.email, e.contact, e.address, e.gender, e.date_of_birth, 
       j.job_title, d.department_name
FROM payroll_employee e
LEFT JOIN payroll_job j ON e.job_id = j.job_id
LEFT JOIN payroll_department d ON e.department_id = d.department_id
WHERE e.user_id = %s

4. Query 4
Description: Check if attendance for a specific employee on a specific date exists.

SELECT attendance_id 
FROM payroll_attendance
WHERE employee_id = %s AND date = %s

5. Query 5
Description: Insert a new attendance record for an employee

INSERT INTO payroll_attendance (employee_id, date, hours_worked, overtime_hours, leave_status)
VALUES (%s, %s, 8, 0, 'Present')

6. Query 6
Description: Update an employee's profile details such as address, gender, and date of birth.

UPDATE payroll_employee
SET address = %s, gender = %s, date_of_birth = %s
WHERE user_id = %s

7. Query 7
Description: Fetch attendance details for an employee

SELECT a.date, a.hours_worked, a.overtime_hours, a.leave_status
FROM payroll_attendance a
INNER JOIN payroll_employee e ON a.employee_id = e.employee_id
WHERE e.user_id = %s
ORDER BY a.date DESC

8. Query 8
Description: Fetch the employee ID for a specific user.
SELECT employee_id 
FROM payroll_employee 
WHERE user_id = %s

9. Query 9
Description: Update overtime hours for a specific employee on a specific date.

UPDATE payroll_attendance
SET overtime_hours = %s
WHERE employee_id = %s AND date = %s

