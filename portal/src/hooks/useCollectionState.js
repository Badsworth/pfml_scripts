import { useState } from "react";

/** @typedef {import('../models/BaseCollection')} BaseCollection */

/**
 * React hook for creating a state for a Collection of objects
 * @param {BaseCollection} [initialCollection] - initial collection state
 * @returns {Array} - [collection, setCollection, addItem, updateItem, removeItem];
 */
const useCollectionState = (initialCollection) => {
  const [collection, setCollection] = useState(initialCollection);

  const addItem = (item) => {
    setCollection((prevCollection) => prevCollection.addItem(item));
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
