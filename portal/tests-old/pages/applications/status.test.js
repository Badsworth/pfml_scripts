import Document, { DocumentType } from "../../../src/models/Document";
import Status, { LeaveDetails } from "../../../src/pages/applications/status";

import AppErrorInfo from "../../../src/models/AppErrorInfo";
import AppErrorInfoCollection from "../../../src/models/AppErrorInfoCollection";
import ClaimDetail from "../../../src/models/ClaimDetail";
import DocumentCollection from "../../../src/models/DocumentCollection";
import LeaveReason from "../../../src/models/LeaveReason";
import { act } from "react-dom/test-utils";
import { mockRouter } from "next/router";
import { renderWithAppLogic } from "../../test-utils";
import routes from "../../../src/routes";

jest.mock("next/router");

mockRouter.asPath = routes.applications.status;

const CLAIM_DETAIL = new ClaimDetail({
  application_id: "application-id",
  fineos_absence_id: "fineos-abence-id",
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

const DOCUMENT_COLLECTION = new DocumentCollection([
  new Document({
    application_id: "application-id",
    content_type: "image/png",
    created_at: "2020-04-05",
    document_type: DocumentType.denialNotice,
    fineos_document_id: "fineos-id-4",
    name: "legal notice 1",
  }),
  new Document({
    application_id: "not-my-application-id",
    content_type: "image/png",
    created_at: "2020-04-05",
    document_type: DocumentType.requestForInfoNotice,
    fineos_document_id: "fineos-id-5",
    name: "legal notice 2",
  }),
  new Document({
    application_id: "application-id",
    content_type: "image/png",
    created_at: "2020-04-05",
    document_type: DocumentType.identityVerification,
    fineos_document_id: "fineos-id-6",
    name: "non-legal notice 1",
  }),
  new Document({
    application_id: "application-id",
    content_type: "image/png",
    created_at: "2020-04-05",
    document_type: DocumentType.requestForInfoNotice,
    fineos_document_id: "fineos-id-7",
    name: "legal notice 3",
  }),
]);

describe("status page", () => {
  beforeEach(() => {
    process.env.featureFlags = {
      claimantShowStatusPage: true,
    };
  });

  const setup = ({
    appErrors = new AppErrorInfoCollection(),
    claimDetail = CLAIM_DETAIL,
    documentCollection = DOCUMENT_COLLECTION,
    isLoadingClaimDetail = false,
    isLoadingDocuments = false,
    render = "shallow",
    query,
  } = {}) => {
    const hasLoadedClaimDocuments = () => !isLoadingDocuments;
    let appLogic;
    const mockAppLogic = (_appLogic) => {
      appLogic = _appLogic;
      appLogic.appErrors = appErrors;
      appLogic.claims.claimDetail = claimDetail;
      appLogic.claims.loadClaimDetail = jest.fn();
      appLogic.claims.isLoadingClaimDetail = isLoadingClaimDetail;
      appLogic.documents.documents = documentCollection;
      appLogic.documents.loadAll = jest.fn();
      appLogic.documents.hasLoadedClaimDocuments = hasLoadedClaimDocuments;
      appLogic.portalFlow.goTo = jest.fn();
    };

    const { wrapper } = renderWithAppLogic(Status, {
      diveLevels: 0,
      mockAppLogic,
      props: {
        query: {
          absence_case_id: "absence-case-id",
          ...query,
        },
      },
      render,
    });

    return {
      appLogic,
      wrapper,
    };
  };

  it("redirects page if feature flag is not enabled", () => {
    process.env.featureFlags = {
      claimantShowStatusPage: false,
    };

    const { appLogic } = setup({ render: "mount" });

    expect(appLogic.portalFlow.goTo).toHaveBeenCalledWith(
      routes.applications.index
    );
  });

  it("renders the page with back button if error exists", () => {
    const appErrors = new AppErrorInfoCollection([new AppErrorInfo()]);

    const { wrapper } = setup({ appErrors });
    expect(wrapper.find("BackButton").exists()).toBe(true);
  });

  it("still renders the page if DocumentsLoadError exists", () => {
    const { appLogic, wrapper } = setup({
      documentCollection: new DocumentCollection(),
      isLoadingDocuments: true,
      render: "mount",
    });

    act(() => {
      wrapper.setProps({
        appLogic: {
          ...appLogic,
          appErrors: new AppErrorInfoCollection([
            new AppErrorInfo({ name: "DocumentsLoadError" }),
          ]),
        },
      });
    });
    wrapper.update();

    expect(wrapper.isEmptyRender()).toBe(false);
  });

  it("shows a spinner if there is no claim detail", () => {
    const { wrapper } = setup({
      claimDetail: undefined,
      documentCollection: new DocumentCollection(),
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

  describe("", () => {
    it("renders success alert when document type param is given", () => {
      const { wrapper } = setup({
        query: {
          uploaded_document_type: "proof-of-birth",
          claim_id: "12342323",
          absence_case_id: "absence-case-id",
        },
      });
      const uploadSuccessAlertComponent = wrapper.find("Alert");
      expect(uploadSuccessAlertComponent.exists()).toBe(true);
      expect(uploadSuccessAlertComponent.dive()).toMatchSnapshot();
    });
    it("displays the category message depending on uploaded document type", () => {
      const { wrapper } = setup({
        query: {
          uploaded_document_type: "state-id",
        },
      });

      expect(
        wrapper.find("Alert").dive().find("Heading").children().text()
      ).toBe("You've successfully submitted your identification documents");
      wrapper.setProps({
        query: {
          uploaded_document_type: "family-member-medical-certification",
        },
      });
      expect(
        wrapper.find("Alert").dive().find("Heading").children().text()
      ).toBe("You've successfully submitted your certification form");
    });
  });

  describe("info alert", () => {
    it("displays if claimant has bonding-newborn but not pregnancy claims", () => {
      const claimWithoutPregnancy = new ClaimDetail({
        ...CLAIM_DETAIL,
        absence_periods: [
          { reason: LeaveReason.bonding },
          { request_decision: "Pending" },
          { reason_qualifier_one: "Newborn" },
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
          { request_decision: "Approved" },
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

    it("does not display if claimant has Denied claims", () => {
      const claimsWithPregnancy = new ClaimDetail({
        ...CLAIM_DETAIL,
        absence_periods: [
          { reason: LeaveReason.pregnancy, request_decision: "Denied" },
        ],
      });

      const { wrapper } = setup({ claimDetail: claimsWithPregnancy });

      expect(wrapper.find({ "data-test": "info-alert" }).exists()).toBe(false);
    });

    it("does not display if claimant has Withdrawn claims", () => {
      const claimsWithoutPregnancy = new ClaimDetail({
        ...CLAIM_DETAIL,
        absence_periods: [
          { reason: LeaveReason.bonding },
          { request_decision: "Withdrawn" },
          { reason_qualifier_one: "Newborn" },
        ],
      });

      const { wrapper } = setup({ claimDetail: claimsWithoutPregnancy });

      expect(wrapper.find({ "data-test": "info-alert" }).exists()).toBe(false);
    });

    it("does not render Timeline if no absence_periods are available", () => {
      const { wrapper } = setup({
        claimDetail: new ClaimDetail({
          ...CLAIM_DETAIL,
          absence_periods: [],
        }),
      });
      expect(wrapper.find("Timeline").exists()).toBe(false);
    });
  });

  describe("ViewYourNotices", () => {
    it("shows a spinner while loading", () => {
      const { wrapper } = setup({
        documentCollection: new DocumentCollection(),
        isLoadingDocuments: true,
        render: "mount",
      });

      const expectedAriaValueText = "Loading legal notices";
      const documentSpinner = wrapper.find("Spinner", {
        "aria-valuetext": expectedAriaValueText,
      });
      expect(documentSpinner.exists()).toBe(true);
    });

    it("displays only legal notices for the current application_id", () => {
      const expectedDocuments = [
        DOCUMENT_COLLECTION.items[0],
        DOCUMENT_COLLECTION.items[3],
      ];

      const { wrapper } = setup({ render: "mount" });
      wrapper.update();

      const viewYourNoticesComponent = wrapper.find("ViewYourNotices");
      const documentsProp = viewYourNoticesComponent
        .find("LegalNoticeList")
        .prop("documents");
      expect(documentsProp).toEqual(expectedDocuments);
      expect(viewYourNoticesComponent).toMatchSnapshot();
    });

    it("displays the fallback text if there are no legal notices", () => {
      const { wrapper } = setup({
        documentCollection: new DocumentCollection(),
        isLoadingDocuments: false,
        render: "mount",
      });
      wrapper.update();

      expect(wrapper.find("ViewYourNotices").find("p").exists()).toBe(true);
    });
  });

  it("includes a button to upload additional documents", () => {
    const { wrapper } = setup();

    const button = wrapper.find("ButtonLink");
    expect(button.children().text()).toEqual("Upload additional documents");
    expect(button.exists()).toBe(true);
    expect(wrapper).toMatchSnapshot();
    expect(button.prop("href")).toBe(
      `${routes.applications.upload.index}?absence_case_id=${CLAIM_DETAIL.fineos_absence_id}`
    );
  });
});

const SECONDARY_CLAIM_DETAIL = new ClaimDetail({
  fineos_absence_id: "fineos-abence-id",
  absence_periods: [
    {
      period_type: "Reduced",
      absence_period_start_date: "2021-06-01",
      absence_period_end_date: "2021-06-08",
      request_decision: "Approved",
      fineos_leave_request_id: "PL-14432-0000002026",
      reason: LeaveReason.bonding,
      reason_qualifier_one: "Newborn",
    },
    {
      period_type: "Reduced Leave",
      absence_period_start_date: "2021-08-01",
      absence_period_end_date: "2021-08-08",
      request_decision: "Pending",
      fineos_leave_request_id: "PL-14434-0000002026",
      reason: LeaveReason.pregnancy,
      reason_qualifier_one: "Postnatal Disability",
    },
    {
      period_type: "Continuous",
      absence_period_start_date: "2021-08-01",
      absence_period_end_date: "2021-08-08",
      request_decision: "Withdrawn",
      fineos_leave_request_id: "PL-14434-0000002326",
      reason: LeaveReason.medical,
    },
  ],
});

/** Test LeaveDetails component */
describe("leave details page", () => {
  it("does not render LeaveDetails if absenceDetails not given", () => {
    const { wrapper } = renderWithAppLogic(LeaveDetails, {
      diveLevels: 0,
      props: { absenceDetails: {} },
    });
    expect(wrapper).toMatchSnapshot();
  });

  it("does render page separated by keys if object of absenceDetails has more keys", () => {
    const { wrapper } = renderWithAppLogic(LeaveDetails, {
      diveLevels: 0,
      props: { absenceDetails: SECONDARY_CLAIM_DETAIL.absencePeriodsByReason },
    });
    expect(wrapper).toMatchSnapshot();
  });

  it("does render page with one section if absenceDetails has only one key", () => {
    const { wrapper } = renderWithAppLogic(LeaveDetails, {
      diveLevels: 0,
      props: {
        absenceDetails: {
          [LeaveReason.medical]:
            SECONDARY_CLAIM_DETAIL.absencePeriodsByReason[LeaveReason.medical],
        },
      },
    });
    expect(wrapper).toMatchSnapshot();
  });
});
