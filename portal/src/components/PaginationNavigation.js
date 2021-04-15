import Pagination from "@massds/mayflower-react/dist/Pagination";
import PropTypes from "prop-types";
import React from "react";
import { times } from "lodash";
import { useTranslation } from "../locales/i18n";

const PaginationNavigation = (props) => {
  const { pageIndex, totalPages, onClick } = props;
  const { t } = useTranslation();
  const isFirstPage = pageIndex === 0;
  const isLastPage = pageIndex + 1 === totalPages;

  const handlePageClick = (pageIndex, event) => {
    event.preventDefault();
    onClick(pageIndex);
  };

  const handlePreviousClick = () => {
    if (!isFirstPage) {
      const newPageIndex = pageIndex - 1;
      onClick(newPageIndex);
    }
  };

  const handleNextClick = () => {
    if (!isLastPage) {
      const newPageIndex = pageIndex + 1;
      onClick(newPageIndex);
    }
  };

  return (
    <Pagination
      next={{
        disabled: isLastPage,
        onClick: handleNextClick,
        text: t("components.pagination.nextLabel"),
      }}
      pages={times(totalPages, (i) => {
        const pageNumber = i + 1;
        return {
          active: pageIndex === i,
          onClick: (e) => handlePageClick(i, e),
          text: pageNumber.toString(),
        };
      })}
      prev={{
        disabled: isFirstPage,
        onClick: handlePreviousClick,
        text: t("components.pagination.previousLabel"),
      }}
    />
  );
};

PaginationNavigation.propTypes = {
  /** Zero-based index representing the current page */
  pageIndex: PropTypes.number.isRequired,
  totalPages: PropTypes.number.isRequired,
  onClick: PropTypes.func.isRequired,
};

export default PaginationNavigation;
