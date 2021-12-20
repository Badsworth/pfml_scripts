import React from "react";
import { useTranslation } from "../locales/i18n";

interface PaginationSummaryProps {
  pageOffset: number;
  pageSize: number;
  totalRecords: number;
}

const PaginationSummary = (props: PaginationSummaryProps) => {
  const { pageOffset, pageSize, totalRecords } = props;
  const { t } = useTranslation();

  const firstRecordNumber = pageSize * (pageOffset - 1) + 1;
  const maxRecordNumberForPage = firstRecordNumber + pageSize - 1;
  const lastRecordNumber =
    maxRecordNumberForPage > totalRecords
      ? totalRecords
      : maxRecordNumberForPage;

  return (
    <p className="line-height-sans-2" aria-live="polite">
      {t("components.pagination.summary", {
        context: totalRecords === 0 ? "empty" : undefined,
        firstRecordNumber: Number(firstRecordNumber).toLocaleString(),
        lastRecordNumber: Number(lastRecordNumber).toLocaleString(),
        totalRecords: Number(totalRecords).toLocaleString(),
      })}
    </p>
  );
};

export default PaginationSummary;
