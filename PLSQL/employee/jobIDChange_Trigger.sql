DELIMITER $$
CREATE TRIGGER after_employee_job_update
AFTER UPDATE ON payroll_employee
FOR EACH ROW
BEGIN
    DECLARE base_salary DECIMAL(10,2);
    DECLARE allowance_amt DECIMAL(10,2);
    DECLARE payroll_id_var INT;
    
    -- Only proceed if job_id changed
    IF NEW.job_id != OLD.job_id OR (NEW.job_id IS NOT NULL AND OLD.job_id IS NULL) THEN
        -- Get the new salary from job
        SELECT jsr.salary_range INTO base_salary
        FROM payroll_jobsalaryrange jsr
        WHERE jsr.job_id = NEW.job_id;
        
        -- Get the payroll record and allowances
        SELECT p.payroll_id, p.allowances INTO payroll_id_var, allowance_amt
        FROM payroll_payroll p
        WHERE p.employee_id = NEW.employee_id;
        
        IF payroll_id_var IS NOT NULL THEN
            -- Update the tax amount based on new salary
            UPDATE payroll_deduction d
            SET tax_amount = calculate_tax((base_salary + allowance_amt) * 12)
            WHERE d.payroll_id = payroll_id_var;
        END IF;
    END IF;
END$$

DELIMITER ;