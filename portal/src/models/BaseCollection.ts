import { findIndex, keyBy } from "lodash";

/**
 * Read only abstract class representing a collection of models. Subclass this class
 * to create a specific collection class. Methods of BaseCollection returns new
 * instances of the collection rather than modifying the original collection.
 */
abstract class BaseCollection<T> {
  items: T[];
  /**
   * The name of the id property for the items in the collection.
   */
  abstract get idProperty(): string;

  constructor(items?: T[]) {
    this.items = items || [];
  }

  get itemsById(): { [key: string]: T } {
    return keyBy(this.items, this.idProperty);
  }

  get isEmpty() {
    return this.items.length === 0;
  }

  /**
   * Return a single item from the id of the item or
   * undefined if the item is not in the collection
   */
  getItem(itemId: string): T | undefined {
    return this.itemsById[itemId];
  }

  /**
   * Adds an item to the collection. Returns a new collection with the item added.
   * Does not modify the original collection.
   */
  addItem(item: T) {
    // @ts-expect-error TODO (PORTAL-265) Redesign BaseCollection
    const itemId = item[this.idProperty];
    if (!itemId) {
      throw new Error(`Item ${this.idProperty} is null or undefined`);
    }
    if (this.getItem(itemId)) {
      throw new Error(
        `Item with ${this.idProperty} ${itemId} already exists in collection`
      );
    }
    const newItems = this.items.concat(item);
    return new (<new (args: T[]) => BaseCollection<T>>this.constructor)(
      newItems
    );
  }

  /**
   * Adds items to the collection. Returns a new collection with the items added.
   * Does not modify the original collection.
   */
  addItems(items: T[]) {
    if (!Array.isArray(items)) {
      throw new Error(`Items must be an array`);
    }
    return items.reduce((collection, item) => {
      return collection.addItem(item);
    }, this as BaseCollection<T>);
  }

  /**
   * Updates an item in a collection. Returns a new collection with the item updated.
   * Does not modify the original collection.
   */
  updateItem(item: T) {
    const items = this.items;
    // @ts-expect-error TODO (PORTAL-265) Redesign BaseCollection
    const itemId = item[this.idProperty];
    if (!itemId) {
      throw new Error(`Item ${this.idProperty} is null or undefined`);
    }
    const itemIndex = findIndex(items, [this.idProperty, itemId]);
    if (itemIndex === -1) {
      throw new Error(
        `Cannot find item with ${this.idProperty} ${itemId} in collection`
      );
    }
    const newItems = items
      .slice(0, itemIndex)
      .concat([item])
      .concat(items.slice(itemIndex + 1));
    return new (<new (args: T[]) => BaseCollection<T>>this.constructor)(
      newItems
    );
  }

  /**
   * Removes an item from the collection. Returns a new collection with the item removed.
   * Does not modify the original collection.
   */
  removeItem(itemId: string) {
    const items = this.items;
    const itemIndex = findIndex(items, [this.idProperty, itemId]);
    if (itemIndex === -1) {
      throw new Error(
        `Cannot find item with ${this.idProperty} ${itemId} in collection`
      );
    }
    const newItems = items
      .slice(0, itemIndex)
      .concat(items.slice(itemIndex + 1));
    return new (<new (args: T[]) => BaseCollection<T>>this.constructor)(
      newItems
    );
  }
}

export default BaseCollection;
