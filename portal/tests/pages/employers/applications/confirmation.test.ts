import { MockEmployerClaimBuilder, renderPage } from "../../../test-utils";
import Confirmation from "../../../../src/pages/employers/applications/confirmation";
import MockDate from "mockdate";

describe("Confirmation", () => {
  it("renders the component", () => {
    MockDate.set("2020-10-01");
    const claim = new MockEmployerClaimBuilder()
      .completed()
      .reviewable("2020-10-10")
      .absenceId("my-absence-id")
      .create();

    const { container } = renderPage(
      Confirmation,
      {
        addCustomSetup: (appLogicHook) => {
          appLogicHook.employers.claim = claim;
          appLogicHook.portalFlow.getNextPageRoute = jest.fn();
        },
      },
      {
        query: { absence_id: "my-absence-id" },
      }
    );

    expect(container).toMatchSnapshot();
  });
});
