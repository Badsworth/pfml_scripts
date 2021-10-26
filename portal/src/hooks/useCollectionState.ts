import BaseCollection from "../models/BaseCollection";
import { useState } from "react";

// Gets the typeof for the class we're storing in the collection
type InferCollectionItem<TCollection> = TCollection extends BaseCollection<
  infer K
>
  ? K
  : unknown;

/**
 * React hook for creating a state for a Collection of objects
 */
const useCollectionState = <
  TCollection extends BaseCollection<TItem>,
  TItem = InferCollectionItem<TCollection>
>(
  initialCollection: TCollection
) => {
  const [collection, setCollection] = useState(initialCollection);

  const addItem = (item: TItem) => {
    setCollection(
      (prevCollection) => prevCollection.addItem(item) as TCollection
    );
  };

  const addItems = (items: TItem[]) => {
    setCollection(
      (prevCollection) => prevCollection.addItems(items) as TCollection
    );
  };

  const updateItem = (item: TItem) => {
    setCollection(
      (prevCollection) => prevCollection.updateItem(item) as TCollection
    );
  };

  const removeItem = (itemId: string) => {
    setCollection(
      (prevCollection) => prevCollection.removeItem(itemId) as TCollection
    );
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
