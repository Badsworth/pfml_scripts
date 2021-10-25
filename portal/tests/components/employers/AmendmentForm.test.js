import { render, screen } from "@testing-library/react";
import AmendmentForm from "../../../src/components/employers/AmendmentForm";
import React from "react";
import userEvent from "@testing-library/user-event";

describe("AmendmentForm", () => {
  const onDestroy = jest.fn();
  const destroyButtonLabel = "Destroy";

  it("renders the component", () => {
    const { container } = render(
      <AmendmentForm
        onDestroy={onDestroy}
        destroyButtonLabel={destroyButtonLabel}
      >
        <p>Testing</p>
      </AmendmentForm>
    );

    expect(container.firstChild).toMatchSnapshot();
  });

  it("shows a button labeled with destroyButtonLabel", () => {
    render(
      <AmendmentForm
        onDestroy={onDestroy}
        destroyButtonLabel={destroyButtonLabel}
      >
        <p>Testing</p>
      </AmendmentForm>
    );
    expect(screen.getByRole("button", { name: "Destroy" })).toBeInTheDocument();
  });

  it("calls 'onDestroy' when the destroy button is clicked", () => {
    render(
      <AmendmentForm
        onDestroy={onDestroy}
        destroyButtonLabel={destroyButtonLabel}
      >
        <p>Testing</p>
      </AmendmentForm>
    );
    userEvent.click(screen.getByRole("button", { name: "Destroy" }));
    expect(onDestroy).toHaveBeenCalled();
  });
});
