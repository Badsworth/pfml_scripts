import Type from "src/pages/applications/modify/type";
import { renderPage } from "../../../test-utils";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

jest.mock("../../../../src/hooks/useAppLogic");

const props = {
  query: { change_request_id: "7180eae0-0ad8-46a9-b140-5076863330d2" },
};

const setup = () => {
  return renderPage(
    Type,
    {
      addCustomSetup: (_appLogic) => null,
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
});
