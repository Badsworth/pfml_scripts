import React, {
  ReactChild,
  ReactFragment,
  ReactPortal,
  MouseEvent,
  useState,
} from "react";
import { create } from "react-test-renderer";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import SlideOut, {
  Props as SlideOutProps,
} from "../../src/components/SlideOut";

// Make all optional for passed props so we
// only have to pass what we want to test
type PassedProps<T = unknown> = {
  title?: string;
  isOpen?: boolean;
  close?: (event: MouseEvent) => void;
  open?: (data?: T) => (event: MouseEvent) => void;
  data?: T;
  children?:
    | ((data?: T) => JSX.Element)
    | ReactChild
    | ReactFragment
    | ReactPortal;
};

type Test = {
  first_name: string;
  last_name: string;
};

const renderComponent = (passedProps: PassedProps<Test> = {}) => {
  // Prop defaults
  const props: SlideOutProps<Test> = {
    title: "Test SlideOut Title",
    // Overwrite defaults with passed props
    ...passedProps,
  };

  return render(<SlideOut<Test> {...props} />);
};

describe("SlideOut", () => {
  test("renders the default component", () => {
    const props: SlideOutProps<Test> = {
      title: "Test SlideOut Title",
    };

    const component = create(<SlideOut<Test> {...props} />).toJSON();
    expect(component).toMatchSnapshot();
  });

  test("children render correctly when passed as a function", () => {
    renderComponent({
      children: (() => <h1>This is a test body.</h1>) as (
        data?: Test,
      ) => JSX.Element,
    });

    expect(screen.getByTestId("slideout-body")).toContainHTML(
      "<h1>This is a test body.</h1>",
    );
  });
});
