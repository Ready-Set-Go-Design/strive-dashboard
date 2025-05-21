import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text
from utils.db import engine

SQL = r"""
-- drop old view
DROP VIEW IF EXISTS public.vw_evaluations_by_level_by_season CASCADE;

-- recreate view with manual level ordering (1,34,35,36,37,38,67,68)
CREATE OR REPLACE VIEW public.vw_evaluations_by_level_by_season AS
WITH base AS (
  SELECT
    u.club_id,
    CASE
      WHEN EXTRACT(MONTH FROM cr.created_at) >= 7 THEN
        CONCAT(EXTRACT(YEAR FROM cr.created_at)::INT, '/', (EXTRACT(YEAR FROM cr.created_at)::INT + 1))
      ELSE
        CONCAT((EXTRACT(YEAR FROM cr.created_at)::INT - 1), '/', EXTRACT(YEAR FROM cr.created_at)::INT)
    END AS season,
    cr.level_id,
    COALESCE(l.name, 'Level ' || cr.level_id::text) AS level_name,
    cr.passed::INT AS passed
  FROM coach_rankings cr
  JOIN users u       ON u.id = cr.coach_id
  LEFT JOIN levels l ON l.id = cr.level_id
  WHERE u.club_id IS NOT NULL
)
SELECT
  b.season,
  c.name       AS club_name,
  c.ptso       AS ptso,
  b.level_id,
  b.level_name,
  COUNT(*)     AS eval_total,
  SUM(b.passed) AS eval_passed
FROM base b
JOIN clubs c ON c.id = b.club_id
GROUP BY
  b.season,
  c.name,
  c.ptso,
  b.level_id,
  b.level_name
ORDER BY
  CASE b.level_id
    WHEN 1  THEN 1
    WHEN 34 THEN 2
    WHEN 35 THEN 3
    WHEN 36 THEN 4
    WHEN 37 THEN 5
    WHEN 38 THEN 6
    WHEN 67 THEN 7
    WHEN 68 THEN 8
    ELSE 9
  END;
"""

def create_view():
    with engine.begin() as conn:
        conn.execute(text(SQL))
        print("✅ Updated vw_evaluations_by_level_by_season with manual level order")

if __name__ == "__main__":
    create_view()
