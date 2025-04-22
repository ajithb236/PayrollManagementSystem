DELIMITER $$

CREATE TRIGGER after_payroll_update
AFTER UPDATE ON payroll_payroll
FOR EACH ROW
BEGIN
    DECLARE base_salary DECIMAL(10,2);
    
    -- Only proceed if allowances changed
    IF NEW.allowances != OLD.allowances THEN
        -- Get the base salary
        SELECT jsr.salary_range INTO base_salary
        FROM payroll_employee e
        JOIN payroll_jobsalaryrange jsr ON jsr.job_id = e.job_id
        WHERE e.employee_id = NEW.employee_id;
        
        -- Update the tax amount
        UPDATE payroll_deduction
        SET tax_amount = calculate_tax_amount((base_salary + NEW.allowances) * 12)
        WHERE payroll_id = NEW.payroll_id;
    END IF;
END$$

DELIMITER ;