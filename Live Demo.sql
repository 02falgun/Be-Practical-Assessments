USE enterprise_retail_db;

-- -----------------------------------------------------------------------------
-- DEMO 1: Second-Highest Salary per Department (Using DENSE_RANK)
-- -----------------------------------------------------------------------------
WITH DepartmentSalaryRanks AS (
    SELECT 
        e.employee_id,
        CONCAT(e.first_name, ' ', e.last_name) AS employee_name,
        d.department_name,
        e.salary,
        DENSE_RANK() OVER (
            PARTITION BY e.department_id 
            ORDER BY e.salary DESC
        ) AS salary_rank
    FROM employees e
    JOIN departments d ON e.department_id = d.department_id
)
SELECT 
    department_name,
    employee_name,
    salary AS second_highest_salary
FROM DepartmentSalaryRanks
WHERE salary_rank = 2;


-- -----------------------------------------------------------------------------
-- DEMO 2: Top 3 Products per Category by Net Revenue
-- -----------------------------------------------------------------------------
WITH ProductRevenueByCategory AS (
    SELECT 
        c.category_name,
        p.product_name,
        ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount_pct)), 2) AS total_net_revenue,
        DENSE_RANK() OVER (
            PARTITION BY c.category_id 
            ORDER BY SUM(oi.quantity * oi.unit_price * (1 - oi.discount_pct)) DESC
        ) AS revenue_rank
    FROM categories c
    JOIN products p ON c.category_id = p.category_id
    JOIN order_items oi ON p.product_id = oi.product_id
    JOIN orders o ON oi.order_id = o.order_id
    WHERE o.order_status = 'Completed'
    GROUP BY c.category_id, c.category_name, p.product_id, p.product_name
)
SELECT 
    category_name,
    revenue_rank,
    product_name,
    total_net_revenue
FROM ProductRevenueByCategory
WHERE revenue_rank <= 3
ORDER BY category_name ASC, revenue_rank ASC;