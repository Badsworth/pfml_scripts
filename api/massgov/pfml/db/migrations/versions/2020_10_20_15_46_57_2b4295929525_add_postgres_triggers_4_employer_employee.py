"""Add postgres triggers.

Revision ID: 2b4295929525
Revises: aee3c2d906fb
Create Date: 2020-10-05 15:46:57.426024

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "2b4295929525"
down_revision = "aee3c2d906fb"
branch_labels = None
depends_on = None


def upgrade():
    # create triggers in Postgres
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto";')
    op.execute(
        "CREATE OR REPLACE FUNCTION audit_employee_func() RETURNS TRIGGER AS $$\
            DECLARE affected_record record;\
            BEGIN\
                IF (TG_OP = 'DELETE') THEN\
                    FOR affected_record IN SELECT * FROM old_table\
                        LOOP\
                            INSERT INTO employee_log(employee_log_id, employee_id, action, modified_at)\
                                VALUES (gen_random_uuid(), affected_record.employee_id,\
                                    TG_OP, current_timestamp);\
                        END loop;\
                ELSE\
                    FOR affected_record IN SELECT * FROM new_table\
                        LOOP\
                            INSERT INTO employee_log(employee_log_id, employee_id, action, modified_at)\
                                VALUES (gen_random_uuid(), affected_record.employee_id,\
                                    TG_OP, current_timestamp);\
                        END loop;\
                END IF;\
                RETURN NEW;\
            END;\
        $$ LANGUAGE plpgsql;"
    )
    op.execute(
        "CREATE TRIGGER after_employee_insert AFTER INSERT ON employee\
            REFERENCING NEW TABLE AS new_table\
            FOR EACH STATEMENT EXECUTE PROCEDURE audit_employee_func();"
    )
    op.execute(
        "CREATE TRIGGER after_employee_update AFTER UPDATE ON employee\
            REFERENCING OLD TABLE AS old_table NEW TABLE AS new_table\
            FOR EACH STATEMENT EXECUTE PROCEDURE audit_employee_func();"
    )
    op.execute(
        "CREATE TRIGGER after_employee_delete AFTER DELETE ON employee\
            REFERENCING OLD TABLE AS old_table\
            FOR EACH STATEMENT EXECUTE PROCEDURE audit_employee_func();"
    )

    op.execute(
        "CREATE OR REPLACE FUNCTION audit_employer_func() RETURNS TRIGGER AS $$\
            DECLARE affected_record record;\
            BEGIN\
                IF (TG_OP = 'DELETE') THEN\
                    FOR affected_record IN SELECT * FROM old_table\
                        LOOP\
                            INSERT INTO employer_log(employer_log_id, employer_id, action, modified_at)\
                                VALUES (gen_random_uuid(), affected_record.employer_id,\
                                    TG_OP, current_timestamp);\
                        END loop;\
                ELSE\
                    FOR affected_record IN SELECT * FROM new_table\
                        LOOP\
                            INSERT INTO employer_log(employer_log_id, employer_id, action, modified_at)\
                                VALUES (gen_random_uuid(), affected_record.employer_id,\
                                    TG_OP, current_timestamp);\
                        END loop;\
                END IF;\
                RETURN NEW;\
            END;\
        $$ LANGUAGE plpgsql;"
    )
    op.execute(
        "CREATE TRIGGER after_employer_insert AFTER INSERT ON employer\
            REFERENCING NEW TABLE AS new_table\
            FOR EACH STATEMENT EXECUTE PROCEDURE audit_employer_func();"
    )
    op.execute(
        "CREATE TRIGGER after_employer_update AFTER UPDATE ON employer\
            REFERENCING OLD TABLE AS old_table NEW TABLE AS new_table\
            FOR EACH STATEMENT EXECUTE PROCEDURE audit_employer_func();"
    )
    op.execute(
        "CREATE TRIGGER after_employer_delete AFTER DELETE ON employer\
            REFERENCING OLD TABLE AS old_table\
            FOR EACH STATEMENT EXECUTE PROCEDURE audit_employer_func();"
    )


def downgrade():
    # Drop triggers and functions
    op.execute("DROP TRIGGER IF EXISTS after_employee_insert on employee;")
    op.execute("DROP TRIGGER IF EXISTS after_employee_update on employee;")
    op.execute("DROP TRIGGER IF EXISTS after_employee_delete on employee;")
    op.execute("DROP FUNCTION IF EXISTS audit_employee_func CASCADE;")
    op.execute("DROP TRIGGER IF EXISTS after_employer_insert on employer;")
    op.execute("DROP TRIGGER IF EXISTS after_employer_update on employer;")
    op.execute("DROP TRIGGER IF EXISTS after_employer_delete on employer;")
    op.execute("DROP FUNCTION IF EXISTS audit_employer_func CASCADE;")
    op.execute('DROP EXTENSION IF EXISTS "pgcrypto";')
