import AppErrorInfo from "../models/AppErrorInfo";
import Document from "../models/Document";
import FileCard from "./FileCard";
import PropTypes from "prop-types";
import React from "react";
import TempFile from "../models/TempFile";
import TempFileCollection from "../models/TempFileCollection";
import { ValidationError } from "../errors";
import { snakeCase } from "lodash";
import { t } from "../locales/i18n";
import tracker from "../services/tracker";

// Only image and pdf files are allowed to be uploaded
const defaultAllowedFileTypes = ["image/png", "image/jpeg", "application/pdf"];

// Max file size in bytes
const defaultMaximumFileSize = 3500000;

// Exclusion reasons
const disallowedReasons = {
  size: "size",
  sizeAndType: "sizeAndType",
  type: "type",
};

/**
 * Return ValidationError issues for disallowed file
 * @param {File} disallowedFile - file that is not allowed
 * @param {string} disallowedReason - reason file is not allowed (size, sizeAndType, or type)
 * @returns {Issue}
 */
function getIssueForDisallowedFile(disallowedFile, disallowedReason) {
  const i18nKey = `errors.invalidFile_${disallowedReason}`;

  return {
    message: t(i18nKey, {
      context: disallowedReason,
      disallowedFileNames: disallowedFile.name,
    }),
  };
}

/**
 * Filter a list of files into sets of allowed files and disallowed files based on file types and sizes.
 * Track disallowed files with a ValidationError event.
 * @param {File[]} files Files to filter
 * @returns {Array.<Array.<File>>} Arrays of Files -- [allowedFiles, disallowedFilesForSize, disallowedFilesForType, disallowedFilesForSizeAndType]
 * @example const [allowedFiles, disallowedFilesForSize, disallowedFilesForType, disallowedFilesForSizeAndType] = filterAllowedFiles(files);
 */
function filterAllowedFiles(files, { allowedFileTypes, maximumFileSize }) {
  const allowedFiles = [];
  const issues = [];

  files.forEach((file) => {
    let disallowedReason = null;

    if (file.size > maximumFileSize) {
      disallowedReason = disallowedReasons.size;
    }
    if (!allowedFileTypes.includes(file.type)) {
      if (disallowedReason === disallowedReasons.size) {
        disallowedReason = disallowedReasons.sizeAndType;
      } else {
        disallowedReason = disallowedReasons.type;
      }
    }

    const fileTrackingData = {
      fileSize: file.size,
      fileType: file.type,
    };

    if (disallowedReason) {
      issues.push(getIssueForDisallowedFile(file, disallowedReason));
      // TODO (CP-1771): Remove tracking once error handling supports additional event data
      tracker.trackEvent("FileValidationError", {
        ...fileTrackingData,
        issueType: `invalid_${snakeCase(disallowedReason)}`,
        issueField: "file",
      });
    } else {
      allowedFiles.push(file);
      tracker.trackEvent("File selected", fileTrackingData);
    }
  });

  return {
    allowedFiles,
    issues,
  };
}

/**
 * Return an onChange handler which filters out invalid file types and then saves any new
 * files with onAddTempFiles.
 * @param {Function} onAddTempFiles a setter function for updating the files state
 * @param {Function} onInvalidFilesError a setter function for updating the files state
 * @param {number} maximumFileSize Maximum allowed file size
 * @param {string[]} allowedFileTypes Array of allowed file mimetypes
 * @returns {Function} onChange handler function
 */
function useChangeHandler(
  onAddTempFiles,
  onInvalidFilesError,
  maximumFileSize,
  allowedFileTypes
) {
  return (event) => {
    // This will only have files selected this time, not previously selected files
    // e.target.files is a FileList type which isn't an array, but we can turn it into one
    // @see https://developer.mozilla.org/en-US/docs/Web/API/FileList
    const files = Array.from(event.target.files);

    // Reset the input element's value. When a user selects a file which was already
    // selected it normally won't trigger the onChange event, but that's not what we want.
    // By resetting the value here we ensure that the onChange event occurs even if the
    // user just selects the same file(s). This is important eg if the user selected file 'A',
    // removed that file, and then selected file 'A' again. We tried using the onInput event
    // instead of onChange but it behaved the same way as onChange.
    // Additionally, we do this step _after_ we've already retrieved the event's files because
    // this step will reset event.target.files to an empty FileList.
    event.target.value = "";

    const { allowedFiles, issues } = filterAllowedFiles(files, {
      maximumFileSize,
      allowedFileTypes,
    });

    onAddTempFiles(allowedFiles.map((file) => new TempFile({ file })));

    if (issues.length > 0) {
      const i18nPrefix = "files";
      onInvalidFilesError(new ValidationError(issues, i18nPrefix));
    }
  };
}

/**
 * Render a FileCard. This handles some busy work such as creating a onRemove handler and
 * interpolating a heading string for the file. Renders the FileCard inside of a <li> element.
 * @param {TempFile} tempFile The file to render as a FileCard
 * @param {integer} index The zero-based index of the file in the list. This is used to
 * to interpolate a heading for the file.
 * @param {Function} onRemoveTempFile Handler for removing a single file.
 * @param {string} fileHeadingPrefix A string prefix we'll use as a heading in each FileCard. We
 * will use the index param to interpolate the heading.
 * @param {string} [errorMsg]
 * @returns {React.Component} A <li> element containing the rendered FileCard.
 */
function renderFileCard(
  tempFile,
  index,
  onRemoveTempFile,
  fileHeadingPrefix,
  errorMsg = null
) {
  const handleRemoveClick = () => onRemoveTempFile(tempFile.id);
  const heading = `${fileHeadingPrefix} ${index + 1}`;

  return (
    <li key={tempFile.id}>
      <FileCard
        heading={heading}
        file={tempFile.file}
        onRemoveClick={handleRemoveClick}
        errorMsg={errorMsg}
      />
    </li>
  );
}

/**
 * Render a read-only FileCard for a document. These represent documents that have already been uploaded,
 * and can no longer be removed from the application. Renders the FileCard inside of a <li> element.
 * @param {Document} document The document to render as a FileCard
 * @param {integer} index The zero-based index of the file in the list. This is used to
 * to interpolate a heading for the file.
 * @param {string} fileHeadingPrefix A string prefix we'll use as a heading in each FileCard. We
 * will use the index param to interpolate the heading.
 * @returns {React.Component} A <li> element containing the rendered FileCard.
 */
function renderDocumentFileCard(document, index, fileHeadingPrefix) {
  const heading = `${fileHeadingPrefix} ${index + 1}`;

  return (
    <li key={document.fineos_document_id}>
      <FileCard document={document} heading={heading} />
    </li>
  );
}

/**
 * A list of previously uploaded files and a button to upload additional files. This component
 * renders an invisible input component to handle file selection and then renders a list of
 * FileCards for each selected file.
 */
const FileCardList = (props) => {
  const {
    documents,
    tempFiles,
    onAddTempFiles,
    onInvalidFilesError,
    onRemoveTempFile,
    fileHeadingPrefix,
    fileErrors,
    maximumFileSize,
    allowedFileTypes,
  } = props;

  let documentFileCount = 0;
  let documentFileCards = [];

  if (documents) {
    documentFileCount = documents.length;
    documentFileCards = documents.map((file, index) =>
      renderDocumentFileCard(file, index, fileHeadingPrefix)
    );
  }

  const fileCards = tempFiles.items.map((file, index) => {
    const fileError = fileErrors.find(
      (appErrorInfo) => appErrorInfo.meta.file_id === file.id
    );
    const errorMsg = fileError ? fileError.message : null;
    return renderFileCard(
      file,
      index + documentFileCount,
      onRemoveTempFile,
      fileHeadingPrefix,
      errorMsg
    );
  });

  const button = tempFiles.isEmpty
    ? props.addFirstFileButtonText
    : props.addAnotherFileButtonText;

  const handleChange = useChangeHandler(
    onAddTempFiles,
    onInvalidFilesError,
    maximumFileSize,
    allowedFileTypes
  );

  return (
    <div className="margin-bottom-4">
      <ul className="usa-list usa-list--unstyled measure-5">
        {documentFileCards}
      </ul>
      <ul className="usa-list usa-list--unstyled measure-5">{fileCards}</ul>
      <label className="margin-top-2 usa-button usa-button--outline">
        {button}
        <input
          className="c-file-card-list__input"
          type="file"
          accept="image/*,.pdf"
          multiple
          onChange={handleChange}
        />
      </label>
    </div>
  );
};

FileCardList.defaultProps = {
  allowedFileTypes: defaultAllowedFileTypes,
  maximumFileSize: defaultMaximumFileSize,
};

FileCardList.propTypes = {
  /**
   * Instance of TempFileCollection representing files selected by the user but not yet uploaded
   * and are rendered as FileCards. This should be a state variable which can be set
   * with onAddTempFiles below.
   */
  tempFiles: PropTypes.instanceOf(TempFileCollection).isRequired,
  fileErrors: PropTypes.arrayOf(PropTypes.instanceOf(AppErrorInfo)),
  /**
   * Files change event handler. Receives array of allowed files
   *
   */
  onAddTempFiles: PropTypes.func.isRequired,
  /**
   * Invalid file error handler. Receives ValidationError with list of
   * validation issues
   */
  onInvalidFilesError: PropTypes.func.isRequired,
  /** Remove file event handlers. Receives a single file instance */
  onRemoveTempFile: PropTypes.func.isRequired,
  /**
   * File descriptor prefix. This will be displayed in each file card. For example
   * if you specify "Document" file headings will be "Document 1", "Document 2", etc.
   */
  fileHeadingPrefix: PropTypes.string.isRequired,
  /** Button text to use when no files have been selected yet */
  addFirstFileButtonText: PropTypes.string.isRequired,
  /** Button text to use when one or more files have already been selected */
  addAnotherFileButtonText: PropTypes.string.isRequired,
  /** Documents that need to be rendered as read-only FileCards, representing previously uploaded files */
  documents: PropTypes.arrayOf(PropTypes.instanceOf(Document)),
  /** Maximum allowed file size in bytes */
  maximumFileSize: PropTypes.number,
  /** Array of allowed file mimetypes */
  allowedFileTypes: PropTypes.arrayOf(PropTypes.string),
};

export default FileCardList;
