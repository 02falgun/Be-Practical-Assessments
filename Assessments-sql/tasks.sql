-- =============================================================================
-- ENTERPRISE RETAIL ANALYTICS: 20 ADVANCED SQL TASKS & SOLUTIONS
-- DATABASE: enterprise_retail_db
-- =============================================================================

USE enterprise_retail_db;

-- =============================================================================
-- PART A: JOINS, ADVANCED FILTERING & SUBQUERIES (Q1 - Q5)
-- =============================================================================

-- [TASK Q1]
-- Task: Find all customers from 'USA' who placed completed orders in Q1 2024 (Jan–Mar).
--       Return customer_name, order_id, order_date, and order net revenue.
-- SOLUTION:
SELECT 
    c.customer_name,
    o.order_id,
    o.order_date,
    ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount_pct)), 2) AS net_revenue
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
JOIN order_items oi ON o.order_id = oi.order_id
WHERE c.country = 'USA'
  AND o.order_status = 'Completed'
  AND o.order_date BETWEEN '2024-01-01' AND '2024-03-31'
GROUP BY c.customer_name, o.order_id, o.order_date
ORDER BY o.order_date ASC;


-- [TASK Q2]
-- Task: Identify all sales reps (department_id = 2) who have NEVER closed an order.
--       Use an Anti-Join pattern (LEFT JOIN + IS NULL or NOT EXISTS).
-- SOLUTION:
SELECT 
    e.employee_id,
    CONCAT(e.first_name, ' ', e.last_name) AS sales_rep_name,
    e.email
FROM employees e
LEFT JOIN orders o ON e.employee_id = o.sales_rep_id
WHERE e.department_id = 2
  AND o.order_id IS NULL;


-- [TASK Q3]
-- Task: List all products that have never been ordered in the entire history of the company.
-- SOLUTION:
SELECT 
    p.product_id,
    p.product_name,
    p.category_id,
    p.unit_price
FROM products p
LEFT JOIN order_items oi ON p.product_id = oi.product_id
WHERE oi.order_item_id IS NULL;


-- [TASK Q4]
-- Task: Find all employees whose salary is strictly higher than the average salary of their department.
--       Display employee name, department name, salary, and the department average salary.
-- SOLUTION:
SELECT 
    CONCAT(e.first_name, ' ', e.last_name) AS employee_name,
    d.department_name,
    e.salary,
    ROUND(dept_avg.avg_salary, 2) AS dept_avg_salary
FROM employees e
JOIN departments d ON e.department_id = d.department_id
JOIN (
    SELECT 
        department_id, 
        AVG(salary) AS avg_salary
    FROM employees
    GROUP BY department_id
) dept_avg ON e.department_id = dept_avg.department_id
WHERE e.salary > dept_avg.avg_salary
ORDER BY d.department_name ASC, e.salary DESC;


-- [TASK Q5]
-- Task: Find all customer segments where the total net revenue exceeds $30,000 across completed orders.
--       Display segment, total orders count, and net revenue sorted descending.
-- SOLUTION:
SELECT 
    c.segment,
    COUNT(DISTINCT o.order_id) AS total_orders_count,
    ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount_pct)), 2) AS total_net_revenue
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.order_status = 'Completed'
GROUP BY c.segment
HAVING SUM(oi.quantity * oi.unit_price * (1 - oi.discount_pct)) > 30000.00
ORDER BY total_net_revenue DESC;


-- =============================================================================
-- PART B: COMMON TABLE EXPRESSIONS (CTEs) & COMPLEX LOGIC (Q6 - Q8)
-- =============================================================================

-- [TASK Q6]
-- Task: Using a CTE, calculate the Total Spend per customer. In the main query,
--       classify customers into 'High Spender' (>= $20k), 'Mid Spender' ($5k-$20k),
--       and 'Low Spender' (< $5k). Count the number of customers in each bracket.
-- SOLUTION:
WITH CustomerSpend AS (
    SELECT 
        c.customer_id,
        COALESCE(SUM(oi.quantity * oi.unit_price * (1 - oi.discount_pct)), 0.00) AS total_spend
    FROM customers c
    LEFT JOIN orders o ON c.customer_id = o.customer_id AND o.order_status = 'Completed'
    LEFT JOIN order_items oi ON o.order_id = oi.order_id
    GROUP BY c.customer_id
)
SELECT 
    CASE 
        WHEN total_spend >= 20000 THEN 'High Spender'
        WHEN total_spend >= 5000 THEN 'Mid Spender'
        ELSE 'Low Spender'
    END AS spending_bracket,
    COUNT(customer_id) AS customer_count,
    ROUND(SUM(total_spend), 2) AS bracket_total_spend
FROM CustomerSpend
GROUP BY 
    CASE 
        WHEN total_spend >= 20000 THEN 'High Spender'
        WHEN total_spend >= 5000 THEN 'Mid Spender'
        ELSE 'Low Spender'
    END
ORDER BY bracket_total_spend DESC;


-- [TASK Q7]
-- Task: Find customers who placed more than one completed order. Return customer_id,
--       customer_name, first order date, and most recent order date.
-- SOLUTION:
SELECT 
    c.customer_id,
    c.customer_name,
    MIN(o.order_date) AS first_order_date,
    MAX(o.order_date) AS most_recent_order_date,
    COUNT(o.order_id) AS completed_orders_count
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
WHERE o.order_status = 'Completed'
GROUP BY c.customer_id, c.customer_name
HAVING COUNT(o.order_id) > 1
ORDER BY completed_orders_count DESC, c.customer_id ASC;


-- [TASK Q8]
-- Task: Using a RECURSIVE CTE, generate a date series from '2024-01-01' to '2024-01-10'
--       and count how many orders were placed on each calendar day (including 0-order days).
-- SOLUTION:
WITH RECURSIVE DateSeries AS (
    SELECT CAST('2024-01-01' AS DATE) AS calendar_date
    UNION ALL
    SELECT DATE_ADD(calendar_date, INTERVAL 1 DAY)
    FROM DateSeries
    WHERE calendar_date < '2024-01-10'
)
SELECT 
    ds.calendar_date,
    COUNT(o.order_id) AS order_count
FROM DateSeries ds
LEFT JOIN orders o ON ds.calendar_date = o.order_date
GROUP BY ds.calendar_date
ORDER BY ds.calendar_date ASC;


-- =============================================================================
-- PART C: RANKING WINDOW FUNCTIONS (Q9 - Q12)
-- =============================================================================

-- [TASK Q9]
-- Task: Find the highest paid employee in EACH department without using GROUP BY or subquery filters.
--       Use DENSE_RANK() or ROW_NUMBER() in a CTE.
-- SOLUTION:
WITH RankedSalaries AS (
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
    salary
FROM RankedSalaries
WHERE salary_rank = 1
ORDER BY salary DESC;


-- [TASK Q10]
-- Task: (Deduplication Simulation) If duplicate orders existed, how would you pick only
--       the earliest order per customer? Write a query using ROW_NUMBER() partitioned
--       by customer_id ordered by order_date ASC.
-- SOLUTION:
WITH DeduplicatedOrders AS (
    SELECT 
        order_id,
        customer_id,
        order_date,
        ship_date,
        ship_mode,
        order_status,
        sales_rep_id,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id 
            ORDER BY order_date ASC, order_id ASC
        ) AS rn
    FROM orders
)
SELECT 
    order_id,
    customer_id,
    order_date,
    ship_date,
    ship_mode,
    order_status,
    sales_rep_id
FROM DeduplicatedOrders
WHERE rn = 1
ORDER BY customer_id ASC;


-- [TASK Q11]
-- Task: Divide all products into 4 equal price quartiles using NTILE(4) based on unit_price.
--       Display product_name, unit_price, and price_quartile (1 = lowest, 4 = highest).
-- SOLUTION:
SELECT 
    product_name,
    unit_price,
    NTILE(4) OVER (ORDER BY unit_price ASC) AS price_quartile
FROM products
ORDER BY price_quartile ASC, unit_price ASC;


-- [TASK Q12]
-- Task: Rank all products by unit_price within their category using both RANK() and DENSE_RANK()
--       to demonstrate how ties are treated.
-- SOLUTION:
SELECT 
    c.category_name,
    p.product_name,
    p.unit_price,
    RANK() OVER (
        PARTITION BY p.category_id 
        ORDER BY p.unit_price DESC
    ) AS rank_tier,
    DENSE_RANK() OVER (
        PARTITION BY p.category_id 
        ORDER BY p.unit_price DESC
    ) AS dense_rank_tier
FROM products p
JOIN categories c ON p.category_id = c.category_id
ORDER BY c.category_name ASC, p.unit_price DESC;


-- =============================================================================
-- PART D: OFFSET FUNCTIONS: LAG & LEAD (Q13 - Q15)
-- =============================================================================

-- [TASK Q13]
-- Task: (Month-over-Month Growth) Calculate the total net revenue for each calendar month,
--       and use LAG() to compute the previous month's revenue and the MoM Dollar Growth.
-- SOLUTION:
WITH MonthlyRevenue AS (
    SELECT 
        DATE_FORMAT(o.order_date, '%Y-%m') AS order_month,
        ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount_pct)), 2) AS current_month_revenue
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.order_status = 'Completed'
    GROUP BY DATE_FORMAT(o.order_date, '%Y-%m')
)
SELECT 
    order_month,
    current_month_revenue,
    LAG(current_month_revenue, 1) OVER (ORDER BY order_month ASC) AS previous_month_revenue,
    ROUND(
        current_month_revenue - LAG(current_month_revenue, 1) OVER (ORDER BY order_month ASC), 
        2
    ) AS mom_dollar_growth
FROM MonthlyRevenue
ORDER BY order_month ASC;


-- [TASK Q14]
-- Task: (Customer Inactivity Interval) For each customer, list all their orders in chronological
--       order and use LAG() to calculate the days elapsed since their previous order.
-- SOLUTION:
SELECT 
    c.customer_id,
    c.customer_name,
    o.order_id,
    o.order_date,
    LAG(o.order_date, 1) OVER (
        PARTITION BY c.customer_id 
        ORDER BY o.order_date ASC, o.order_id ASC
    ) AS previous_order_date,
    DATEDIFF(
        o.order_date,
        LAG(o.order_date, 1) OVER (
            PARTITION BY c.customer_id 
            ORDER BY o.order_date ASC, o.order_id ASC
        )
    ) AS days_since_previous_order
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
ORDER BY c.customer_id ASC, o.order_date ASC;


-- [TASK Q15]
-- Task: For each order, display the current order's date, customer_id, and use LEAD()
--       to show the date of that customer's next upcoming order.
-- SOLUTION:
SELECT 
    o.order_id,
    o.customer_id,
    o.order_date AS current_order_date,
    LEAD(o.order_date, 1) OVER (
        PARTITION BY o.customer_id 
        ORDER BY o.order_date ASC, o.order_id ASC
    ) AS next_order_date
FROM orders o
ORDER BY o.customer_id ASC, o.order_date ASC;


-- =============================================================================
-- PART E: AGGREGATE WINDOW FUNCTIONS & FRAMES (Q16 - Q20)
-- =============================================================================

-- [TASK Q16]
-- Task: (Running Total) Calculate a running cumulative total of net revenue ordered chronologically
--       by order_date across all completed orders.
-- SOLUTION:
WITH CompletedOrderRevenue AS (
    SELECT 
        o.order_id,
        o.order_date,
        ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount_pct)), 2) AS order_net_revenue
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.order_status = 'Completed'
    GROUP BY o.order_id, o.order_date
)
SELECT 
    order_id,
    order_date,
    order_net_revenue,
    ROUND(SUM(order_net_revenue) OVER (
        ORDER BY order_date ASC, order_id ASC
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ), 2) AS running_cumulative_revenue
FROM CompletedOrderRevenue
ORDER BY order_date ASC, order_id ASC;


-- [TASK Q17]
-- Task: (3-Day Moving Average) For each order date, calculate the daily revenue and a 3-day
--       moving average (current day and 2 preceding days) using ROWS BETWEEN 2 PRECEDING AND CURRENT ROW.
-- SOLUTION:
WITH DailyNetRevenue AS (
    SELECT 
        o.order_date,
        ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount_pct)), 2) AS daily_revenue
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.order_status = 'Completed'
    GROUP BY o.order_date
)
SELECT 
    order_date,
    daily_revenue,
    ROUND(AVG(daily_revenue) OVER (
        ORDER BY order_date ASC
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ), 2) AS moving_avg_3_days
FROM DailyNetRevenue
ORDER BY order_date ASC;


-- [TASK Q18]
-- Task: (Percentage of Total) For each product sold in completed orders, display product_name,
--       category_name, product revenue, and calculate what percentage that product contributes
--       to its parent category's total revenue.
-- SOLUTION:
WITH ProductRevenue AS (
    SELECT 
        c.category_id,
        c.category_name,
        p.product_id,
        p.product_name,
        ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount_pct)), 2) AS product_revenue
    FROM products p
    JOIN categories c ON p.category_id = c.category_id
    JOIN order_items oi ON p.product_id = oi.product_id
    JOIN orders o ON oi.order_id = o.order_id
    WHERE o.order_status = 'Completed'
    GROUP BY c.category_id, c.category_name, p.product_id, p.product_name
)
SELECT 
    category_name,
    product_name,
    product_revenue,
    ROUND(SUM(product_revenue) OVER (PARTITION BY category_id), 2) AS category_total_revenue,
    ROUND(
        (product_revenue / SUM(product_revenue) OVER (PARTITION BY category_id)) * 100, 
        2
    ) AS pct_of_category_revenue
FROM ProductRevenue
ORDER BY category_name ASC, pct_of_category_revenue DESC;


-- [TASK Q19]
-- Task: Calculate the difference between each employee's salary and the highest salary
--       in their department using MAX() OVER (PARTITION BY ...).
-- SOLUTION:
SELECT 
    e.employee_id,
    CONCAT(e.first_name, ' ', e.last_name) AS employee_name,
    d.department_name,
    e.salary,
    MAX(e.salary) OVER (PARTITION BY e.department_id) AS dept_highest_salary,
    ROUND(MAX(e.salary) OVER (PARTITION BY e.department_id) - e.salary, 2) AS salary_gap_from_max
FROM employees e
JOIN departments d ON e.department_id = d.department_id
ORDER BY d.department_name ASC, e.salary DESC;


-- [TASK Q20]
-- Task: (Executive Retention Challenge) Identify customers who placed orders in two consecutive
--       months in 2024. Return distinct customer_id and customer_name.
-- SOLUTION:
WITH CustomerActiveMonths AS (
    SELECT DISTINCT 
        customer_id,
        EXTRACT(YEAR_MONTH FROM order_date) AS order_year_month
    FROM orders
    WHERE order_date >= '2024-01-01' AND order_date <= '2024-12-31'
),
MonthlySequences AS (
    SELECT 
        customer_id,
        order_year_month,
        LAG(order_year_month, 1) OVER (
            PARTITION BY customer_id 
            ORDER BY order_year_month ASC
        ) AS prev_year_month
    FROM CustomerActiveMonths
)
SELECT DISTINCT 
    c.customer_id,
    c.customer_name
FROM MonthlySequences ms
JOIN customers c ON ms.customer_id = c.customer_id
WHERE PERIOD_DIFF(ms.order_year_month, ms.prev_year_month) = 1;
