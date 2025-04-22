DELIMITER $$

CREATE TRIGGER after_salary_range_update
AFTER UPDATE ON payroll_jobsalaryrange
FOR EACH ROW
BEGIN
    -- Only proceed if salary range has changed
    IF NEW.salary_range != OLD.salary_range THEN
        -- Update tax deductions for all affected employees
        UPDATE payroll_deduction d
        JOIN payroll_payroll p ON d.payroll_id = p.payroll_id
        JOIN payroll_employee e ON p.employee_id = e.employee_id
        SET d.tax_amount = calculate_tax((NEW.salary_range + COALESCE(p.allowances, 0)) * 12)
        WHERE e.job_id = NEW.job_id;
    END IF;
END$$

DELIMITER ;