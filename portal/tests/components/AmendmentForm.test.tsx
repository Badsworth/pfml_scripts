import { act, render, screen } from "@testing-library/react";
import AmendmentForm from "src/components/AmendmentForm";
import React from "react";
import userEvent from "@testing-library/user-event";

describe("AmendmentForm", () => {
  const onDestroy = jest.fn();
  const handleSave = jest.fn().mockImplementation(() => Promise.resolve(null));
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

  it("shows a button labeled with saveButtonText", () => {
    render(
      <AmendmentForm
        onDestroy={onDestroy}
        destroyButtonLabel={destroyButtonLabel}
        saveButtonText="Save"
        onSave={handleSave}
      >
        <p>Testing</p>
      </AmendmentForm>
    );
    expect(screen.getByRole("button", { name: "Save" })).toBeInTheDocument();
  });

  it("calls 'onSave' when the save button is clicked", async () => {
    render(
      <AmendmentForm
        onDestroy={onDestroy}
        destroyButtonLabel={destroyButtonLabel}
        saveButtonText="Save"
        onSave={handleSave}
      >
        <p>Testing</p>
      </AmendmentForm>
    );
    await act(
      async () =>
        await userEvent.click(screen.getByRole("button", { name: "Save" }))
    );
    expect(handleSave).toHaveBeenCalled();
  });
});
