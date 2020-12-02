import Confirmation from "../../../../src/pages/employers/applications/confirmation";
import { renderWithAppLogic } from "../../../test-utils";

describe("Confirmation", () => {
  let wrapper;

  const renderPage = (query) => {
    ({ wrapper } = renderWithAppLogic(Confirmation, {
      diveLevels: 1,
      props: { query },
    }));
  };

  it("renders the page", () => {
    const query = {
      absence_id: "test-absence-id",
      follow_up_date: "2022-01-01",
    };
    renderPage(query);

    expect(wrapper).toMatchSnapshot();
    expect(wrapper.find("Trans")).toHaveLength(3);
  });

  it("does not display due date if not provided", () => {
    const query = { absence_id: "test-absence-id", follow_up_date: null };
    renderPage(query);

    expect(wrapper.find("Trans")).toHaveLength(2);
  });
});
