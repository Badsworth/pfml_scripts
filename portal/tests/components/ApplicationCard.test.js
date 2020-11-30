import Document, { DocumentType } from "../../src/models/Document";
import AppErrorInfo from "../../src/models/AppErrorInfo";
import AppErrorInfoCollection from "../../src/models/AppErrorInfoCollection";
import { ApplicationCard } from "../../src/components/ApplicationCard";
import { MockClaimBuilder } from "../test-utils";
import React from "react";
import { shallow } from "enzyme";

describe("ApplicationCard", () => {
  let props;
  const render = (claim, additionalProps = {}) => {
    props = Object.assign(
      {
        appLogic: {
          appErrors: new AppErrorInfoCollection([]),
          documents: {
            download: jest.fn(),
          },
        },
        documents: [],
      },
      additionalProps
    );

    return shallow(<ApplicationCard claim={claim} number={2} {...props} />);
  };

  it("uses generic text as the main heading", () => {
    const wrapper = render(new MockClaimBuilder().create());

    expect(wrapper.find("header")).toMatchSnapshot();
  });

  it("renders empty div for details section when claim is empty", () => {
    const wrapper = render(new MockClaimBuilder().create());

    expect(wrapper.find("ApplicationDetails").dive()).toMatchInlineSnapshot(
      `<div />`
    );
  });

  it("renders EIN", () => {
    const wrapper = render(new MockClaimBuilder().employed().create());

    expect(wrapper.find("ApplicationDetails").dive()).toMatchSnapshot();
  });

  it("renders continuous and reduced schedule leave period date ranges", () => {
    const wrapper = render(
      new MockClaimBuilder().reducedSchedule().continuous().create()
    );

    expect(wrapper.find("ApplicationDetails").dive()).toMatchSnapshot();
  });

  it("renders Intermittent leave period date range", () => {
    const wrapper = render(new MockClaimBuilder().intermittent().create());

    expect(wrapper.find("ApplicationDetails").dive()).toMatchSnapshot();
  });

  it("does not render legal notices section when claim is not submitted", () => {
    const wrapper = render(new MockClaimBuilder().create());

    expect(wrapper.find("LegalNotices").dive().isEmptyRender()).toBe(true);
  });

  describe("when the claim status is Submitted", () => {
    const submittedClaim = new MockClaimBuilder().submitted().create();

    it("includes a link to complete the claim", () => {
      const wrapper = render(submittedClaim);
      const actions = wrapper.find("ApplicationActions").dive();

      expect(actions.find("ButtonLink")).toMatchSnapshot();
    });

    it("uses the Case ID as the main heading and includes leave reason", () => {
      const wrapper = render(submittedClaim);

      expect(wrapper.find("header")).toMatchSnapshot();
    });

    it("renders legal notices text", () => {
      const wrapper = render(new MockClaimBuilder().completed().create());

      expect(wrapper.find("LegalNotices").dive()).toMatchSnapshot();
    });
  });

  describe("when the claim status is Completed", () => {
    it("includes a button to upload additional documents", () => {
      const wrapper = render(new MockClaimBuilder().completed().create());
      const actions = wrapper.find("ApplicationActions").dive();

      expect(actions.find("ButtonLink")).toMatchSnapshot();
    });

    it("renders instructions about reductions", () => {
      const wrapper = render(
        new MockClaimBuilder()
          .completed()
          .bondingBirthLeaveReason()
          .hasFutureChild()
          .create()
      );
      const actions = wrapper.find("ApplicationActions").dive();

      expect(actions.find("Trans").dive()).toMatchSnapshot();
      expect(actions.find("ul")).toMatchSnapshot();
    });

    describe("when it's a bonding claim with no cert doc", () => {
      it("renders guidance to upload a birth cert doc for new birth", () => {
        const wrapper = render(
          new MockClaimBuilder()
            .completed()
            .bondingBirthLeaveReason()
            .hasFutureChild()
            .create()
        );
        const actions = wrapper.find("ApplicationActions").dive();

        expect(actions.html()).toMatch(
          `Once your child is born, submit proof of birth so that we can make a decision.`
        );
      });

      it("renders guidance to upload an adoption cert doc for adoption", () => {
        const wrapper = render(
          new MockClaimBuilder()
            .completed()
            .bondingAdoptionLeaveReason()
            .hasFutureChild()
            .create()
        );
        const actions = wrapper.find("ApplicationActions").dive();

        expect(actions.html()).toMatch(
          `Once your child arrives, submit proof of placement so that we can make a decision.`
        );
      });
    });
  });

  describe("when there is a denial notice", () => {
    it("includes a button to upload additional documents", () => {
      const claim = new MockClaimBuilder().submitted().create();
      const documents = [
        new Document({
          application_id: claim.application_id,
          created_at: "2021-01-01",
          document_type: DocumentType.denialNotice,
          fineos_document_id: "mock-document-4",
        }),
      ];

      const wrapper = render(claim, { documents });
      const actions = wrapper.find("ApplicationActions").dive();

      expect(actions.find("ButtonLink")).toMatchSnapshot();
    });

    it("does not include a link to complete the claim", () => {
      const claim = new MockClaimBuilder().create();
      const documents = [
        new Document({
          application_id: claim.application_id,
          created_at: "2021-01-01",
          document_type: DocumentType.denialNotice,
          fineos_document_id: "mock-document-4",
        }),
      ];

      const wrapper = render(claim, { documents });
      const actions = wrapper.find("ApplicationActions").dive();

      expect(actions.find({ "data-test": "resume-button" }).exists()).toBe(
        false
      );
    });
  });

  describe("when there are legal notices", () => {
    it("displays legal notices", () => {
      const claim = new MockClaimBuilder().submitted().create();
      const documents = [
        new Document({
          application_id: claim.application_id,
          created_at: "2021-01-01",
          document_type: DocumentType.approvalNotice,
          fineos_document_id: "mock-document-3",
        }),
        new Document({
          application_id: claim.application_id,
          created_at: "2021-01-01",
          document_type: DocumentType.denialNotice,
          fineos_document_id: "mock-document-4",
        }),
        new Document({
          application_id: claim.application_id,
          created_at: "2021-01-01",
          document_type: DocumentType.requestForInfoNotice,
          fineos_document_id: "mock-document-5",
        }),
        // Throw in a non-legal notice to confirm it doesn't get rendered
        new Document({
          application_id: claim.application_id,
          created_at: "2020-12-01",
          document_type: DocumentType.medicalCertification,
          fineos_document_id: "mock-document-6",
        }),
      ];

      const wrapper = render(claim, { documents });
      const legalNotices = wrapper.find("LegalNotices").dive();

      const listItems = legalNotices.find("LegalNoticeListItem");

      expect.assertions(3);
      listItems.forEach((listItem) =>
        expect(listItem.dive()).toMatchSnapshot()
      );
    });

    describe("when the user clicks on the download link", () => {
      it("calls documentsLogic.download", () => {
        const claim = new MockClaimBuilder().completed().create();
        const documents = [
          new Document({
            application_id: claim.application_id,
            created_at: "2021-01-01",
            document_type: DocumentType.approvalNotice,
            fineos_document_id: "mock-document-3",
          }),
        ];

        const wrapper = render(claim, { documents });
        const legalNotices = wrapper.find("LegalNotices").dive();

        legalNotices
          .find("LegalNoticeListItem")
          .dive()
          .find("a")
          .simulate("click", {
            preventDefault: () => jest.fn(),
          });

        expect(props.appLogic.documents.download).toHaveBeenCalledWith(
          documents[0]
        );
      });
    });
  });

  it("renders Alert inside the component when there is an error loading documents", () => {
    const claim = new MockClaimBuilder().completed().create();
    const appLogic = {
      appErrors: new AppErrorInfoCollection([
        new AppErrorInfo({
          meta: { application_id: "mock_application_id" },
          name: "DocumentsRequestError",
        }),
      ]),
    };
    const wrapper = render(claim, { appLogic });
    const legalNotices = wrapper.find("LegalNotices").dive();

    expect(legalNotices.find("Alert")).toMatchSnapshot();
  });
});
