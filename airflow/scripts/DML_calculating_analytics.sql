WITH per_month AS (
    SELECT vv.id, vv.work_format, vv.experience_from, vv.grade, vv.published_at::date AS pub_date
    FROM vacancies_vacancy vv 
    WHERE vv.published_at > CURRENT_DATE - 30
),
dynamic_per_day AS (
    SELECT pub_date, count(*) AS count 
    FROM per_month
    GROUP BY pub_date 
    ORDER BY pub_date DESC
),
by_grade AS (
    SELECT 
        CASE 
            WHEN grade IS NULL THEN 'Uncnown'
            WHEN grade = 'INT' THEN 'Intern'
            WHEN grade = 'JUN' THEN 'Junior'
            WHEN grade = 'MID' THEN 'Middle'
            WHEN grade = 'SEN' THEN 'Senior'
            WHEN grade = 'LED' THEN 'Lead'
            WHEN grade = 'DIR' THEN 'Director'
        END AS formatted_grade,
        count(*) AS count
    FROM per_month 
    GROUP BY formatted_grade
),
by_experience AS (
    SELECT COALESCE(experience_from::text, 'Uncnown') AS exp_level, count(*) AS count
    FROM per_month 
    GROUP BY exp_level
),
by_work_format AS (
    SELECT 
        CASE 
            WHEN work_format IS NULL THEN 'Uncnown'
            WHEN work_format = 'RMT' THEN 'Remote'
            WHEN work_format = 'OFF' THEN 'Office'
            WHEN work_format = 'HBR' THEN 'Hybrid'
        END AS formatted_format,
        count(*) AS count
    FROM per_month
    GROUP BY formatted_format 
),
by_skill AS (
    SELECT vs.name, count(*) AS count
    FROM vacancies_skill vs
    JOIN vacancies_vacancy_skills vvs ON vs.id = vvs.skill_id
    JOIN per_month pm ON vvs.vacancy_id = pm.id
    GROUP BY vs.name
    ORDER BY count DESC
    LIMIT 10
)
INSERT INTO analytics_global_snapshot (
    total_vacancies,
    top_skills,
    work_formats,
    experience_funnel,
    grades_distribution,
    vacancies_per_day,
    created_at,
    updated_at
)
SELECT
    (SELECT count(*) FROM per_month) AS total_vacancies,
    COALESCE(
        (SELECT json_agg(json_build_object('skill', name, 'count', count)) FROM by_skill), 
        '[]'::json
    ) AS top_skills,
    COALESCE(
        (SELECT json_object_agg(formatted_format, count) FROM by_work_format), 
        '{}'::json
    ) AS work_formats,
    COALESCE(
        (SELECT json_object_agg(exp_level, count) FROM by_experience), 
        '{}'::json
    ) AS experience_funnel,
    COALESCE(
        (SELECT json_object_agg(formatted_grade, count) FROM by_grade), 
        '{}'::json
    ) AS grades_distribution,
    COALESCE(
        (SELECT json_agg(json_build_object('day', to_char(pub_date, 'DD-MM'), 'count', count)) FROM dynamic_per_day), 
        '[]'::json
    ) AS vacancies_per_day,
    CURRENT_TIMESTAMP AS created_at,
    CURRENT_TIMESTAMP AS updated_at;