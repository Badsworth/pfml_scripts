/* eslint-disable import/first */
jest.mock("../../../src/hooks/useAppLogic");

import Status, { LeaveDetails } from "../../../src/pages/applications/status";
import { renderWithAppLogic, testHook } from "../../test-utils";
import ClaimDetail from "../../../src/models/ClaimDetail";
import LeaveReason from "../../../src/models/LeaveReason";
import routes from "../../../src/routes";
import useAppLogic from "../../../src/hooks/useAppLogic";

const CLAIM_DETAIL = new ClaimDetail({
  application_id: "application-id",
  employer: {
    employer_fein: "employer-fein",
  },
  absence_periods: [
    {
      period_type: "Reduced",
      absence_period_start_date: "2021-06-01",
      absence_period_end_date: "2021-06-08",
      request_decision: "Approved",
      fineos_leave_request_id: "PL-14432-0000002026",
      reason: LeaveReason.medical,
    },
    {
      period_type: "Continuous",
      absence_period_start_date: "2021-07-01",
      absence_period_end_date: "2021-07-08",
      request_decision: "Pending",
      fineos_leave_request_id: "PL-14432-0000002326",
      reason: LeaveReason.medical,
    },
    {
      period_type: "Reduced",
      absence_period_start_date: "2021-08-01",
      absence_period_end_date: "2021-08-08",
      request_decision: "Denied",
      fineos_leave_request_id: "PL-14434-0000002026",
      reason: LeaveReason.pregnancy,
    },
    {
      period_type: "Continuous",
      absence_period_start_date: "2021-08-01",
      absence_period_end_date: "2021-08-08",
      request_decision: "Withdrawn",
      fineos_leave_request_id: "PL-14434-0000002326",
      reason: LeaveReason.bonding,
    },
  ],
});

describe("status page", () => {
  beforeEach(() => {
    process.env.featureFlags = {
      claimantShowStatusPage: true,
    };
  });

  const setup = ({
    claimDetail = CLAIM_DETAIL,
    docList,
    isLoadingClaimDetail = false,
    render = "shallow",
  } = {}) => {
    let appLogic;

    testHook(() => {
      appLogic = useAppLogic();
      appLogic.claims.claimDetail = claimDetail;
      appLogic.claims.isLoadingClaimDetail = isLoadingClaimDetail;
    });

    const { wrapper } = renderWithAppLogic(Status, {
      diveLevels: 0,
      props: {
        appLogic,
        docList,
        query: {
          absence_case_id: "absence-case-id",
        },
      },
      render,
    });

    return {
      appLogic,
      wrapper,
    };
  };

  it("displays an error if feature flag is disabled", () => {
    process.env.featureFlags = {
      claimantShowStatusPage: false,
    };
    const { wrapper } = setup();
    expect(wrapper).toMatchSnapshot();
  });

  it("shows a spinner if there is no claim detail", () => {
    const { wrapper } = setup({
      claimDetail: undefined,
      isLoadingClaimDetail: true,
      render: "mount",
    });
    expect(wrapper.find("Spinner").exists()).toBe(true);
    expect(wrapper).toMatchSnapshot();
  });

  it("fetches claim detail on if none is loaded", () => {
    const { appLogic } = setup({
      claimDetail: undefined,
      isLoadingClaimDetail: true,
      render: "mount",
    });
    expect(appLogic.claims.loadClaimDetail).toHaveBeenCalledWith(
      "absence-case-id"
    );
  });

  it("renders the page", () => {
    const { wrapper } = setup();
    expect(wrapper).toMatchSnapshot();
  });

  describe("info alert", () => {
    it("displays if claimant has bonding but not pregnancy claims", () => {
      const claimWithoutPregnancy = new ClaimDetail({
        ...CLAIM_DETAIL,
        absence_periods: [
          { reason: LeaveReason.bonding },
          { reason: LeaveReason.care },
        ],
      });

      const { wrapper } = setup({ claimDetail: claimWithoutPregnancy });

      const infoAlertComponent = wrapper.find({ "data-test": "info-alert" });
      expect(infoAlertComponent.exists()).toBe(true);
      expect(infoAlertComponent.dive()).toMatchSnapshot();
      expect(infoAlertComponent.find("Trans").dive()).toMatchSnapshot();
    });

    it("displays if claimant has pregnancy but not bonding claims", () => {
      const claimsWithoutBonding = new ClaimDetail({
        ...CLAIM_DETAIL,
        absence_periods: [
          { reason: LeaveReason.pregnancy },
          { reason: LeaveReason.care },
        ],
      });

      const { wrapper } = setup({ claimDetail: claimsWithoutBonding });

      const infoAlertComponent = wrapper.find({ "data-test": "info-alert" });
      expect(infoAlertComponent.exists()).toBe(true);
      expect(infoAlertComponent.dive()).toMatchSnapshot();
      expect(infoAlertComponent.find("Trans").dive()).toMatchSnapshot();
    });

    it("does not display if claimant has bonding AND pregnancy claims", () => {
      const claimsWithBondingAndPregnancy = new ClaimDetail({
        ...CLAIM_DETAIL,
        absence_periods: [
          { reason: LeaveReason.bonding },
          { reason: LeaveReason.pregnancy },
        ],
      });

      const { wrapper } = setup({ claimDetail: claimsWithBondingAndPregnancy });

      expect(wrapper.find({ "data-test": "info-alert" }).exists()).toBe(false);
    });
  });

  it("does not render ViewYourNotices if documents not given", () => {
    const { wrapper } = setup({ docList: [] });
    expect(wrapper).toMatchSnapshot();
  });

  it("does not render LeaveDetails if absenceDetails not given", () => {
    const { wrapper } = setup({
      claimDetail: new ClaimDetail({
        ...CLAIM_DETAIL,
        absence_periods: null,
      }),
    });
    expect(wrapper).toMatchSnapshot();
  });

  it("includes a button to upload additional documents", () => {
    const { wrapper } = setup();

    const button = wrapper.find("ButtonLink");
    expect(button.children().text()).toEqual("Upload additional documents");
    expect(button.exists()).toBe(true);
    expect(wrapper).toMatchSnapshot();
    expect(button.prop("href")).toBe(
      `${routes.applications.uploadDocsOptions}?claim_id=${CLAIM_DETAIL.application_id}`
    );
  });
});

/** Test LeaveDetails component */
// TODO(CP-2482): replace with AbsencePeriodModel
const ABSENCE_DETAIL_LIST = {
  medical: [
    {
      period_type: "Reduced",
      absence_period_start_date: "2021-06-01",
      absence_period_end_date: "2021-06-08",
      request_decision: "Approved",
      fineos_leave_request_id: "PL-14432-0000002026",
    },
    {
      period_type: "Continuous",
      absence_period_start_date: "2021-07-01",
      absence_period_end_date: "2021-07-08",
      request_decision: "Pending",
      fineos_leave_request_id: "PL-14432-0000002326",
    },
  ],
  bonding: [
    {
      period_type: "Reduced",
      absence_period_start_date: "2021-08-01",
      absence_period_end_date: "2021-08-08",
      request_decision: "Denied",
      fineos_leave_request_id: "PL-14434-0000002026",
    },
    {
      period_type: "Continuous",
      absence_period_start_date: "2021-08-01",
      absence_period_end_date: "2021-08-08",
      request_decision: "Withdrawn",
      fineos_leave_request_id: "PL-14434-0000002326",
    },
  ],
};

describe("leave details page", () => {
  it("does not render LeaveDetails if absenceDetails not given", () => {
    const { wrapper } = renderWithAppLogic(LeaveDetails, {
      diveLevels: 0,
      props: { absenceDetails: {} },
    });
    expect(wrapper).toMatchSnapshot();
  });

  it("does renders page separated by keys if object of absenceDetails has more keys", () => {
    const { wrapper } = renderWithAppLogic(LeaveDetails, {
      diveLevels: 0,
      props: { absenceDetails: ABSENCE_DETAIL_LIST },
    });
    expect(wrapper).toMatchSnapshot();
  });

  it("does renders page with one section if absenceDetails has only one key", () => {
    const { wrapper } = renderWithAppLogic(LeaveDetails, {
      diveLevels: 0,
      props: { absenceDetails: { medical: ABSENCE_DETAIL_LIST.medical } },
    });
    expect(wrapper).toMatchSnapshot();
  });
});
