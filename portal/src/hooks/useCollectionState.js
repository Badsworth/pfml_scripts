import Collection from "../models/Collection";
import { useState } from "react";

/**
 * React hook for creating a state for a Collection of objects
 * @param {Collection|Function} initialCollection - initial collection state
 * @returns {Array} - [collection, setCollection, addItem, updateItem, removeItem];
 */
const useCollectionState = (initialCollection) => {
  const initialCollectionIsInstance = initialCollection instanceof Collection;
  const initialCollectionIsFunction = initialCollection instanceof Function;

  if (!initialCollectionIsInstance && !initialCollectionIsFunction) {
    throw new Error(
      "useCollectionState expected an instance of Collection or a Function that returns a Collection"
    );
  }

  const [collection, setCollection] = useState(
    initialCollectionIsInstance ? initialCollection : null
  );

  // Support adding items in a collection when initial collection
  // is not defined
  const getCollection = (prevCollection) =>
    prevCollection || initialCollection();

  const addItem = (item) => {
    setCollection((prevCollection) =>
      getCollection(prevCollection).addItem(item)
    );
  };

  const updateItem = (item) => {
    setCollection((prevCollection) => prevCollection.updateItem(item));
  };

  const removeItem = (itemId) => {
    setCollection((prevCollection) => prevCollection.removeItem(itemId));
  };

  return { collection, setCollection, addItem, updateItem, removeItem };
};

export default useCollectionState;
