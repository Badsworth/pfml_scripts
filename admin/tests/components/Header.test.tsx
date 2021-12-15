import React from "react";
import { create } from "react-test-renderer";
import { act, fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";
import Header from "../../src/components/Header";
import { Props as HeaderProps } from "../../src/components/Header";
import * as api from "../../src/_api";
import { LoadingState } from "../../src/pages/_app";
import * as azureAuth from "../../src/utils/azure_sso_authorization";

// Make all optional for passed props so we
// only have to pass what we want to test
type PassedProps = {
  showUserOptions?: boolean;
  user?: api.AdminUserResponse | null;
  setUser?: React.Dispatch<React.SetStateAction<api.AdminUserResponse | null>>;
  setError?: React.Dispatch<
    React.SetStateAction<Partial<api.ErrorResponse | undefined>>
  >;
  loadingState?: LoadingState;
  setLoadingState?: React.Dispatch<React.SetStateAction<LoadingState>>;
};

const renderComponent = (passedProps: PassedProps = {}) => {
  // Prop defaults
  const props: HeaderProps = {
    user: {
      email_address: "john.smith@email.com",
      first_name: "John",
      groups: [],
      last_name: "Smith",
      permissions: [],
      sub_id: "abc123",
    },
    setUser: jest.fn(),
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

  return render(<Header {...props} />);
};

describe("Header", () => {
  test("renders the default component", () => {
    const props: HeaderProps = {
      user: null,
      setUser: jest.fn(),
      setError: jest.fn(),
      loadingState: {
        loading: false,
        loggingIn: false,
        loggingOut: false,
      },
      setLoadingState: jest.fn(),
    };

    const component = create(<Header {...props} />).toJSON();
    expect(component).toMatchSnapshot();
  });

  test("shows dropdown when user options trigger is clicked", () => {
    renderComponent();

    expect(
      screen.queryByTestId("user-options-dropdown"),
    ).not.toBeInTheDocument();

    userEvent.click(screen.getByTestId("user-options-trigger"));

    expect(screen.getByTestId("user-options-dropdown")).toBeInTheDocument();
  });

  test("hides dropdown when dropdown is open and user clicks to close it", () => {
    renderComponent();

    userEvent.click(screen.getByTestId("user-options-trigger"));

    expect(screen.getByTestId("user-options-dropdown")).toBeInTheDocument();

    userEvent.click(screen.getByTestId("user-options-trigger"));

    expect(
      screen.queryByTestId("user-options-dropdown"),
    ).not.toBeInTheDocument();
  });

  test("hides dropdown when user mouses out", async () => {
    jest.useFakeTimers();

    renderComponent();

    userEvent.click(screen.getByTestId("user-options-trigger"));

    expect(screen.getByTestId("user-options-dropdown")).toBeInTheDocument();

    act(() => {
      userEvent.unhover(screen.getByTestId("user-options"));
      jest.advanceTimersByTime(500);
    });

    expect(
      screen.queryByTestId("user-options-dropdown"),
    ).not.toBeInTheDocument();

    jest.useRealTimers();
  });

  test("dropdown remains hidden when user mouses over and out of closed user dropdown", () => {
    renderComponent();

    userEvent.hover(screen.getByTestId("user-options"));
    userEvent.unhover(screen.getByTestId("user-options"));

    expect(
      screen.queryByTestId("user-options-dropdown"),
    ).not.toBeInTheDocument();
  });

  test("hides dropdown when focus leaves", () => {
    renderComponent();

    userEvent.click(screen.getByTestId("user-options-trigger"));

    expect(screen.getByTestId("user-options-dropdown")).toBeInTheDocument();
    expect(screen.getByTestId("user-options-trigger")).toHaveFocus();

    userEvent.tab(); // Tab from trigger to sign out
    userEvent.tab(); // Tab out of the dropdown from sign out

    expect(screen.getByTestId("user-options-trigger")).not.toHaveFocus();
    expect(
      screen.queryByTestId("user-options-dropdown"),
    ).not.toBeInTheDocument();
  });

  test("calls logout function when logout is clicked", () => {
    const logoutFunction = jest.spyOn(azureAuth, "logout");

    renderComponent();

    userEvent.click(screen.getByTestId("user-options-trigger"));
    userEvent.click(screen.getByText("Sign out"));

    expect(logoutFunction).toHaveBeenCalled();
  });
});
