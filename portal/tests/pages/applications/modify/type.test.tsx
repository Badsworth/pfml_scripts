import ChangeRequest from "src/models/ChangeRequest";
import ClaimDetail from "src/models/ClaimDetail";
import Type from "src/pages/applications/modify/type";
import { act } from "react-dom/test-utils";
import { renderPage } from "../../../test-utils";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

jest.mock("../../../../src/hooks/useAppLogic");

const props = {
  query: {
    change_request_id: "7180eae0-0ad8-46a9-b140-5076863330d2",
    absence_id: "absence-id",
  },
};

const goToNextPage = jest.fn();

const setup = () => {
  return renderPage(
    Type,
    {
      addCustomSetup: (appLogic) => {
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

describe("Claim Modification Type", () => {
  it("renders page content", () => {
    const { container } = setup();
    expect(container.firstChild).toMatchSnapshot();
  });

  it("does not render the enter leave dates section", () => {
    setup();
    expect(
      screen.queryByText(/Enter your new leave end date/)
    ).not.toBeInTheDocument();
  });

  it("renders the enter leave dates when user chooses modification", () => {
    setup();

    userEvent.click(screen.getByLabelText(/Change my leave end date/));
    const label = screen.getByText(/Enter your new leave end date/);
    expect(label).toBeInTheDocument();
    expect(label.closest("fieldset")).toMatchSnapshot();

    userEvent.click(
      screen.getByLabelText(/Cancel my entire leave application/)
    );
    expect(
      screen.queryByText(/Enter your new leave end date/)
    ).not.toBeInTheDocument();
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
        expect.objectContaining({
          changeRequest: expect.any(ChangeRequest),
          claimDetail: expect.any(ClaimDetail),
        }),
        {
          absence_id: props.query.absence_id,
          change_request_id: props.query.change_request_id,
          claim_id: expect.any(String),
        }
      );
    });
  });
});
