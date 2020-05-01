import Collection from "../models/Collection";
import { useState } from "react";

/**
 * React hook for creating a state for a Collection of objects
 * @param {Collection} initialCollection - initial collection state
 * @returns {Array} - [collection, setCollection, addItem, updateItem, removeItem];
 */
const useCollectionState = (initialCollection) => {
  if (!(initialCollection instanceof Collection)) {
    throw new Error("useCollectionState expected an instance of Collection.");
  }

  const [collection, setCollection] = useState(initialCollection);

  const addItem = (item) => {
    const nextCollection = Collection.addItem(collection, item);
    setCollection(nextCollection);
  };

  const updateItem = (item) => {
    const nextCollection = Collection.updateItem(collection, item);
    setCollection(nextCollection);
  };

  const removeItem = (itemId) => {
    const nextCollection = Collection.removeItem(collection, itemId);
    setCollection(nextCollection);
  };

  return { collection, setCollection, addItem, updateItem, removeItem };
};

export default useCollectionState;
