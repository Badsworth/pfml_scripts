import { render, screen } from "@testing-library/react";
import BackButton from "../../src/components/BackButton";
import React from "react";
import tracker from "../../src/services/tracker";
import userEvent from "@testing-library/user-event";

function mockHistoryApi(length) {
  class MockHistory {
    back() {}

    get length() {
      return length;
    }
  }

  return new MockHistory();
}

describe("<BackButton>", () => {
  beforeEach(() => {
    // Simulate browser history so the button thinks there's a page to go back to
    history.pushState({}, "Mock page");
  });

  it("renders the back button", () => {
    const { container } = render(<BackButton />);

    expect(container.firstChild).toHaveAccessibleName("Back");
  });

  it("does not render the back button when there's no page to go back to", () => {
    const mockHistory = mockHistoryApi(1);

    const { container } = render(<BackButton history={mockHistory} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("routes to previous page when clicked", () => {
    const spy = jest.spyOn(window.history, "back");

    render(<BackButton />);

    userEvent.click(screen.getByRole("button"));

    expect(spy).toHaveBeenCalledTimes(1);
  });

  it("tracks event when clicked", () => {
    const spy = jest.spyOn(tracker, "trackEvent");

    render(<BackButton />);

    userEvent.click(screen.getByRole("button"));

    expect(spy).toHaveBeenCalledWith("BackButton clicked", {
      behaveLikeBrowserBackButton: true,
    });
  });

  it("sets back button label", () => {
    const label = "Back to checklist";
    const { container } = render(<BackButton label={label} />);

    expect(container.firstChild).toHaveAccessibleName(label);
  });

  it("renders button link when href prop is defined", () => {
    render(<BackButton href="/prev" />);
    const link = screen.getByRole("link");
    expect(link).toBeInTheDocument();

    expect(link).toHaveAccessibleName("Back");
    expect(link).toHaveAttribute("href", "/prev");
  });

  it("tracks event when the link is clicked", () => {
    const spy = jest.spyOn(tracker, "trackEvent");

    render(<BackButton href="/prev" />);

    userEvent.click(screen.getByRole("link"));

    expect(spy).toHaveBeenCalledWith("BackButton clicked", {
      behaveLikeBrowserBackButton: false,
    });
  });
});
