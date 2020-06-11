import { findIndex, keyBy } from "lodash";

/**
 * Read only Class representing a collection of models
 */
class BaseCollection {
  /**
   * Create a new collection
   * @param {BaseModel[]} [items] Optional list of items. If no list is provided an empty collection will be created.
   */
  constructor(items) {
    // TODO enforce properties as readonly after _app.js is refactored to use static methods
    this.items = items || [];
  }

  /**
   * @type {object.<string, *>}
   * @readonly
   */
  get itemsById() {
    return keyBy(this.items, this.idProperty);
  }

  /**
   * The name of the id property for the items in the collection
   * @type {string}
   * @readonly
   */
  get idProperty() {
    throw new Error("Not implemented");
  }

  /**
   * Return a single item
   * @param {string} itemId - item id
   * @returns {BaseModel} item - instance of item
   */
  get(itemId) {
    return this.itemsById[itemId];
  }

  /**
   * Adds an item to the collection. Returns a new collection with the item added.
   * Does not change the original collection.
   * @param {BaseModel} item The item to add to the collection
   * @returns {BaseCollection}
   */
  addItem(item) {
    const itemId = item[this.idProperty];
    if (this.get(itemId)) {
      throw new Error(`Item with id ${itemId} already exists in collection`);
    }
    const newItems = this.items.concat(item);
    return new this.constructor(newItems);
  }

  /**
   * Updates an item in a collection. Returns a new collection with the item updated.
   * Does not change the original collection.
   * @param {BaseModel} item - the item to update in the collection
   * @returns {BaseCollection} - new instance of a collection with updated item
   */
  updateItem(item) {
    const items = this.items;
    const itemId = item[this.idProperty];
    const itemIndex = findIndex(items, { [this.idProperty]: itemId });
    if (itemIndex === -1) {
      throw new Error(`Item with id ${itemId} does not exist in collection`);
    }
    const newItems = items
      .slice(0, itemIndex)
      .concat([item])
      .concat(items.slice(itemIndex + 1));
    return new this.constructor(newItems);
  }

  /**
   * Removes an item to the collection
   * @param {string} itemId - the item to remove from the collection
   * @returns {BaseCollection} - new instance of a collection with item removed
   */
  removeItem(itemId) {
    const items = this.items;
    const itemIndex = findIndex(items, { [this.idProperty]: itemId });
    if (itemIndex === -1) {
      throw new Error(`Item with id ${itemId} does not exist in collection`);
    }
    const newItems = items
      .slice(0, itemIndex)
      .concat(items.slice(itemIndex + 1));
    return new this.constructor(newItems);
  }
}

export default BaseCollection;
