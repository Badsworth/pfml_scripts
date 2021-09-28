-- email: james+prod@navapbc.com
-- keep: '16bc1539-0e2e-4c12-8911-e62a6da9b3d7'::uuid
-- delete: '7e5d9dfb-32b2-4e2a-bb70-de014961f594'::uuid
UPDATE
    "document"
SET
    user_id = '16bc1539-0e2e-4c12-8911-e62a6da9b3d7'::uuid
WHERE
    user_id IN ('7e5d9dfb-32b2-4e2a-bb70-de014961f594'::uuid);

UPDATE
    application
SET
    user_id = '16bc1539-0e2e-4c12-8911-e62a6da9b3d7'::uuid
WHERE
    user_id IN ('7e5d9dfb-32b2-4e2a-bb70-de014961f594'::uuid);

UPDATE
    link_user_leave_administrator
SET
    user_id = '16bc1539-0e2e-4c12-8911-e62a6da9b3d7'::uuid
WHERE
    user_id IN ('7e5d9dfb-32b2-4e2a-bb70-de014961f594'::uuid);

UPDATE
    managed_requirement
SET
    respondent_user_id = '16bc1539-0e2e-4c12-8911-e62a6da9b3d7'::uuid
WHERE
    respondent_user_id IN ('7e5d9dfb-32b2-4e2a-bb70-de014961f594'::uuid);

INSERT INTO
    link_user_role (user_id, role_id)
SELECT
    '16bc1539-0e2e-4c12-8911-e62a6da9b3d7'::uuid,
    lur.role_id
FROM
    link_user_role lur
WHERE lur.user_id IN ('7e5d9dfb-32b2-4e2a-bb70-de014961f594'::uuid) ON CONFLICT DO NOTHING;
    
DELETE FROM link_user_role lur
WHERE lur.user_id IN ('7e5d9dfb-32b2-4e2a-bb70-de014961f594'::uuid);

DELETE FROM "user"
WHERE user_id IN ('7e5d9dfb-32b2-4e2a-bb70-de014961f594'::uuid);

--
-- email: nicolebudzius@navapbc.com
-- keep: 'f16b76d5-5620-43f4-bbe5-b57baf1abd0f'::uuid
-- delete: '1041dd08-adf1-4389-8683-214ba86e757b'::uuid
UPDATE
    "document"
SET
    user_id = 'f16b76d5-5620-43f4-bbe5-b57baf1abd0f'::uuid
WHERE
    user_id IN ('1041dd08-adf1-4389-8683-214ba86e757b'::uuid);

UPDATE
    application
SET
    user_id = 'f16b76d5-5620-43f4-bbe5-b57baf1abd0f'::uuid
WHERE
    user_id IN ('1041dd08-adf1-4389-8683-214ba86e757b'::uuid);

UPDATE
    link_user_leave_administrator
SET
    user_id = 'f16b76d5-5620-43f4-bbe5-b57baf1abd0f'::uuid
WHERE
    user_id IN ('1041dd08-adf1-4389-8683-214ba86e757b'::uuid);

UPDATE
    managed_requirement
SET
    respondent_user_id = 'f16b76d5-5620-43f4-bbe5-b57baf1abd0f'::uuid
WHERE
    respondent_user_id IN ('1041dd08-adf1-4389-8683-214ba86e757b'::uuid);

INSERT INTO
    link_user_role (user_id, role_id)
SELECT
    'f16b76d5-5620-43f4-bbe5-b57baf1abd0f'::uuid,
    lur.role_id
FROM
    link_user_role lur
WHERE lur.user_id IN ('1041dd08-adf1-4389-8683-214ba86e757b'::uuid) ON CONFLICT DO NOTHING;
    
DELETE FROM link_user_role lur
WHERE lur.user_id IN ('1041dd08-adf1-4389-8683-214ba86e757b'::uuid);

DELETE FROM "user"
WHERE user_id IN ('1041dd08-adf1-4389-8683-214ba86e757b'::uuid);
--
-- email: adiaz@eliotchs.org
-- keep: '66967aee-9359-470d-94e0-29bb4b343f98'::uuid
-- delete: '11aed47f-194b-475b-a791-933afb1c6e08'::uuid
UPDATE
    "document"
SET
    user_id = '66967aee-9359-470d-94e0-29bb4b343f98'::uuid
WHERE
    user_id IN ('11aed47f-194b-475b-a791-933afb1c6e08'::uuid);

UPDATE
    application
SET
    user_id = '66967aee-9359-470d-94e0-29bb4b343f98'::uuid
WHERE
    user_id IN ('11aed47f-194b-475b-a791-933afb1c6e08'::uuid);

UPDATE
    link_user_leave_administrator
SET
    user_id = '66967aee-9359-470d-94e0-29bb4b343f98'::uuid
WHERE
    user_id IN ('11aed47f-194b-475b-a791-933afb1c6e08'::uuid);

UPDATE
    managed_requirement
SET
    respondent_user_id = '66967aee-9359-470d-94e0-29bb4b343f98'::uuid
WHERE
    respondent_user_id IN ('11aed47f-194b-475b-a791-933afb1c6e08'::uuid);

INSERT INTO
    link_user_role (user_id, role_id)
SELECT
    '66967aee-9359-470d-94e0-29bb4b343f98'::uuid,
    lur.role_id
FROM
    link_user_role lur
WHERE lur.user_id IN ('11aed47f-194b-475b-a791-933afb1c6e08'::uuid) ON CONFLICT DO NOTHING;
    
DELETE FROM link_user_role lur
WHERE lur.user_id IN ('11aed47f-194b-475b-a791-933afb1c6e08'::uuid);

DELETE FROM "user"
WHERE user_id IN ('11aed47f-194b-475b-a791-933afb1c6e08'::uuid);