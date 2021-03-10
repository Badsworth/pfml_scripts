import massgov.pfml.db as db
import massgov.pfml.reductions.dua as dua
import massgov.pfml.reductions.reports.dua_payments_reports as dua_reports
import massgov.pfml.util.logging as logging

# import massgov.pfml.reductions.dia as dia
# import massgov.pfml.reductions.reports.dia_payments_reports as dia_reports

logger = logging.get_logger(__name__)


def main():
    logging.audit.init_security_logging()
    logging.init("Sending wage replacement payments")

    with db.session_scope(db.init(), close=True) as db_session:
        #   Expect create_wage_replacement_payments_list() to retrieve environment variables set via terraform.

        dua.create_report_new_dua_payments_to_dfml(db_session)
        dua_reports.send_dua_reductions_report(db_session)

        # dia.create_list_of_approved_claimants(db_session)
        # dia_reports.send_dia_reductions_report(db_session)
