import React from "react";
import { create } from "react-test-renderer";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";
import VerticalMenu, {
  Option as VerticalMenuOption,
  Props as VerticalMenuProps,
} from "../../src/components/VerticalMenu";

// Make all optional for passed props so we
// only have to pass what we want to test
type PassedProps = {
  options?: VerticalMenuOption[];
};

const renderComponent = (passedProps: PassedProps = {}) => {
  // Prop defaults
  const props: VerticalMenuProps = {
    options: [
      {
        enabled: true,
        text: "Test Option",
        type: "button",
      },
    ],
    // Overwrite defaults with passed props
    ...passedProps,
  };

  return render(<VerticalMenu {...props} />);
};

describe("VerticalMenu", () => {
  test("renders the default component", () => {
    const props: VerticalMenuProps = {
      options: [
        {
          enabled: true,
          text: "Test Option",
          type: "button",
        },
      ],
    };

    const component = create(<VerticalMenu {...props} />).toJSON();
    expect(component).toMatchSnapshot();
  });

  test("renders menu with enabled buttons", () => {
    renderComponent({
      options: [
        {
          enabled: true,
          text: "Button One",
          type: "button",
          onClick: jest.fn(),
        },
        {
          enabled: true,
          text: "Button Two",
          type: "button",
          onClick: jest.fn(),
        },
      ],
    });

    userEvent.click(screen.getByTestId("vertical-menu-trigger"));

    expect(
      screen.getByRole("button", { name: "Button One" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Button Two" }),
    ).toBeInTheDocument();
  });

  test("renders menu with disabled buttons", () => {
    renderComponent({
      options: [
        {
          enabled: false,
          text: "Button One",
          type: "button",
          onClick: jest.fn(),
        },
        {
          enabled: false,
          text: "Button Two",
          type: "button",
          onClick: jest.fn(),
        },
      ],
    });

    userEvent.click(screen.getByTestId("vertical-menu-trigger"));

    expect(
      screen.queryByRole("button", { name: "Button One" }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Button Two" }),
    ).not.toBeInTheDocument();

    expect(screen.getByText("Button One")).toBeInTheDocument();
    expect(screen.getByText("Button Two")).toBeInTheDocument();
  });

  test("renders menu with enabled links", () => {
    renderComponent({
      options: [
        {
          enabled: true,
          text: "Link One",
          type: "link",
          href: "#",
        },
        {
          enabled: true,
          text: "Link Two",
          type: "link",
          href: "#",
        },
      ],
    });

    userEvent.click(screen.getByTestId("vertical-menu-trigger"));

    expect(screen.getByRole("link", { name: "Link One" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Link Two" })).toBeInTheDocument();
  });

  test("renders menu with disabled links", () => {
    renderComponent({
      options: [
        {
          enabled: false,
          text: "Link One",
          type: "link",
          href: "#",
        },
        {
          enabled: false,
          text: "Link Two",
          type: "link",
          href: "#",
        },
      ],
    });

    userEvent.click(screen.getByTestId("vertical-menu-trigger"));

    expect(
      screen.queryByRole("link", { name: "Link One" }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("link", { name: "Link Two" }),
    ).not.toBeInTheDocument();

    expect(screen.getByText("Link One")).toBeInTheDocument();
    expect(screen.getByText("Link Two")).toBeInTheDocument();
  });

  test("fires `onClick` callback prop when button is clicked", () => {
    const onClick = jest.fn();

    renderComponent({
      options: [
        {
          enabled: true,
          text: "Button One",
          type: "button",
          onClick: onClick,
        },
        {
          enabled: true,
          text: "Button Two",
          type: "button",
          onClick: jest.fn(),
        },
      ],
    });

    userEvent.click(screen.getByTestId("vertical-menu-trigger"));
    userEvent.click(screen.getByRole("button", { name: "Button One" }));

    expect(onClick).toHaveBeenCalled();
  });
});
