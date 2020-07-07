import { makeFile, testHook } from "../../test-utils";
import Claim from "../../../src/models/Claim";
import React from "react";
import { UploadHealthcareForm } from "../../../src/pages/claims/upload-healthcare-form";
import { shallow } from "enzyme";
import useAppLogic from "../../../src/hooks/useAppLogic";

jest.mock("../../../src/hooks/useAppLogic");

describe("UploadHealthcareForm", () => {
  let appLogic, claim, wrapper;

  beforeEach(() => {
    claim = new Claim({ application_id: "mock-claim-id" });

    testHook(() => {
      appLogic = useAppLogic({ user: {} });
    });

    wrapper = shallow(
      <UploadHealthcareForm
        appLogic={appLogic}
        claim={claim}
        query={{ claim_id: claim.application_id }}
      />
    );
  });

  it("initially renders the page without any file cards", () => {
    expect(wrapper).toMatchSnapshot();
  });

  describe("when the user uploads files", () => {
    it("passes files to FileCardList", () => {
      const files = [makeFile(), makeFile(), makeFile()];
      const event = {
        target: {
          files,
        },
      };
      const input = wrapper.find("FileCardList").dive().find("input");
      input.simulate("change", event);

      expect(wrapper.find("FileCardList").prop("files")).toHaveLength(3);
    });
  });

  describe("when the form is successfully submitted", () => {
    it.todo("uploads the files to the API");
  });
});
