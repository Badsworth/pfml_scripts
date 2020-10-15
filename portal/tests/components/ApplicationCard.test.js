import Document, { DocumentType } from "../../src/models/Document";
import AppErrorInfo from "../../src/models/AppErrorInfo";
import AppErrorInfoCollection from "../../src/models/AppErrorInfoCollection";
import { ApplicationCard } from "../../src/components/ApplicationCard";
import { MockClaimBuilder } from "../test-utils";
import React from "react";
import { shallow } from "enzyme";

describe("ApplicationCard", () => {
  const render = (claim, props = {}) => {
    props = Object.assign(
      {
        appLogic: {
          appErrors: new AppErrorInfoCollection([]),
        },
        documents: [],
      },
      props
    );

    return shallow(<ApplicationCard claim={claim} number={2} {...props} />);
  };

  it("renders a card for the given application", () => {
    const wrapper = render(new MockClaimBuilder().create());

    expect(wrapper).toMatchSnapshot();
  });

  it("renders Continuous leave period date range", () => {
    const wrapper = render(new MockClaimBuilder().continuous().create());

    const leavePeriodHeading = wrapper
      .find("Heading")
      .filterWhere(
        (heading) => heading.children().text() === "Continuous leave"
      );

    expect(leavePeriodHeading.exists()).toBe(true);
    expect(wrapper.html()).toMatch("1/1/2021 – 6/1/2021");
  });

  it("renders Reduced Schedule leave period date range", () => {
    const wrapper = render(new MockClaimBuilder().reducedSchedule().create());

    const leavePeriodHeading = wrapper
      .find("Heading")
      .filterWhere(
        (heading) => heading.children().text() === "Reduced leave schedule"
      );

    expect(leavePeriodHeading.exists()).toBe(true);
    expect(wrapper.html()).toMatch("2/1/2021 – 7/1/2021");
  });

  it("renders Intermittent leave period date range", () => {
    const wrapper = render(new MockClaimBuilder().intermittent().create());

    const leavePeriodHeading = wrapper
      .find("Heading")
      .filterWhere(
        (heading) => heading.children().text() === "Intermittent leave"
      );

    expect(leavePeriodHeading.exists()).toBe(true);
    expect(wrapper.html()).toMatch("2/1/2021 – 7/1/2021");
  });

  describe("when the claim status is Submitted", () => {
    const submittedClaim = new MockClaimBuilder().submitted().create();

    it("includes a link to edit the claim", () => {
      const wrapper = render(submittedClaim);

      expect(wrapper.find("ButtonLink")).toHaveLength(1);
    });

    it("uses the Case ID as the main heading", () => {
      const wrapper = render(submittedClaim);

      expect(wrapper.find("Heading[level='2']").children().text()).toBe(
        submittedClaim.fineos_absence_id
      );
    });
  });

  describe("when the claim status is Completed", () => {
    it("does not include a link to edit the claim", () => {
      const wrapper = render(new MockClaimBuilder().completed().create());

      expect(wrapper.find("ButtonLink")).toHaveLength(0);
    });
  });

  it("displays legal notices", () => {
    const claim = new MockClaimBuilder().completed().create();
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

    expect(wrapper.find(".usa-list")).toMatchSnapshot();
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

    expect(wrapper.exists("Alert")).toBe(true);
    expect(wrapper.find("Alert")).toMatchSnapshot();
  });
});
