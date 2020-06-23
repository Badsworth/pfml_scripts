# Script to create a User for RDS.
#
# This relies on resources and outputs created in infra/api, which should
# be updated prior to running this script.
#
from massgov.pfml.db import create_engine


def create_user():
    engine = create_engine()
    with engine.connect() as con:
        user = con.execute("CREATE USER pfmlwrite; GRANT rds_iam TO pfmlwrite;")
        print(user)
