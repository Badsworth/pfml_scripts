import PaginationNavigation, {
  truncationStates,
} from "src/components/PaginationNavigation";
import FlowDiagram from "../../utils/FlowDiagram";
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

// @ts-expect-error ts-migrate(7006) FIXME: Parameter 'args' implicitly has an 'any' type.
export const Default = (args) => <PaginationNavigation {...args} />;
export const TruncationLogic = () => <FlowDiagram states={truncationStates} />;
