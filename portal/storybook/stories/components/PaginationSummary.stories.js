import PaginationSummary from "src/components/PaginationSummary";
import React from "react";

export default {
  title: "Components/PaginationSummary",
  component: PaginationSummary,
  args: {
    pageIndex: 0,
    pageSize: 25,
    totalPages: 4,
    totalRecords: 100,
  },
};
export const Default = (args) => <PaginationSummary {...args} />;
