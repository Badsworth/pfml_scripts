import PaginationNavigation, {
  getTruncatedPageRange,
} from "../../src/components/PaginationNavigation";
import { render, screen, within } from "@testing-library/react";
import React from "react";
import userEvent from "@testing-library/user-event";

const onClick = jest.fn();
const renderComponent = (customProps) => {
  const props = {
    pageOffset: 2,
    totalPages: 3,
    onClick,
    ...customProps,
  };
  return render(<PaginationNavigation {...props} />);
};

describe("PaginationNavigation", () => {
  it("renders the component with a truncated pagination range", () => {
    const { container } = renderComponent({ totalPages: 10 });
    expect(screen.getAllByRole("button")).toHaveLength(11);
    expect(container.firstChild).toMatchSnapshot();
  });

  it("displays a link for previous, next, and each page number", () => {
    renderComponent({ totalPages: 2 });

    const [previous, goToOne, goToTwo, next] = screen.getAllByRole("button");

    expect(within(previous).getByText(/Previous/)).toBeInTheDocument();
    expect(within(next).getByText(/Next/)).toBeInTheDocument();
    expect(within(goToOne).getByText(/1/)).toBeInTheDocument();
    expect(within(goToTwo).getByText(/2/)).toBeInTheDocument();
  });

  it("calls function to fetch updated list when a page is selected", () => {
    renderComponent();
    userEvent.click(screen.getByRole("button", { name: "Go to Page 3" }));
    expect(onClick).toHaveBeenCalledWith(3);
  });

  it("calls function to fetch updated list when 'Previous' is clicked", () => {
    renderComponent();
    userEvent.click(
      screen.getByRole("button", { name: "Go to Previous page" })
    );
    expect(onClick).toHaveBeenCalledWith(1); // 1st page
  });

  it("calls function to fetch updated list when 'Next' is clicked", () => {
    renderComponent();
    userEvent.click(screen.getByRole("button", { name: "Go to Next page" }));
    expect(onClick).toHaveBeenCalledWith(3); // 3rd page
  });

  describe("when selected page is first page", () => {
    it("disables the 'Previous' link", () => {
      renderComponent({ pageOffset: 1 });
      expect(
        screen.getByRole("button", { name: "Go to Previous page" })
      ).toHaveAttribute("aria-disabled", "true");
    });

    it("does not call function to fetch updated list when 'Previous' is clicked", () => {
      renderComponent({ pageOffset: 1 });
      const previous = screen.getByRole("button", {
        name: "Go to Previous page",
      });
      userEvent.click(previous);
      expect(onClick).not.toHaveBeenCalled();
    });
  });

  describe("when selected page is last page", () => {
    it("disables the 'Next' link", () => {
      renderComponent({ pageOffset: 3, totalPages: 3 });
      expect(
        screen.getByRole("button", { name: "Go to Next page" })
      ).toHaveAttribute("aria-disabled", "true");
    });

    it("does not call function to fetch updated list when 'Next' is clicked", () => {
      renderComponent({ pageOffset: 3, totalPages: 3 });
      const next = screen.getByRole("button", { name: "Go to Next page" });
      userEvent.click(next);
      expect(onClick).not.toHaveBeenCalled();
    });
  });
});

describe("getTruncatedPageRange", () => {
  it("does not truncate", () => {
    expect(getTruncatedPageRange(1, 9)).toEqual([1, 2, 3, 4, 5, 6, 7, 8, 9]);
    expect(getTruncatedPageRange(1, 1)).toEqual([1]);
  });

  it("truncates left and right side", () => {
    const range = getTruncatedPageRange(10, 30);
    expect(range).toEqual([1, "spacer", 7, 8, 9, 10, 11, 12, 13, "spacer", 30]);
  });

  it("truncates only left side", () => {
    const rangeA = getTruncatedPageRange(30, 30);
    const rangeB = getTruncatedPageRange(26, 30);

    expect(rangeA).toEqual([1, "spacer", 23, 24, 25, 26, 27, 28, 29, 30]);
    expect(rangeB).toEqual([1, "spacer", 23, 24, 25, 26, 27, 28, 29, 30]);
  });

  it("truncates only right side", () => {
    const rangeA = getTruncatedPageRange(1, 30);
    const rangeB = getTruncatedPageRange(5, 30);

    expect(rangeA).toEqual([1, 2, 3, 4, 5, 6, 7, 8, "spacer", 30]);
    expect(rangeB).toEqual([1, 2, 3, 4, 5, 6, 7, 8, "spacer", 30]);
  });
});
