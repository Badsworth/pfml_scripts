import { MockEmployerClaimBuilder, renderPage } from "../../../test-utils";
import Confirmation from "../../../../src/pages/employers/applications/confirmation";

describe("Confirmation", () => {
  it("renders the component", () => {
    const claim = new MockEmployerClaimBuilder()
      .completed()
      .reviewable(true)
      .absenceId("my-absence-id")
      .create();

    const { container } = renderPage(
      Confirmation,
      {
        addCustomSetup: (appLogicHook) => {
          appLogicHook.employers.claim = claim;
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
