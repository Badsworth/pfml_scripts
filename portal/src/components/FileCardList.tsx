import React, { useState } from "react";
import AppErrorInfo from "../models/AppErrorInfo";
import BenefitsApplicationDocument from "../models/BenefitsApplicationDocument";
import FileCard from "./FileCard";
import Spinner from "./Spinner";
import TempFile from "../models/TempFile";
import TempFileCollection from "../models/TempFileCollection";
import { useTranslation } from "../locales/i18n";

/**
 * Render a FileCard. This handles some busy work such as creating a onRemove handler and
 * interpolating a heading string for the file. Renders the FileCard inside of a <li> element.
 * @param index The zero-based index of the file in the list. This is used to
 * to interpolate a heading for the file.
 * @param fileHeadingPrefix A string prefix we'll use as a heading in each FileCard. We
 * will use the index param to interpolate the heading.
 */
function renderFileCard(
  tempFile: TempFile,
  index: number,
  onRemoveTempFile: (id: string) => void,
  fileHeadingPrefix: string,
  errorMsg: React.ReactNode = null
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
 * @param index The zero-based index of the file in the list. This is used to
 * to interpolate a heading for the file.
 * @param fileHeadingPrefix A string prefix we'll use as a heading in each FileCard. We
 * will use the index param to interpolate the heading.
 */
function renderDocumentFileCard(
  document: BenefitsApplicationDocument,
  index: number,
  fileHeadingPrefix: string
) {
  const heading = `${fileHeadingPrefix} ${index + 1}`;

  return (
    <li key={document.fineos_document_id}>
      <FileCard document={document} heading={heading} />
    </li>
  );
}

interface FileCardListProps {
  tempFiles: TempFileCollection;
  fileErrors: AppErrorInfo[];
  onChange: (files: File[]) => Promise<void>;
  onRemoveTempFile: (id: string) => void;
  fileHeadingPrefix: string;
  addFirstFileButtonText: string;
  addAnotherFileButtonText: string;
  documents: BenefitsApplicationDocument[];
}
/**
 * A list of previously uploaded files and a button to upload additional files. This component
 * renders an invisible input component to handle file selection and then renders a list of
 * FileCards for each selected file.
 */
const FileCardList = (props: FileCardListProps) => {
  const { t } = useTranslation();
  const [isLoading, setIsLoading] = useState(false);
  const {
    documents,
    tempFiles,
    onChange,
    onRemoveTempFile,
    fileHeadingPrefix,
    fileErrors,
  } = props;

  let documentFileCount = 0;
  let documentFileCards: JSX.Element[] = [];

  if (documents) {
    documentFileCount = documents.length;
    documentFileCards = documents.map((file, index) =>
      renderDocumentFileCard(file, index, fileHeadingPrefix)
    );
  }

  const fileCards = tempFiles.items.map((file, index) => {
    const fileError = fileErrors.find(
      (appErrorInfo) => appErrorInfo.meta?.file_id === file.id
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

  const handleChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    // This will only have files selected this time, not previously selected files
    // e.target.files is a FileList type which isn't an array, but we can turn it into one
    // @see https://developer.mozilla.org/en-US/docs/Web/API/FileList
    const files = event.target.files ? Array.from(event.target.files) : [];

    // Reset the input element's value. When a user selects a file which was already
    // selected it normally won't trigger the onChange event, but that's not what we want.
    // By resetting the value here we ensure that the onChange event occurs even if the
    // user just selects the same file(s). This is important eg if the user selected file 'A',
    // removed that file, and then selected file 'A' again. We tried using the onInput event
    // instead of onChange but it behaved the same way as onChange.
    // Additionally, we do this step _after_ we've already retrieved the event's files because
    // this step will reset event.target.files to an empty FileList.
    event.target.value = "";
    setIsLoading(true);
    await onChange(files);
    setIsLoading(false);
  };

  return (
    <div className="margin-bottom-4">
      <ul className="usa-list usa-list--unstyled measure-5">
        {documentFileCards}
      </ul>
      <ul className="usa-list usa-list--unstyled measure-5">{fileCards}</ul>
      {isLoading ? (
        <div className="text-center measure-5">
          <Spinner aria-valuetext={t("components.fileCardList.loadingLabel")} />
        </div>
      ) : (
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
      )}
    </div>
  );
};

export default FileCardList;
