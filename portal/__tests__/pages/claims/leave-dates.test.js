import LeaveDates from "../../../src/pages/claims/leave-dates";
import { renderWithAppLogic } from "../../test-utils";

describe("LeaveDates", () => {
  it("renders the page", () => {
    const { wrapper } = renderWithAppLogic(LeaveDates);

    expect(wrapper).toMatchSnapshot();
  });
});
