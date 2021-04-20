import {
  MockEmployerClaimBuilder,
  renderWithAppLogic,
  simulateEvents,
  testHook,
} from "../../../test-utils";
import ConditionalContent from "../../../../src/components/ConditionalContent";
import NewApplication from "../../../../src/pages/employers/applications/new-application";
import { act } from "react-dom/test-utils";
import { clone } from "lodash";
import useAppLogic from "../../../../src/hooks/useAppLogic";

jest.mock("../../../../src/hooks/useAppLogic");

describe("NewApplication", () => {
  const claim = new MockEmployerClaimBuilder()
    .completed()
    .reviewable(true)
    .create();
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

  it("shows organization name if employer_dba is populated", () => {
    expect(wrapper.exists('StatusRow[label="Organization"]')).toBe(true);
  });

  it("hides organization name if 'employer_dba' is falsy", () => {
    const employerClaimAttrs = clone(claim);
    employerClaimAttrs.employer_dba = undefined;

    act(() => {
      testHook(() => {
        appLogic = useAppLogic();
      });
      appLogic.employers.claim = employerClaimAttrs;

      ({ wrapper } = renderWithAppLogic(NewApplication, {
        employerClaimAttrs,
        props: {
          appLogic,
          query,
        },
      }));
    });

    expect(wrapper.exists('StatusRow[label="Organization"]')).toBe(false);
  });

  it("does not redirect if is_reviewable is true", () => {
    expect(appLogic.portalFlow.goToPageFor).not.toHaveBeenCalled();
  });

  it("redirects to the status page if is_reviewable is false", () => {
    ({ appLogic } = renderWithAppLogic(NewApplication, {
      employerClaimAttrs: new MockEmployerClaimBuilder()
        .completed()
        .reviewable(false)
        .create(),
      props: {
        query,
      },
    }));

    expect(appLogic.portalFlow.goToPageFor).toHaveBeenCalledWith(
      "CLAIM_NOT_REVIEWABLE",
      {},
      {
        absence_id: "mock-absence-id",
      },
      { redirect: true }
    );
  });

  describe("when user responds to question", () => {
    let changeRadioGroup, submitForm;

    beforeEach(() => {
      ({ changeRadioGroup, submitForm } = simulateEvents(wrapper));
      changeRadioGroup("hasReviewerVerified", "true");
      wrapper.update();
    });

    it("displays conditional content with truth attestation and button when user selects yes", () => {
      expect(wrapper.find(ConditionalContent).props().visible).toBe(true);
      expect(wrapper.find(ConditionalContent).children()).toHaveLength(4);
    });

    it("displays conditional content with button only when user selects no", () => {
      changeRadioGroup("hasReviewerVerified", "false");

      expect(wrapper.find(ConditionalContent).props().visible).toBe(true);
      expect(wrapper.find(ConditionalContent).children()).toHaveLength(1);
    });

    it("navigates to claim review page when user selects yes and submits form", async () => {
      await submitForm();

      expect(appLogic.portalFlow.goToNextPage).toHaveBeenCalled();
    });

    it("navigates to confirmation page when user selects no and submits form", async () => {
      changeRadioGroup("hasReviewerVerified", "false");

      await submitForm();

      expect(appLogic.portalFlow.goToPageFor).toHaveBeenCalledWith(
        "CONFIRMATION",
        {},
        {
          absence_id: "mock-absence-id",
        }
      );
    });
  });
});
