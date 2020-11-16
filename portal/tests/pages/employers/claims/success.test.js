import Success from "../../../../src/pages/employers/claims/success";
import { renderWithAppLogic } from "../../../test-utils";

describe("Success", () => {
  it("renders Success page", () => {
    const query = { absence_id: "test-absence-id" };
    const { wrapper } = renderWithAppLogic(Success, {
      diveLevels: 1,
      props: { query },
    });

    expect(wrapper).toMatchSnapshot();
  });
});
