import BaseCollection from "../models/BaseCollection";
import { useState } from "react";

/**
 * React hook for creating a state for a Collection of objects
 */
const useCollectionState = <TCollectionItem>(
  initialCollection?: BaseCollection<TCollectionItem>
) => {
  const [collection, setCollection] = useState(initialCollection);

  const addItem = (item: TCollectionItem) => {
    setCollection((prevCollection) => prevCollection.addItem(item));
  };

  const addItems = (items: TCollectionItem[]) => {
    setCollection((prevCollection) => prevCollection.addItems(items));
  };

  const updateItem = (item: TCollectionItem) => {
    setCollection((prevCollection) => prevCollection.updateItem(item));
  };

  const removeItem = (itemId: string) => {
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
