import Collection from "../models/Collection";
import { useState } from "react";

/**
 * React hook for creating a state for a Collection of objects
 * @param {Collection} initialCollection - initial collection state
 * @param {object} configs - if initializing collection state without a value, define Collection parameters
 * @param {string} configs.idProperty
 * @returns {Array} - [collection, setCollection, addItem, updateItem, removeItem];
 */
const useCollectionState = (initialCollection, configs) => {
  if (!(initialCollection instanceof Collection) && !configs) {
    throw new Error(
      "useCollectionState expected an instance of Collection or Collection configurations."
    );
  }

  const [collection, setCollection] = useState(initialCollection);

  // Support adding and updating items in a collection when initial collection
  // is not defined
  const getCollection = (prevCollection) =>
    prevCollection || new Collection(configs);

  const addItem = (item) => {
    setCollection((prevCollection) =>
      Collection.addItem(getCollection(prevCollection), item)
    );
  };

  const updateItem = (item) => {
    setCollection((prevCollection) =>
      Collection.updateItem(getCollection(prevCollection), item)
    );
  };

  const removeItem = (itemId) => {
    setCollection((prevCollection) =>
      Collection.removeItem(prevCollection, itemId)
    );
  };

  return { collection, setCollection, addItem, updateItem, removeItem };
};

export default useCollectionState;
