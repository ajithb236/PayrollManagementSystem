DELIMITER $$

CREATE TRIGGER after_employee_insert
AFTER INSERT ON payroll_employee
FOR EACH ROW
BEGIN
    DECLARE new_employee_id INT;
    DECLARE new_payroll_id INT;
    DECLARE role_id_var INT;
    DECLARE dept_id_var INT;
    DECLARE user_role VARCHAR(10);
    
    SET new_employee_id = NEW.employee_id;
    
    
    SELECT role INTO user_role 
    FROM accounts_customuser 
    WHERE id = NEW.user_id;
    
    INSERT INTO payroll_payroll (
        employee_id, 
        allowances
    ) VALUES (
        new_employee_id, 
        0
    );
    

    SELECT payroll_id INTO new_payroll_id 
    FROM payroll_payroll 
    WHERE employee_id = new_employee_id;
    

    INSERT INTO payroll_deduction (
        payroll_id,
        other_deductions,
        tax_amount
    ) VALUES (
        new_payroll_id,
        0,
        0
    );
    

    INSERT INTO payroll_bonus (
        payroll_id,
        bonus_amount
    ) VALUES (
        new_payroll_id,
        0
    );
    
  
    IF user_role = 'HR' THEN
       
        SELECT role_id INTO role_id_var 
        FROM payroll_role 
        WHERE role_name = 'HR' 
        LIMIT 1;
        
        IF role_id_var IS NULL THEN
            INSERT INTO payroll_role (role_name) 
            VALUES ('HR');
            
            SELECT LAST_INSERT_ID() INTO role_id_var;
        END IF;
        
        
        INSERT INTO payroll_employeerole (
            employee_id, 
            role_id
        ) VALUES (
            new_employee_id, 
            role_id_var
        );
        
    
        SELECT department_id INTO dept_id_var 
        FROM payroll_department 
        WHERE department_name = 'HR' 
        LIMIT 1;
        
        IF dept_id_var IS NULL THEN
            INSERT INTO payroll_department (department_name) 
            VALUES ('HR');
            
            SELECT LAST_INSERT_ID() INTO dept_id_var;
        END IF;
        
       
        UPDATE payroll_employee 
        SET department_id = dept_id_var 
        WHERE employee_id = new_employee_id;
    END IF;
END$$

DELIMITER ;