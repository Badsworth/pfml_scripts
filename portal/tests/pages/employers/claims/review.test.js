import {
  MockEmployerClaimBuilder,
  renderWithAppLogic,
  testHook,
} from "../../../test-utils";
import Review from "../../../../src/pages/employers/claims/review";
import useAppLogic from "../../../../src/hooks/useAppLogic";

jest.mock("../../../../src/hooks/useAppLogic");

describe("Review", () => {
  const claim = new MockEmployerClaimBuilder().completed().create();
  const query = { absence_id: "NTN-111-ABS-01" };
  let appLogic, wrapper;

  beforeEach(() => {
    testHook(() => {
      appLogic = useAppLogic();
    });
    appLogic.employers.claim = claim;

    ({ wrapper } = renderWithAppLogic(Review, {
      employerClaimAttrs: claim,
      props: {
        appLogic,
        query,
      },
    }));
  });

  it("renders the page", () => {
    const components = [
      "EmployeeInformation",
      "EmployerBenefits",
      "EmployerDecision",
      "Feedback",
      "FraudReport",
      "LeaveDetails",
      "LeaveSchedule",
      "PreviousLeaves",
      "SupportingWorkDetails",
    ];

    components.forEach((component) => {
      expect(wrapper.find(component).exists()).toEqual(true);
    });
  });
});
