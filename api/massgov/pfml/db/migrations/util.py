from alembic import op

def op_copy_trigger(table_name: str, old_column: str, new_column: str) -> None:
    """ alembic operation to support column renames.
        this operation does the following:

        1. Creates a trigger that copies new values from OLD_COLUMN to NEW_COLUMN and vice versa, keeping them in sync.
        2. Does a one-off UPDATE to copy all the existing values in OLD_COLUMN to NEW_COLUMN.

        Use this within an autogenerated migration, after the new column has been created.

        example for nullable columns:
    
          op.add_column("user", sa.Column("sub_id", sa.Text(), nullable=True))
          op.create_index(op.f("ix_user_sub_id"), "user", ["sub_id"], unique=True)
          migration_utils.op_copy_trigger("user", "active_directory_id", "sub_id")

        example for non-nullable columns:

          op.add_column("user", sa.Column("sub_id", sa.Text(), nullable=True))
          migration_utils.op_copy_trigger("user", "active_directory_id", "sub_id")
          op.alter_column("user", "sub_id", existing_type=sa.Text(), nullable=False)
    """
    fn_name = f"copy_{table_name}_{old_column}_{new_column}"

    op.execute(
        f"""
        CREATE OR REPLACE FUNCTION {fn_name}() RETURNS TRIGGER AS $func$
        BEGIN
            IF NEW.{new_column} IS NULL THEN
                NEW.{new_column} := NEW.{old_column};
            ELSIF NEW.{old_column} IS NULL THEN
                NEW.{old_column} := NEW.{new_column};
            END IF;
            RETURN NEW;
        END
        $func$ LANGUAGE plpgsql;

        CREATE TRIGGER {fn_name}
        BEFORE INSERT OR UPDATE ON "{table_name}"
        FOR EACH ROW
        WHEN (NEW.{new_column} IS NULL OR NEW.{old_column} IS NULL)
        EXECUTE FUNCTION {fn_name}();

        UPDATE "{table_name}"
        SET {new_column} = {old_column};
        """
    )


def op_copy_trigger_drop(table_name: str, old_column: str, new_column: str) -> None:
    """ alembic operation to drop resources created from op_copy_trigger.
    fn_name = f"copy_{table_name}_{old_column}_{new_column}"
    """    

    op.execute(
        f"""
        DROP TRIGGER IF EXISTS {fn_name} ON "{table_name}";
        DROP FUNCTION IF EXISTS {fn_name}();
        """
    )
