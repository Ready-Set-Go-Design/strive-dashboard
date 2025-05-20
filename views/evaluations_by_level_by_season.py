import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text
from utils.db import engine

SQL = r"""

-- drop any old version
DROP VIEW IF EXISTS public.vw_evaluations_by_level_by_season CASCADE;

-- recreate with both total and passed counts
CREATE OR REPLACE VIEW public.vw_evaluations_by_level_by_season AS
WITH base AS (
  SELECT
    u.club_id,
    /* build a "2024/2025"‐style season string based on created_at */
    CASE
      WHEN EXTRACT(MONTH FROM cr.created_at) >= 7
        THEN CONCAT((EXTRACT(YEAR FROM cr.created_at))::INT,
                    '/',
                    (EXTRACT(YEAR FROM cr.created_at)::INT + 1))
      ELSE CONCAT((EXTRACT(YEAR FROM cr.created_at)::INT - 1),
                  '/',
                   (EXTRACT(YEAR FROM cr.created_at))::INT)
    END AS season,
    cr.level_id,
    COALESCE(l.name, 'Level ' || cr.level_id) AS level_name,
    l.sort_order,
    cr.passed AS passed
  FROM coach_rankings cr
  JOIN users u       ON u.id       = cr.coach_id
  LEFT JOIN levels l ON l.id       = cr.level_id
  WHERE u.club_id IS NOT NULL
)
SELECT
  b.season,
  c.name      AS club_name,
  c.ptso      AS ptso,
  b.level_id,
  b.level_name,
  /* total # of eval rows for this level */
  COUNT(*)                AS eval_total,
  /* how many of those were passed */
  SUM(b.passed::INT)      AS eval_passed
FROM base b
JOIN clubs c ON c.id = b.club_id
GROUP BY
  b.season,
  c.name,
  c.ptso,
  b.level_id,
  b.level_name,
  b.sort_order
-- ordering goes here if you SELECT from the view
;

"""

def create_view():
    with engine.begin() as conn:
        conn.execute(text(SQL))
        print("✅ Updated vw_evaluations_by_level_by_season")

if __name__ == "__main__":
    create_view()
