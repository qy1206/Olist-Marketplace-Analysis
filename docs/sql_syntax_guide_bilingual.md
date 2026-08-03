# Olist SQL Syntax Guide / SQL 语法速查表

This guide contains the SQL syntax used in the Olist portfolio project.
Use it for project revision and interview preparation.

## 1. Basic query / 基础查询

```sql
SELECT column_name
FROM `project.dataset.table`
WHERE condition
ORDER BY column_name DESC
LIMIT 10;
```

- `SELECT`: choose output columns / 选择输出字段
- `FROM`: choose the source table / 指定来源表
- `WHERE`: filter rows before aggregation / 在汇总前筛选行
- `ORDER BY`: sort the result / 排序
- `LIMIT`: restrict displayed rows / 限制显示行数

## 2. Aliases / 别名

```sql
SELECT COUNT(*) AS order_count
FROM `project.dataset.orders` AS orders;
```

- `AS order_count`: rename an output column / 为结果字段命名
- `AS orders`: give a table a shorter name / 给表格取短名称

## 3. DISTINCT and aggregation / 去重与汇总

```sql
SELECT
  order_status,
  COUNT(*) AS row_count,
  COUNT(DISTINCT order_id) AS unique_orders,
  SUM(payment_value) AS payment_value,
  AVG(review_score) AS average_review_score,
  MAX(payment_installments) AS maximum_installments
FROM `project.dataset.table`
GROUP BY order_status;
```

- `COUNT(*)`: count rows / 计算行数
- `COUNT(DISTINCT column)`: count unique values / 计算不重复值
- `SUM()`: add values vertically / 向下加总
- `AVG()`: calculate an average / 计算平均值
- `MAX()`: return the largest value / 取得最大值
- `GROUP BY`: combine rows into groups / 按字段分组汇总

## 4. WHERE versus HAVING / 筛选原始行与汇总结果

```sql
SELECT
  order_id,
  COUNT(*) AS row_count
FROM `project.dataset.order_items`
WHERE order_id IS NOT NULL
GROUP BY order_id
HAVING COUNT(*) > 1;
```

- `WHERE`: filters rows before `GROUP BY`
- `HAVING`: filters groups after `GROUP BY`

## 5. Multiple conditions / 多个条件

```sql
WHERE order_id IS NOT NULL
  AND price >= 0
  AND freight_value >= 0
```

```sql
WHERE order_status IN ('delivered', 'shipped')
```

- `AND`: every condition must be true / 所有条件必须成立
- `OR`: at least one condition must be true / 至少一个条件成立
- `IN`: match one value from a list / 匹配清单中的任一值

## 6. CASE / 条件判断

```sql
CASE
  WHEN delivery_date IS NULL THEN 'not_delivered'
  WHEN delivery_date <= estimated_date THEN 'on_time'
  ELSE 'late'
END AS delivery_status
```

Meaning: test conditions from top to bottom and return the first matching
result. / 从上到下检查条件，返回第一个符合的结果。

## 7. NULL handling / 空值处理

```sql
column_name IS NULL
column_name IS NOT NULL
```

```sql
NULLIF(TRIM(origin), '')
```

If the cleaned value is an empty string, return `NULL`.

```sql
COALESCE(value, 'unknown')
```

Return the first non-`NULL` value.

Combined example:

```sql
COALESCE(
  NULLIF(LOWER(TRIM(origin)), ''),
  'unknown'
) AS origin
```

Clean the text and replace missing or blank origins with `unknown`.

## 8. Text cleaning / 文字清理

```sql
LOWER(TRIM(payment_type)) AS payment_type
```

- `TRIM()`: remove outer spaces / 删除前后空格
- `LOWER()`: convert text to lowercase / 转成小写

## 9. Data-type conversion / 类型转换

```sql
CAST(price AS NUMERIC) AS item_price
```

Convert a value to another data type. `NUMERIC` is appropriate for exact
monetary calculations. / 把数值转换成适合精确金额计算的类型。

## 10. Date functions / 日期函数

```sql
DATE(timestamp_column)
```

Convert a timestamp to a date.

```sql
DATE_TRUNC(purchase_date, MONTH) AS purchase_month
```

Convert dates in the same month to the month's first date.

```sql
DATE_DIFF(delivery_date, purchase_date, DAY) AS delivery_days
```

Calculate the number of days between two dates.

## 11. Conditional counting / 条件计数

```sql
COUNTIF(order_status = 'delivered') AS delivered_orders
```

Count only rows where the condition is true.

## 12. Safe division and rounding / 安全除法与小数

```sql
ROUND(
  SAFE_DIVIDE(won_leads, total_leads) * 100,
  2
) AS conversion_rate_pct
```

- `SAFE_DIVIDE(A, B)`: return `NULL` instead of an error when `B = 0`
- `ROUND(value, 2)`: keep two decimal places

## 13. JOIN / 连接表格

```sql
SELECT
  leads.mql_id,
  deals.seller_id
FROM `project.dataset.leads` AS leads
LEFT JOIN `project.dataset.deals` AS deals
  ON leads.mql_id = deals.mql_id;
```

`LEFT JOIN` keeps every row from the left table. Unmatched right-side fields
become `NULL`. / 保留左表全部记录，右表没有匹配时显示 `NULL`。

Important grain rule:

> Aggregate one-to-many tables before joining them to prevent join fanout and
> duplicated revenue.

## 14. CTE with WITH / 临时命名查询

```sql
WITH item_summary AS (
  SELECT
    order_id,
    SUM(item_price) AS product_value
  FROM `project.dataset.order_items`
  GROUP BY order_id
)

SELECT *
FROM item_summary;
```

`WITH name AS (query)` temporarily names a query result so it can be used like
a table later in the same SQL statement.

## 15. STRING_AGG / 合并多行文字

```sql
STRING_AGG(
  DISTINCT payment_type,
  ', '
  ORDER BY payment_type
) AS payment_types
```

Example:

```text
credit_card
voucher
```

becomes:

```text
credit_card, voucher
```

## 16. Window functions / 窗口函数

```sql
RANK() OVER (
  ORDER BY post_win_product_value DESC
) AS overall_rank
```

Rank all sellers without combining or removing their original rows.

```sql
RANK() OVER (
  PARTITION BY origin
  ORDER BY post_win_product_value DESC
) AS origin_rank
```

Restart the ranking inside every origin.

Key distinction:

- `GROUP BY` reduces many rows into fewer rows.
- A window function keeps the rows and adds a calculated value.

## 17. UNION ALL / 上下合并结果

```sql
SELECT 'orders' AS metric_name, COUNT(*) AS metric_value
FROM `project.dataset.orders`

UNION ALL

SELECT 'sellers', COUNT(*)
FROM `project.dataset.sellers`;
```

`UNION ALL` stacks compatible query results vertically.

## 18. Views and schemas / 数据集与虚拟表

```sql
CREATE SCHEMA IF NOT EXISTS `project.dataset`;
```

Create a dataset if it does not already exist.

```sql
CREATE OR REPLACE VIEW `project.dataset.view_name` AS
SELECT ...
```

Save a reusable query as a virtual table.

## 19. Logical SQL order / SQL 逻辑执行顺序

Remember this order for interviews:

```text
FROM / JOIN
WHERE
GROUP BY
HAVING
SELECT
ORDER BY
LIMIT
```

The written query starts with `SELECT`, but SQL logically identifies and
filters the source rows before producing the selected output.

## 20. Project validation pattern / 项目验证模式

```sql
SELECT
  source_value,
  model_value,
  model_value - source_value AS difference,
  CASE
    WHEN model_value = source_value THEN 'PASS'
    ELSE 'FAIL'
  END AS check_status;
```

Use reconciliation to prove that joins and transformations did not duplicate
rows or monetary values.
