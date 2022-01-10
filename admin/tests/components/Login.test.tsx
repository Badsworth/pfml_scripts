import React from "react";
import { create } from "react-test-renderer";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";
import Login, { Props as LoginProps } from "../../src/components/Login";
import * as api from "../../src/_api";
import { LoadingState } from "../../src/pages/_app";
import * as azureAuth from "../../src/utils/azure_sso_authorization";
import { mocked } from "ts-jest/utils";
import isClient from "../../src/utils/isClient";
import mockRouter from "next/router";

jest.mock("next/router", () => require("next-router-mock"));
jest.mock("../../src/utils/isClient", () => {
  return jest.fn(() => true);
});
const mockedIsClient = mocked(isClient);

// Make all optional for passed props so we
// only have to pass what we want to test
type PassedProps = {
  error?: Partial<api.ErrorResponse> | undefined;
  setError?: React.Dispatch<
    React.SetStateAction<Partial<api.ErrorResponse> | undefined>
  >;
  loadingState?: LoadingState;
  setLoadingState?: React.Dispatch<React.SetStateAction<LoadingState>>;
};

const renderComponent = (passedProps: PassedProps = {}) => {
  // Prop defaults
  const props: LoginProps = {
    error: undefined,
    setError: jest.fn(),
    loadingState: {
      loading: false,
      loggingIn: false,
      loggingOut: false,
    },
    setLoadingState: jest.fn(),
    // Overwrite defaults with passed props
    ...passedProps,
  };

  return render(<Login {...props} />);
};

describe("Login", () => {
  test("renders the default component", () => {
    const props: LoginProps = {
      error: undefined,
      setError: jest.fn(),
      loadingState: {
        loading: false,
        loggingIn: false,
        loggingOut: false,
      },
      setLoadingState: jest.fn(),
    };

    const component = create(<Login {...props} />).toJSON();
    expect(component).toMatchSnapshot();
  });

  test("executes authentication flow when login is clicked", async () => {
    const loginFunction = jest.spyOn(azureAuth, "startLogin");

    renderComponent();

    userEvent.click(screen.getByText("Login"));

    expect(loginFunction).toHaveBeenCalled();
  });

  test("renders successful logged out alert", () => {
    mockRouter.query.logged_out = "true";

    renderComponent();

    expect(
      screen.getByText("You have successfully logged out!"),
    ).toBeInTheDocument();
  });

  test("renders error alert when error is present", () => {
    // This is not necessary for this test but covers the
    // isClient() if check in Login component
    mockedIsClient.mockReturnValue(false);

    renderComponent({
      error: {
        data: {
          message: "This is a test error!",
        },
      },
    });

    expect(screen.getByText("This is a test error!")).toBeInTheDocument();
  });
});
