import PaginationSummary from "../../src/components/PaginationSummary";
import React from "react";
import { shallow } from "enzyme";

describe("PaginationSummary", () => {
  it("displays numbers of first and last records for selected page and total number of records", () => {
    const wrapper = shallow(
      <PaginationSummary pageOffset={2} pageSize={25} totalRecords={7500} />
    );

    expect(wrapper.find("p").text()).toEqual(
      "Viewing 26 to 50 of 7,500 results"
    );
  });

  it("displays only up to the total number of records, even if it is less than the page size", () => {
    const wrapper = shallow(
      <PaginationSummary pageOffset={1} pageSize={25} totalRecords={20} />
    );

    expect(wrapper.find("p").text()).toEqual("Viewing 1 to 20 of 20 results");
  });
});
