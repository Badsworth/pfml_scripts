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

function assertStatusRow(wrapper, expectedValue) {
  const label = wrapper.prop("label");
  const child = wrapper.childAt(0).text();
  expect([label, child]).toEqual(expectedValue);
}

describe("Status", () => {
  const query = { absence_id: "NTN-111-ABS-01" };
  let appLogic;
  let wrapper;

  beforeEach(() => {
    process.env.featureFlags = {
      employerShowDashboard: false,
    };

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
    const applicationIdRow = wrapper.find("StatusRow").first();
    // added to satisfy "Test has no assertions" lint
    expect(applicationIdRow.exists()).toBe(true);
    assertStatusRow(applicationIdRow, ["Application ID", "NTN-111-ABS-01"]);
  });

  it("shows the leave type", () => {
    const leaveTypeRow = wrapper.find("StatusRow").at(1);
    // added to satisfy "Test has no assertions" lint
    expect(leaveTypeRow.exists()).toBe(true);
    assertStatusRow(leaveTypeRow, ["Leave type", "Medical leave"]);
  });

  it("shows the leave duration", () => {
    const leaveDurationRow = wrapper.find("StatusRow").at(2);
    // added to satisfy "Test has no assertions" lint
    expect(leaveDurationRow.exists()).toBe(true);
    assertStatusRow(leaveDurationRow, [
      "Leave duration",
      "1/1/2021 – 7/1/2021",
    ]);
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

    const leaveDurationRows = wrapper.find("StatusRow");
    // added to satisfy "Test has no assertions" lint
    expect(leaveDurationRows.exists()).toBe(true);

    const continuousRow = leaveDurationRows.at(3);
    const intermittentRow = leaveDurationRows.at(4);
    const reducedScheduleRow = leaveDurationRows.at(5);

    assertStatusRow(continuousRow, ["Continuous leave", "1/1/2021 – 6/1/2021"]);
    assertStatusRow(intermittentRow, [
      "Intermittent leave",
      "2/1/2021 – 7/1/2021",
    ]);
    assertStatusRow(reducedScheduleRow, [
      "Reduced leave schedule",
      "2/1/2021 – 7/1/2021",
    ]);
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

  describe("when 'employerShowDashboard' is enabled", () => {
    beforeEach(() => {
      process.env.featureFlags = {
        employerShowDashboard: true,
      };

      ({ wrapper } = renderWithAppLogic(Status, {
        employerClaimAttrs: CLAIM,
        props: {
          query,
        },
      }));
    });

    it("displays status if status is a valid and expected value", () => {
      const tagComponent = wrapper
        .find("StatusRow")
        .at(1)
        .dive()
        .find("AbsenceCaseStatusTag");

      expect(tagComponent.exists()).toBe(true);
      expect(tagComponent.prop("status")).toEqual("Approved");
    });

    it("displays -- if status is an invalid or unexpected value", () => {
      ({ wrapper } = renderWithAppLogic(Status, {
        employerClaimAttrs: PENDING_CLAIM,
        props: {
          query,
        },
      }));
      const tagComponent = wrapper
        .find("StatusRow")
        .at(1)
        .dive()
        .find("AbsenceCaseStatusTag");

      expect(tagComponent.exists()).toBe(true);
      expect(tagComponent.dive().text()).toEqual("--");
    });
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
