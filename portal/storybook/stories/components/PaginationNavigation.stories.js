import PaginationNavigation from "src/components/PaginationNavigation";
import React from "react";

export default {
  title: "Components/PaginationNavigation",
  component: PaginationNavigation,
  args: {
    pageIndex: 0,
    totalPages: 4,
    onClick: () => {},
  },
};
export const Default = (args) => <PaginationNavigation {...args} />;
