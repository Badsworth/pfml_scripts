import Document, { DocumentType } from "../../../../src/models/Document";
import {
  MockEmployerClaimBuilder,
  renderWithAppLogic,
} from "../../../test-utils";
import DocumentCollection from "../../../../src/models/DocumentCollection";
import Status from "../../../../src/pages/employers/applications/status";

jest.mock("../../../../src/hooks/useAppLogic");

const CLAIM = new MockEmployerClaimBuilder()
  .status("Approved")
  .completed()
  .create();
const PENDING_CLAIM = new MockEmployerClaimBuilder()
  .status("Adjudication")
  .completed()
  .create();
const DOCUMENTS = new DocumentCollection([
  new Document({
    content_type: "application/pdf",
    created_at: "2020-01-02",
    document_type: DocumentType.approvalNotice,
    fineos_document_id: "fineos-id-1",
    name: "Approval notice doc",
  }),
  new Document({
    content_type: "application/pdf",
    created_at: "2020-02-03",
    document_type: DocumentType.denialNotice,
    fineos_document_id: "fineos-id-2",
    name: "Denial notice doc",
  }),
  new Document({
    content_type: "image/png",
    created_at: "2020-04-05",
    document_type: DocumentType.certification.medicalCertification,
    fineos_document_id: "fineos-id-4",
    name: "Medical cert doc",
  }),
  new Document({
    content_type: "image/png",
    created_at: "2020-03-04",
    document_type: DocumentType.requestForInfoNotice,
    fineos_document_id: "fineos-id-3",
    name: "Request for info doc",
  }),
]);

describe("Status", () => {
  const query = { absence_id: "NTN-111-ABS-01" };
  let appLogic;
  let wrapper;

  beforeEach(() => {
    ({ appLogic, wrapper } = renderWithAppLogic(Status, {
      employerClaimAttrs: CLAIM,
      props: {
        query,
      },
    }));
  });

  it("renders the page and correct content in Trans component", () => {
    expect(wrapper).toMatchSnapshot();
    expect(wrapper.find("Trans").dive()).toMatchSnapshot();
  });

  it("shows the claimant name as the title", () => {
    expect(wrapper.find("Title").childAt(0).text()).toEqual(
      "Application status for Jane Doe"
    );
  });

  it("shows lead text for a claim that has a decision", () => {
    expect(
      wrapper.find("Trans[data-test='lead-text']").dive()
    ).toMatchSnapshot();
  });

  it("shows lead text for a claim that is pending", () => {
    ({ appLogic, wrapper } = renderWithAppLogic(Status, {
      employerClaimAttrs: PENDING_CLAIM,
      props: {
        query,
      },
    }));

    expect(
      wrapper.find("Trans[data-test='lead-text']").dive()
    ).toMatchSnapshot();
  });

  it("shows lead text for resolved claims", () => {
    const resolvedClaim = new MockEmployerClaimBuilder()
      .status("Approved")
      .completed()
      .create();
    ({ wrapper } = renderWithAppLogic(Status, {
      employerClaimAttrs: resolvedClaim,
      props: {
        query,
      },
    }));

    expect(wrapper.find("Lead").exists()).toEqual(true);
    expect(wrapper.find("Trans").dive()).toMatchSnapshot();
  });

  it("shows the application ID", () => {
    const applicationIdRow = wrapper.find("StatusRow[data-test='id']");

    expect(applicationIdRow.exists()).toBe(true);
    expect(applicationIdRow).toMatchSnapshot();
  });

  it("shows the leave type", () => {
    const leaveTypeRow = wrapper.find("StatusRow[data-test='reason']");

    expect(leaveTypeRow.exists()).toBe(true);
    expect(leaveTypeRow).toMatchSnapshot();
  });

  it("shows the leave duration", () => {
    const leaveDurationRow = wrapper.find("StatusRow[data-test='duration']");

    expect(leaveDurationRow.exists()).toBe(true);
    expect(leaveDurationRow).toMatchSnapshot();
  });

  it("shows the leave duration types", () => {
    const busyClaim = new MockEmployerClaimBuilder()
      .completed()
      .continuous()
      .intermittent()
      .reducedSchedule()
      .create();
    ({ appLogic, wrapper } = renderWithAppLogic(Status, {
      employerClaimAttrs: busyClaim,
      props: {
        query,
      },
    }));

    const continuousRow = wrapper.find(
      "StatusRow[data-test='duration-continuous']"
    );
    const intermittentRow = wrapper.find(
      "StatusRow[data-test='duration-intermittent']"
    );
    const reducedScheduleRow = wrapper.find(
      "StatusRow[data-test='duration-reduced']"
    );

    expect(continuousRow.exists()).toBe(true);
    expect(continuousRow).toMatchSnapshot();
    expect(intermittentRow.exists()).toBe(true);
    expect(intermittentRow).toMatchSnapshot();
    expect(reducedScheduleRow.exists()).toBe(true);
    expect(reducedScheduleRow).toMatchSnapshot();
  });

  describe("when documents haven't been loaded yet", () => {
    it("only shows the 'Leave details' section title", () => {
      const sectionTitle = wrapper.find("Heading");
      expect(sectionTitle.first()).toStrictEqual(sectionTitle.last());
      expect(sectionTitle.childAt(0).text()).toEqual("Leave details");
    });

    it("loads the documents", () => {
      ({ appLogic } = renderWithAppLogic(Status, {
        employerClaimAttrs: CLAIM,
        props: {
          query,
        },
        render: "mount",
      }));

      expect(appLogic.employers.loadDocuments).toHaveBeenCalledWith(
        query.absence_id
      );
    });
  });

  describe("when there are no documents", () => {
    it("only shows the 'Leave details' section title", () => {
      ({ appLogic } = renderWithAppLogic(Status, {
        employerClaimAttrs: CLAIM,
        props: {
          query,
        },
        render: "mount",
      }));
      appLogic.employers.documents = new DocumentCollection([]);

      const sectionTitle = wrapper.find("Heading");
      expect(sectionTitle.first()).toStrictEqual(sectionTitle.last());
      expect(sectionTitle.childAt(0).text()).toEqual("Leave details");
    });
  });

  it("displays status", () => {
    const row = wrapper.find("StatusRow[data-test='status']");

    expect(row.exists()).toBe(true);
    expect(row).toMatchSnapshot();
  });

  describe("when there are documents", () => {
    beforeEach(() => {
      appLogic.employers.documents = DOCUMENTS;
      appLogic.employers.downloadDocument = jest.fn();

      ({ wrapper } = renderWithAppLogic(Status, {
        employerClaimAttrs: CLAIM,
        props: {
          appLogic,
          query,
        },
      }));
    });

    it("shows the appropriate headings", () => {
      const sectionTitles = wrapper
        .find("Heading")
        .map((section) => section.childAt(0).text());
      expect(sectionTitles).toEqual(["Leave details", "Notices"]);
    });

    it("shows only legal documents", () => {
      const documentDivs = wrapper.find("DocumentListItem");
      const entries = documentDivs.map((div) => {
        const title = div.dive().find("p").at(0).text();
        const date = div.dive().find("p").at(1).text();
        return [title, date];
      });

      expect(entries).toEqual([
        ["Approval notice (PDF)", "Posted 1/2/2020"],
        ["Denial notice (PDF)", "Posted 2/3/2020"],
        ["Request for more information", "Posted 3/4/2020"],
      ]);
    });

    it("makes a call to download documents on click", async () => {
      const downloadDocumentSpy = jest
        .spyOn(appLogic.employers, "downloadDocument")
        .mockImplementation(() => Promise.resolve(new Blob()));

      await wrapper
        .find("DocumentListItem")
        .at(0)
        .dive()
        .find("a")
        .simulate("click", {
          preventDefault: () => jest.fn(),
        });

      expect(downloadDocumentSpy).toHaveBeenCalledWith(
        "NTN-111-ABS-01",
        expect.objectContaining({
          content_type: "application/pdf",
          created_at: "2020-01-02",
          document_type: "Approval Notice",
          fineos_document_id: "fineos-id-1",
          name: "Approval notice doc",
        })
      );
    });
  });
});
