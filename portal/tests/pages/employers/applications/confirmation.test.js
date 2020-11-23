import Confirmation from "../../../../src/pages/employers/applications/confirmation";
import { renderWithAppLogic } from "../../../test-utils";

describe("Confirmation", () => {
  it("renders Confirmation page", () => {
    const query = { absence_id: "test-absence-id", due_date: "2022-01-01" };
    const { wrapper } = renderWithAppLogic(Confirmation, {
      diveLevels: 1,
      props: { query },
    });

    expect(wrapper).toMatchSnapshot();
  });
});
