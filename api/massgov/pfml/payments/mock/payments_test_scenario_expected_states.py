import enum
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Tuple

from massgov.pfml.api.util.state_log_util import AssociatedClass
from massgov.pfml.db.models.employees import LkState, State
from massgov.pfml.payments.mock.payments_test_scenario_generator import ScenarioName


class TestStage(Enum):
    FINEOS_PROCESS_VENDOR_FILES = enum.auto()
    CTR_EXPORT_VCC = enum.auto()
    FINEOS_PROCESS_PAYMENT_FILES = enum.auto()
    CTR_EXPORT_GAX = enum.auto()
    CTR_PROCESS_OUTBOUND_STATUS_PAYMENT_RETURNS = enum.auto()
    FINEOS_PEI_WRITEBACK = enum.auto()


@dataclass
class ScenarioExpectedState:
    test_stage: TestStage
    associated_class: AssociatedClass
    scenario_name: ScenarioName
    expected_state: LkState

    def __repr__(self):
        return f"[{self.test_stage} - {self.associated_class.value} - {self.scenario_name.value} - {self.expected_state.state_description} ({self.expected_state.state_id})]"


def generate_expected_state_for_scenarios(
    test_stage: TestStage,
    associated_class: AssociatedClass,
    expected_state: LkState,
    scenario_names: List[ScenarioName],
) -> List[ScenarioExpectedState]:
    scenario_expected_states = []
    for scenario_name in scenario_names:
        scenario_expected_state = ScenarioExpectedState(
            test_stage, associated_class, scenario_name, expected_state
        )
        scenario_expected_states.append(scenario_expected_state)
    return scenario_expected_states


SCENARIO_EXPECTED_STATES: List[ScenarioExpectedState] = []

# ============================================================
# Stage: FINEOS_PROCESS_VENDOR_FILES (Day 1)
# ============================================================

# Employee States

SCENARIO_EXPECTED_STATES.extend(
    generate_expected_state_for_scenarios(
        TestStage.FINEOS_PROCESS_VENDOR_FILES,
        AssociatedClass.EMPLOYEE,
        State.IDENTIFY_MMARS_STATUS,
        [
            ScenarioName.SCENARIO_A,
            ScenarioName.SCENARIO_B,
            ScenarioName.SCENARIO_C,
            ScenarioName.SCENARIO_D,
            ScenarioName.SCENARIO_M,
            ScenarioName.SCENARIO_N,
            ScenarioName.SCENARIO_O,
            ScenarioName.SCENARIO_P,
            ScenarioName.SCENARIO_Q,
            ScenarioName.SCENARIO_R,
            ScenarioName.SCENARIO_S,
            ScenarioName.SCENARIO_U,
            ScenarioName.SCENARIO_V,
            ScenarioName.SCENARIO_W,
            ScenarioName.SCENARIO_X,
            ScenarioName.SCENARIO_Y,
            ScenarioName.SCENARIO_Z,
        ],
    )
)

SCENARIO_EXPECTED_STATES.extend(
    generate_expected_state_for_scenarios(
        TestStage.FINEOS_PROCESS_VENDOR_FILES,
        AssociatedClass.EMPLOYEE,
        State.EFT_REQUEST_RECEIVED,
        [
            ScenarioName.SCENARIO_C,
            ScenarioName.SCENARIO_D,
            ScenarioName.SCENARIO_Q,
            ScenarioName.SCENARIO_W,
            ScenarioName.SCENARIO_X,
            ScenarioName.SCENARIO_Y,
        ],
    )
)

SCENARIO_EXPECTED_STATES.extend(
    generate_expected_state_for_scenarios(
        TestStage.FINEOS_PROCESS_VENDOR_FILES,
        AssociatedClass.EMPLOYEE,
        State.VENDOR_EXPORT_ERROR_REPORT_SENT,
        [
            ScenarioName.SCENARIO_G,
            ScenarioName.SCENARIO_H,
            ScenarioName.SCENARIO_I,
            ScenarioName.SCENARIO_J,
        ],
    )
)

# ============================================================
# Stage: CTR_EXPORT_VCC (Day 1)
# ============================================================

# Employee States

SCENARIO_EXPECTED_STATES.extend(
    generate_expected_state_for_scenarios(
        TestStage.CTR_EXPORT_VCC,
        AssociatedClass.EMPLOYEE,
        State.VCC_SENT,
        [
            ScenarioName.SCENARIO_A,
            ScenarioName.SCENARIO_B,
            ScenarioName.SCENARIO_C,
            ScenarioName.SCENARIO_D,
            ScenarioName.SCENARIO_M,
            ScenarioName.SCENARIO_O,
            ScenarioName.SCENARIO_P,
            ScenarioName.SCENARIO_Q,
            ScenarioName.SCENARIO_R,
            ScenarioName.SCENARIO_S,
            ScenarioName.SCENARIO_X,
            ScenarioName.SCENARIO_Y,
            ScenarioName.SCENARIO_Z,
        ],
    )
)

# TODO enable once this state workflow is available
# SCENARIO_EXPECTED_STATES.extend(
#     generate_expected_state_for_scenarios(
#         TestStage.CTR_EXPORT_VCC,
#         AssociatedClass.EMPLOYEE,
#         State.EFT_PENDING,
#         [
#             ScenarioName.SCENARIO_C,
#             ScenarioName.SCENARIO_D,
#             ScenarioName.SCENARIO_Q,
#             ScenarioName.SCENARIO_W,
#             ScenarioName.SCENARIO_X,
#             ScenarioName.SCENARIO_Y,
#         ],
#     )
# )

SCENARIO_EXPECTED_STATES.extend(
    generate_expected_state_for_scenarios(
        TestStage.CTR_EXPORT_VCC,
        AssociatedClass.EMPLOYEE,
        State.MMARS_STATUS_CONFIRMED,
        [ScenarioName.SCENARIO_N,],
    )
)

SCENARIO_EXPECTED_STATES.extend(
    generate_expected_state_for_scenarios(
        TestStage.CTR_EXPORT_VCC,
        AssociatedClass.EMPLOYEE,
        State.VCM_REPORT_SENT,
        [ScenarioName.SCENARIO_U, ScenarioName.SCENARIO_V, ScenarioName.SCENARIO_W,],
    )
)

# ============================================================
# Stage: FINEOS_PROCESS_PAYMENT_FILES (Day 2)
# ============================================================

# Employee States - Remain unchanged from above

# Payment States
SCENARIO_EXPECTED_STATES.extend(
    generate_expected_state_for_scenarios(
        TestStage.FINEOS_PROCESS_PAYMENT_FILES,
        AssociatedClass.PAYMENT,
        State.CONFIRM_VENDOR_STATUS_IN_MMARS,
        [
            ScenarioName.SCENARIO_A,
            ScenarioName.SCENARIO_B,
            ScenarioName.SCENARIO_C,
            ScenarioName.SCENARIO_D,
            ScenarioName.SCENARIO_Z,
        ],
    )
)

SCENARIO_EXPECTED_STATES.extend(
    generate_expected_state_for_scenarios(
        TestStage.FINEOS_PROCESS_PAYMENT_FILES,
        AssociatedClass.PAYMENT,
        State.PAYMENT_EXPORT_ERROR_REPORT_SENT,
        [
            ScenarioName.SCENARIO_O,
            ScenarioName.SCENARIO_P,
            ScenarioName.SCENARIO_Q,
            ScenarioName.SCENARIO_R,
            ScenarioName.SCENARIO_S,
        ],
    )
)

# ============================================================
# Stage: CTR_EXPORT_GAX (Day 2)
# ============================================================

# Employee States

SCENARIO_EXPECTED_STATES.extend(
    generate_expected_state_for_scenarios(
        TestStage.CTR_EXPORT_GAX,
        AssociatedClass.EMPLOYEE,
        State.MMARS_STATUS_CONFIRMED,
        [
            ScenarioName.SCENARIO_A,
            ScenarioName.SCENARIO_B,
            ScenarioName.SCENARIO_C,
            ScenarioName.SCENARIO_D,
            ScenarioName.SCENARIO_O,
            ScenarioName.SCENARIO_P,
            ScenarioName.SCENARIO_Q,
            ScenarioName.SCENARIO_R,
            ScenarioName.SCENARIO_S,
            ScenarioName.SCENARIO_X,
            ScenarioName.SCENARIO_Y,
            ScenarioName.SCENARIO_Z,
        ],
    )
)

# TODO enable once this state workflow is available
# SCENARIO_EXPECTED_STATES.extend(
#     generate_expected_state_for_scenarios(
#         TestStage.CTR_EXPORT_GAX,
#         AssociatedClass.EMPLOYEE,
#         State.EFT_PENDING,
#         [
#             ScenarioName.SCENARIO_C,
#             ScenarioName.SCENARIO_D,
#             ScenarioName.SCENARIO_Q,
#         ],
#     )
# )

SCENARIO_EXPECTED_STATES.extend(
    generate_expected_state_for_scenarios(
        TestStage.CTR_EXPORT_GAX,
        AssociatedClass.EMPLOYEE,
        State.EFT_ERROR_REPORT_SENT,
        [ScenarioName.SCENARIO_X,],
    )
)

SCENARIO_EXPECTED_STATES.extend(
    generate_expected_state_for_scenarios(
        TestStage.CTR_EXPORT_GAX,
        AssociatedClass.EMPLOYEE,
        State.EFT_ELIGIBLE,
        [ScenarioName.SCENARIO_Y,],
    )
)

# TODO enable once this state workflow is available
# SCENARIO_EXPECTED_STATES.extend(
#     generate_expected_state_for_scenarios(
#         TestStage.CTR_EXPORT_GAX,
#         AssociatedClass.EMPLOYEE,
#         State.VCC_ERROR_REPORT_SENT,
#         [
#             ScenarioName.SCENARIO_M,
#         ],
#     )
# )

# Payment States

SCENARIO_EXPECTED_STATES.extend(
    generate_expected_state_for_scenarios(
        TestStage.CTR_EXPORT_GAX,
        AssociatedClass.PAYMENT,
        State.GAX_SENT,
        [
            ScenarioName.SCENARIO_A,
            ScenarioName.SCENARIO_B,
            ScenarioName.SCENARIO_C,
            ScenarioName.SCENARIO_D,
            ScenarioName.SCENARIO_Z,
        ],
    )
)

SCENARIO_EXPECTED_STATES.extend(
    generate_expected_state_for_scenarios(
        TestStage.CTR_EXPORT_GAX,
        AssociatedClass.PAYMENT,
        State.PAYMENT_EXPORT_ERROR_REPORT_SENT,
        [ScenarioName.SCENARIO_R, ScenarioName.SCENARIO_S,],
    )
)

# ============================================================
# Stage: CTR_PROCESS_OUTBOUND_STATUS_PAYMENT_RETURNS (Day 3)
# ============================================================

# Employee States - Remain unchanged from above

# Payment States

SCENARIO_EXPECTED_STATES.extend(
    generate_expected_state_for_scenarios(
        TestStage.CTR_PROCESS_OUTBOUND_STATUS_PAYMENT_RETURNS,
        AssociatedClass.PAYMENT,
        State.SEND_PAYMENT_DETAILS_TO_FINEOS,
        [
            ScenarioName.SCENARIO_A,
            ScenarioName.SCENARIO_B,
            ScenarioName.SCENARIO_C,
            ScenarioName.SCENARIO_D,
        ],
    )
)

SCENARIO_EXPECTED_STATES.extend(
    generate_expected_state_for_scenarios(
        TestStage.CTR_PROCESS_OUTBOUND_STATUS_PAYMENT_RETURNS,
        AssociatedClass.PAYMENT,
        State.GAX_ERROR_REPORT_SENT,
        [ScenarioName.SCENARIO_Z,],
    )
)

# ============================================================
# Stage: FINEOS_PEI_WRITEBACK (Day 4)
# ============================================================

# Employee States - Remain unchanged from above

# Payment States

SCENARIO_EXPECTED_STATES.extend(
    generate_expected_state_for_scenarios(
        TestStage.FINEOS_PEI_WRITEBACK,
        AssociatedClass.PAYMENT,
        State.PAYMENT_COMPLETE,
        [
            ScenarioName.SCENARIO_A,
            ScenarioName.SCENARIO_B,
            ScenarioName.SCENARIO_C,
            ScenarioName.SCENARIO_D,
        ],
    )
)

SCENARIO_EXPECTED_STATES.extend(
    generate_expected_state_for_scenarios(
        TestStage.FINEOS_PEI_WRITEBACK,
        AssociatedClass.PAYMENT,
        State.GAX_ERROR_REPORT_SENT,
        [ScenarioName.SCENARIO_Z,],
    )
)


def get_scenario_expected_states(
    test_stage: TestStage, associated_class: AssociatedClass
) -> Tuple[List[ScenarioExpectedState], Dict[ScenarioName, List[ScenarioExpectedState]]]:
    expected_states = [
        scenario_expected_state
        for scenario_expected_state in SCENARIO_EXPECTED_STATES
        if scenario_expected_state.test_stage == test_stage
        and scenario_expected_state.associated_class.value == associated_class.value
    ]

    expected_states_by_scneario_name = {}
    for expected_state in expected_states:
        scenario_name = expected_state.scenario_name
        if expected_states_by_scneario_name.get(scenario_name) is None:
            expected_states_by_scneario_name[scenario_name] = []

        expected_states_by_scneario_name[scenario_name].append(expected_state)

    return expected_states, expected_states_by_scneario_name
