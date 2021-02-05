import useCollectionState from "./useCollectionState";

/**
 * Convenience hook for managing TempFileCollection, usually used in conjunction with FileCardList
 * @param {TempFileCollection} initialState - initial TempFileCollection
 * @param {object} options
 * @param {Function} options.clearErrors - function that clears any FileValidationErrors
 * @returns {{ addTempFiles, removeTempFile, tempFiles, setTempFiles }}
 */
const useTempFileCollection = (initialState, { clearErrors }) => {
  const {
    collection: tempFiles,
    addItems: addFiles,
    removeItem: removeTempFile,
    setCollection: setTempFiles,
  } = useCollectionState(initialState);

  /**
   * Clear any errors and add files to collection
   * @param {TempFile[]} tempFiles - array of TempFiles
   */
  const addTempFiles = (tempFiles) => {
    clearErrors();
    addFiles(tempFiles);
  };

  return {
    addTempFiles,
    removeTempFile,
    tempFiles,
    setTempFiles,
  };
};

export default useTempFileCollection;
