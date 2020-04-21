/**
 * Class representing a collection of models
 */
class Collection {
  /**
   * Create a new collection
   * @param {string} idProperty The name of the property containing the id for the model.
   */
  constructor({ idProperty }) {
    this.idProperty = idProperty;
    this.byId = {};
    this.ids = [];
  }

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
}

export default Collection;
