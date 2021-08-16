import { useState } from "react";

/** @typedef {import('../models/BaseCollection').default} BaseCollection */

/**
 * React hook for creating a state for a Collection of objects
 * @param {BaseCollection} [initialCollection] - initial collection state
 * @returns {{addItem: addItemFunction, collection: BaseCollection, removeItem: removeItemFunction, setCollection: Function, updateItem: updateItemFunction}}
 */
const useCollectionState = (initialCollection) => {
  /**
   * @type {[BaseCollection, Function]}
   */
  const [collection, setCollection] = useState(initialCollection);

  /**
   * Function that adds an item to the collection
   * @callback addItemFunction
   * @param {BaseModel} item The item to add to the collection
   */
  const addItem = (item) => {
    setCollection((prevCollection) => prevCollection.addItem(item));
  };

  /**
   * Function that adds an item to the collection
   * @callback addItemsFunction
   * @param {BaseModel} items The items to add to the collection
   */
  const addItems = (items) => {
    setCollection((prevCollection) => prevCollection.addItems(items));
  };

  /**
   * Function that updates an item within the collection
   * @callback updateItemFunction
   * @param {BaseModel} item The item to update
   */
  const updateItem = (item) => {
    setCollection((prevCollection) => prevCollection.updateItem(item));
  };

  /**
   * Function that removes an item within the collection
   * @callback removeItemFunction
   * @param {string} itemId The id of the item to remove
   */
  const removeItem = (itemId) => {
    setCollection((prevCollection) => prevCollection.removeItem(itemId));
  };

  return {
    collection,
    setCollection,
    addItem,
    addItems,
    updateItem,
    removeItem,
  };
};

export default useCollectionState;
