import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";

/**
 * Create a URL for an image preview of image files and then trigger the component to render.
 * @param {File} file File whose preview we should load
 * @param {Function} setPreviewLoading State-setter to cause the component to render
 * @param {Function} setImageSrc State-setter to set the preview URL
 * @returns {undefined|Function} If a preview URL is loaded we'll return a function to clean up
 * the URL resource.
 */
const loadImagePreview = (file, setPreviewLoading, setImageSrc) => {
  if (file && file.type.startsWith("image/")) {
    const imageUrl = URL.createObjectURL(file);
    setImageSrc(imageUrl);
    setPreviewLoading(false);

    // On unmount we can clean up the URL.
    // Browsers will release object URLs automatically when the document is unloaded; however, for
    // optimal performance and memory usage, we can do it here manually when we know it's no longer
    // needed. Read more: https://developer.mozilla.org/en-US/docs/Web/API/URL/createObjectURL
    return () => URL.revokeObjectURL(imageUrl);
  } else {
    setPreviewLoading(false);
  }
};

/**
 * Displays a thumbnail preview for a file input field
 */
const Thumbnail = (props) => {
  const { file } = props;
  const [previewLoading, setPreviewLoading] = useState(true);
  const [imageSrc, setImageSrc] = useState();

  // Asynchronously load a preview of the file the first time this component is rendered.
  useEffect(() => {
    return loadImagePreview(file, setPreviewLoading, setImageSrc);
  }, [file]);

  if (previewLoading) {
    // Avoid showing a flash of the wrong content while we load a preview
    return null;
  }
  const hasImage = !!imageSrc;

  let thumbnailClass = "c-thumbnail margin-right-2 display-flex";
  if (!hasImage) {
    thumbnailClass =
      thumbnailClass + " c-thumbnail--fallback border-1px border-base-lighter";
  }

  return (
    <div className={thumbnailClass}>
      {hasImage ? (
        <img src={imageSrc} alt="" />
      ) : (
        <svg
          width="30"
          height="40"
          viewBox="0 0 30 40"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            stroke="black"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M12 14.61H8M18.5 1.34H4.5C2.567 1.34 1 2.984 1 5.013V34.413C1 36.443 2.567 38.088 4.5 38.088H25.5C27.433 38.088 29 36.443 29 34.413V12.363L18.5 1.34ZM18 1.34V12.568H29L18 1.34ZM22 21.756H8H22ZM22 28.902H8H22Z"
          />
        </svg>
      )}
    </div>
  );
};

Thumbnail.propTypes = {
  /** File we'll display a thumbnail for */
  file: PropTypes.object,
};

export default Thumbnail;
