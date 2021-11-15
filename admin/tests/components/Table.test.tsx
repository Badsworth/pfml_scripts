import React from "react";
import { create } from "react-test-renderer";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";
import Table, { Props as TableProps } from "../../src/components/Table";

// Make all optional for passed props so we
// only have to pass what we want to test
type PassedProps<T = unknown> = {
  rows?: T[];
  cols?: {
    title?: string;
    width?: string;
    align?: "left" | "center" | "right" | "justify" | "char" | undefined;
    content: (data: T) => React.ReactChild;
  }[];
  hideHeaders?: boolean;
  noResults?: JSX.Element;
  rowClasses?: string;
  colClasses?: string;
};

type Test = {
  title: string;
  description: string;
};

const mockGetTitle = (t: Test) => <>{t.title}</>;
const mockGetDescription = (t: Test) => <>{t.description}</>;
const mockProps = {
  rows: [
    {
      title: "Test One",
      description: "Test description one",
    },
    {
      title: "Test Two",
      description: "Test description two",
    },
  ],
  cols: [
    {
      title: "Title",
      width: "25%",
      content: mockGetTitle,
    },
    {
      title: "Description",
      width: "75%",
      content: mockGetDescription,
    },
  ],
};

const renderComponent = (passedProps: PassedProps<Test> = {}) => {
  // Prop defaults
  const props: TableProps<Test> = {
    ...mockProps,
    // Overwrite defaults with passed props
    ...passedProps,
  };

  return render(<Table {...props} />);
};

describe("ActionCard", () => {
  test("renders the default component", () => {
    const props: TableProps<Test> = {
      ...mockProps,
    };

    const component = create(<Table {...props} />).toJSON();
    expect(component).toMatchSnapshot();
  });

  test("does not render headers when `hideHeaders` prop is true", () => {
    renderComponent({
      hideHeaders: true,
    });

    expect(screen.queryByText("Title")).not.toBeInTheDocument();
    expect(screen.queryByText("Description")).not.toBeInTheDocument();
  });

  test("renders 'no results' when no data is available", () => {
    renderComponent({
      rows: [],
      cols: [],
      noResults: <div>No test results found.</div>,
    });

    expect(screen.getByText("No test results found.")).toBeInTheDocument();
  });

  test("renders default 'no results' message when no data is available and `noResults` prop is not passed", () => {
    renderComponent({
      rows: [],
      cols: [],
    });

    expect(screen.getByText("No results found")).toBeInTheDocument();
  });
});
