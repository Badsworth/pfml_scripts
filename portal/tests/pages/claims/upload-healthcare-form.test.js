import { makeFile, renderWithAppLogic } from "../../test-utils";
import UploadHealthcareForm from "../../../src/pages/claims/upload-healthcare-form";

jest.mock("../../../src/hooks/useAppLogic");

describe("UploadHealthcareForm", () => {
  let wrapper;

  beforeEach(() => {
    ({ wrapper } = renderWithAppLogic(UploadHealthcareForm));
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
