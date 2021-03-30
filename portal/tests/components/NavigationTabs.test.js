import NavigationTabs from "../../src/components/NavigationTabs";
import React from "react";
import routes from "../../src/routes";
import { shallow } from "enzyme";

describe("NavigationTabs", () => {
  let wrapper;
  const tabs = [
    {
      label: "Employer Welcome",
      href: routes.employers.welcome,
    },
    {
      label: "Employer Organizations",
      href: routes.employers.organizations,
    },
  ];

  beforeEach(() => {
    wrapper = shallow(<NavigationTabs tabs={tabs} activePath={tabs[0].href} />);
  });

  it("renders the component", () => {
    expect(wrapper).toMatchSnapshot();
  });

  it("shows a button for each route", () => {
    wrapper.find("Link").forEach((link, index) => {
      const label = link.dive().text();
      const href = link.dive().find("a").prop("href");
      expect(label).toEqual(tabs[index].label);
      expect(href).toEqual(tabs[index].href);
    });
  });

  it("gives special styling to the active tab", () => {
    const activeClasses = ["border-primary", "text-primary"];
    const activeTab = wrapper.find("Link").first().find("a");
    const inactiveTab = wrapper.find("Link").last().find("a");

    activeClasses.forEach((className) => {
      expect(activeTab.hasClass(className)).toBe(true);
      expect(inactiveTab.hasClass(className)).toBe(false);
    });
  });
});
