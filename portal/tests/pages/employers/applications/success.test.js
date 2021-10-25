import Success from "../../../../src/pages/employers/applications/success";
import { renderPage } from "../../../test-utils/renderPage";

describe("Success", () => {
  it("renders the page", () => {
    const { container } = renderPage(
      Success,
      {
        addCustomSetup: (appLogicHook) => {
          appLogicHook.portalFlow.getNextPageRoute = jest.fn();
          appLogicHook.pathname = "";
        },
      },
      {
        query: { absence_id: "my-absence-id" },
      }
    );

    expect(container).toMatchSnapshot();
  });
});
