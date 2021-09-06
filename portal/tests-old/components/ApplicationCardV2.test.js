import Document, { DocumentType } from "../../src/models/Document";

import AppErrorInfoCollection from "../../src/models/AppErrorInfoCollection";
import { ApplicationCardV2 } from "../../src/components/ApplicationCardV2";
import { MockBenefitsApplicationBuilder } from "../test-utils";
import React from "react";
import { mount } from "enzyme";

describe("ApplicationCardV2", () => {
  const appLogic = {
    appErrors: new AppErrorInfoCollection([]),
    documents: {
      download: () => {},
    },
  };

  const testDocuments = [
    new Document({
      created_at: "2021-01-15",
      document_type: DocumentType.requestForInfoNotice,
      fineos_document_id: "a",
    }),
    new Document({
      created_at: "2021-01-30",
      document_type: DocumentType.denialNotice,
      fineos_document_id: "b",
    }),
  ];

  describe("components match their snapshots", () => {
    it("in progress status matches snapshot", () => {
      const claim = new MockBenefitsApplicationBuilder().submitted().create();
      const wrapper = mount(
        <ApplicationCardV2 appLogic={appLogic} claim={claim} number={2} />
      );

      expect(wrapper).toMatchSnapshot();
    });

    it("in progress status with documents matches snapshot", () => {
      const claim = new MockBenefitsApplicationBuilder().submitted().create();
      const wrapper = mount(
        <ApplicationCardV2
          appLogic={appLogic}
          claim={claim}
          documents={testDocuments}
          number={2}
        />
      );

      expect(wrapper).toMatchSnapshot();
    });

    it("in progress status with no EIN does not show the EIN title section", () => {
      const claim = new MockBenefitsApplicationBuilder().address().create();
      const wrapper = mount(
        <ApplicationCardV2 appLogic={appLogic} claim={claim} number={2} />
      );

      expect(wrapper.find("TitleAndDetailSectionItem").exists()).toBeFalsy();
    });

    it("completed status matches snapshot", () => {
      const claim = new MockBenefitsApplicationBuilder().completed().create();
      const wrapper = mount(<ApplicationCardV2 claim={claim} />);

      expect(wrapper).toMatchSnapshot();
    });
  });
});
