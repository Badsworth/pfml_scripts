import ReasonPregnancy from "../../../src/pages/applications/reason-pregnancy";
import { renderWithAppLogic } from "../../test-utils";

describe("ReasonPregnancy", () => {
  it("renders the page", () => {
    const { wrapper } = renderWithAppLogic(ReasonPregnancy, {
      claimAttrs: {
        leave_details: {
          pregnant_or_recent_birth: false,
        },
      },
    });

    expect(wrapper).toMatchSnapshot();
  });
});
