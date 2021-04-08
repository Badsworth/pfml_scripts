/* eslint-disable no-alert */
import Document from "src/models/Document";
import FileCardList from "src/components/FileCardList";
import React from "react";
import useFilesLogic from "src/hooks/useFilesLogic";

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

  const { files, processFiles, removeFile } = useFilesLogic({
    clearErrors: () => {},
    catchError: () => {
      alert("invaid file");
    },
  });

  return (
    <FileCardList
      documents={initialDocuments}
      tempFiles={files}
      onChange={processFiles}
      onRemoveTempFile={removeFile}
      fileErrors={[]}
      {...args}
    />
  );
};
