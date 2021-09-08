import Document, { DocumentType } from "../../../src/models/Document";
import Status, {
  ApplicationUpdates,
  LeaveDetails,
} from "../../../src/pages/applications/status";
import { generateNotice, renderWithAppLogic, testHook } from "../../test-utils";
import AppErrorInfo from "../../../src/models/AppErrorInfo";
import AppErrorInfoCollection from "../../../src/models/AppErrorInfoCollection";
import ClaimDetail from "../../../src/models/ClaimDetail";
import DocumentCollection from "../../../src/models/DocumentCollection";
import LeaveReason from "../../../src/models/LeaveReason";
import { act } from "react-dom/test-utils";
import routes from "../../../src/routes";
import useAppLogic from "../../../src/hooks/useAppLogic";

jest.mock("../../../src/hooks/useAppLogic");

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

const DOCUMENT_COLLECTION = new DocumentCollection([
  new Document({
    content_type: "image/png",
    created_at: "2020-04-05",
    document_type: DocumentType.denialNotice,
    fineos_document_id: "fineos-id-4",
    name: "legal notice 1",
  }),
  new Document({
    content_type: "image/png",
    created_at: "2020-04-05",
    document_type: DocumentType.requestForInfoNotice,
    fineos_document_id: "fineos-id-5",
    name: "legal notice 2",
  }),
  new Document({
    content_type: "image/png",
    created_at: "2020-04-05",
    document_type: DocumentType.identityVerification,
    fineos_document_id: "fineos-id-6",
    name: "non-legal notice 1",
  }),
  new Document({
    content_type: "image/png",
    created_at: "2020-04-05",
    document_type: DocumentType.requestForInfoNotice,
    fineos_document_id: "fineos-id-7",
    name: "legal notice 2",
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
  } = {}) => {
    const hasLoadedClaimDocuments = () => !isLoadingDocuments;
    let appLogic;

    testHook(() => {
      appLogic = useAppLogic();
      appLogic.appErrors = appErrors;
      appLogic.claims.claimDetail = claimDetail;
      appLogic.claims.isLoadingClaimDetail = isLoadingClaimDetail;
      appLogic.documents.documents = documentCollection;
      appLogic.documents.hasLoadedClaimDocuments = hasLoadedClaimDocuments;
    });

    const { wrapper } = renderWithAppLogic(Status, {
      diveLevels: 0,
      props: {
        appLogic,
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

  it("redirects page if feature flag is not enabled", () => {
    process.env.featureFlags = {
      claimantShowStatusPage: false,
    };

    const { appLogic } = setup({ render: "mount" });

    expect(appLogic.portalFlow.goTo).toHaveBeenCalledWith(
      routes.applications.index
    );
  });

  it("doesn't render the page if there is a ClaimDetailLoadError", () => {
    const appErrors = new AppErrorInfoCollection([
      new AppErrorInfo({ name: "ClaimDetailLoadError" }),
    ]);

    const { wrapper } = setup({ appErrors });

    expect(wrapper.isEmptyRender()).toBe(true);
  });

  describe("when DocumentsLoadError exists", () => {
    const documentsLoadError = new AppErrorInfo({
      name: "DocumentsLoadError",
    });

    const setupWithDocumentsLoadError = () => {
      const { appLogic, wrapper } = setup({
        documentCollection: new DocumentCollection(),
        isLoadingDocuments: true,
        render: "mount",
      });

      act(() => {
        wrapper.setProps({
          appLogic: {
            ...appLogic,
            appErrors: new AppErrorInfoCollection([documentsLoadError]),
          },
        });
      });
      wrapper.update();

      return { wrapper };
    };

    it("still renders the page", () => {
      const { wrapper } = setupWithDocumentsLoadError();

      expect(wrapper.isEmptyRender()).toBe(false);
    });

    it("doesn't show the ViewYourNotices section", () => {
      const { wrapper } = setupWithDocumentsLoadError();

      expect(wrapper.find("ViewYourNotices").isEmptyRender()).toBe(true);
    });
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

    it("displays only legal notices", () => {
      const legalNoticeTypes = new Set([
        DocumentType.approvalNotice,
        DocumentType.denialNotice,
        DocumentType.requestForInfoNotice,
      ]);

      const { wrapper } = setup({ render: "mount" });
      wrapper.update();

      const viewYourNoticesComponent = wrapper.find("ViewYourNotices");
      const legalNoticeListProps = viewYourNoticesComponent
        .find("LegalNoticeList")
        .prop("documents");
      expect(viewYourNoticesComponent).toMatchSnapshot();
      for (const document of legalNoticeListProps) {
        expect(legalNoticeTypes.has(document.document_type)).toBe(true);
      }
    });

    it("does not appear if there are no legal notices", () => {
      const { wrapper } = setup({
        documentCollection: new DocumentCollection(),
        isLoadingDocuments: false,
        render: "mount",
      });
      wrapper.update();

      expect(wrapper.find("ViewYourNotices").isEmptyRender()).toBe(true);
    });
  });

  it("includes a button to upload additional documents", () => {
    const { wrapper } = setup();

    const button = wrapper.find("ButtonLink");
    expect(button.children().text()).toEqual("Upload additional documents");
    expect(button.exists()).toBe(true);
    expect(wrapper).toMatchSnapshot();
    expect(button.prop("href")).toBe(
      `${routes.applications.upload.index}?absence_case_id=${CLAIM_DETAIL.application_id}`
    );
  });
});

const SECONDARY_CLAIM_DETAIL = new ClaimDetail({
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

const TERTIARY_CLAIM_DETAIL = new ClaimDetail({
  absence_periods: [
    {
      period_type: "Continuous",
      absence_period_start_date: "2021-07-01",
      absence_period_end_date: "2021-07-08",
      request_decision: "Pending",
      fineos_leave_request_id: "PL-14432-0000002326",
      reason: LeaveReason.bonding,
      reason_qualifier_one: "Adoption",
    },
  ],
});

const TEST_DOCS = [
  generateNotice("approvalNotice", "2021-08-21"),
  generateNotice("denialNotice", "2021-08-21"),
];

const CERTIFICATION_DOC = [
  new Document({
    content_type: "image/png",
    created_at: "2020-04-05",
    document_type: DocumentType.certification[LeaveReason.bonding],
    fineos_document_id: "fineos-id-5",
    name: "legal notice 2",
  }),
];

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

/** Test ApplicationUpdates component */
describe("application updates page", () => {
  it("does not render ApplicationUpdates if absenceDetails not given", () => {
    const { wrapper } = renderWithAppLogic(ApplicationUpdates, {
      diveLevels: 0,
      props: { absenceDetails: {} },
    });
    expect(wrapper).toMatchSnapshot();
  });

  it("does render Proof of Placement button if given 'Adoption' as reason_qualifier and leave_reason as 'Child Bonding'", () => {
    const { wrapper } = renderWithAppLogic(ApplicationUpdates, {
      diveLevels: 0,
      props: {
        absenceDetails: TERTIARY_CLAIM_DETAIL.absencePeriodsByReason,
        docList: TEST_DOCS,
      },
    });
    const button = wrapper.find("ButtonLink");
    expect(button.children().text()).toEqual("Upload proof of placement");
  });

  it("does render Proof of Birth button if given 'Newborn' as reason_qualifier and reason as 'Child Bonding'", () => {
    const { wrapper } = renderWithAppLogic(ApplicationUpdates, {
      diveLevels: 0,
      props: {
        absenceDetails: {
          [LeaveReason.bonding]:
            SECONDARY_CLAIM_DETAIL.absencePeriodsByReason[LeaveReason.bonding],
        },
        docList: TEST_DOCS,
      },
    });
    const button = wrapper.find("ButtonLink");
    expect(button.children().text()).toEqual("Upload proof of birth");
  });

  it("does render Proof of Birth button if given reason is Pregnancy/Maternity", () => {
    const { wrapper } = renderWithAppLogic(ApplicationUpdates, {
      diveLevels: 0,
      props: {
        absenceDetails: {
          [LeaveReason.pregnancy]:
            SECONDARY_CLAIM_DETAIL.absencePeriodsByReason[
              LeaveReason.pregnancy
            ],
        },
        docList: TEST_DOCS,
      },
    });
    const button = wrapper.find("ButtonLink");
    expect(button.children().text()).toEqual("Upload proof of birth");
  });

  it("does update the rendered content on prop update", () => {
    const { wrapper } = renderWithAppLogic(ApplicationUpdates, {
      diveLevels: 0,
      props: {
        absenceDetails: TERTIARY_CLAIM_DETAIL.absencePeriodsByReason,
        docList: TEST_DOCS,
      },
    });
    let button = wrapper.find("ButtonLink");
    expect(button.children().text()).toEqual("Upload proof of placement");
    wrapper.setProps({
      absenceDetails: {
        [LeaveReason.pregnancy]:
          SECONDARY_CLAIM_DETAIL.absencePeriodsByReason[LeaveReason.pregnancy],
      },
      docList: TEST_DOCS,
    });
    button = wrapper.find("ButtonLink");
    expect(button.children().text()).toEqual("Upload proof of birth");
  });

  it("does not render an upload button given leave_reason is not Pregnancy/Maternity or Child Bonding", () => {
    const { wrapper } = renderWithAppLogic(ApplicationUpdates, {
      diveLevels: 0,
      props: {
        absenceDetails: {
          [LeaveReason.medical]:
            SECONDARY_CLAIM_DETAIL.absencePeriodsByReason[LeaveReason.medical],
        },
        docList: TEST_DOCS,
      },
    });
    expect(wrapper.find("ButtonLink").exists()).toBe(false);
  });

  it("does not render an upload button if the correct certification form is given", () => {
    const { wrapper } = renderWithAppLogic(ApplicationUpdates, {
      diveLevels: 0,
      props: {
        absenceDetails: {
          [LeaveReason.bonding]:
            SECONDARY_CLAIM_DETAIL.absencePeriodsByReason[LeaveReason.bonding],
        },
        docList: CERTIFICATION_DOC,
      },
    });
    expect(wrapper.find("ButtonLink").exists()).toBe(false);
  });
});
