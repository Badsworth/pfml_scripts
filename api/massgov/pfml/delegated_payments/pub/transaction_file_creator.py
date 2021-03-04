import massgov.pfml.db as db


class TransactionFileCreator:
    db_session: db.Session
    # check_file: Optional[CheckFile]
    # ach_file: Optional[AchFile]

    def __init__(self, db_session: db.Session):
        self.db_session = db_session

    def create_check_file(self) -> None:
        # TODO: After PUB-30 is complete, call the function that adds check payments to an ACH
        # transaction file.
        #
        # self.check_file = _create_check_file()

        return None

    def add_prenotes(self) -> None:
        # TODO: After PUB-42 is complete, call the function that adds pre-notes to an ACH
        # transaction file.
        #
        # self._create_ach_file_if_not_exists()
        # self.ach_file.add_prenotes()

        return None

    def add_ach_payments(self) -> None:
        # TODO: After PUB-42 is complete, call the function that adds payments to an ACH
        # transaction file.
        #
        # self._create_ach_file_if_not_exists()
        # self.ach_file.add_payments()

        return None

    # Do not send files immediately after creating them so that we can manually inspect the files
    # before sending them to PUB.
    def send_payment_files(self) -> None:
        # TODO: If we've created a check and/or ACH file send them to PUB's S3 bucket, FTP server,
        # or whatever else.
        #
        # if self.check_file is not None:
        #     _send_to_pub(self.check_file)
        #
        # if self.ach_file is not None:
        #     _send_to_pub(self.ach_file)

        return None

    # Pre-notes and ACH payments are sent to PUB in the same transaction file. We add them to that
    # file separately (so that we can create pre-note only files and payment only files) so we
    # separate the creation of the ACH transaction file from the process that adds records to it.
    def _create_ach_file_if_not_exists(self) -> None:
        # TODO: After PUB-42 is complete, call the function that creates an ACH transaction file.
        #
        # if self.ach_file is None:
        #     self.ach_file = _create_ach_file()

        return None
