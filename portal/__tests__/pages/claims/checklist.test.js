import Checklist from "../../../src/pages/claims/checklist";
import { renderWithAppLogic } from "../../test-utils";

describe("Checklist", () => {
  it("renders page", () => {
    const { wrapper } = renderWithAppLogic(Checklist);

    expect(wrapper).toMatchSnapshot();
  });
});
