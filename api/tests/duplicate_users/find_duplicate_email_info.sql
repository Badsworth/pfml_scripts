SELECT
    "user".email_address,
    count(application.application_id) AS application_count,
    count(document.document_id) AS document_count,
    count(link_user_leave_administrator.user_leave_administrator_id) AS user_leave_administrator_count,
    count(managed_requirement.managed_requirement_id) AS managed_requirement_count
FROM
    "user"
    FULL OUTER JOIN application ON application.user_id = "user".user_id
    FULL OUTER JOIN document ON document.user_id = "user".user_id
    FULL OUTER JOIN link_user_leave_administrator ON link_user_leave_administrator.user_id = "user".user_id
    FULL OUTER JOIN managed_requirement ON managed_requirement.respondent_user_id = "user".user_id
GROUP BY
    "user".email_address
HAVING
    count("user".email_address) > 1;