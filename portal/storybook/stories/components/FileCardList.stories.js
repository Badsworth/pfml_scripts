import React, { useEffect, useState } from "react";
import Alert from "src/components/Alert";
import FileCardList from "src/components/FileCardList";
import { uniqueId } from "lodash";

export default {
  title: "Components/FileCardList",
  component: FileCardList,
};

export const Default = () => {
  // This example is more complicated because we need to get an object which can be processed
  // with URL.createObjectURL() by the Thumbnail component. What we'll do is fetch the
  // Storybook favicon (it needs to be a locally served image in order to avoid CORS errors),
  // convert it to a File, and then pass that to the FileCard component.

  // Asynchronously fetch an image file to use as our thumbnail
  const [filesFailed, setFilesFailed] = useState(false);
  const [filesLoaded, setFilesLoaded] = useState(false);
  const [files, setFiles] = useState([]);
  useEffect(() => {
    const fetchImage = async () => {
      try {
        const response = await fetch("/favicon.ico");
        // Convert the image response to a Blob
        const blob = await response.blob();
        // Attempt to create the example FileCards. Internet Explorer doesn't support the File
        // constructor and will fail here.
        const newFiles = [
          {
            file: new File([], "WH-380-E.pdf", {
              type: "application/pdf",
            }),
            id: uniqueId("File"),
          },
          {
            file: new File([blob], "favicon.png", { type: "image/png" }),
            id: uniqueId("File"),
          },
        ];
        setFiles((files) => [...files, ...newFiles]);
      } catch (err) {
        // Trigger an error alert to display saying that we failed to load the example FileCards
        console.error(`Failed to load example FileCards: ${err.message}`);
        setFilesFailed(true);
      } finally {
        // Trigger the FileCardList component to render
        setFilesLoaded(true);
      }
    };

    fetchImage();
  }, []);

  return (
    <div>
      {filesFailed ? (
        <Alert>
          Failed to load example FileCards. This may be because you're using
          Internet Explorer, where the File constructor isn't supported, or
          because we weren't able to fetch a image to use. Choose your own files
          using the button below.
        </Alert>
      ) : null}
      {filesLoaded ? (
        <FileCardList
          files={files}
          setFiles={setFiles}
          fileHeadingPrefix="Document"
          addFirstFileButtonText="Choose a document"
          addAnotherFileButtonText="Choose another document"
          onRemoveClick={() => {}}
        />
      ) : null}
    </div>
  );
};
