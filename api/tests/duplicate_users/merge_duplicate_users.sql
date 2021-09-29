WITH duplicate_user_emails AS (
    SELECT
        "user".email_address,
        MIN("user".created_at) AS oldest_created_at
    FROM
        "user"
    GROUP BY
        "user".email_address
    HAVING
        count("user".user_id) > 1
),
duplicated_users AS (
    SELECT
        "user".created_at,
        "user".updated_at,
        "user".user_id,
        "user".sub_id,
        "user".email_address,
        "user".consented_to_data_sharing
    FROM
        "user"
    WHERE
        "user".email_address IN (
            SELECT
                email_address
            FROM
                duplicate_user_emails
        )
),
oldest_created_users AS (
    SELECT
        u.created_at,
        u.updated_at,
        u.user_id,
        u.sub_id,
        u.email_address,
        u.consented_to_data_sharing
    FROM
        duplicate_user_emails u_dup
        INNER JOIN "user" u ON u.email_address = u_dup.email_address
        AND u_dup.oldest_created_at = u.created_at
),
duplicated_users_to_remove AS (
    SELECT
        luu.user_id AS user_id_to_keep,
        u.email_address,
        u.user_id,
        u.created_at,
        u.updated_at,
        u.sub_id,
        u.consented_to_data_sharing
    FROM
        duplicate_user_emails u_dup
        INNER JOIN "user" u ON u.email_address = u_dup.email_address
        INNER JOIN oldest_created_users luu ON luu.email_address = u.email_address
    WHERE
        u.user_id NOT IN (
            SELECT
                user_id
            FROM
                oldest_created_users
        )
),
merged_documents AS (
    UPDATE
        "document"
    SET
        user_id = duu.user_id_to_keep
    FROM
        "document" doc
        INNER JOIN duplicated_users_to_remove duu ON duu.user_id = doc.user_id
),
merged_applications AS (
    UPDATE
        application
    SET
        user_id = duu.user_id_to_keep
    FROM
        application a
        INNER JOIN duplicated_users_to_remove duu ON duu.user_id = a.user_id
),
merged_user_leave_administrators AS (
    UPDATE
        link_user_leave_administrator
    SET
        user_id = duu.user_id_to_keep::uuid
    FROM
        link_user_leave_administrator lula
        INNER JOIN duplicated_users_to_remove duu ON duu.user_id = lula.user_id
),
merged_requirements AS (
    UPDATE
        managed_requirement
    SET
        respondent_user_id = duu.user_id_to_keep
    FROM
        managed_requirement mr
        INNER JOIN duplicated_users_to_remove duu ON duu.user_id = mr.respondent_user_id 
),
merged_user_roles AS (
    INSERT INTO
        link_user_role (user_id, role_id)
    SELECT
        duu.user_id_to_keep,
        lur.role_id
    FROM
        link_user_role lur
    INNER JOIN duplicated_users_to_remove duu ON duu.user_id = lur.user_id
    WHERE
        lur.user_id IN (
            SELECT
                duu.user_id
            FROM
                duplicated_users_to_remove duu
        ) ON CONFLICT (user_id, role_id) DO NOTHING
),
deleted_user_roles AS (
    DELETE FROM
        link_user_role lur USING duplicated_users_to_remove
    WHERE
        lur.user_id IN (
            SELECT
                duu.user_id
            FROM
                duplicated_users_to_remove duu
        ) 
),
deleted_users AS (
    DELETE FROM
        "user" uu USING duplicated_users_to_remove
    WHERE
        uu.user_id IN (
            SELECT
                duu.user_id
            FROM
                duplicated_users_to_remove duu
        ) 
)
SELECT
    *
FROM
    oldest_created_users;