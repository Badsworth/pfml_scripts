import PaginationNavigation, {
  truncationStates,
} from "src/components/PaginationNavigation";
import FlowDiagram from "../../utils/FlowDiagram";
import { Props } from "types/common";
import React from "react";

export default {
  title: "Components/PaginationNavigation",
  component: PaginationNavigation,
  args: {
    pageOffset: 1,
    totalPages: 20,
    // eslint-disable-next-line no-console
    onClick: console.log,
  },
};

export const Default = (args: Props<typeof PaginationNavigation>) => (
  <PaginationNavigation {...args} />
);
export const TruncationLogic = () => <FlowDiagram states={truncationStates} />;
