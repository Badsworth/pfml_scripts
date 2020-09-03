import {
  MockClaimBuilder,
  makeFile,
  renderWithAppLogic,
} from "../../test-utils";
import UploadCertification from "../../../src/pages/claims/upload-certification";

jest.mock("../../../src/hooks/useAppLogic");

describe("UploadCertification", () => {
  let claim, wrapper;

  function render() {
    ({ wrapper } = renderWithAppLogic(UploadCertification, {
      claimAttrs: claim,
    }));
  }

  it("initially renders an empty FileCardList", () => {
    claim = new MockClaimBuilder().medicalLeaveReason().create();
    render();
    expect(wrapper.find("FileCardList")).toMatchSnapshot();
  });

  describe("when leave reason is Medical leave", () => {
    it("renders page with medical leave content", () => {
      claim = new MockClaimBuilder().medicalLeaveReason().create();
      render();
      // Only take snapshots of the i18n content
      expect(wrapper.find("Heading")).toMatchSnapshot();
      expect(wrapper.find("Trans").dive()).toMatchSnapshot();
    });
  });

  describe("when leave reason is Bonding leave", () => {
    it("renders page with bonding leave content", () => {
      claim = new MockClaimBuilder().bondingBirthLeaveReason().create();
      render();
      // Only take snapshots of the i18n content
      expect(wrapper.find("Heading")).toMatchSnapshot();
      expect(wrapper.find("Trans").dive()).toMatchSnapshot();
    });
  });

  describe("when the user uploads files", () => {
    it("passes files to FileCardList", () => {
      claim = new MockClaimBuilder().medicalLeaveReason().create();
      render();
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
