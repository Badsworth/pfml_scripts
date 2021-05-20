import os
import sys

import massgov.pfml.payments.data_mart as data_mart
import massgov.pfml.util.logging as logging

logger = logging.get_logger(__name__)


def main():
    logging.init(__name__)
    logger.info("Starting rotate_data_mart_password task")

    data_mart_config = data_mart.DataMartConfig()

    data_mart_password_old = os.getenv("CTR_DATA_MART_PASSWORD_OLD")

    if not data_mart_password_old:
        logger.error("No old password is set or it is empty. Can't rotate.")
        sys.exit(1)

    data_mart_config_for_old_password = data_mart_config.copy()
    data_mart_config_for_old_password.password = data_mart_password_old

    logger.info("Connecting to Data Mart with old/current password")
    data_mart_engine_for_old_password = data_mart.init(data_mart_config_for_old_password)
    with data_mart_engine_for_old_password.connect() as data_mart_conn:
        data_mart.change_password_unsafe(
            data_mart_conn,
            username=data_mart_config.username,
            old_password=data_mart_password_old,
            new_password=data_mart_config.password,
        )
        logger.info("Successfully changed password in Data Mart")

    logger.info("Reconnecting with new password")
    data_mart_engine_for_new_password = data_mart.init(data_mart_config)
    with data_mart_engine_for_new_password.connect() as data_mart_conn:
        data_mart_conn.execute("SELECT 1")
        logger.info("Successfully connected with new password")
