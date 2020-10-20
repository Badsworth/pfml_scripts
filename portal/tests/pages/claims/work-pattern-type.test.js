import WorkPatternType from "../../../src/pages/claims/work-pattern-type";
import { renderWithAppLogic } from "../../test-utils";

jest.mock("../../../src/hooks/useAppLogic");

describe("WorkPatternType", () => {
  it("renders the page with expected content", () => {
    const { wrapper } = renderWithAppLogic(WorkPatternType);

    expect(wrapper).toMatchSnapshot();
  });
});
