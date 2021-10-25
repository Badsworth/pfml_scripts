import { render, screen } from "@testing-library/react";
import ConditionalContent from "../../src/components/ConditionalContent";
import React from "react";

const renderComponent = (customProps = {}) => {
  const defaultProps = {
    children: <h1>Hello I am a child</h1>,
    fieldNamesClearedWhenHidden: [],
    clearField: jest.fn(),
    getField: jest.fn(),
    updateFields: jest.fn(),
    visible: true,
    ...customProps,
  };
  return render(<ConditionalContent {...defaultProps} />);
};

describe("ConditionalContent", () => {
  it("renders children when visible is true", () => {
    renderComponent();
    expect(screen.getByText(/Hello I am a child/)).toBeInTheDocument();
  });

  it("doesn't render children when visible is false", () => {
    renderComponent({
      children: <h1>Hello I am a custom child</h1>,
      visible: false,
    });
    expect(
      screen.queryByText(/Hello I am a custom child/)
    ).not.toBeInTheDocument();
  });

  it("restores previous data when prop visible changes from true to false to true", () => {
    const clearField = jest.fn();
    const getField = jest.fn((name) => name + "_fetched");
    const updateField = jest.fn();
    const props = {
      children: <h1 name="hello">Hello I am a child</h1>,
      fieldNamesClearedWhenHidden: ["hello"],
      clearField,
      getField,
      updateFields: updateField,
      visible: true,
    };
    const { rerender } = render(<ConditionalContent {...props} />);
    expect(screen.getByText(/Hello I am a child/)).toBeInTheDocument();
    rerender(<ConditionalContent {...props} visible={false} />);
    expect(screen.queryByText(/Hello I am a child/)).not.toBeInTheDocument();
    expect(clearField).toHaveBeenNthCalledWith(1, "hello");
    rerender(<ConditionalContent {...props} visible={true} />);
    expect(screen.getByText(/Hello I am a child/)).toBeInTheDocument();
    expect(updateField).toHaveBeenNthCalledWith(1, { hello: "hello_fetched" });
  });

  it("clears all necessary fields when a component is hidden", () => {
    const clearField = jest.fn();
    const props = {
      children: <h1 name="hello">Hello I am a child</h1>,
      fieldNamesClearedWhenHidden: ["hello", "world"],
      clearField,
      getField: jest.fn(),
      updateFields: jest.fn(),
      visible: true,
    };
    const { rerender } = render(<ConditionalContent {...props} />);
    rerender(<ConditionalContent {...props} visible={false} />);
    expect(clearField).toHaveBeenCalledTimes(2);
    expect(clearField).toHaveBeenNthCalledWith(1, "hello");
    expect(clearField).toHaveBeenNthCalledWith(2, "world");
  });

  it("doesn't attempt updates if fieldNamesClearedWhenHidden is undefined", () => {
    const clearField = jest.fn();
    const props = {
      children: <h1 name="hello">Hello I am a child</h1>,
      clearField,
      getField: jest.fn(),
      updateFields: jest.fn(),
      visible: true,
    };
    const { rerender } = render(<ConditionalContent {...props} />);
    rerender(<ConditionalContent {...props} visible={false} />);
    expect(clearField).toHaveBeenCalledTimes(0);
  });
});
