import { Machine } from "xstate";
import Pagination from "@massds/mayflower-react/dist/Pagination";
import PropTypes from "prop-types";
import React from "react";
import { times } from "lodash";
import { useTranslation } from "../locales/i18n";

/**
 * Limit the number of visible page number buttons to this amount
 */
const MAX_TOTAL_PAGE_NUMBERS = 9;
/**
 * Minimum amount of page number buttons to display between the [current] page
 * and the "..." spacer. For example "[6] 7 8 9 ... 15 Next"
 * The math for this is based on the following rules:
 * - Always show the first and last page (- 2)
 * - Always show the current page (- 1)
 */
const MIN_SURROUNDING_PAGES = (MAX_TOTAL_PAGE_NUMBERS - 2 - 1) / 2;

/**
 * Truncation states the pagination navigation may render as
 */
export const truncationStates = {
  unknown: {
    // Transient node: immediately transitions to the first state where `cond` is `true`
    always: [
      {
        target: "noTruncation",
        cond: "isTotalPageNumLessOrEqualToMax",
      },
      {
        target: "truncateRight",
        cond: "isPageLessThanMidpoint",
      },
      {
        target: "truncateLeft",
        cond: "canVisiblePagesAfterCurrentPageExtendToLastPage",
      },
      {
        target: "truncateLeftAndRight",
      },
    ],
  },
  noTruncation: {},
  truncateLeft: {},
  truncateRight: {},
  truncateLeftAndRight: {},
};

/**
 * State machine representing the truncation states and their conditions (guards)
 */
const truncationMachine = Machine(
  {
    context: {
      // These should be defined when starting the machine, using withContext
      pageOffset: null,
      totalPages: null,
    },
    initial: "unknown",
    states: { ...truncationStates }, // using destructuring to avoid a weird TS build error in Storybook
  },
  {
    guards: {
      /**
       * Is the current page number less than the middle rendered number?
       * @param {object} context
       * @returns {boolean}
       */
      isPageLessThanMidpoint: (context) =>
        context.pageOffset <= Math.ceil(MAX_TOTAL_PAGE_NUMBERS / 2),
      /**
       * Do the numbers after the current page sequentially connect with the last page number?
       * For example [current page] 7 8 9 10
       *                                  ^ last page
       * @param {object} context
       * @returns {boolean}
       */
      canVisiblePagesAfterCurrentPageExtendToLastPage: (context) =>
        // +1 is for the last page that's always displayed
        context.pageOffset + MIN_SURROUNDING_PAGES + 1 >= context.totalPages,
      /**
       * Can all pages be displayed?
       * @param {object} context
       * @returns {boolean}
       */
      isTotalPageNumLessOrEqualToMax: (context) =>
        context.totalPages <= MAX_TOTAL_PAGE_NUMBERS,
    },
  }
);

/**
 * Get a list of page numbers to display to the user, and include
 * spacers (...) when there are too many pages to display.
 * @param {number} pageOffset - current page
 * @param {number} totalPages
 * @returns {Array<number|'spacer'>} The page numbers (or spacers) that should be rendered
 */
export const getTruncatedPageRange = (pageOffset, totalPages) => {
  const truncationState = truncationMachine.withContext({
    pageOffset,
    totalPages,
  }).initialState.value;
  const firstPageNumber = 1;
  const lastPageNumber = totalPages;
  const spacer = "spacer"; // Mayflower renders this as "..."

  switch (truncationState) {
    case "truncateRight":
      // For example: [1, 2, 3, 4, 5, 6, 7, 8, spacer, 17]
      return [
        // Start from 1 and go up to the max visible count, leaving space for the last page number
        ...times(MAX_TOTAL_PAGE_NUMBERS - 1, (index) => index + 1),
        spacer,
        lastPageNumber,
      ];
    case "truncateLeft":
      // For example: [1, spacer, 10, 11, 12, 13, 14, 15, 16, 17]
      return [
        firstPageNumber,
        spacer,
        // Count backwards until we hit the max visible count, leaving space for the first page number
        ...times(
          MAX_TOTAL_PAGE_NUMBERS - 1,
          (index) => totalPages - index
        ).reverse(),
      ];
    case "truncateLeftAndRight":
      // For example: [1, spacer, 5, 6, 7, 8, 9, 10, 11, spacer, 17]
      return [
        firstPageNumber,
        spacer,
        ...times(
          MIN_SURROUNDING_PAGES,
          // Count backwards from the current page
          (index) => pageOffset - index - 1
        ).reverse(),
        pageOffset,
        // Count forwards from the current page
        ...times(MIN_SURROUNDING_PAGES, (index) => pageOffset + index + 1),
        spacer,
        lastPageNumber,
      ];
    default:
      // All the pages. Count from 1 until we hit the last page.
      return times(totalPages, (index) => index + 1);
  }
};

/**
 * Next/previous navigation and page number buttons
 */
const PaginationNavigation = (props) => {
  const { pageOffset, totalPages, onClick } = props;
  const { t } = useTranslation();
  const isFirstPage = pageOffset === 1;
  const isLastPage = pageOffset === totalPages;

  const handlePreviousClick = () => {
    if (!isFirstPage) {
      onClick(pageOffset - 1);
    }
  };

  const handleNextClick = () => {
    if (!isLastPage) {
      onClick(pageOffset + 1);
    }
  };

  /**
   * Form the props object for a pagination button
   * @param {number|'spacer'} pageNumberOrSpacer
   * @returns {object}
   */
  const getPageButtonProps = (pageNumberOrSpacer) => {
    return {
      active: pageOffset === pageNumberOrSpacer,
      onClick:
        pageNumberOrSpacer === "spacer"
          ? null
          : () => onClick(pageNumberOrSpacer),
      text: pageNumberOrSpacer.toString(),
    };
  };

  /**
   * @type {Pagination.propTypes.pages}
   */
  const pageButtons = getTruncatedPageRange(pageOffset, totalPages).map(
    (pageNumberOrSpacer) => getPageButtonProps(pageNumberOrSpacer)
  );

  return (
    <Pagination
      next={{
        disabled: isLastPage,
        onClick: handleNextClick,
        text: t("components.pagination.nextLabel"),
      }}
      pages={pageButtons}
      prev={{
        disabled: isFirstPage,
        onClick: handlePreviousClick,
        text: t("components.pagination.previousLabel"),
      }}
    />
  );
};

PaginationNavigation.propTypes = {
  /** The current page's number */
  pageOffset: PropTypes.number.isRequired,
  /** Total pages available. Also can be read as "The last page number" */
  totalPages: PropTypes.number.isRequired,
  /** Page button click handler. Gets the requested page number as a param */
  onClick: PropTypes.func.isRequired,
};

export default PaginationNavigation;
