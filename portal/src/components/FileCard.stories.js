import React, { useEffect, useState } from "react";
import FileCard from "./FileCard";

export default {
  title: "Components/FileCard",
  component: FileCard,
};

export const PdfFileCard = () => (
  <FileCard
    heading="Document 1"
    filename="WH-380-E.pdf"
    file={new Blob([], { type: "application/pdf" })}
    onRemoveClick={() => {}}
  />
);

export const ImageFileCard = () => {
  // This example is more complicated because we need to get an object which can be processed
  // with URL.createObjectURL() by the Thumbnail component. What we'll do is fetch the
  // Storybook favicon (it needs to be a locally served image in order to avoid CORS errors),
  // convert it to a Blob, and then pass that to the FileCard as though it were a File.

  // Asynchronously fetch an image file to use as our thumbnail
  const [file, setFile] = useState();
  useEffect(() => {
    const fetchImage = async () => {
      // If we change the port that storybook is served on we'll need to update it here
      await fetch("http://localhost:6006/favicon.ico")
        .then((response) => {
          // Convert the image response to a Blob
          return response.blob();
        })
        .then((blob) => {
          // Now that we have our image we can trigger the FileCard to render
          setFile(blob);
        });
    };

    fetchImage();
  }, []);

  // Only render the FileCard once we've asynchronously downloaded an image to send to it
  return (
    <div>
      {file ? (
        <FileCard
          heading="Document 2"
          filename="favicon.png"
          file={file}
          onRemoveClick={() => {}}
        />
      ) : null}
    </div>
  );
};
