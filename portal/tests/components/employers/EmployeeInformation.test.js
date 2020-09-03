import { MockClaimBuilder, claim } from "../../test-utils";
import EmployeeInformation from "../../../src/components/employers/EmployeeInformation";
import React from "react";
import ReviewRow from "../../../src/components/ReviewRow";
import { shallow } from "enzyme";

describe("EmployeeInformation", () => {
  const getAddressHtml = (secondLine) =>
    `<span class="residential-address">1234 My St.<br/>${
      secondLine ? secondLine + "<br/>" : ""
    }Boston, MA 00000</span>`;
  let wrapper;

  beforeEach(() => {
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
    const claimWithUpdatedAddress = new MockClaimBuilder()
      .address({
        city: "Boston",
        line_1: "1234 My St.",
        line_2: secondAddressLine,
        state: "MA",
        zip: "00000",
      })
      .verifiedId()
      .create();

    const wrapper = shallow(
      <EmployeeInformation claim={claimWithUpdatedAddress} />
    );

    expect(wrapper.find(".residential-address").html()).toEqual(
      getAddressHtml(secondAddressLine)
    );
  });

  it("renders formatted date of birth", () => {
    expect(wrapper.find(ReviewRow).last().children().first().text()).toMatch(
      "7/17/1980"
    );
  });
});
