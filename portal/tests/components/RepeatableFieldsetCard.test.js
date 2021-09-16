import { render, screen } from "@testing-library/react";
import React from "react";
import RepeatableFieldsetCard from "../../src/components/RepeatableFieldsetCard";
import userEvent from "@testing-library/user-event";

const renderComponent = (customProps = {}) => {
  const props = {
    className: "custom-class-name",
    entry: { first_name: "Bud" },
    heading: "Person",
    index: 0,
    removeButtonLabel: "Remove",
    onRemoveClick: jest.fn(),
  };
  return render(
    <RepeatableFieldsetCard {...props} {...customProps}>
      <p>Hello world</p>
    </RepeatableFieldsetCard>
  );
};

describe("RepeatableFieldsetCard", () => {
  it("renders with the given content", () => {
    const { container } = renderComponent();

    expect(container.firstChild).toMatchSnapshot();
  });

  it("shows the remove button when showRemoveButton is true", () => {
    renderComponent({ showRemoveButton: true });
    expect(screen.getByRole("button")).toMatchInlineSnapshot(`
<button
  class="usa-button position-relative text-error hover:text-error-dark active:text-error-darker usa-button--unstyled"
  name="remove-entry-button"
  type="button"
>
  Remove
</button>
`);
  });

  it("calls the onRemoveClick handler when the remove button is clicked", () => {
    const onRemoveClickMock = jest.fn();
    renderComponent({
      showRemoveButton: true,
      onRemoveClick: onRemoveClickMock,
    });
    userEvent.click(screen.getByRole("button"));

    expect(onRemoveClickMock).toHaveBeenCalledWith({ first_name: "Bud" }, 0);
  });
});
