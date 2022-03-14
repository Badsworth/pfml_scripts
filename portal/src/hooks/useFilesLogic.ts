import { Issue, ValidationError } from "../errors";
import ApiResourceCollection from "../models/ApiResourceCollection";
import Compressor from "compressorjs";
import { ErrorsLogic } from "./useErrorsLogic";
import TempFile from "../models/TempFile";
import bytesToMb from "../utils/bytesToMb";
import { isFeatureEnabled } from "../services/featureFlags";
import { snakeCase } from "lodash";
import tracker from "../services/tracker";
import useCollectionState from "./useCollectionState";

// Only image and pdf files are allowed to be uploaded
const defaultAllowedFileTypes = [
  "image/png",
  "image/jpeg",
  "application/pdf",
] as const;

// Exclusion reasons
const disallowedReasons = {
  size: "size",
  apiGatewaySize: "apiGatewaySize",
  sizeAndType: "sizeAndType",
  type: "type",
} as const;

/**
 * Compress an image which size is greater than maximum file size and  returns a promise
 * @param maximumFileSize - Size at which compression will be attempted
 */
function optimizeImageSize(file: File): Promise<File> {
  const maximumImageSize = Number(process.env.fileSizeMaxBytesFineos);

  return new Promise((resolve) => {
    if (
      file.size <= maximumImageSize ||
      !["image/png", "image/jpeg"].includes(file.type)
    ) {
      return resolve(file);
    }
    // eslint-disable-next-line no-new
    new Compressor(file, {
      quality: 0.6,
      checkOrientation: false, // Improves compression speed for larger files
      convertSize: maximumImageSize,
      success: (compressedBlob: File) => {
        tracker.trackEvent("CompressorSize", {
          originalSize: file.size,
          compressedSize: compressedBlob.size,
        });

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
 * @param maximumFileSize - Size at which compression will be attempted
 */
function optimizeFiles(files: File[]) {
  const compressPromises = files.map((file) => optimizeImageSize(file));

  return Promise.all(compressPromises);
}

/**
 * Filter a list of files into sets of allowed files and disallowed files based on file types and sizes.
 * Track disallowed files with a ValidationError event.
 * @example const { allowedFiles,issues }  = filterAllowedFiles(files);
 */
function filterAllowedFiles(
  files: File[],
  {
    allowedFileTypes,
  }: {
    allowedFileTypes: readonly string[];
  }
) {
  const allowedFiles: File[] = [];
  const issues: Issue[] = [];

  files.forEach((file) => {
    let disallowedReason = "";
    const useApiGatewaySizeLimit =
      file.type === "application/pdf" && isFeatureEnabled("sendLargePdfToApi");

    const exceedsSizeLimit = useApiGatewaySizeLimit
      ? file.size >= Number(process.env.fileSizeMaxBytesApiGateway)
      : file.size > Number(process.env.fileSizeMaxBytesFineos);

    if (exceedsSizeLimit) {
      disallowedReason = useApiGatewaySizeLimit
        ? disallowedReasons.apiGatewaySize
        : disallowedReasons.size;
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
      // TODO (PORTAL-375): Remove tracking once error handling supports additional event data
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
 * @param disallowedReason - reason file is not allowed (size, sizeAndType, or type)
 */
function getIssueForDisallowedFile(
  disallowedFile: File,
  disallowedReason: string
): Issue {
  const context =
    disallowedReason === disallowedReasons.apiGatewaySize
      ? disallowedReasons.size
      : disallowedReason;

  const issueType = `clientSideError_${context}`;

  return {
    field: "file",
    namespace: "documents",
    type: issueType,
    extra: {
      sizeLimit:
        disallowedReason === disallowedReasons.apiGatewaySize
          ? bytesToMb(Number(process.env.fileSizeMaxBytesApiGateway))
          : bytesToMb(Number(process.env.fileSizeMaxBytesFineos)),
      disallowedFileNames:
        disallowedFile instanceof File ? disallowedFile.name : "",
    },
  };
}

const useFilesLogic = ({
  allowedFileTypes = defaultAllowedFileTypes,
  catchError,
  clearErrors,
}: {
  allowedFileTypes?: readonly string[];
  catchError: ErrorsLogic["catchError"];
  clearErrors: ErrorsLogic["clearErrors"];
}) => {
  const {
    collection: files,
    addItems: addFiles,
    removeItem: removeFile,
  } = useCollectionState(new ApiResourceCollection<TempFile>("id"));

  /**
   * Async function handles file optimization and filter logic
   */
  const processFiles = async (files: File[]) => {
    clearErrors();
    const compressedFiles = await optimizeFiles(files);

    const { allowedFiles, issues } = filterAllowedFiles(compressedFiles, {
      allowedFileTypes,
    });

    addFiles(allowedFiles.map((file) => new TempFile({ file })));

    if (issues.length > 0) {
      catchError(new ValidationError(issues));
    }
  };

  return { files, processFiles, removeFile };
};

export default useFilesLogic;
