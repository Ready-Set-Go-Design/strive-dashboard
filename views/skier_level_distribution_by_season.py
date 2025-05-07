import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text
from utils.db import engine

SQL = r"""
CREATE OR REPLACE VIEW public.vw_skier_level_distribution_by_season AS
SELECT
  /* Season bucket: July 1 → next June 30 */
  CASE
    WHEN EXTRACT(MONTH FROM u.created_at) >= 7 THEN
      CONCAT(EXTRACT(YEAR FROM u.created_at)::INT, '/', (EXTRACT(YEAR FROM u.created_at)::INT + 1))
    ELSE
      CONCAT((EXTRACT(YEAR FROM u.created_at)::INT - 1), '/', EXTRACT(YEAR FROM u.created_at)::INT)
  END                                   AS season,

  u.current_level                       AS level_id,

  COALESCE(l.name, 'Level ' || u.current_level::text)
                                         AS level_name,

  COUNT(*)                              AS skier_count
FROM users u
LEFT JOIN levels l
  ON l.id::text = u.current_level::text          -- tolerate type mismatch
WHERE lower(u.role) = 'skier'
  AND u.active IS TRUE
  AND u.current_level IS NOT NULL
GROUP BY season, u.current_level, l.name, u.current_level
ORDER BY season, u.current_level;                -- guarantees 1..2..3 order
"""

def create_view():
    with engine.begin() as conn:
        conn.execute(text(SQL))
        print("✅ Updated vw_skier_level_distribution_by_season")

if __name__ == "__main__":
    create_view()
