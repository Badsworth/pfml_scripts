import { makeFile, renderWithAppLogic } from "../../test-utils";
import { LeaveReason } from "../../../src/models/Claim";
import UploadCertification from "../../../src/pages/claims/upload-certification";

jest.mock("../../../src/hooks/useAppLogic");

function render(reason = LeaveReason.medical) {
  const { wrapper } = renderWithAppLogic(UploadCertification, {
    claimAttrs: { leave_details: { reason } },
  });

  return wrapper;
}

describe("UploadCertification", () => {
  it("initially renders an empty FileCardList", () => {
    const wrapper = render();

    expect(wrapper.find("FileCardList")).toMatchSnapshot();
  });

  describe("when leave reason is Medical leave", () => {
    it("renders page with medical leave content", () => {
      const wrapper = render(LeaveReason.medical);

      // Only take snapshots of the i18n content
      expect(wrapper.find("Heading")).toMatchSnapshot();
      expect(wrapper.find("Trans").dive()).toMatchSnapshot();
    });
  });

  describe("when leave reason is Bonding leave", () => {
    it("renders page with bonding leave content", () => {
      const wrapper = render(LeaveReason.bonding);

      // Only take snapshots of the i18n content
      expect(wrapper.find("Heading")).toMatchSnapshot();
      expect(wrapper.find("Trans").dive()).toMatchSnapshot();
    });
  });

  describe("when the user uploads files", () => {
    it("passes files to FileCardList", () => {
      const wrapper = render();
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
