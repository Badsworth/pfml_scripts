from massgov.pfml.delegated_payments.mock.scenario_data_generator import (
    ScenarioDataConfig,
    ScenarioNameWithCount,
    generate_scenario_dataset,
)
from massgov.pfml.delegated_payments.mock.scenarios import SCENARIO_DESCRIPTORS


def test_e2e_pub_payments(test_db_session, initialize_factories_session):
    config = ScenarioDataConfig(
        scenarios_with_count=[
            ScenarioNameWithCount(scenario_name=scenario_descriptor.scenario_name, count=1)
            for scenario_descriptor in SCENARIO_DESCRIPTORS
        ]
    )
    scenario_dataset = generate_scenario_dataset(config=config)

    assert len(scenario_dataset) == len(SCENARIO_DESCRIPTORS)

    # TODO - Day 1 FINEOS Extract ECS Task

    # TODO - Day 2 PUB Processing ECS Task

    # TODO - Day 3 PUB Returns ECS Task
