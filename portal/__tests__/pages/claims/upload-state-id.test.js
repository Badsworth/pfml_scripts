import { makeFile, renderWithAppLogic } from "../../test-utils";
import UploadStateId from "../../../src/pages/claims/upload-state-id";

describe("UploadStateId", () => {
  let wrapper;

  beforeEach(() => {
    ({ wrapper } = renderWithAppLogic(UploadStateId));
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
      input.simulate("change", event);

      expect(wrapper).toMatchSnapshot();
    });
  });

  describe("when the form is successfully submitted", () => {
    it.todo("uploads the files to the API");
  });
});
