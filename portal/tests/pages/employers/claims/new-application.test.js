import {
  MockEmployerClaimBuilder,
  renderWithAppLogic,
  simulateEvents,
  testHook,
} from "../../../test-utils";
import ConditionalContent from "../../../../src/components/ConditionalContent";
import NewApplication from "../../../../src/pages/employers/claims/new-application";
import { act } from "react-dom/test-utils";
import useAppLogic from "../../../../src/hooks/useAppLogic";

jest.mock("../../../../src/hooks/useAppLogic");

describe("NewApplication", () => {
  const claim = new MockEmployerClaimBuilder().completed().create();
  const query = { absence_id: "mock-absence-id" };
  let appLogic, wrapper;

  beforeEach(() => {
    testHook(() => {
      appLogic = useAppLogic();
    });
    appLogic.employers.claim = claim;

    act(() => {
      ({ wrapper } = renderWithAppLogic(NewApplication, {
        employerClaimAttrs: claim,
        props: {
          appLogic,
          query,
        },
      }));
    });
  });

  it("renders the page", () => {
    expect(wrapper).toMatchSnapshot();
  });

  describe("when user responds to question", () => {
    let changeRadioGroup, submitForm;

    beforeEach(() => {
      ({ changeRadioGroup, submitForm } = simulateEvents(wrapper));
      changeRadioGroup("hasReviewerVerified", "true");
      wrapper.update();
    });

    it("displays truth attestation content whether user selects yes or no", () => {
      expect(wrapper.find(ConditionalContent).props().visible).toBe(true);
    });

    it("navigates to claim review page when user selects yes and submits form", () => {
      submitForm();

      expect(appLogic.portalFlow.goToNextPage).toHaveBeenCalled();
    });

    it("navigates to confirmation page when user selects no and submits form", () => {
      changeRadioGroup("hasReviewerVerified", "false");

      submitForm();

      expect(appLogic.portalFlow.goToPageFor).toHaveBeenCalledWith(
        "CONFIRMATION",
        {},
        {
          absence_id: "mock-absence-id",
          due_date: "2020-10-10",
        }
      );
    });
  });
});
