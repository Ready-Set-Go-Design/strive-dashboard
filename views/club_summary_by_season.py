from sqlalchemy import text
import os, sys

# ─── Bring the project root into Python’s import path ─────────
sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

from utils.db import engine

SQL = r"""
DROP VIEW IF EXISTS public.vw_club_summary_by_season CASCADE;

CREATE OR REPLACE VIEW public.vw_club_summary_by_season AS
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
      u.club_id,
      CASE
        WHEN EXTRACT(MONTH FROM u.created_at) >= 7 THEN
          CONCAT(EXTRACT(YEAR FROM u.created_at)::INT, '/', EXTRACT(YEAR FROM u.created_at)::INT + 1)
        ELSE
          CONCAT((EXTRACT(YEAR FROM u.created_at)::INT - 1), '/', EXTRACT(YEAR FROM u.created_at)::INT)
      END AS season,
      COUNT(*) AS parents
    FROM users u
    WHERE u.role    = 'guardian'
      AND u.active  IS TRUE
      AND u.club_id IS NOT NULL
    GROUP BY u.club_id, season
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

  contact_cte AS (
    SELECT
      u.club_id,
      season,
      primary_contact,
      primary_contact_email
    FROM (
      SELECT
        club_id,
        firstname || ' ' || lastname       AS primary_contact,
        email                              AS primary_contact_email,
        CASE
          WHEN EXTRACT(MONTH FROM created_at) >= 7 THEN
            CONCAT(EXTRACT(YEAR FROM created_at)::INT, '/', EXTRACT(YEAR FROM created_at)::INT + 1)
          ELSE
            CONCAT((EXTRACT(YEAR FROM created_at)::INT - 1), '/', EXTRACT(YEAR FROM created_at)::INT)
        END                                AS season,
        ROW_NUMBER() OVER (
          PARTITION BY club_id,
                       CASE
                         WHEN EXTRACT(MONTH FROM created_at) >= 7 THEN
                           CONCAT(EXTRACT(YEAR FROM created_at)::INT, '/', EXTRACT(YEAR FROM created_at)::INT + 1)
                         ELSE
                           CONCAT((EXTRACT(YEAR FROM created_at)::INT - 1), '/', EXTRACT(YEAR FROM created_at)::INT)
                       END
          ORDER BY created_at
        )                                  AS rn
      FROM users
      WHERE role    = 'coach'
        AND active  IS TRUE
        AND club_id IS NOT NULL
    ) u
    WHERE u.rn = 1
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
  c.id                         AS sr_id,
  c.ptso                       AS ptso,
  COALESCE(co.coaches,  0)     AS coaches,
  COALESCE(pa.parents,   0)    AS parents,
  COALESCE(sk.skiers,    0)    AS skiers,
  COALESCE(ct.primary_contact, '')       AS primary_contact,
  COALESCE(ct.primary_contact_email, '') AS primary_contact_email,
  'Active'                     AS status
FROM clubs c
JOIN seasons_union su
  ON su.club_id = c.id
LEFT JOIN coach_cte co
  ON co.club_id = c.id AND co.season = su.season
LEFT JOIN parent_cte pa
  ON pa.club_id = c.id AND pa.season = su.season
LEFT JOIN skier_cte sk
  ON sk.club_id = c.id AND sk.season = su.season
LEFT JOIN contact_cte ct
  ON ct.club_id = c.id AND ct.season = su.season
ORDER BY su.season, c.name;
"""

def create_view():
    """
    Execute the DROP + CREATE VIEW for vw_club_summary_by_season
    """
    with engine.begin() as conn:
        conn.execute(text(SQL))
        print("✅ Created or replaced view: vw_club_summary_by_season")

if __name__ == '__main__':
    create_view()
