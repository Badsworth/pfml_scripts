import ApiResourceCollection, {
  ApiResource,
} from "../models/ApiResourceCollection";
import { useState } from "react";

/**
 * React hook for creating a state for a Collection of objects
 */
const useCollectionState = <TApiResource extends ApiResource>(
  initialCollection: ApiResourceCollection<TApiResource>
) => {
  const [collection, setCollection] = useState(initialCollection);

  const addItem = (item: TApiResource) => {
    setCollection((prevCollection) => prevCollection.setItem(item));
  };

  const addItems = (items: TApiResource[]) => {
    setCollection((prevCollection) => prevCollection.setItems(items));
  };

  const updateItem = (item: TApiResource) => {
    setCollection((prevCollection) => prevCollection.setItem(item));
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
