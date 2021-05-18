import Document, { DocumentType } from "../../../src/models/Document";
import { MockEmployerClaimBuilder, renderWithAppLogic } from "../../test-utils";
import DocumentCollection from "../../../src/models/DocumentCollection";
import LeaveReason from "../../../src/models/LeaveReason";
import LeaveSchedule from "../../../src/components/employers/LeaveSchedule";

jest.mock("../../../src/hooks/useAppLogic");

const COMPLETED_CLAIM = new MockEmployerClaimBuilder().completed().create();
const CARING_LEAVE_CLAIM = new MockEmployerClaimBuilder()
  .caringLeaveReason()
  .absenceId()
  .create();
const INTERMITTENT_CLAIM = new MockEmployerClaimBuilder()
  .intermittent()
  .absenceId()
  .create();
const DOCUMENTS = new DocumentCollection([
  new Document({
    content_type: "image/png",
    created_at: "2020-04-05",
    document_type: DocumentType.certification.medicalCertification,
    fineos_document_id: "fineos-id-4",
    name: "Medical cert doc",
  }),
  new Document({
    content_type: "application/pdf",
    created_at: "2020-01-02",
    document_type: DocumentType.approvalNotice,
    fineos_document_id: "fineos-id-1",
    name: "Approval notice doc",
  }),
  new Document({
    content_type: "application/pdf",
    created_at: "2020-02-01",
    document_type: DocumentType.certification.medicalCertification,
    fineos_document_id: "fineos-id-9",
    // intentionally omit name
  }),
  new Document({
    content_type: "application/pdf",
    created_at: "2020-02-01",
    document_type: DocumentType.certification[LeaveReason.care],
    fineos_document_id: "fineos-id-10",
    name: "Caring cert doc",
  }),
]);
const DOCUMENTATION_HEADING_SELECTOR = 'ReviewRow[level="3"]';

describe("LeaveSchedule", () => {
  let appLogic;
  let wrapper;

  const renderWithClaim = (claim, render = "shallow") => {
    ({ appLogic, wrapper } = renderWithAppLogic(LeaveSchedule, {
      diveLevels: 0,
      employerClaimAttrs: claim,
      props: {
        absenceId: "NTN-111-ABS-01",
        claim,
      },
      render,
    }));
  };

  beforeEach(() => {
    renderWithClaim(COMPLETED_CLAIM);
  });

  it("renders continuous schedule", () => {
    const continuousClaim = new MockEmployerClaimBuilder()
      .continuous()
      .absenceId()
      .create();
    renderWithClaim(continuousClaim);
    const cellValues = wrapper
      .find("tbody")
      .find("tr")
      .children()
      .map((cell) => cell.text());

    expect(cellValues).toEqual(["1/1/2021 – 6/1/2021", "Continuous leave"]);
    expect(wrapper).toMatchSnapshot();
  });

  it("renders intermittent schedule", () => {
    renderWithClaim(INTERMITTENT_CLAIM);
    expect(wrapper.find("IntermittentLeaveSchedule").exists()).toEqual(true);
    expect(wrapper).toMatchSnapshot();
    expect(wrapper.find("Trans").last().dive()).toMatchSnapshot();
  });

  it("renders reduced schedule", () => {
    const reducedScheduleClaim = new MockEmployerClaimBuilder()
      .reducedSchedule()
      .absenceId()
      .create();
    renderWithClaim(reducedScheduleClaim);

    expect(wrapper).toMatchSnapshot();
    expect(wrapper.find("Trans").last().dive()).toMatchSnapshot();
  });

  it("renders multiple schedule types", () => {
    const multipleSchedulesClaim = new MockEmployerClaimBuilder()
      .continuous()
      .intermittent()
      .reducedSchedule()
      .absenceId()
      .create();

    renderWithClaim(multipleSchedulesClaim, "mount");
    const rows = wrapper.find("tbody").find("tr");
    // if previous three tests pass, assume that the three rows correspond to the three types
    expect(rows.length).toEqual(3);
  });

  describe("when there are documents", () => {
    let downloadDocumentSpy;

    beforeEach(() => {
      appLogic.employers.documents = DOCUMENTS;
      appLogic.employers.downloadDocument = jest.fn();
      downloadDocumentSpy = jest
        .spyOn(appLogic.employers, "downloadDocument")
        .mockImplementation(() => Promise.resolve(new Blob()));

      ({ appLogic, wrapper } = renderWithAppLogic(LeaveSchedule, {
        diveLevels: 0,
        employerClaimAttrs: COMPLETED_CLAIM,
        props: {
          appLogic,
          absenceId: "NTN-111-ABS-01",
          claim: COMPLETED_CLAIM,
        },
      }));
    });

    it("shows the documents heading", () => {
      expect(
        wrapper.find(DOCUMENTATION_HEADING_SELECTOR).prop("label")
      ).toEqual("Documentation");
    });

    it("displays caption for a non-intermittent schedule with documents", () => {
      expect(wrapper.find("caption").find("Trans").dive().text()).toEqual(
        "This is your employee’s expected leave schedule. Download the attached documentation for more details."
      );
    });

    it("only shows medical certification documents", () => {
      const medicalDocuments = wrapper.find("HcpDocumentItem");
      expect(medicalDocuments.length).toBe(2);
      expect(medicalDocuments.map((node) => node.dive().text())).toEqual([
        "Medical cert doc",
        "Certification of a Serious Health Condition",
      ]);
    });

    it("makes a call to download documents on click", async () => {
      await wrapper
        .find("HcpDocumentItem")
        .at(0)
        .dive()
        .find("a")
        .simulate("click", {
          preventDefault: jest.fn(),
        });

      expect(downloadDocumentSpy).toHaveBeenCalledWith(
        "NTN-111-ABS-01",
        expect.objectContaining({
          content_type: "image/png",
          created_at: "2020-04-05",
          document_type: "State managed Paid Leave Confirmation",
          fineos_document_id: "fineos-id-4",
          name: "Medical cert doc",
        })
      );
    });
  });

  describe("when there are documents for intermittent schedule", () => {
    beforeEach(() => {
      appLogic.employers.documents = DOCUMENTS;
      ({ appLogic, wrapper } = renderWithAppLogic(LeaveSchedule, {
        diveLevels: 0,
        employerClaimAttrs: INTERMITTENT_CLAIM,
        props: {
          appLogic,
          absenceId: "NTN-111-ABS-01",
          claim: INTERMITTENT_CLAIM,
        },
      }));

      it("displays caption for an intermittent schedule with documents", () => {
        expect(wrapper.find("caption").find("Trans").dive().text()).toEqual(
          "Download the attached documentation for details about the employee’s intermittent leave schedule."
        );
      });
    });
  });

  describe("while documents are undefined", () => {
    beforeEach(() => {
      renderWithClaim(COMPLETED_CLAIM, "mount");
    });

    it("loads the documents", () => {
      expect(appLogic.employers.loadDocuments).toHaveBeenCalledWith(
        "NTN-111-ABS-01"
      );
    });

    it("does not show the document section", () => {
      expect(wrapper.find(DOCUMENTATION_HEADING_SELECTOR).exists()).toBe(false);
    });
  });

  describe("when there are no documents", () => {
    beforeEach(() => {
      appLogic.employers.documents = new DocumentCollection([]);
      ({ wrapper } = renderWithAppLogic(LeaveSchedule, {
        diveLevels: 0,
        employerClaimAttrs: COMPLETED_CLAIM,
        props: {
          appLogic,
          absenceId: "NTN-111-ABS-01",
          claim: COMPLETED_CLAIM,
        },
      }));
    });

    it("displays caption for a schedule without documents", () => {
      expect(wrapper.find("caption").find("Trans").dive().text()).toEqual(
        "This is your employee’s expected leave schedule."
      );
    });

    it("does not show the document section", () => {
      expect(wrapper.find(DOCUMENTATION_HEADING_SELECTOR).exists()).toBe(false);
    });
  });

  describe("when the claim is a caring leave", () => {
    function render() {
      appLogic.employers.documents = DOCUMENTS;
      ({ appLogic, wrapper } = renderWithAppLogic(LeaveSchedule, {
        diveLevels: 0,
        employerClaimAttrs: CARING_LEAVE_CLAIM,
        props: {
          appLogic,
          absenceId: "NTN-111-ABS-01",
          claim: CARING_LEAVE_CLAIM,
        },
      }));
    }

    it("shows only medical cert when feature flag is false", () => {
      render();
      const medicalDocuments = wrapper.find("HcpDocumentItem");
      expect(medicalDocuments.length).toBe(2);
      expect(medicalDocuments.map((node) => node.dive().text())).toEqual([
        "Medical cert doc",
        "Certification of a Serious Health Condition",
      ]);
    });

    it("shows medical cert and caring cert when feature flag is true", () => {
      process.env.featureFlags = {
        showCaringLeaveType: true,
      };
      render();
      const documents = wrapper.find("HcpDocumentItem");
      expect(documents.length).toBe(3);
      expect(documents.map((node) => node.dive().text())).toEqual([
        "Medical cert doc",
        "Certification of a Serious Health Condition",
        "Caring cert doc",
      ]);
    });
  });
});
