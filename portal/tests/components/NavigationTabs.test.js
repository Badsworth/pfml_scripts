import { render, screen } from "@testing-library/react";
import NavigationTabs from "../../src/components/NavigationTabs";
import React from "react";
import routes from "../../src/routes";

const renderTabs = (customProps) => {
  const props = {
    tabs: [
      {
        label: "Employer Welcome",
        href: routes.employers.welcome,
      },
      {
        label: "Employer Organizations",
        href: routes.employers.organizations,
      },
    ],
    activePath: routes.employers.welcome,
    ...customProps,
  };
  return render(<NavigationTabs {...props} />);
};

describe("NavigationTabs", () => {
  it("renders the component", () => {
    const { container } = renderTabs();
    expect(container.firstChild).toMatchSnapshot();
  });

  it("shows a link for each route", () => {
    renderTabs();
    expect(screen.getAllByRole("link")).toHaveLength(2);
    expect(
      screen.getByRole("link", { name: "Employer Welcome" })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Employer Organizations" })
    ).toBeInTheDocument();
  });

  it("gives special styling to the active tab", () => {
    renderTabs();
    expect(
      screen.getByRole("link", { name: "Employer Welcome", current: "page" })
    ).toHaveClass("border-primary", "text-primary");
    expect(
      screen.getByRole("link", { name: "Employer Organizations" })
    ).not.toHaveClass("border-primary", "text-primary");
  });
});
