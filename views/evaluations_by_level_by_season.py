import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text
from utils.db import engine

SQL = r"""

/* ❶ Replace the old view with pass / total counts */
DROP VIEW IF EXISTS public.vw_evaluations_by_level_by_season CASCADE;

CREATE OR REPLACE VIEW public.vw_evaluations_by_level_by_season AS
WITH base AS (
  SELECT
    u.club_id,
    CASE
      WHEN EXTRACT(MONTH FROM cr.created_at) >= 7
        THEN CONCAT(EXTRACT(YEAR FROM cr.created_at)::INT, '/',
                    EXTRACT(YEAR FROM cr.created_at)::INT + 1)
      ELSE CONCAT(EXTRACT(YEAR FROM cr.created_at)::INT - 1, '/',
                  EXTRACT(YEAR FROM cr.created_at)::INT)
    END                         AS season,
    cr.level_id,
    COALESCE(l.name, 'Level '||cr.level_id) AS level_name,
    l.sort_order,
    cr.passed                   AS passed    -- ⭐ NEW
  FROM coach_rankings cr
  JOIN users  u ON u.id   = cr.coach_id
  LEFT JOIN levels l ON l.id = cr.level_id
  WHERE u.club_id IS NOT NULL
)
SELECT
  b.season,
  c.name    AS club_name,
  c.ptso,
  b.level_id,
  b.level_name,
  COUNT(*)                         AS eval_total,
  SUM(b.passed::int)               AS eval_passed   -- ⭐ NEW
FROM base b
JOIN clubs c ON c.id = b.club_id
GROUP BY
  b.season, c.name, c.ptso,
  b.level_id, b.level_name, b.sort_order
ORDER BY
  b.season, c.name,
  b.sort_order NULLS LAST, b.level_id;

"""

def create_view():
    with engine.begin() as conn:
        conn.execute(text(SQL))
        print("✅ Updated vw_evaluations_by_level_by_season")

if __name__ == "__main__":
    create_view()
