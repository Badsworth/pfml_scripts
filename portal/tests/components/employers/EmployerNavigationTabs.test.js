import EmployerNavigationTabs from "../../../src/components/employers/EmployerNavigationTabs";
import React from "react";
import { render } from "@testing-library/react";
import routes from "../../../src/routes";

describe("EmployerNavigationTabs", () => {
  it("renders the component", () => {
    const { container } = render(
      <EmployerNavigationTabs activePath={routes.employers.welcome} />
    );
    expect(container.firstChild).toMatchSnapshot();
  });
});
