import { render, screen } from "@testing-library/react";
import ButtonLink from "../../src/components/ButtonLink";
import React from "react";
import userEvent from "@testing-library/user-event";

describe("ButtonLink", () => {
  it("renders button link with default styling", () => {
    render(<ButtonLink href="http://www.example.com">Click Me</ButtonLink>);
    const buttonLink = screen.getByRole("link");
    expect(buttonLink).toMatchInlineSnapshot(`
      <a
        class="usa-button"
        href="http://www.example.com"
      >
        Click Me
      </a>
    `);
    expect(buttonLink).toHaveAccessibleName("Click Me");
  });

  it("renders a vanilla button if disabled", () => {
    render(
      <ButtonLink disabled={true} href="http://www.example.com">
        Click Me
      </ButtonLink>
    );
    expect(screen.queryByRole("link")).not.toBeInTheDocument();
    const buttonLink = screen.getByRole("button");
    expect(buttonLink).toMatchInlineSnapshot(`
      <button
        class="usa-button disabled"
        disabled=""
        type="button"
      >
        Click Me
      </button>
    `);
    expect(buttonLink).toBeDisabled();
  });

  it("can accept an onClick and use it", () => {
    const onClickHandler = jest.fn();
    render(
      <ButtonLink onClick={onClickHandler} href="http://www.example.com">
        Click me
      </ButtonLink>
    );
    userEvent.click(screen.getByText(/Click me/));
    expect(onClickHandler).toHaveBeenCalled();
  });

  it("can receive styling variations that take effect", () => {
    render(
      <ButtonLink variation="outline" href="http://www.example.com">
        Click Me
      </ButtonLink>
    );
    expect(screen.getByRole("link")).toHaveClass(
      "usa-button usa-button--outline"
    );
  });

  it("inversed passes through with impact on class styles", () => {
    render(
      <ButtonLink inversed={true} href="http://www.example.com">
        Click Me
      </ButtonLink>
    );
    expect(screen.getByRole("link")).toHaveClass(
      "usa-button usa-button--inverse"
    );
  });

  it("inversed passes through with expected impact on class styles when unstyled", () => {
    render(
      <ButtonLink
        inversed={true}
        variation="unstyled"
        href="http://www.example.com"
      >
        Click Me
      </ButtonLink>
    );
    expect(screen.getByRole("link")).toHaveClass("usa-button--outline");
  });

  it("can render a button with an aria-label", () => {
    render(
      <ButtonLink aria-label="example label" href="http://www.example.com">
        Click Me
      </ButtonLink>
    );
    const button = screen.getByLabelText("example label");
    expect(button).toBeInTheDocument();
  });

  it("can handle additional custom classes passed through", () => {
    render(
      <ButtonLink className="hi hi hi" href="http://www.example.com">
        Click Me
      </ButtonLink>
    );
    expect(screen.getByRole("link")).toHaveClass("usa-button hi hi hi");
  });
});
