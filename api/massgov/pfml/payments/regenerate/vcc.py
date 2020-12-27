#
# Regenerate payments files - VCC specific methods.
#

import massgov.pfml.api.util.state_log_util
import massgov.pfml.payments.vcc
from massgov.pfml.db.models.employees import LatestStateLog, State, StateLog

from . import base


class RegeneratorVCC(base.ReferenceFileRegenerator):
    def update_entries(self):
        """Create a state log entry for each payment/employee to move them to state ADD_TO_VCC"""
        employees = [link.employee for link in self.reference_file.employees]
        for employee in employees:
            state_log = (
                self.db_session.query(StateLog)
                .join(LatestStateLog)
                .filter(LatestStateLog.employee == employee)
                .one()
            )
            # TODO how should this use start_state? Or end_state if present?
            new_state_log = massgov.pfml.api.util.state_log_util.create_state_log(
                state_log.start_state, employee, self.db_session, False
            )
            massgov.pfml.api.util.state_log_util.finish_state_log(
                new_state_log, State.ADD_TO_VCC, {}, self.db_session, False
            )
        self.db_session.commit()

    def create_new_file(self):
        """Build new VCC files."""
        massgov.pfml.payments.vcc.build_vcc_files(self.db_session, self.outbound_path)

    def send_bie(self):
        # TODO: generate and send the appropriate BIE (API-783 for GAX and API-975 for VCC)
        pass
