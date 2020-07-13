import DateOfBirth from "../../../src/pages/claims/date-of-birth";
import { act } from "react-dom/test-utils";
import { mockUpdateUser } from "../../../src/api/UsersApi";
import { renderWithAppLogic } from "../../test-utils";

jest.mock("../../../src/api/UsersApi");

describe("DateOfBirth", () => {
  let wrapper;

  beforeEach(() => {
    ({ wrapper } = renderWithAppLogic(DateOfBirth));
  });

  it("renders the page", () => {
    expect(wrapper).toMatchSnapshot();
  });

  describe("when the form is successfully submitted", () => {
    it("calls updateUser and updates the state", async () => {
      expect.assertions();
      await act(async () => {
        await wrapper.find("QuestionPage").simulate("save");
      });
      expect(mockUpdateUser).toHaveBeenCalledTimes(1);
    });
  });
});
