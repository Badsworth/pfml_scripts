import EmployeeInformation from "../../../src/components/employers/EmployeeInformation";
import { MockEmployerClaimBuilder } from "../../test-utils";
import React from "react";
import ReviewRow from "../../../src/components/ReviewRow";
import { shallow } from "enzyme";

describe("EmployeeInformation", () => {
  const getAddressHtml = (secondLine) =>
    `<span class="residential-address">1234 My St.<br/>${
      secondLine ? secondLine + "<br/>" : ""
    }Boston, MA 00000</span>`;
  let claim, wrapper;

  beforeEach(() => {
    claim = new MockEmployerClaimBuilder().completed().create();
    wrapper = shallow(<EmployeeInformation claim={claim} />);
  });

  it("renders the component", () => {
    expect(wrapper).toMatchSnapshot();
  });

  it("renders one line break if second address line does not exist", () => {
    expect(wrapper.find(".residential-address").html()).toEqual(
      getAddressHtml()
    );
  });

  it("renders two line breaks if second address line exists", () => {
    const secondAddressLine = "Apt 1";
    const claimWithSecondAddressLine = new MockEmployerClaimBuilder()
      .address({
        city: "Boston",
        line_1: "1234 My St.",
        line_2: secondAddressLine,
        state: "MA",
        zip: "00000",
      })
      .create();

    const wrapper = shallow(
      <EmployeeInformation claim={claimWithSecondAddressLine} />
    );

    expect(wrapper.find(".residential-address").html()).toEqual(
      getAddressHtml(secondAddressLine)
    );
  });

  it("renders formatted date of birth", () => {
    expect(
      wrapper.find(ReviewRow).last().children().first().text()
    ).toMatchInlineSnapshot(`"7/17/****"`);
  });
});
