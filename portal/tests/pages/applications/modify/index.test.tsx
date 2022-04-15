import ApiResourceCollection from "../../../../src/models/ApiResourceCollection";
import ChangeRequest from "../../../../src/models/ChangeRequest";
import Index from "../../../../src/pages/applications/modify/index";
import { act } from "react-dom/test-utils";
import { renderPage } from "../../../test-utils";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

jest.mock("../../../../src/hooks/useAppLogic");

const props = {
  query: { absence_id: "7180eae0-0ad8-46a9-b140-5076863330d2" },
};

const goToNextPage = jest.fn();

const setup = () => {
  return renderPage(
    Index,
    {
      addCustomSetup: (appLogic) => {
        appLogic.changeRequests.changeRequests =
          new ApiResourceCollection<ChangeRequest>("change_request_id", []);
        appLogic.portalFlow.goToNextPage = goToNextPage;
      },
    },
    props
  );
};

beforeEach(() => {
  process.env.featureFlags = JSON.stringify({
    claimantShowModifications: true,
  });
});

describe("Claim Modification Index", () => {
  it("renders page content", () => {
    const { container } = setup();
    expect(container).toMatchSnapshot();
  });

  it("renders PageNotFound if the claimantShowModifications feature flag is not set", () => {
    process.env.featureFlags = JSON.stringify({
      claimantShowModification: false,
    });
    setup();

    const pageNotFoundHeading = screen.getByRole("heading", {
      name: /Page not found/,
    });
    expect(pageNotFoundHeading).toBeInTheDocument();
  });

  describe("button click", () => {
    beforeEach(async () => {
      setup();
      const submitButton = screen.getByRole("button");
      await act(async () => {
        await userEvent.click(submitButton);
      });
    });

    it("goes to next page", () => {
      expect(goToNextPage).toHaveBeenCalledWith(
        expect.objectContaining({ changeRequest: expect.any(ChangeRequest) }),
        {
          absence_id: props.query.absence_id,
          change_request_id: "change-request-id",
        }
      );
    });
  });
});
