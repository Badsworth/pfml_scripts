#
# Regenerate payments files - VCC specific methods.
#

import os

import massgov.pfml.payments.vcc

from . import base


class RegeneratorVCC(base.ReferenceFileRegenerator):
    def update_entries(self):
        # TODO: create a state log entry for each payment/employee to move them to <state TBD>
        pass

    def create_new_file(self):
        # get list of employees (vendors) and update their state
        employees = [link.employee for link in self.reference_file.employees]
        # TODO: determine batch count to use here
        # TODO: we shouldn't use the same directory_name, but a new name with the new batch count
        # When #2364 is merged it will handle this part
        destination_path = f"{self.outbound_path}/ready/{self.directory_name}/"
        if not destination_path.startswith("s3:"):
            os.makedirs(destination_path, exist_ok=True)
        massgov.pfml.payments.vcc.build_vcc_files(employees, destination_path, 99)

    def send_bie(self):
        # TODO: generate and send the appropriate BIE (API-783 for GAX and API-975 for VCC)
        pass
