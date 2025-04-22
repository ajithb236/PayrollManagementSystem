DELIMITER $$

CREATE TRIGGER after_leave_approval
AFTER UPDATE ON payroll_leave
FOR EACH ROW
BEGIN
    DECLARE curr_date DATE;
    DECLARE end_date DATE;
    
    -- Check if the status was changed to 'Approved'
    IF NEW.status = 'Approved' AND OLD.status != 'Approved' THEN
        -- Initialize the date counter with start date
        SET curr_date = NEW.start_date;
        SET end_date = NEW.end_date;
        
        -- Loop through each day in the leave period
        WHILE curr_date <= end_date DO
            -- Check if an attendance record already exists
            IF EXISTS (SELECT 1 FROM payroll_attendance 
                      WHERE employee_id = NEW.employee_id AND date = curr_date) THEN
                -- Update existing attendance record
                UPDATE payroll_attendance 
                SET leave_status = NEW.leave_type, 
                    hours_worked = 0, 
                    overtime_hours = 0
                WHERE employee_id = NEW.employee_id AND date = curr_date;
            ELSE
                -- Create new attendance record
                INSERT INTO payroll_attendance 
                    (employee_id, date, hours_worked, overtime_hours, leave_status)
                VALUES 
                    (NEW.employee_id, curr_date, 0, 0, NEW.leave_type);
            END IF;
            
            -- Move to the next day
            SET curr_date = DATE_ADD(curr_date, INTERVAL 1 DAY);
        END WHILE;
    END IF;
END $$

DELIMITER ;