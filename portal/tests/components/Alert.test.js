import { render, screen } from "@testing-library/react";
import Alert from "../../src/components/Alert";
import React from "react";

const renderComponent = (customProps = {}) => {
  return render(<Alert {...customProps}>This is an alert</Alert>);
};

describe("Alert", () => {
  it("renders the children as the alert body text", () => {
    const { container } = renderComponent();

    expect(container.firstChild).toMatchSnapshot();
    expect(screen.getByText("This is an alert")).toBeInTheDocument();
  });

  it("renders an h2 when the heading prop is set", () => {
    renderComponent({ heading: "Alert heading" });
    expect(
      screen.getByRole("heading", { level: 2, name: "Alert heading" })
    ).toBeInTheDocument();
  });

  it("renders an h3 when headingLevel is set to 3", () => {
    renderComponent({ heading: "Alert heading", headingLevel: "3" });

    const h3 = screen.getByRole("heading", { level: 3 });
    expect(h3).toBeInTheDocument();
  });

  it("overrides the Heading size when headingSize is set to 3", () => {
    renderComponent({ heading: "Alert heading", headingSize: "3" });

    const h2 = screen.getByRole("heading", { level: 2 });
    expect(h2).toBeInTheDocument();
    expect(h2).toHaveClass("font-heading-sm");
  });

  it("renders the 'error' state by default", () => {
    const { container } = renderComponent();

    expect(container.firstChild).toHaveClass("usa-alert--error");
  });

  it("forwards the ref to the alert element", () => {
    const alertRef = React.createRef();
    const { container } = renderComponent({ ref: alertRef });

    expect(container.firstChild).toBe(alertRef.current);
  });

  it("renders role='region' by default", () => {
    renderComponent();
    const alertBody = screen.getByRole("region");
    expect(alertBody).toBeInTheDocument();
    expect(alertBody).toHaveClass("usa-alert__body");
  });

  it("adds the role to the alert body element", () => {
    renderComponent({ role: "alert" });
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });

  it("renders the 'info' state when the state prop is set to 'info'", () => {
    const { container } = renderComponent({ state: "info" });
    expect(container.firstChild).toHaveClass("usa-alert--info");
  });

  it("renders the 'success' state when the state prop is set to 'success'", () => {
    const { container } = renderComponent({ state: "success" });
    expect(container.firstChild).toHaveClass("usa-alert--success");
  });

  it("renders the 'warning' state when the state prop is set to 'warning'", () => {
    const { container } = renderComponent({ state: "warning" });
    expect(container.firstChild).toHaveClass("usa-alert--warning");
  });

  it("renders with an icon when the noIcon prop is not set", () => {
    const { container } = renderComponent();
    expect(container.firstChild).not.toHaveClass("usa-alert--no-icon");
  });

  it("renders without an icon when the noIcon prop is set", () => {
    const { container } = renderComponent({ noIcon: true });
    expect(container.firstChild).toHaveClass("usa-alert--no-icon");
  });

  it("renders slim when the slim prop is set", () => {
    const { container } = renderComponent({ slim: true });
    expect(container.firstChild).toHaveClass("usa-alert--slim");
  });

  it("renders with a neutral background color when the neutral prop is set", () => {
    const { container } = renderComponent({ neutral: true });
    expect(container.firstChild).toHaveClass("c-alert--neutral");
  });

  it("renders auto-width when the autoWidth prop is set", () => {
    const { container } = renderComponent({ autoWidth: true });
    expect(container.firstChild).toHaveClass("c-alert--auto-width");
  });
});
