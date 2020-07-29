import { makeFile, renderWithAppLogic } from "../../test-utils";
import UploadOtherId from "../../../src/pages/claims/upload-other-id";
import { act } from "react-dom/test-utils";

describe("UploadOtherId", () => {
  let wrapper;

  beforeEach(() => {
    ({ wrapper } = renderWithAppLogic(UploadOtherId));
  });

  it("initially renders the page without any filecards", () => {
    expect(wrapper).toMatchSnapshot();
  });

  describe("when the user uploads files", () => {
    it("renders filecards for the files", () => {
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
