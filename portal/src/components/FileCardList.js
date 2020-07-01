import { partition, uniqueId } from "lodash";
import AppErrorInfo from "../models/AppErrorInfo";
import AppErrorInfoCollection from "../models/AppErrorInfoCollection";
import FileCard from "./FileCard";
import PropTypes from "prop-types";
import React from "react";
import { useTranslation } from "../locales/i18n";

// Only image and pdf files are allowed to be uploaded
// todo: (CP-396) limit the set of image types allowed to those supported by the API
const allowedFileTypes = [/^image\//, "application/pdf"];

/**
 * Partition a list of files into a set of allowed files and a set of disallowed files based on
 * their file types.
 * @param {File[]} files Files to filter
 * @param {Array.<RegExp|string>} allowedFileTypes Array of strings and/or regexps of allowed
 * file types.
 * @returns {Array.<Array.<File>>} Pair of arrays of Files -- [allowedFiles, disallowedFiles]
 * @example const [allowedFiles, disallowedFiles] = filterAllowedFiles(files, allowedFileTypes);
 */
function filterAllowedFiles(files, allowedFileTypes) {
  // Filter files into allowed or disallowed based on each file's type.
  return partition(files, (file) => {
    // File is allowed if it matches any of the allowed types
    return allowedFileTypes.some((allowedType) => file.type.match(allowedType));
  });
}

/**
 * Return an onChange handler which filters out invalid file types and then saves any new
 * files with setFiles.
 * @param {Function} setFiles a setter function for updating the files state
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

    const [allowedFiles, disallowedFiles] = filterAllowedFiles(
      files,
      allowedFileTypes
    );

    if (disallowedFiles.length > 0) {
      const disallowedFileNames = disallowedFiles
        .map((file) => file.name)
        .join(", ");
      const message = t("errors.invalidFileType", { disallowedFileNames });
      setAppErrors(new AppErrorInfoCollection([new AppErrorInfo({ message })]));
    } else {
      setAppErrors(null);
    }

    const newFiles = allowedFiles.map((file) => {
      return {
        // Generate unique ID for each file so React can keep track of them in a list and we can
        // reference specific files to delete
        id: uniqueId("File"),
        file,
      };
    });

    setFiles((files) => [...files, ...newFiles]);
  };
}

/**
 * Render a FileCard. This handles some busy work such as creating a onRemove handler and
 * interpolating a heading string for the file. Renders the FileCard inside of a <li> element.
 * @param {object} file The files to render as FileCards
 * @param {integer} index The zero-based index of the file in the list. This is used to
 * to interpolate a heading for the file.
 * @param {Function} setFiles Setter function for updating the list of files. This is needed
 * for the onRemoveClick handler function that we pass into each FileCard.
 * @param {string} fileHeadingPrefix A string prefix we'll use as a heading in each FileCard. We
 * will use the index param to interpolate the heading.
 * @returns {React.Component} A <li> element containing the rendered FileCard.
 */
function renderFileCard(file, index, setFiles, fileHeadingPrefix) {
  const removeFile = (id) => {
    // Given a file id remove it from the list of files
    setFiles((files) => {
      return files.filter((file) => file.id !== id);
    });
  };

  const handleRemoveClick = () => removeFile(file.id);
  const heading = `${fileHeadingPrefix} ${index + 1}`;

  return (
    <li key={file.id}>
      <FileCard
        heading={heading}
        file={file.file}
        onRemoveClick={handleRemoveClick}
      />
    </li>
  );
}

/**
 * A list of previously uploaded files and a button to upload additional files. This component
 * renders an invisible input component to handle file selection and then renders a list of
 * FileCards for each selected file.
 */
const FileCardList = (props) => {
  const { files, setFiles, fileHeadingPrefix } = props;
  const fileCards = files.map((file, index) =>
    renderFileCard(file, index, setFiles, fileHeadingPrefix)
  );
  const button = files.length
    ? props.addAnotherFileButtonText
    : props.addFirstFileButtonText;

  const { t } = useTranslation();
  const setAppErrors = props.setAppErrors;
  const handleChange = useChangeHandler(setFiles, setAppErrors, t);

  return (
    <div>
      <ul className="usa-list usa-list--unstyled">{fileCards}</ul>
      <label className="margin-bottom-4 margin-top-2 usa-button usa-button--outline">
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
  files: PropTypes.arrayOf(
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
};

export default FileCardList;
