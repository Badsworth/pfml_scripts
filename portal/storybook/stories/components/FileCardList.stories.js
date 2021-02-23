import Document from "src/models/Document";
import FileCardList from "src/components/FileCardList";
import React from "react";
import TempFile from "src/models/TempFile";
import TempFileCollection from "src/models/TempFileCollection";
import useTempFileCollection from "src/hooks/useTempFileCollection";

export default {
  title: "Components/FileCardList",
  component: FileCardList,
  args: {
    fileHeadingPrefix: "Document",
    addFirstFileButtonText: "Choose a document",
    addAnotherFileButtonText: "Choose another document",
  },
};

export const Default = (args) => {
  const initialDocuments = [
    new Document({
      content_type: "image/jpeg",
      created_at: "2021-01-30",
    }),
  ];
  const initialFiles = new TempFileCollection([
    new TempFile({
      file: new File([], "WH-380-E.pdf", {
        type: "application/pdf",
      }),
    }),
  ]);

  const { tempFiles, addTempFiles, removeTempFile } = useTempFileCollection(
    initialFiles,
    {
      clearErrors: () => {},
    }
  );

  return (
    <FileCardList
      documents={initialDocuments}
      tempFiles={tempFiles}
      onAddTempFiles={addTempFiles}
      onInvalidFilesError={alert}
      onRemoveTempFile={removeTempFile}
      fileErrors={[]}
      {...args}
    />
  );
};
