-- Drop the existing function
DROP FUNCTION IF EXISTS calculate_tax;

DELIMITER $$

CREATE FUNCTION calculate_tax(annual_income DECIMAL(12,2)) 
RETURNS DECIMAL(10,2)
DETERMINISTIC
BEGIN
    DECLARE tax_amount DECIMAL(10,2) DEFAULT 0;
    DECLARE monthly_salary DECIMAL(10,2);
    DECLARE epf DECIMAL(10,2);
    DECLARE prof_tax DECIMAL(10,2);
    DECLARE total_deduction DECIMAL(10,2);
    
    -- Calculate monthly salary
    SET monthly_salary = annual_income / 12;
    
    -- Calculate EPF (12% of monthly salary)
    SET epf = monthly_salary * 0.12;
    
    -- Set Professional Tax (fixed amount)
    SET prof_tax = 200;
    
    -- Calculate income tax based on slabs
    -- No tax up to 3 lakh
    IF annual_income <= 300000 THEN
        SET tax_amount = 0;
    
    -- 5% from 3-6 lakh
    ELSEIF annual_income <= 600000 THEN
        SET tax_amount = (annual_income - 300000) * 0.05;
    
    -- 10% from 6-9 lakh
    ELSEIF annual_income <= 900000 THEN
        SET tax_amount = 15000 + (annual_income - 600000) * 0.10;
    
    -- 15% from 9-12 lakh
    ELSEIF annual_income <= 1200000 THEN
        SET tax_amount = 15000 + 30000 + (annual_income - 900000) * 0.15;
    
    -- 20% from 12-15 lakh
    ELSEIF annual_income <= 1500000 THEN
        SET tax_amount = 15000 + 30000 + 45000 + (annual_income - 1200000) * 0.20;
    
    -- 30% above 15 lakh
    ELSE
        SET tax_amount = 15000 + 30000 + 45000 + 60000 + (annual_income - 1500000) * 0.30;
    END IF;
    
    -- Add 4% health and education cess to income tax
    SET tax_amount = tax_amount * 1.04;
    
    -- Calculate monthly income tax
    SET tax_amount = ROUND(tax_amount / 12, 2);
    
    -- Combine all deductions for monthly total
    SET total_deduction = tax_amount + epf + prof_tax;
    
    -- Return total monthly deduction
    RETURN total_deduction;
END$$

DELIMITER ;