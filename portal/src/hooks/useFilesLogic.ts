import Compressor from "compressorjs";
import TempFile from "../models/TempFile";
import TempFileCollection from "../models/TempFileCollection";
import { ValidationError } from "../errors";
import { snakeCase } from "lodash";
import { t } from "../locales/i18n";
import tracker from "../services/tracker";
import useCollectionState from "./useCollectionState";

// Only image and pdf files are allowed to be uploaded
const defaultAllowedFileTypes = ["image/png", "image/jpeg", "application/pdf"];

// Max file size in bytes
const defaultMaximumFileSize = 4500000;

// Exclusion reasons
const disallowedReasons = {
  size: "size",
  sizeAndType: "sizeAndType",
  type: "type",
};

/**
 * Compress an image which size is greater than maximum file size and  returns a promise
 * @param {File} file
 * @param {number} maximumFileSize - Size at which compression will be attempted
 * @returns {Promise<File>}
 */
function optimizeFileSize(file, maximumFileSize) {
  return new Promise((resolve) => {
    if (
      file.size <= maximumFileSize ||
      !["image/png", "image/jpeg"].includes(file.type)
    ) {
      return resolve(file);
    }
    // eslint-disable-next-line no-new
    new Compressor(file, {
      quality: 0.6,
      checkOrientation: false, // Improves compression speed for larger files
      convertSize: maximumFileSize,
      success: (compressedBlob) => {
        // @ts-expect-error ts-migrate(2339) FIXME: Property 'name' does not exist on type 'Blob'.
        const fileName = compressedBlob.name;
        const fileNameWithPrefix = "Compressed_" + fileName;

        tracker.trackEvent("CompressorSize", {
          originalSize: file.size,
          compressedSize: compressedBlob.size,
        });
        // @ts-expect-error ts-migrate(2339) FIXME: Property 'name' does not exist on type 'Blob'.
        compressedBlob.name = fileNameWithPrefix;
        resolve(compressedBlob);
      },
      error: (error) => {
        tracker.noticeError(error, {
          fileSize: file.size,
          fileType: file.type,
        });

        tracker.trackEvent("CompressorError", {
          errorMessage: error.message,
          fileSize: file.size,
          fileType: file.type,
        });
        resolve(file);
      },
    });
  });
}

/**
 * Attempt to reduce the size of files
 * @param {File[]} files
 * @param {number} maximumFileSize - Size at which compression will be attempted
 * @returns {Promise<File[]>}
 */
function optimizeFiles(files, maximumFileSize) {
  const compressPromises = files.map((file) =>
    optimizeFileSize(file, maximumFileSize)
  );

  return Promise.all(compressPromises);
}

/**
 * Filter a list of files into sets of allowed files and disallowed files based on file types and sizes.
 * Track disallowed files with a ValidationError event.
 * @param {File[]} files Files to filter
 * @param {object} options
 * @param {string[]} options.allowedFileTypes
 * @param {number} options.maximumFileSize
 * @returns {object} { allowedFiles: File[], issues:Issue[] }
 * @example const { allowedFiles,issues }  = filterAllowedFiles(files);
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

const useFilesLogic = ({
  allowedFileTypes = defaultAllowedFileTypes,
  catchError,
  clearErrors,
  maximumFileSize = defaultMaximumFileSize,
}) => {
  const {
    collection: files,
    addItems: addFiles,
    removeItem: removeFile,
    // @ts-expect-error ts-migrate(2554) FIXME: Expected 1 arguments, but got 0.
  } = useCollectionState(new TempFileCollection());

  /**
   * Async function handles file optimization and filter logic
   * @param {File[]} files
   */
  const processFiles = async (files) => {
    clearErrors();
    const compressedFiles = await optimizeFiles(files, maximumFileSize);

    const { allowedFiles, issues } = filterAllowedFiles(compressedFiles, {
      maximumFileSize,
      allowedFileTypes,
    });

    addFiles(allowedFiles.map((file) => new TempFile({ file })));

    if (issues.length > 0) {
      const i18nPrefix = "files";
      catchError(new ValidationError(issues, i18nPrefix));
    }
  };

  return { files, processFiles, removeFile };
};

export default useFilesLogic;
