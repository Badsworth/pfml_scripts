import PaginationNavigation, {
  getTruncatedPageRange,
} from "../../src/components/PaginationNavigation";
import React from "react";
import { shallow } from "enzyme";

const setup = (customProps = {}) => {
  const props = Object.assign(
    {
      pageOffset: 2,
      totalPages: 3,
      onClick: jest.fn(),
    },
    customProps
  );

  const wrapper = shallow(<PaginationNavigation {...props} />);

  return { wrapper, props };
};

describe("PaginationNavigation", () => {
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

  it("renders the component with a truncated pagination range", () => {
    const { wrapper } = setup({ totalPages: 10 });

    expect(wrapper).toMatchSnapshot();
  });

  it("displays a link for previous, next, and each page number", () => {
    const { wrapper } = setup();

    expect(wrapper.find("Pagination").dive().find("a")).toHaveLength(5);
  });

  it("calls function to fetch updated list when a page is selected", () => {
    const { props, wrapper } = setup();

    selectNthLink(wrapper, 3); // Select 3rd page
    expect(props.onClick).toHaveBeenCalled();
  });

  it("calls function to fetch updated list when 'Previous' is clicked", () => {
    const { props, wrapper } = setup();

    selectNthLink(wrapper, 0); // Select 'Previous' link
    expect(props.onClick).toHaveBeenCalledWith(1); // 1st page
  });

  it("calls function to fetch updated list when 'Next' is clicked", () => {
    const { props, wrapper } = setup();

    selectNthLink(wrapper, 4); // Select 'Next' link
    expect(props.onClick).toHaveBeenCalledWith(3); // 3rd page
  });

  describe("when selected page is first page", () => {
    it("disables the 'Previous' link", () => {
      const { wrapper } = setup({ pageOffset: 1 });

      expect(wrapper.find("Pagination").prop("prev").disabled).toBe(true);
    });

    it("does not call function to fetch updated list when 'Previous' is clicked", () => {
      const { props, wrapper } = setup({ pageOffset: 1 });

      selectNthLink(wrapper, 0);
      expect(props.onClick).not.toHaveBeenCalled();
    });
  });

  describe("when selected page is last page", () => {
    it("disables the 'Next' link", () => {
      const { wrapper } = setup({ pageOffset: 3, totalPages: 3 });

      expect(wrapper.find("Pagination").prop("next").disabled).toBe(true);
    });

    it("does not call function to fetch updated list when 'Next' is clicked", () => {
      const { props, wrapper } = setup({ pageOffset: 3, totalPages: 3 });

      selectNthLink(wrapper, 4);
      expect(props.onClick).not.toHaveBeenCalled();
    });
  });
});

describe("getTruncatedPageRange", () => {
  it("does not truncate", () => {
    expect(getTruncatedPageRange(1, 9)).toEqual([1, 2, 3, 4, 5, 6, 7, 8, 9]);
    expect(getTruncatedPageRange(1, 1)).toEqual([1]);
  });

  it("truncates left and right side", () => {
    const range = getTruncatedPageRange(10, 30);
    expect(range).toEqual([1, "spacer", 7, 8, 9, 10, 11, 12, 13, "spacer", 30]);
  });

  it("truncates only left side", () => {
    const rangeA = getTruncatedPageRange(30, 30);
    const rangeB = getTruncatedPageRange(26, 30);

    expect(rangeA).toEqual([1, "spacer", 23, 24, 25, 26, 27, 28, 29, 30]);
    expect(rangeB).toEqual([1, "spacer", 23, 24, 25, 26, 27, 28, 29, 30]);
  });

  it("truncates only right side", () => {
    const rangeA = getTruncatedPageRange(1, 30);
    const rangeB = getTruncatedPageRange(5, 30);

    expect(rangeA).toEqual([1, 2, 3, 4, 5, 6, 7, 8, "spacer", 30]);
    expect(rangeB).toEqual([1, 2, 3, 4, 5, 6, 7, 8, "spacer", 30]);
  });
});
