import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text
from utils.db import engine

SQL = r"""

DROP VIEW IF EXISTS public.vw_skier_level_distribution_by_season CASCADE;
CREATE OR REPLACE VIEW public.vw_skier_level_distribution_by_season AS
WITH base AS (
  SELECT
    u.club_id,
    CASE
      WHEN EXTRACT(MONTH FROM u.created_at) >= 7 THEN
        CONCAT(EXTRACT(YEAR FROM u.created_at)::INT, '/', (EXTRACT(YEAR FROM u.created_at)::INT + 1))
      ELSE
        CONCAT((EXTRACT(YEAR FROM u.created_at)::INT - 1), '/', EXTRACT(YEAR FROM u.created_at)::INT)
    END AS season,
    u.current_level       AS level_id,
    COALESCE(l.name, 'Level ' || u.current_level::text) AS level_name
  FROM users u
  LEFT JOIN levels l
    ON l.id::text = u.current_level::text
  WHERE lower(u.role) = 'skier'
    AND u.active IS TRUE
    AND u.current_level IS NOT NULL
)
SELECT
  b.season,
  c.name   AS club_name,
  c.ptso   AS ptso,
  b.level_id,
  b.level_name,
  COUNT(*) AS skier_count
FROM base b
JOIN clubs c
  ON b.club_id = c.id
GROUP BY
  b.season,
  c.name,
  c.ptso,
  b.level_id,
  b.level_name
ORDER BY
  b.season,
  c.name,
  c.ptso,
  b.level_id;
"""

def create_view():
    with engine.begin() as conn:
        conn.execute(text(SQL))
        print("✅ Updated vw_skier_level_distribution_by_season")

if __name__ == "__main__":
    create_view()
