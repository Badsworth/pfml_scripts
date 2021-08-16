import { findIndex, keyBy } from "lodash";

/**
 * Read only abstract class representing a collection of models. Subclass this class
 * to create a specific collection class. Methods of BaseCollection returns new
 * instances of the collection rather than modifying the original collection.
 */
class BaseCollection {
  /**
   * Create a new collection from an array of items
   * @param {BaseModel[]} [items] Optional list of items. If no list is provided an empty collection will be created.
   */
  constructor(items) {
    /**
     * Array of the items in the collection
     * @type {BaseModel[]}
     */
    // @ts-expect-error ts-migrate(2339) FIXME: Property 'items' does not exist on type 'BaseColle... Remove this comment to see the full error message
    this.items = items || [];

    /**
     * Object mapping item ids to items in the collection
     * @type {object.<string, *>}
     */
    // @ts-expect-error ts-migrate(2339) FIXME: Property 'itemsById' does not exist on type 'BaseC... Remove this comment to see the full error message
    this.itemsById = keyBy(this.items, this.idProperty);
  }

  /**
   * The name of the id property for the items in the collection.
   * This is an abstract method that must be implemented by subclasses of BaseCollection.
   * @type {string}
   * @readonly
   * @abstract
   */
  get idProperty() {
    throw new Error("Not implemented");
  }

  get isEmpty() {
    // @ts-expect-error ts-migrate(2339) FIXME: Property 'items' does not exist on type 'BaseColle... Remove this comment to see the full error message
    return this.items.length === 0;
  }

  /**
   * Return a single item from the id of the item or
   * undefined if the item is not in the collection
   * @param {string} itemId - item id
   * @returns {BaseModel|undefined} item - instance of item
   */
  getItem(itemId) {
    // @ts-expect-error ts-migrate(2339) FIXME: Property 'itemsById' does not exist on type 'BaseC... Remove this comment to see the full error message
    return this.itemsById[itemId];
  }

  /**
   * Adds an item to the collection. Returns a new collection with the item added.
   * Does not modify the original collection.
   * @param {BaseModel} item The item to add to the collection
   * @returns {BaseCollection}
   */
  addItem(item) {
    // @ts-expect-error ts-migrate(2538) FIXME: Type 'void' cannot be used as an index type.
    const itemId = item[this.idProperty];
    if (!itemId) {
      throw new Error(`Item ${this.idProperty} is null or undefined`);
    }
    if (this.getItem(itemId)) {
      throw new Error(
        `Item with ${this.idProperty} ${itemId} already exists in collection`
      );
    }
    // @ts-expect-error ts-migrate(2339) FIXME: Property 'items' does not exist on type 'BaseColle... Remove this comment to see the full error message
    const newItems = this.items.concat(item);
    // @ts-expect-error ts-migrate(2351) FIXME: This expression is not constructable.
    return new this.constructor(newItems);
  }

  /**
   * Adds items to the collection. Returns a new collection with the items added.
   * Does not modify the original collection.
   * @param {BaseModel[]} items The items to add to the collection
   * @returns {BaseCollection}
   */
  addItems(items) {
    if (!Array.isArray(items)) {
      throw new Error(`Items must be an array`);
    }
    return items.reduce((collection, item) => {
      return collection.addItem(item);
    }, this);
  }

  /**
   * Updates an item in a collection. Returns a new collection with the item updated.
   * Does not modify the original collection.
   * @param {BaseModel} item - the item to update in the collection
   * @returns {BaseCollection} - new instance of a collection with updated item
   */
  updateItem(item) {
    // @ts-expect-error ts-migrate(2339) FIXME: Property 'items' does not exist on type 'BaseColle... Remove this comment to see the full error message
    const items = this.items;
    // @ts-expect-error ts-migrate(2538) FIXME: Type 'void' cannot be used as an index type.
    const itemId = item[this.idProperty];
    if (!itemId) {
      throw new Error(`Item ${this.idProperty} is null or undefined`);
    }
    // @ts-expect-error ts-migrate(2464) FIXME: A computed property name must be of type 'string',... Remove this comment to see the full error message
    const itemIndex = findIndex(items, { [this.idProperty]: itemId });
    if (itemIndex === -1) {
      throw new Error(
        `Cannot find item with ${this.idProperty} ${itemId} in collection`
      );
    }
    const newItems = items
      .slice(0, itemIndex)
      .concat([item])
      .concat(items.slice(itemIndex + 1));
    // @ts-expect-error ts-migrate(2351) FIXME: This expression is not constructable.
    return new this.constructor(newItems);
  }

  /**
   * Removes an item from the collection. Returns a new collection with the item removed.
   * Does not modify the original collection.
   * @param {string} itemId - the item to remove from the collection
   * @returns {BaseCollection} - new instance of a collection with item removed
   */
  removeItem(itemId) {
    // @ts-expect-error ts-migrate(2339) FIXME: Property 'items' does not exist on type 'BaseColle... Remove this comment to see the full error message
    const items = this.items;
    // @ts-expect-error ts-migrate(2464) FIXME: A computed property name must be of type 'string',... Remove this comment to see the full error message
    const itemIndex = findIndex(items, { [this.idProperty]: itemId });
    if (itemIndex === -1) {
      throw new Error(
        `Cannot find item with ${this.idProperty} ${itemId} in collection`
      );
    }
    const newItems = items
      .slice(0, itemIndex)
      .concat(items.slice(itemIndex + 1));
    // @ts-expect-error ts-migrate(2351) FIXME: This expression is not constructable.
    return new this.constructor(newItems);
  }
}

export default BaseCollection;
