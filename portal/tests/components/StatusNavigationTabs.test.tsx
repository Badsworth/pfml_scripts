import React from "react";
import StatusNavigationTabs from "../../src/components/status/StatusNavigationTabs";
import { render } from "@testing-library/react";
import routes from "../../src/routes";

describe("StatusNavigationTabs", () => {
  it("renders the component", () => {
    const { container } = render(
      <StatusNavigationTabs activePath={routes.applications.status.payments} />
    );
    expect(container.firstChild).toMatchSnapshot();
  });
});
