import React, { useEffect, useState } from "react";
import FileCard from "./FileCard";

export default {
  title: "Components/FileCard",
  component: FileCard,
};

export const PdfFileCard = () => {
  try {
    // The File constructor can fail -- in particular in Internet Explorer where it isn't
    // supported.
    return (
      <FileCard
        heading="Document 1"
        file={new File([], "WH-380-E.pdf", { type: "application/pdf" })}
        onRemoveClick={() => {}}
      />
    );
  } catch (err) {
    // Unable to create a File -- fallback to displaying an error
    console.error(err.message);
    return "Unable to render this story because the File constructor failed. This usually happens when you're using Internet Explorer which doesn't support the File constructor. You can see the FileCardList component to select your own files to view FileCards with.";
  }
};

export const ImageFileCard = () => {
  // This example is more complicated because we need to get an object which can be processed
  // with URL.createObjectURL() by the Thumbnail component. What we'll do is fetch the
  // Storybook favicon (it needs to be a locally served image in order to avoid CORS errors),
  // convert it to a Blob, use that to create a File, and then pass that to the FileCard.
  // If the File constructor fails we'll just render an error instead because the user is
  // probably using Internet Explorer.

  // Asynchronously fetch an image file to use as our thumbnail
  const [file, setFile] = useState();
  const [fileFailed, setFileFailed] = useState(false);
  useEffect(() => {
    const fetchImage = async () => {
      const response = await fetch("/favicon.ico");
      // Convert the image response to a Blob
      const blob = await response.blob();
      // Now that we have our image we can trigger the FileCard to render
      try {
        setFile(new File([blob], "favicon.png", { type: "image/png" }));
      } catch (err) {
        console.error(err.message);
        setFileFailed(true);
      }
    };

    fetchImage();
  }, []);

  if (fileFailed) {
    // Unable to create a File -- fallback to displaying an error
    return "Unable to render this story because the File constructor failed. This usually happens when you're using Internet Explorer which doesn't support the File constructor. You can see the FileCardList component to select your own files to view FileCards with.";
  }

  // Only render the FileCard once we've asynchronously downloaded an image to send to it
  return (
    <div>
      {file ? (
        <FileCard heading="Document 2" file={file} onRemoveClick={() => {}} />
      ) : null}
    </div>
  );
};
