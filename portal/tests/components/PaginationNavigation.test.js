import PaginationNavigation from "../../src/components/PaginationNavigation";
import React from "react";
import { shallow } from "enzyme";

describe("PaginationNavigation", () => {
  const onClick = jest.fn();
  const wrapper = shallow(
    <PaginationNavigation pageIndex={1} totalPages={3} onClick={onClick} />
  );
  const selectNthLink = (wrapper, index) => {
    return wrapper
      .find("Pagination")
      .dive()
      .find("a")
      .at(index)
      .simulate("click", {
        preventDefault: () => jest.fn(),
      });
  };

  it("renders the component", () => {
    expect(wrapper).toMatchSnapshot();
  });

  it("displays a link for previous, next, and each page number", () => {
    expect(wrapper.find("Pagination").dive().find("a")).toHaveLength(5);
  });

  it("calls function to fetch updated list when a page is selected", () => {
    selectNthLink(wrapper, 3); // Select 3rd page
    expect(onClick).toHaveBeenCalled();
  });

  it("calls function to fetch updated list when 'Previous' is clicked", () => {
    selectNthLink(wrapper, 0); // Select 'Previous' link
    expect(onClick).toHaveBeenCalledWith(0); // 1st page
  });

  it("calls function to fetch updated list when 'Next' is clicked", () => {
    selectNthLink(wrapper, 4); // Select 'Next' link
    expect(onClick).toHaveBeenCalledWith(2); // 3rd page
  });

  describe("when selected page is first page", () => {
    let wrapper;

    beforeEach(() => {
      wrapper = shallow(
        <PaginationNavigation pageIndex={0} totalPages={3} onClick={onClick} />
      );
    });

    it("disables the 'Previous' link", () => {
      expect(wrapper.find("Pagination").prop("prev").disabled).toBe(true);
    });

    it("does not call function to fetch updated list when 'Previous' is clicked", () => {
      selectNthLink(wrapper, 0);
      expect(onClick).not.toHaveBeenCalled();
    });
  });

  describe("when selected page is last page", () => {
    let wrapper;

    beforeEach(() => {
      wrapper = shallow(
        <PaginationNavigation pageIndex={2} totalPages={3} onClick={onClick} />
      );
    });

    it("disables the 'Next' link", () => {
      expect(wrapper.find("Pagination").prop("next").disabled).toBe(true);
    });

    it("does not call function to fetch updated list when 'Next' is clicked", () => {
      selectNthLink(wrapper, 4);
      expect(onClick).not.toHaveBeenCalled();
    });
  });
});
