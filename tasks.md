# Enterprise Retail Analytics: 20 Advanced SQL Interview Tasks & Solutions

**Database:** `enterprise_retail_db`  
**Dialect:** MySQL 8.0+

---

## PART A: JOINS, ADVANCED FILTERING & SUBQUERIES (Q1 – Q5)

### [Task Q1]
**Task:** Find all customers from 'USA' who placed completed orders in Q1 2024 (Jan–Mar).  
**Return:** `customer_name`, `order_id`, `order_date`, and order `net_revenue`.

#### Solution
```sql
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
```

#### Output
| customer_name | order_id | order_date | net_revenue |
| :--- | :--- | :--- | :--- |
| Acme Global Corp | 101 | 2024-01-15 | 20362.50 |
| TechNova Solutions | 102 | 2024-01-20 | 17800.00 |
| Apex Financial Group | 103 | 2024-02-02 | 21900.80 |
| Beacon Design Studio | 104 | 2024-02-10 | 1080.00 |
| Acme Global Corp | 106 | 2024-03-01 | 21600.00 |

---

### [Task Q2]
**Task:** Identify all sales reps (`department_id = 2`) who have NEVER closed an order.  
**Pattern:** Anti-Join pattern (`LEFT JOIN` + `IS NULL` or `NOT EXISTS`).

#### Solution
```sql
SELECT 
    e.employee_id,
    CONCAT(e.first_name, ' ', e.last_name) AS sales_rep_name,
    e.email
FROM employees e
LEFT JOIN orders o ON e.employee_id = o.sales_rep_id
WHERE e.department_id = 2
  AND o.order_id IS NULL;
```

#### Output
| employee_id | sales_rep_name | email |
| :--- | :--- | :--- |
| 2 | Marcus Brody | marcus.brody@company.com |

---

### [Task Q3]
**Task:** List all products that have never been ordered in the entire history of the company.

#### Solution
```sql
SELECT 
    p.product_id,
    p.product_name,
    p.category_id,
    p.unit_price
FROM products p
LEFT JOIN order_items oi ON p.product_id = oi.product_id
WHERE oi.order_item_id IS NULL;
```

#### Output
| product_id | product_name | category_id | unit_price |
| :--- | :--- | :--- | :--- |
| 6 | Executive Oak Bookshelf | 3 | 320.00 |

---

### [Task Q4]
**Task:** Find all employees whose salary is strictly higher than the average salary of their department.  
**Return:** Employee name, department name, salary, and the department average salary.

#### Solution
```sql
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
```

#### Output
| employee_name | department_name | salary | dept_avg_salary |
| :--- | :--- | :--- | :--- |
| Donna Paulsen | Customer Support | 75000.00 | 71500.00 |
| Harvey Specter | Data & Technology | 140000.00 | 120000.00 |
| Sophia Chen | Data & Technology | 135000.00 | 120000.00 |
| Carlos Santana | Sales & Commercial | 130000.00 | 111250.00 |
| Marcus Brody | Sales & Commercial | 125000.00 | 111250.00 |

---

### [Task Q5]
**Task:** Find all customer segments where the total net revenue exceeds $30,000 across completed orders.  
**Return:** `segment`, `total_orders_count`, and `total_net_revenue` sorted descending.

#### Solution
```sql
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
```

#### Output
| segment | total_orders_count | total_net_revenue |
| :--- | :--- | :--- |
| Corporate | 9 | 160053.30 |

---

## PART B: COMMON TABLE EXPRESSIONS (CTEs) & COMPLEX LOGIC (Q6 – Q8)

### [Task Q6]
**Task:** Using a CTE, calculate the Total Spend per customer. In the main query, classify customers into:
- `'High Spender'` (>= $20k)
- `'Mid Spender'` ($5k–$20k)
- `'Low Spender'` (< $5k)  
Count the number of customers in each bracket.

#### Solution
```sql
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
```

#### Output
| spending_bracket | customer_count | bracket_total_spend |
| :--- | :--- | :--- |
| High Spender | 3 | 140613.30 |
| Mid Spender | 1 | 18000.00 |
| Low Spender | 6 | 5965.00 |

---

### [Task Q7]
**Task:** Find customers who placed more than one completed order. Return `customer_id`, `customer_name`, first order date, and most recent order date.

#### Solution
```sql
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
```

#### Output
| customer_id | customer_name | first_order_date | most_recent_order_date | completed_orders_count |
| :--- | :--- | :--- | :--- | :--- |
| 1 | Acme Global Corp | 2024-01-15 | 2024-06-01 | 3 |
| 2 | TechNova Solutions | 2024-01-20 | 2024-04-05 | 2 |
| 3 | Apex Financial Group | 2024-02-02 | 2024-05-15 | 2 |
| 4 | Beacon Design Studio | 2024-02-10 | 2024-06-12 | 2 |

---

### [Task Q8]
**Task:** Using a `RECURSIVE CTE`, generate a date series from `'2024-01-01'` to `'2024-01-10'` and count how many orders were placed on each calendar day (including 0-order days).

#### Solution
```sql
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
```

#### Output
| calendar_date | order_count |
| :--- | :--- |
| 2024-01-01 | 0 |
| 2024-01-02 | 0 |
| 2024-01-03 | 0 |
| 2024-01-04 | 0 |
| 2024-01-05 | 0 |
| 2024-01-06 | 0 |
| 2024-01-07 | 0 |
| 2024-01-08 | 0 |
| 2024-01-09 | 0 |
| 2024-01-10 | 0 |

---

## PART C: RANKING WINDOW FUNCTIONS (Q9 – Q12)

### [Task Q9]
**Task:** Find the highest paid employee in EACH department without using `GROUP BY` or subquery filters. Use `DENSE_RANK()` or `ROW_NUMBER()` in a CTE.

#### Solution
```sql
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
```

#### Output
| department_name | employee_name | salary |
| :--- | :--- | :--- |
| Executive Leadership | Eleanor Vance | 185000.00 |
| Data & Technology | Harvey Specter | 140000.00 |
| Sales & Commercial | Carlos Santana | 130000.00 |
| Customer Support | Donna Paulsen | 75000.00 |

---

### [Task Q10]
**Task:** (Deduplication Simulation) If duplicate orders existed, how would you pick only the earliest order per customer? Write a query using `ROW_NUMBER()` partitioned by `customer_id` ordered by `order_date ASC`.

#### Solution
```sql
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
```

#### Output
| order_id | customer_id | order_date | ship_date | ship_mode | order_status | sales_rep_id |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 101 | 1 | 2024-01-15 | 2024-01-18 | Express | Completed | 4 |
| 102 | 2 | 2024-01-20 | 2024-01-25 | Standard | Completed | 6 |
| 103 | 3 | 2024-02-02 | 2024-02-04 | Same Day | Completed | 5 |
| 104 | 4 | 2024-02-10 | 2024-02-14 | Standard | Completed | 4 |
| 105 | 5 | 2024-02-15 | 2024-02-20 | Standard | Refunded | NULL |
| 111 | 6 | 2024-05-02 | 2024-05-06 | Standard | Completed | NULL |
| 107 | 7 | 2024-03-12 | 2024-03-18 | Standard | Completed | 4 |
| 108 | 8 | 2024-03-25 | 2024-03-28 | Express | Completed | 5 |
| 113 | 9 | 2024-05-20 | NULL | Standard | Cancelled | NULL |
| 110 | 10 | 2024-04-18 | 2024-04-20 | Express | Completed | 6 |

---

### [Task Q11]
**Task:** Divide all products into 4 equal price quartiles using `NTILE(4)` based on `unit_price`.  
**Return:** `product_name`, `unit_price`, and `price_quartile` (1 = lowest, 4 = highest).

#### Solution
```sql
SELECT 
    product_name,
    unit_price,
    NTILE(4) OVER (ORDER BY unit_price ASC) AS price_quartile
FROM products
ORDER BY price_quartile ASC, unit_price ASC;
```

#### Output
| product_name | unit_price | price_quartile |
| :--- | :--- | :--- |
| Premium Gel Ink Pens (Box of 50) | 45.00 | 1 |
| Multi-Purpose Laser Paper (10 Reams) | 60.00 | 1 |
| Heavy-Duty Paper Shredder | 120.00 | 1 |
| Wireless Noise-Cancelling Headset | 250.00 | 2 |
| Executive Oak Bookshelf | 320.00 | 2 |
| Ergonomic Mesh Office Chair | 450.00 | 2 |
| Motorized Standing Desk 60x30 | 680.00 | 3 |
| Ultra-Wide Monitor 34-inch | 750.00 | 3 |
| Cloud Storage Enterprise License (Annual) | 1200.00 | 3 |
| SaaS Analytics Platform Seat (Annual) | 1800.00 | 4 |
| Enterprise Laptop Pro 16 | 2400.00 | 4 |

---

### [Task Q12]
**Task:** Rank all products by `unit_price` within their category using both `RANK()` and `DENSE_RANK()` to demonstrate how ties are treated.

#### Solution
```sql
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
```

#### Output
| category_name | product_name | unit_price | rank_tier | dense_rank_tier |
| :--- | :--- | :--- | :--- | :--- |
| Cloud Subscriptions | SaaS Analytics Platform Seat (Annual) | 1800.00 | 1 | 1 |
| Cloud Subscriptions | Cloud Storage Enterprise License (Annual) | 1200.00 | 2 | 2 |
| Furniture | Motorized Standing Desk 60x30 | 680.00 | 1 | 1 |
| Furniture | Ergonomic Mesh Office Chair | 450.00 | 2 | 2 |
| Furniture | Executive Oak Bookshelf | 320.00 | 3 | 3 |
| Office Supplies | Heavy-Duty Paper Shredder | 120.00 | 1 | 1 |
| Office Supplies | Multi-Purpose Laser Paper (10 Reams) | 60.00 | 2 | 2 |
| Office Supplies | Premium Gel Ink Pens (Box of 50) | 45.00 | 3 | 3 |
| Technology | Enterprise Laptop Pro 16 | 2400.00 | 1 | 1 |
| Technology | Ultra-Wide Monitor 34-inch | 750.00 | 2 | 2 |
| Technology | Wireless Noise-Cancelling Headset | 250.00 | 3 | 3 |

---

## PART D: OFFSET FUNCTIONS: LAG & LEAD (Q13 – Q15)

### [Task Q13]
**Task:** (Month-over-Month Growth) Calculate the total net revenue for each calendar month, and use `LAG()` to compute the previous month's revenue and the MoM Dollar Growth.

#### Solution
```sql
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
```

#### Output
| order_month | current_month_revenue | previous_month_revenue | mom_dollar_growth |
| :--- | :--- | :--- | :--- |
| 2024-01 | 38162.50 | NULL | NULL |
| 2024-02 | 22980.80 | 38162.50 | -15181.70 |
| 2024-03 | 25395.00 | 22980.80 | 2414.20 |
| 2024-04 | 50580.00 | 25395.00 | 25185.00 |
| 2024-05 | 16540.00 | 50580.00 | -34040.00 |
| 2024-06 | 10920.00 | 16540.00 | -5620.00 |

---

### [Task Q14]
**Task:** (Customer Inactivity Interval) For each customer, list all their orders in chronological order and use `LAG()` to calculate the days elapsed since their previous order.

#### Solution
```sql
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
```

#### Output (Sample)
| customer_id | customer_name | order_id | order_date | previous_order_date | days_since_previous_order |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Acme Global Corp | 101 | 2024-01-15 | NULL | NULL |
| 1 | Acme Global Corp | 106 | 2024-03-01 | 2024-01-15 | 46 |
| 1 | Acme Global Corp | 114 | 2024-06-01 | 2024-03-01 | 92 |
| 2 | TechNova Solutions | 102 | 2024-01-20 | NULL | NULL |
| 2 | TechNova Solutions | 109 | 2024-04-05 | 2024-01-20 | 76 |
| 3 | Apex Financial Group | 103 | 2024-02-02 | NULL | NULL |
| 3 | Apex Financial Group | 112 | 2024-05-15 | 2024-02-02 | 103 |
| 4 | Beacon Design Studio | 104 | 2024-02-10 | NULL | NULL |
| 4 | Beacon Design Studio | 115 | 2024-06-12 | 2024-02-10 | 123 |

---

### [Task Q15]
**Task:** For each order, display the current order's date, `customer_id`, and use `LEAD()` to show the date of that customer's next upcoming order.

#### Solution
```sql
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
```

#### Output (Sample)
| order_id | customer_id | current_order_date | next_order_date |
| :--- | :--- | :--- | :--- |
| 101 | 1 | 2024-01-15 | 2024-03-01 |
| 106 | 1 | 2024-03-01 | 2024-06-01 |
| 114 | 1 | 2024-06-01 | NULL |
| 102 | 2 | 2024-01-20 | 2024-04-05 |
| 109 | 2 | 2024-04-05 | NULL |
| 103 | 3 | 2024-02-02 | 2024-05-15 |
| 112 | 3 | 2024-05-15 | NULL |

---

## PART E: AGGREGATE WINDOW FUNCTIONS & FRAMES (Q16 – Q20)

### [Task Q16]
**Task:** (Running Total) Calculate a running cumulative total of net revenue ordered chronologically by `order_date` across all completed orders.

#### Solution
```sql
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
```

#### Output (Sample)
| order_id | order_date | order_net_revenue | running_cumulative_revenue |
| :--- | :--- | :--- | :--- |
| 101 | 2024-01-15 | 20362.50 | 20362.50 |
| 102 | 2024-01-20 | 17800.00 | 38162.50 |
| 103 | 2024-02-02 | 21900.80 | 60063.30 |
| 104 | 2024-02-10 | 1080.00 | 61143.30 |
| 106 | 2024-03-01 | 21600.00 | 82743.30 |
| 107 | 2024-03-12 | 1440.00 | 84183.30 |
| 108 | 2024-03-25 | 2355.00 | 86538.30 |
| 109 | 2024-04-05 | 32580.00 | 119118.30 |

---

### [Task Q17]
**Task:** (3-Day Moving Average) For each order date, calculate the daily revenue and a 3-day moving average (current day and 2 preceding days) using `ROWS BETWEEN 2 PRECEDING AND CURRENT ROW`.

#### Solution
```sql
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
```

#### Output (Sample)
| order_date | daily_revenue | moving_avg_3_days |
| :--- | :--- | :--- |
| 2024-01-15 | 20362.50 | 20362.50 |
| 2024-01-20 | 17800.00 | 19081.25 |
| 2024-02-02 | 21900.80 | 20021.10 |
| 2024-02-10 | 1080.00 | 13593.60 |
| 2024-03-01 | 21600.00 | 14860.27 |

---

### [Task Q18]
**Task:** (Percentage of Total) For each product sold in completed orders, display `product_name`, `category_name`, `product_revenue`, and calculate what percentage that product contributes to its parent category's total revenue.

#### Solution
```sql
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
```

#### Output
| category_name | product_name | product_revenue | category_total_revenue | pct_of_category_revenue |
| :--- | :--- | :--- | :--- | :--- |
| Cloud Subscriptions | SaaS Analytics Platform Seat (Annual) | 53100.00 | 77100.00 | 68.87 |
| Cloud Subscriptions | Cloud Storage Enterprise License (Annual) | 24000.00 | 77100.00 | 31.13 |
| Furniture | Motorized Standing Desk 60x30 | 11124.80 | 16929.80 | 65.71 |
| Furniture | Ergonomic Mesh Office Chair | 5805.00 | 16929.80 | 34.29 |
| Office Supplies | Multi-Purpose Laser Paper (10 Reams) | 1080.00 | 1710.00 | 63.16 |
| Office Supplies | Heavy-Duty Paper Shredder | 360.00 | 1710.00 | 21.05 |
| Office Supplies | Premium Gel Ink Pens (Box of 50) | 270.00 | 1710.00 | 15.79 |
| Technology | Enterprise Laptop Pro 16 | 52176.00 | 68901.00 | 75.73 |
| Technology | Ultra-Wide Monitor 34-inch | 13912.50 | 68901.00 | 20.19 |
| Technology | Wireless Noise-Cancelling Headset | 2812.50 | 68901.00 | 4.08 |

---

### [Task Q19]
**Task:** Calculate the difference between each employee's salary and the highest salary in their department using `MAX() OVER (PARTITION BY ...)`.

#### Solution
```sql
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
```

#### Output
| employee_id | employee_name | department_name | salary | dept_highest_salary | salary_gap_from_max |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 9 | Donna Paulsen | Customer Support | 75000.00 | 75000.00 | 0.00 |
| 10 | Mike Ross | Customer Support | 68000.00 | 75000.00 | 7000.00 |
| 8 | Harvey Specter | Data & Technology | 140000.00 | 140000.00 | 0.00 |
| 3 | Sophia Chen | Data & Technology | 135000.00 | 140000.00 | 5000.00 |
| 7 | Rachel Zane | Data & Technology | 85000.00 | 140000.00 | 55000.00 |
| 1 | Eleanor Vance | Executive Leadership | 185000.00 | 185000.00 | 0.00 |
| 6 | Carlos Santana | Sales & Commercial | 130000.00 | 130000.00 | 0.00 |
| 2 | Marcus Brody | Sales & Commercial | 125000.00 | 130000.00 | 5000.00 |
| 5 | Jessica Alba | Sales & Commercial | 98000.00 | 130000.00 | 32000.00 |
| 4 | David Miller | Sales & Commercial | 92000.00 | 130000.00 | 38000.00 |

---

### [Task Q20]
**Task:** (Executive Retention Challenge) Identify customers who placed orders in two consecutive months in 2024. Return distinct `customer_id` and `customer_name`.

#### Solution
```sql
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
```

#### Output
```
(No customers in current seed data have consecutive order months in 2024; logic verified with simulated data)
```
