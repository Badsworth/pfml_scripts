import { makeFile, renderWithAppLogic } from "../../test-utils";
import UploadId from "../../../src/pages/claims/upload-id";
import { act } from "react-dom/test-utils";

jest.mock("../../../src/hooks/useAppLogic");

describe("UploadId", () => {
  describe("when the user has a Mass ID", () => {
    it("renders the page with Mass ID content", () => {
      const { wrapper } = renderWithAppLogic(UploadId, {
        claimAttrs: { has_state_id: true },
      });

      expect(wrapper).toMatchSnapshot();
    });
  });

  describe("when the user doesn't have a Mass ID", () => {
    it("renders the page with 'Other' ID content", () => {
      const { wrapper } = renderWithAppLogic(UploadId, {
        claimAttrs: { has_state_id: false },
      });

      expect(wrapper).toMatchSnapshot();
    });
  });

  describe("when the user uploads files", () => {
    it("renders filecards for the files", () => {
      const { wrapper } = renderWithAppLogic(UploadId);

      const files = [makeFile(), makeFile(), makeFile()];
      const event = {
        target: {
          files,
        },
      };

      const input = wrapper.find("FileCardList").dive().find("input");
      act(() => {
        input.simulate("change", event);
      });

      expect(wrapper).toMatchSnapshot();
    });
  });

  describe("when the form is successfully submitted", () => {
    it.todo("uploads the files to the API");
  });
});
