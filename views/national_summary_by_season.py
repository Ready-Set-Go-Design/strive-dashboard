from sqlalchemy import text
import os, sys
# ─── Bring the project root into Python’s import path ─────────
sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

from utils.db import engine

SQL = r"""
DROP VIEW IF EXISTS public.vw_national_summary_by_season CASCADE;

CREATE OR REPLACE VIEW public.vw_national_summary_by_season AS
WITH
  coach_cte AS (
    SELECT
      u.club_id,
      CASE
        WHEN EXTRACT(MONTH FROM u.created_at) >= 7 THEN
          CONCAT(EXTRACT(YEAR FROM u.created_at)::INT, '/', EXTRACT(YEAR FROM u.created_at)::INT + 1)
        ELSE
          CONCAT((EXTRACT(YEAR FROM u.created_at)::INT - 1), '/', EXTRACT(YEAR FROM u.created_at)::INT)
      END AS season,
      COUNT(*) AS coaches
    FROM users u
    WHERE u.role    = 'coach'
      AND u.active  IS TRUE
      AND u.club_id IS NOT NULL
    GROUP BY u.club_id, season
  ),

  parent_cte AS (
    SELECT
      s.club_id,
      CASE
        WHEN EXTRACT(MONTH FROM g.created_at) >= 7 THEN
          CONCAT(EXTRACT(YEAR FROM g.created_at)::INT, '/', EXTRACT(YEAR FROM g.created_at)::INT + 1)
        ELSE
          CONCAT((EXTRACT(YEAR FROM g.created_at)::INT - 1), '/', EXTRACT(YEAR FROM g.created_at)::INT)
      END AS season,
      COUNT(DISTINCT g.id) AS parents
    FROM users g
    JOIN users s
      ON g.id = CAST(s.guardian_id AS INTEGER)
    WHERE g.role    = 'guardian'
      AND g.active  IS TRUE
      AND s.club_id IS NOT NULL
    GROUP BY s.club_id, season
  ),

  skier_cte AS (
    SELECT
      u.club_id,
      CASE
        WHEN EXTRACT(MONTH FROM u.created_at) >= 7 THEN
          CONCAT(EXTRACT(YEAR FROM u.created_at)::INT, '/', EXTRACT(YEAR FROM u.created_at)::INT + 1)
        ELSE
          CONCAT((EXTRACT(YEAR FROM u.created_at)::INT - 1), '/', EXTRACT(YEAR FROM u.created_at)::INT)
      END AS season,
      COUNT(*) AS skiers
    FROM users u
    WHERE u.role    = 'skier'
      AND u.active  IS TRUE
      AND u.club_id IS NOT NULL
    GROUP BY u.club_id, season
  ),

  eval_cte AS (
    SELECT
      u.club_id,
      CASE
        WHEN EXTRACT(MONTH FROM cr.created_at) >= 7 THEN
          CONCAT(EXTRACT(YEAR FROM cr.created_at)::INT, '/', EXTRACT(YEAR FROM cr.created_at)::INT + 1)
        ELSE
          CONCAT((EXTRACT(YEAR FROM cr.created_at)::INT - 1), '/', EXTRACT(YEAR FROM cr.created_at)::INT)
      END AS season,
      COUNT(*) AS evaluations_completed
    FROM coach_rankings cr
    JOIN users u
      ON cr.coach_id = u.id
    WHERE u.club_id IS NOT NULL
    GROUP BY u.club_id, season
  ),

  drill_cte AS (
    SELECT
      u.club_id,
      CASE
        WHEN EXTRACT(MONTH FROM sd.created_at) >= 7 THEN
          CONCAT(EXTRACT(YEAR FROM sd.created_at)::INT, '/', EXTRACT(YEAR FROM sd.created_at)::INT + 1)
        ELSE
          CONCAT((EXTRACT(YEAR FROM sd.created_at)::INT - 1), '/', EXTRACT(YEAR FROM sd.created_at)::INT)
      END AS season,
      COUNT(*) AS drills_shared
    FROM share_drills sd
    JOIN users u
      ON sd.coach_id = u.id
    WHERE u.club_id IS NOT NULL
    GROUP BY u.club_id, season
  ),

  contact_cte AS (
    SELECT
      club_id,
      season,
      primary_contact,
      primary_contact_email
    FROM (
      SELECT
        u.club_id,
        (u.firstname || ' ' || u.lastname) AS primary_contact,
        u.email                          AS primary_contact_email,
        CASE
          WHEN EXTRACT(MONTH FROM u.created_at) >= 7 THEN
            CONCAT(EXTRACT(YEAR FROM u.created_at)::INT, '/', EXTRACT(YEAR FROM u.created_at)::INT + 1)
          ELSE
            CONCAT((EXTRACT(YEAR FROM u.created_at)::INT - 1), '/', EXTRACT(YEAR FROM u.created_at)::INT)
        END                               AS season,
        ROW_NUMBER() OVER (
          PARTITION BY u.club_id,
                       CASE
                         WHEN EXTRACT(MONTH FROM u.created_at) >= 7 THEN
                           CONCAT(EXTRACT(YEAR FROM u.created_at)::INT, '/', EXTRACT(YEAR FROM u.created_at)::INT + 1)
                         ELSE
                           CONCAT((EXTRACT(YEAR FROM u.created_at)::INT - 1), '/', EXTRACT(YEAR FROM u.created_at)::INT)
                       END
          ORDER BY u.created_at
        )                                  AS rn
      FROM users u
      WHERE u.role    = 'coach'
        AND u.active  IS TRUE
        AND u.club_id IS NOT NULL
    ) sub
    WHERE rn = 1
  ),

  seasons_union AS (
    SELECT club_id, season FROM coach_cte
    UNION
    SELECT club_id, season FROM parent_cte
    UNION
    SELECT club_id, season FROM skier_cte
  )

SELECT
  c.id                         AS club_id,
  su.season,
  c.name                       AS club_name,
  c.ptso                       AS ptso,
  COALESCE(co.coaches, 0)                       AS coaches,
  COALESCE(pa.parents, 0)                       AS parents,
  COALESCE(sk.skiers, 0)                        AS skiers,
  COALESCE(ev.evaluations_completed, 0)         AS evaluations_completed,
  COALESCE(dr.drills_shared, 0)                 AS drills_shared,
  COALESCE(ct.primary_contact, '')              AS primary_contact,
  COALESCE(ct.primary_contact_email, '')        AS primary_contact_email,
  'Active'                                     AS status
FROM clubs c
JOIN seasons_union su
  ON su.club_id = c.id
LEFT JOIN coach_cte co
  ON co.club_id = c.id AND co.season = su.season
LEFT JOIN parent_cte pa
  ON pa.club_id = c.id AND pa.season = su.season
LEFT JOIN skier_cte sk
  ON sk.club_id = c.id AND sk.season = su.season
LEFT JOIN eval_cte ev
  ON ev.club_id = c.id AND ev.season = su.season
LEFT JOIN drill_cte dr
  ON dr.club_id = c.id AND dr.season = su.season
LEFT JOIN contact_cte ct
  ON ct.club_id = c.id AND ct.season = su.season
ORDER BY su.season, c.name;
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
