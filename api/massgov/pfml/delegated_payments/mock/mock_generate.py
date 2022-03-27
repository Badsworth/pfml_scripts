#
# Generate mock files for payments along with supporting data in the database.
#

import massgov.pfml.db
import massgov.pfml.db.models.factories
import massgov.pfml.util.logging
from massgov.pfml.delegated_payments import delegated_config
from massgov.pfml.delegated_payments.mock import (
    fineos_extract_data,
    scenario_data_generator,
    scenarios,
)
from massgov.pfml.util.datetime import get_now_us_eastern


def main():
    massgov.pfml.util.logging.init("pub-payments-mock-generate")
    db_session = massgov.pfml.db.init(sync_lookups=True)
    massgov.pfml.db.models.factories.db_session = db_session

    config = scenario_data_generator.ScenarioDataConfig(
        scenarios_with_count=[
            scenario_data_generator.ScenarioNameWithCount(
                scenario_name=scenario_descriptor.scenario_name, count=1
            )
            for scenario_descriptor in scenarios.SCENARIO_DESCRIPTORS
        ]
    )
    scenario_dataset = scenario_data_generator.generate_scenario_dataset(
        config=config, db_session=db_session
    )

    s3_config = delegated_config.get_s3_config()
    fineos_data_export_path = s3_config.fineos_data_export_path

    # claimant extract
    fineos_extract_data.generate_claimant_data_files(
        scenario_dataset, fineos_data_export_path, get_now_us_eastern()
    )

    # payment extract
    fineos_extract_data.generate_payment_extract_files(
        scenario_dataset, fineos_data_export_path, get_now_us_eastern(), round=1
    )

    # VBI Taskreport Som extract
    fineos_extract_data.generate_vbi_taskreport_som_extract_files(
        scenario_dataset, fineos_data_export_path, get_now_us_eastern()
    )


if __name__ == "__main__":
    main()
