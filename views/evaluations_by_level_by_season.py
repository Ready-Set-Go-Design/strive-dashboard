from sqlalchemy import text

import os, sys
#  ─── Bring the project root into Python’s import path ─────────
sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

from utils.db import engine

# Season-aware summary view definition
SQL = r"""
CREATE OR REPLACE VIEW public.vw_evaluations_by_level_by_season AS
SELECT
  /* Season bucket: July 1 → next June 30 */
  CASE
    WHEN EXTRACT(MONTH FROM cr.created_at) >= 7 THEN
      CONCAT(EXTRACT(YEAR FROM cr.created_at)::INT, '/', (EXTRACT(YEAR FROM cr.created_at)::INT + 1))
    ELSE
      CONCAT((EXTRACT(YEAR FROM cr.created_at)::INT - 1), '/', EXTRACT(YEAR FROM cr.created_at)::INT)
  END                                             AS season,

  cr.level_id                                     AS level_id,

  COALESCE(l.name, 'Level ' || cr.level_id::text) AS level_name,

  COUNT(*)                                        AS eval_count
FROM coach_rankings cr
LEFT JOIN levels l ON l.id = cr.level_id
GROUP BY season, cr.level_id, l.name, l.sort_order
ORDER BY season, l.sort_order NULLS LAST, cr.level_id;
"""


def create_view():
    """
    Execute the CREATE OR REPLACE VIEW statement for vw_evaluations_by_level_by_season
    """
    with engine.begin() as conn:
        conn.execute(text(SQL))
        print("✅ Created or replaced view: vw_evaluations_by_level_by_season")


if __name__ == '__main__':
    create_view()
