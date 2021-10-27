import Button from "./Button";
import Heading from "./Heading";
import React from "react";
import Thumbnail from "./Thumbnail";
import classnames from "classnames";
import formatDateRange from "../utils/formatDateRange";
import { useTranslation } from "../locales/i18n";

interface FileCardProps {
  document?: {
    created_at: string;
  };
  heading: string;
  file?: File;
  /** Event handler for when the "Remove" button is clicked. We'll pass it the `id` prop above. */
  onRemoveClick?: React.MouseEventHandler<HTMLButtonElement>;
  errorMsg?: React.ReactNode;
}

/**
 * A FileCard renders a file's info, thumbnail, and a button to remove the file.
 */
const FileCard = (props: FileCardProps) => {
  const { t } = useTranslation();
  const { document, file, heading, errorMsg } = props;
  const removeButton = t("components.fileCard.removeButton");

  const cardClasses = classnames(
    "c-file-card padding-2 margin-bottom-3 display-flex flex-wrap",
    {
      "border-1px border-base-lighter": !errorMsg,
      "border-2px border-red": errorMsg,
    }
  );

  const filenameClasses =
    "c-file-card__name padding-bottom-1 margin-bottom-1 margin-top-0 border-bottom-2px border-base-lighter font-heading-xs";

  const readOnly = !!document;

  return (
    <div className={cardClasses} data-test="file-card">
      <Thumbnail file={file} />
      <div className="c-file-card__content">
        <Heading level="3" className="margin-bottom-1 margin-top-1" size="4">
          {heading}
          {errorMsg && <p className="text-error">{errorMsg}</p>}
        </Heading>
        {readOnly ? (
          <React.Fragment>
            <div className={filenameClasses}>
              {t("components.fileCard.uploadDate", {
                date: formatDateRange(document.created_at),
              })}
            </div>
            <div className="text-italic">
              {t("components.fileCard.removalWarning")}
            </div>
          </React.Fragment>
        ) : (
          <React.Fragment>
            <div className={filenameClasses}>{file?.name}</div>
            <Button
              className="text-error hover:text-error-dark active:text-error-darker margin-top-0"
              onClick={props.onRemoveClick}
              variation="unstyled"
            >
              {removeButton}
            </Button>
          </React.Fragment>
        )}
      </div>
    </div>
  );
};

export default FileCard;
