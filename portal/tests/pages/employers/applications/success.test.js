import Success from "../../../../src/pages/employers/applications/success";
import { mockRouter } from "next/router";
import { renderWithAppLogic } from "../../../test-utils";
import routes from "../../../../src/routes";

describe("Success", () => {
  mockRouter.pathname = routes.employers.success;
  const query = { absence_id: "test-absence-id" };
  let wrapper;

  it("renders Success page", () => {
    ({ wrapper } = renderWithAppLogic(Success, {
      diveLevels: 1,
      props: { query },
    }));

    expect(wrapper).toMatchSnapshot();
  });
});
