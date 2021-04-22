import PropTypes from "prop-types";
import React from "react";
import { useTranslation } from "../locales/i18n";

const PaginationSummary = (props) => {
  const { pageIndex, pageSize, totalPages, totalRecords } = props;
  const { t } = useTranslation();

  const getFirstRecordIndex = () => {
    return pageSize * pageIndex + 1;
  };

  const getLastRecordIndex = () => {
    const remainder = totalRecords % pageSize;
    const isLastPage = pageIndex + 1 === totalPages;
    return remainder !== 0 && isLastPage
      ? totalRecords
      : pageSize * (pageIndex + 1);
  };

  return (
    <p className="padding-x-2">
      {t("components.pagination.summary", {
        firstRecordIndex: getFirstRecordIndex(),
        lastRecordIndex: getLastRecordIndex(),
        totalRecords,
      })}
    </p>
  );
};

PaginationSummary.propTypes = {
  /** Zero-based index representing the current page */
  pageIndex: PropTypes.number.isRequired,
  pageSize: PropTypes.number.isRequired,
  totalPages: PropTypes.number.isRequired,
  totalRecords: PropTypes.number.isRequired,
};

export default PaginationSummary;
