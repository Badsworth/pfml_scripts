import EmployerNavigationTabs from "../../../src/components/employers/EmployerNavigationTabs";
import React from "react";
import routes from "../../../src/routes";
import { shallow } from "enzyme";

describe("EmployerNavigationTabs", () => {
  let wrapper;

  beforeEach(() => {
    wrapper = shallow(
      <EmployerNavigationTabs activePath={routes.employers.welcome} />
    ).dive();
  });

  it("renders the component", () => {
    expect(wrapper).toMatchSnapshot();
  });
});
