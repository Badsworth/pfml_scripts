/**
 * Read only Class representing a collection of models
 */
class Collection {
  /**
   * Create a new collection
   * @param {object} properties
   * @param {string} properties.idProperty - The name of the property containing the id for the model.
   * @param {object} properties.itemsById - intitial map of items keyed by their id
   */
  constructor({ idProperty, itemsById = {} }) {
    // TODO enforce properties as readonly after _app.js is refactored to use static methods
    this.idProperty = idProperty;
    this.byId = { ...itemsById };
    this.ids = Object.keys(itemsById);
  }

  /**
   * Return a single item
   * @param {string} itemId - item id
   * @returns {BaseModel} item - instance of item
   */
  get(itemId) {
    return this.byId[itemId];
  }

  // TODO: remove class methods when _app.js is refactored to use static methods
  /**
   * Adds an item to the collection.
   * @param {BaseModel} item The item to add to the collection
   */
  add(item) {
    const idProperty = this.idProperty;
    const id = item[idProperty];
    this.byId[id] = item;
    this.ids.push(id);
  }

  /**
   * Adds an item to the collection
   * @param {Collection} collection - the collection to be modified
   * @param {BaseModel} item - the item to add to the collection
   * @returns {Collection} - new instance of a collection with additional item
   */
  static addItem(collection, item) {
    const { idProperty, byId: allItems } = collection;
    const itemId = item[idProperty];

    const itemsById = {
      ...allItems,
      [itemId]: item,
    };

    return new Collection({ idProperty, itemsById });
  }

  /**
   * Updates an item in a collection
   * @param {Collection} collection - the collection to be modified
   * @param {BaseModel} item - the item to update in the collection
   * @returns {Collection} - new instance of a collection with updated item
   */
  static updateItem(collection, item) {
    return Collection.addItem(collection, item);
  }

  /**
   * Removes an item to the collection
   * @param {Collection} collection - the collection to be modified
   * @param {string} itemId - the item to remove from the collection
   * @returns {Collection} - new instance of a collection with item removed
   */
  static removeItem(collection, itemId) {
    const { idProperty, byId } = collection;
    const { [itemId]: removedItem, ...itemsById } = byId;

    return new Collection({ idProperty, itemsById });
  }
}

export default Collection;
