# SQL Revision Checklist

Use this checklist after completing the 15 project SQL files. Practise each
topic in a LeetCode-style question, then explain how it appears in the Olist
project.

## Window functions

- [ ] `RANK() OVER (ORDER BY ... DESC)`
  - Project example: rank activated sellers by post-win product value.
- [ ] `RANK() OVER (PARTITION BY origin ORDER BY ... DESC)`
  - Project example: restart seller ranking inside each acquisition origin.
- [ ] Compare `RANK`, `DENSE_RANK`, and `ROW_NUMBER`.
- [ ] LeetCode-style practice: top earners within each department/group.

Key interview distinction:

- `GROUP BY` combines rows and reduces the result.
- A window function keeps the original rows and adds a calculated value such
  as a rank.
