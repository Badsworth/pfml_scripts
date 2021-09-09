import React from "react";
import { create } from "react-test-renderer";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import { mocked } from "ts-jest/utils";
import Search, { Props as SearchProps } from "../../src/components/Search";
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
  search?: (searchTerm: string) => Promise<unknown>;
  setResults?: any;
  debounceDelay?: number;
};

const mockUserData = [
  {
    name: "User 1",
    email: "user1@email.com",
    type: "Employee",
  },
  {
    name: "User 2",
    email: "user2@email.com",
    type: "Leave Admin",
  },
  {
    name: "User 3",
    email: "user3@email.com",
    type: "Employer",
  },
];

const renderComponent = (passedProps: PassedProps = {}) => {
  // Prop defaults
  const props: SearchProps = {
    search: jest.fn(() => Promise.resolve()),
    setResults: jest.fn((results: any) => results),
    // Overwrite defaults with passed props
    ...passedProps,
  };

  return render(<Search {...props} />);
};

describe("Search", () => {
  test("renders the default component", () => {
    const props: SearchProps = {
      search: jest.fn(() => Promise.resolve()),
      setResults: jest.fn((results: any) => results),
    };

    const component = create(<Search {...props} />).toJSON();
    expect(component).toMatchSnapshot();
  });

  test("typed input fires change event and setResults is called from debounce hook to set and show results", async () => {
    const setResults = jest.fn((results) => results);

    renderComponent({
      search: jest.fn((searchTerm) =>
        Promise.resolve(
          mockUserData.filter((u) => u.name.includes(searchTerm)),
        ),
      ),
      setResults: setResults,
    });

    fireEvent.change(screen.getByTestId("search-input"), {
      target: { value: "User" },
    });

    expect(screen.getByTestId("search-input")).toHaveValue("User");

    await waitFor(() => {
      expect(setResults).toHaveBeenCalled();
    });
  });

  test("default form submission is prevented", () => {
    renderComponent();

    const formSubmitted = fireEvent.submit(screen.getByTestId("search-form"));

    expect(formSubmitted).toBe(false);
  });

  test("saves the search term on user input", () => {
    mockedIsClient.mockReturnValue(true);
    const setItem = jest.spyOn(Storage.prototype, "setItem");

    renderComponent();
    fireEvent.change(screen.getByTestId("search-input"), {
      target: { value: "User" },
    });

    expect(setItem).toHaveBeenCalled();
  });

  test("does not save the search term", () => {
    mockedIsClient.mockReturnValue(false);
    const setItem = jest.spyOn(Storage.prototype, "setItem");

    renderComponent();
    fireEvent.change(screen.getByTestId("search-input"), {
      target: { value: "User" },
    });

    expect(setItem).not.toHaveBeenCalled();
  });

  test("sets the search term on page load when 'search' query parameter is set", () => {
    mockedIsClient.mockReturnValue(true);
    mockRouter.query.search = "User";

    renderComponent();

    expect(screen.getByTestId("search-input")).toHaveValue("User");
  });

  test("sets the search term when the 'search' query parameter changes", () => {
    mockedIsClient.mockReturnValue(true);
    mockRouter.pathname = "/users?search=User";

    renderComponent();

    expect(screen.getByTestId("search-input")).toHaveValue("User");
  });
});
