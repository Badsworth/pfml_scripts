import { MockEmployerClaimBuilder, renderPage } from "../../../test-utils";
import EmployerClaim from "../../../../src/models/EmployerClaim";
import Success from "../../../../src/pages/employers/applications/success";

describe("Success", () => {
  it("renders the page", () => {
    const claim = new MockEmployerClaimBuilder()
      .completed()
      .reviewed()
      .create();
    const { container } = renderPage(
      Success,
      {
        addCustomSetup: (appLogic) => {
          appLogic.employers.claim = new EmployerClaim(claim);
          appLogic.portalFlow.getNextPageRoute = jest.fn();
        },
      },
      {
        query: { absence_id: "NTN-111-ABS-01" },
      }
    );

    expect(container).toMatchSnapshot();
  });
});
