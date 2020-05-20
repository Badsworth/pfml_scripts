import Heading from "./Heading";
import PropTypes from "prop-types";
import React from "react";
import Thumbnail from "./Thumbnail";
import { useTranslation } from "../locales/i18n";

/**
 * A FileCard renders a file's info, thumbnail, and a button to remove the file.
 */
const FileCard = (props) => {
  const { t } = useTranslation();
  const heading = props.heading;
  const removeButton = t("components.fileCard.removeButton");

  const cardClasses =
    "c-file-card usa-card__container padding-2 margin-bottom-3 border-1px border-base-lighter display-flex flex-wrap";
  const filenameClasses =
    "c-file-card__name padding-bottom-2 margin-bottom-2 margin-top-0 border-bottom-2px border-base-lighter";

  return (
    <div className={cardClasses}>
      <Thumbnail file={props.file} />
      <div className="c-file-card__content">
        <Heading level="2" size="3">
          {heading}
        </Heading>
        <div className={filenameClasses}>{props.filename}</div>
        <button
          // a custom class to set the active color?
          className="usa-button usa-button--unstyled text-error hover:text-error-dark active:text-error-darker"
          type="button"
          onClick={() => props.onRemoveClick()}
        >
          {removeButton}
        </button>
      </div>
    </div>
  );
};

FileCard.propTypes = {
  /** The heading displayed for this file */
  heading: PropTypes.string.isRequired,
  /** The file's filename */
  filename: PropTypes.string.isRequired,
  /**
   * File object obtained from an input HTML element. We use a Blob here instead of File because
   * File isn't support in IE. Read more: https://developer.mozilla.org/en-US/docs/Web/API/File
   */
  file: PropTypes.instanceOf(Blob).isRequired,
  /** Event handler for when the "Remove" button is clicked. We'll pass it the `id` prop above. */
  onRemoveClick: PropTypes.func.isRequired,
};

export default FileCard;
