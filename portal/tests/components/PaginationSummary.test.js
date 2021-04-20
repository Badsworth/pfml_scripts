import PaginationSummary from "../../src/components/PaginationSummary";
import React from "react";
import { shallow } from "enzyme";

describe("PaginationSummary", () => {
  it("displays indices of first and last records for selected page and total number of records", () => {
    const wrapper = shallow(
      <PaginationSummary
        pageIndex={1}
        pageSize={25}
        totalPages={3}
        totalRecords={75}
      />
    );

    expect(wrapper.find("p").text()).toEqual("Viewing 26 - 50 of 75 results");
  });

  it("displays only up to the total number of records, even if it is less than the page size", () => {
    const wrapper = shallow(
      <PaginationSummary
        pageIndex={0}
        pageSize={25}
        totalPages={1}
        totalRecords={20}
      />
    );

    expect(wrapper.find("p").text()).toEqual("Viewing 1 - 20 of 20 results");
  });
});
