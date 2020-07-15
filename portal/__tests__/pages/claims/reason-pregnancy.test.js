import ReasonPregnancy from "../../../src/pages/claims/reason-pregnancy";
import { renderWithAppLogic } from "../../test-utils";

describe("ReasonPregnancy", () => {
  it("renders the page", () => {
    const { wrapper } = renderWithAppLogic(ReasonPregnancy, {
      claimAttrs: { pregnant_or_recent_birth: false },
    });

    expect(wrapper).toMatchSnapshot();
  });
});
