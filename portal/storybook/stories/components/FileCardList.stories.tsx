/* eslint-disable no-alert */
import FileCardList from "src/components/FileCardList";
import { Props } from "types/common";
import React from "react";
import useFilesLogic from "src/hooks/useFilesLogic";

export default {
  title: "Components/FileCardList",
  component: FileCardList,
  args: {
    addFirstFileButtonText: "Choose a document",
    addAnotherFileButtonText: "Choose another document",
    documents: [
      {
        content_type: "image/jpeg",
        created_at: "2021-01-30",
      },
    ],
    fileHeadingPrefix: "Document",
    fileErrors: [],
  },
};

export const Default = (args: Props<typeof FileCardList>) => {
  const { files, processFiles, removeFile } = useFilesLogic({
    clearErrors: () => {},
    catchError: () => {
      alert("invaid file");
    },
  });

  return (
    <FileCardList
      {...args}
      tempFiles={files}
      onRemoveTempFile={removeFile}
      onChange={processFiles}
    />
  );
};
