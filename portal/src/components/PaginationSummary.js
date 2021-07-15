import PropTypes from "prop-types";
import React from "react";
import { useTranslation } from "../locales/i18n";

const PaginationSummary = (props) => {
  const { pageOffset, pageSize, totalRecords } = props;
  const { t } = useTranslation();

  const firstRecordNumber = pageSize * (pageOffset - 1) + 1;
  const maxRecordNumberForPage = firstRecordNumber + pageSize - 1;
  const lastRecordNumber =
    maxRecordNumberForPage > totalRecords
      ? totalRecords
      : maxRecordNumberForPage;

  return (
    <p className="line-height-sans-2">
      {t("components.pagination.summary", {
        firstRecordNumber: Number(firstRecordNumber).toLocaleString(),
        lastRecordNumber: Number(lastRecordNumber).toLocaleString(),
        totalRecords: Number(totalRecords).toLocaleString(),
      })}
    </p>
  );
};

PaginationSummary.propTypes = {
  /** Current page number */
  pageOffset: PropTypes.number.isRequired,
  pageSize: PropTypes.number.isRequired,
  totalRecords: PropTypes.number.isRequired,
};

export default PaginationSummary;
