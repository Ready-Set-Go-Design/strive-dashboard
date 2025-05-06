from sqlalchemy import text
from utils.db import engine

# Season-aware summary view definition
SQL = r"""
CREATE OR REPLACE VIEW public.vw_national_summary_by_season AS
WITH
  coach_cte AS (
    SELECT
      CASE
        WHEN EXTRACT(MONTH FROM created_at) >= 7 THEN
          CONCAT(EXTRACT(YEAR FROM created_at)::INT, '/', (EXTRACT(YEAR FROM created_at)::INT + 1))
        ELSE
          CONCAT((EXTRACT(YEAR FROM created_at)::INT - 1), '/', EXTRACT(YEAR FROM created_at)::INT)
      END AS season,
      COUNT(*) AS total_coaches
    FROM users
    WHERE role = 'coach' AND active IS TRUE
    GROUP BY season
  ),
  parent_cte AS (
    SELECT
      CASE
        WHEN EXTRACT(MONTH FROM created_at) >= 7 THEN
          CONCAT(EXTRACT(YEAR FROM created_at)::INT, '/', (EXTRACT(YEAR FROM created_at)::INT + 1))
        ELSE
          CONCAT((EXTRACT(YEAR FROM created_at)::INT - 1), '/', EXTRACT(YEAR FROM created_at)::INT)
      END AS season,
      COUNT(*) AS total_parents
    FROM users
    WHERE role = 'parent' AND active IS TRUE
    GROUP BY season
  ),
  skier_cte AS (
    SELECT
      CASE
        WHEN EXTRACT(MONTH FROM created_at) >= 7 THEN
          CONCAT(EXTRACT(YEAR FROM created_at)::INT, '/', (EXTRACT(YEAR FROM created_at)::INT + 1))
        ELSE
          CONCAT((EXTRACT(YEAR FROM created_at)::INT - 1), '/', EXTRACT(YEAR FROM created_at)::INT)
      END AS season,
      COUNT(*) AS total_skiers
    FROM users
    WHERE role = 'skier' AND active IS TRUE
    GROUP BY season
  ),
  eval_cte AS (
    SELECT
      CASE
        WHEN EXTRACT(MONTH FROM created_at) >= 7 THEN
          CONCAT(EXTRACT(YEAR FROM created_at)::INT, '/', (EXTRACT(YEAR FROM created_at)::INT + 1))
        ELSE
          CONCAT((EXTRACT(YEAR FROM created_at)::INT - 1), '/', EXTRACT(YEAR FROM created_at)::INT)
      END AS season,
      COUNT(*) AS evaluations_completed
    FROM coach_rankings
    GROUP BY season
  ),
  drill_cte AS (
    SELECT
      CASE
        WHEN EXTRACT(MONTH FROM created_at) >= 7 THEN
          CONCAT(EXTRACT(YEAR FROM created_at)::INT, '/', (EXTRACT(YEAR FROM created_at)::INT + 1))
        ELSE
          CONCAT((EXTRACT(YEAR FROM created_at)::INT - 1), '/', EXTRACT(YEAR FROM created_at)::INT)
      END AS season,
      COUNT(*) AS drills_shared
    FROM share_drills
    GROUP BY season
  )
SELECT
  co.season,
  co.total_coaches,
  pa.total_parents,
  sk.total_skiers,
  ev.evaluations_completed,
  dr.drills_shared
FROM coach_cte  co
LEFT JOIN parent_cte  pa ON pa.season = co.season
LEFT JOIN skier_cte   sk ON sk.season = co.season
LEFT JOIN eval_cte    ev ON ev.season = co.season
LEFT JOIN drill_cte   dr ON dr.season = co.season;
"""


def create_view():
    """
    Execute the CREATE OR REPLACE VIEW statement for vw_national_summary_by_season
    """
    with engine.begin() as conn:
        conn.execute(text(SQL))
        print("✅ Created or replaced view: vw_national_summary_by_season")


if __name__ == '__main__':
    create_view()
