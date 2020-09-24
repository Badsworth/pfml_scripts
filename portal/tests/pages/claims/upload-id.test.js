import {
  MockClaimBuilder,
  makeFile,
  renderWithAppLogic,
} from "../../test-utils";
import UploadId from "../../../src/pages/claims/upload-id";
import { act } from "react-dom/test-utils";

jest.mock("../../../src/hooks/useAppLogic");

describe("UploadId", () => {
  let appLogic, claim, wrapper;

  function render() {
    ({ appLogic, wrapper } = renderWithAppLogic(UploadId, {
      claimAttrs: claim,
    }));
  }
  describe("when the user has a Mass ID", () => {
    it("renders the page with Mass ID content", () => {
      claim = { has_state_id: true };
      render();
      expect(wrapper).toMatchSnapshot();
    });
  });

  describe("when the user doesn't have a Mass ID", () => {
    it("renders the page with 'Other' ID content", () => {
      claim = { has_state_id: false };
      render();
      expect(wrapper).toMatchSnapshot();
    });
  });

  describe("when the user uploads files", () => {
    it("renders filecards for the files", () => {
      render();
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
    it("calls claimsLogic.documents.attach", async () => {
      claim = new MockClaimBuilder().create();
      render();
      const files = [makeFile(), makeFile()];
      const formattedFiles = files.map((file) => {
        return { id: expect.any(String), file };
      });
      const event = {
        target: {
          files,
        },
      };
      const input = wrapper.find("FileCardList").dive().find("input");
      input.simulate("change", event);
      await act(async () => {
        await wrapper.find("QuestionPage").simulate("save");
      });

      expect(appLogic.documents.attach).toHaveBeenCalledWith(
        claim.application_id,
        formattedFiles,
        expect.any(String)
      );
    });
  });
});
