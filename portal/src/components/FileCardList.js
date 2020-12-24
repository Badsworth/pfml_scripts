import AppErrorInfo from "../models/AppErrorInfo";
import AppErrorInfoCollection from "../models/AppErrorInfoCollection";
import Document from "../models/Document";
import FileCard from "./FileCard";
import PropTypes from "prop-types";
import React from "react";
import tracker from "../services/tracker";
import { uniqueId } from "lodash";
import { useTranslation } from "../locales/i18n";

// Only image and pdf files are allowed to be uploaded
const allowedFileTypes = [
  "image/png",
  "image/jpeg",
  "image/tiff",
  "image/heic",
  "application/pdf",
];

// Max file size in bytes
const maximumFileSize = 3500000;

// Exclusion reasons reasons
const disallowedReasons = {
  size: "size",
  sizeAndType: "sizeAndType",
  type: "type",
};

/**
 * Filter a list of files into sets of allowed files and disallowed files based on file types and sizes.
 * Track disallowed files with a ValidationError event.
 * @param {File[]} files Files to filter
 * @returns {Array.<Array.<File>>} Arrays of Files -- [allowedFiles, disallowedFilesForSize, disallowedFilesForType, disallowedFilesForSizeAndType]
 * @example const [allowedFiles, disallowedFilesForSize, disallowedFilesForType, disallowedFilesForSizeAndType] = filterAllowedFiles(files);
 */
function filterAllowedFiles(files) {
  const allowedFiles = [];
  const disallowedFilesForSize = [];
  const disallowedFilesForType = [];
  const disallowedFilesForSizeAndType = [];

  files.forEach((file) => {
    let disallowedForSize = false;
    let disallowedForType = false;
    let disallowedForSizeAndType = false;

    if (file.size > maximumFileSize) {
      disallowedForSize = true;
    }
    if (!allowedFileTypes.includes(file.type)) {
      if (disallowedForSize) {
        disallowedForSizeAndType = true;
      } else {
        disallowedForType = true;
      }
    }

    const fileTrackingData = {
      fileSize: file.size,
      fileType: file.type,
    };
    if (disallowedForSizeAndType) {
      disallowedFilesForSizeAndType.push(file);
      tracker.trackEvent("ValidationError", {
        ...fileTrackingData,
        issueType: "invalid_size_and_type",
        issueField: "file",
      });
    } else if (disallowedForSize) {
      disallowedFilesForSize.push(file);
      tracker.trackEvent("ValidationError", {
        ...fileTrackingData,
        issueType: "invalid_size",
        issueField: "file",
      });
    } else if (disallowedForType) {
      disallowedFilesForType.push(file);
      tracker.trackEvent("ValidationError", {
        ...fileTrackingData,
        issueType: "invalid_type",
        issueField: "file",
      });
    } else {
      allowedFiles.push(file);
      tracker.trackEvent("File selected", fileTrackingData);
    }
  });

  return [
    allowedFiles,
    disallowedFilesForSize,
    disallowedFilesForType,
    disallowedFilesForSizeAndType,
  ];
}

/**
 * Returns i18n reason for excluding files from being uploaded, with interpolated filenames.
 * @param {File[]} disallowedFiles - Array of excluded files
 * @param {string} disallowedReason - Enum for exclusion reason
 * @param {Function} t - Localization method
 * @returns {string} Message explaining why the files are disallowed
 */
function getDisallowedMessage(disallowedFiles, disallowedReason, t) {
  let message;
  if (disallowedFiles.length) {
    const disallowedFileNames = disallowedFiles
      .map((file) => file.name)
      .join(", ");

    message = t("errors.invalidFile", {
      context: disallowedReason,
      disallowedFileNames,
    });
  }
  return message;
}

/**
 * Generate error messages for disallowed files and display messages using AppErrors.
 * @param {Array.<Array.<File>>} disallowedFiles - Array of array of File objects
 * @param {Function} setAppErrors - Collection method to update AppErrors
 * @param {Function} t - Localization method
 */
function disallowedFilesMessageHandler(disallowedFiles, setAppErrors, t) {
  const [
    disallowedFilesForSize,
    disallowedFilesForType,
    disallowedFilesForSizeAndType,
  ] = disallowedFiles;
  const errorsCollection = [];

  const sizeMessage = getDisallowedMessage(
    disallowedFilesForSize,
    disallowedReasons.size,
    t
  );
  const typeMessage = getDisallowedMessage(
    disallowedFilesForType,
    disallowedReasons.type,
    t
  );
  const sizeAndTypeMessage = getDisallowedMessage(
    disallowedFilesForSizeAndType,
    disallowedReasons.sizeAndType,
    t
  );

  if (sizeMessage) {
    errorsCollection.push(new AppErrorInfo({ message: sizeMessage }));
  }
  if (typeMessage) {
    errorsCollection.push(new AppErrorInfo({ message: typeMessage }));
  }
  if (sizeAndTypeMessage) {
    errorsCollection.push(new AppErrorInfo({ message: sizeAndTypeMessage }));
  }

  if (errorsCollection.length) {
    setAppErrors(new AppErrorInfoCollection(errorsCollection));
  }
}

/**
 * Return an onChange handler which filters out invalid file types and then saves any new
 * files with setFiles.
 * @param {Function} setFiles a setter function for updating the files state
 * @param {Function} setAppErrors - Collection method to update AppErrors
 * @param {Function} t - Localization method
 * @returns {Function} onChange handler function
 */
function useChangeHandler(setFiles, setAppErrors, t) {
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

    const [allowedFiles, ...disallowedFiles] = filterAllowedFiles(files);

    disallowedFilesMessageHandler(disallowedFiles, setAppErrors, t);

    const newFiles = allowedFiles.map((file) => {
      return {
        // Generate unique ID for each file so React can keep track of them in a list and we can
        // reference specific files to delete
        id: uniqueId("File"),
        file,
      };
    });

    setFiles((filesWithUniqueId) => [...filesWithUniqueId, ...newFiles]);
  };
}

/**
 * Render a FileCard. This handles some busy work such as creating a onRemove handler and
 * interpolating a heading string for the file. Renders the FileCard inside of a <li> element.
 * @param {{id:string, file: File}} fileWithUniqueId The file to render as a FileCard
 * @param {integer} index The zero-based index of the file in the list. This is used to
 * to interpolate a heading for the file.
 * @param {Function} setFiles Setter function for updating the list of files. This is needed
 * for the onRemoveClick handler function that we pass into each FileCard.
 * @param {string} fileHeadingPrefix A string prefix we'll use as a heading in each FileCard. We
 * will use the index param to interpolate the heading.
 * @param {string} [errorMsg]
 * @returns {React.Component} A <li> element containing the rendered FileCard.
 */
function renderFileCard(
  fileWithUniqueId,
  index,
  setFiles,
  fileHeadingPrefix,
  errorMsg = null
) {
  const removeFile = (id) => {
    // Given a file id remove it from the list of files
    setFiles((files) => {
      return files.filter((file) => file.id !== id);
    });
  };

  const handleRemoveClick = () => removeFile(fileWithUniqueId.id);
  const heading = `${fileHeadingPrefix} ${index + 1}`;

  return (
    <li key={fileWithUniqueId.id}>
      <FileCard
        heading={heading}
        file={fileWithUniqueId.file}
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
    filesWithUniqueId,
    setFiles,
    fileHeadingPrefix,
    fileErrors,
  } = props;

  let documentFileCount = 0;
  let documentFileCards = [];

  if (documents) {
    documentFileCount = documents.length;
    documentFileCards = documents.map((file, index) =>
      renderDocumentFileCard(file, index, fileHeadingPrefix)
    );
  }

  const fileCards = filesWithUniqueId.map((file, index) => {
    const fileError = fileErrors.find(
      (appErrorInfo) => appErrorInfo.meta.file_id === file.id
    );
    const errorMsg = fileError ? fileError.message : null;
    return renderFileCard(
      file,
      index + documentFileCount,
      setFiles,
      fileHeadingPrefix,
      errorMsg
    );
  });

  const button = filesWithUniqueId.length
    ? props.addAnotherFileButtonText
    : props.addFirstFileButtonText;

  const { t } = useTranslation();
  const setAppErrors = props.setAppErrors;
  const handleChange = useChangeHandler(setFiles, setAppErrors, t);

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

FileCardList.propTypes = {
  /**
   * Array of files to be rendered as FileCards. This should be a state variable which can be set
   * with setFiles below.
   */
  filesWithUniqueId: PropTypes.arrayOf(
    PropTypes.shape({
      /** A unique ID for each file */
      id: PropTypes.string.isRequired,
      /**
       * Note that this should actually be a File instance. However the File class is a
       * browser feature, not a Node.js feature, and so it isn't available for server-side
       * rendering. For that reason we specify a custom shape here but in reality we expect
       * a File. See [File docs]( https://developer.mozilla.org/en-US/docs/Web/API/File).
       */
      file: PropTypes.shape({
        name: PropTypes.string.isRequired,
        type: PropTypes.string.isRequired,
      }).isRequired,
    })
  ).isRequired,
  fileErrors: PropTypes.arrayOf(PropTypes.instanceOf(AppErrorInfo)),
  /** Errors setter function to use when there are errors in the file upload */
  setAppErrors: PropTypes.func.isRequired,
  /** Setter to update the application's files state */
  setFiles: PropTypes.func.isRequired,
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
};

export default FileCardList;
