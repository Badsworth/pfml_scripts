import { isEqual, merge } from "lodash";

/**
 * Class representing the base class for the application's models
 */
abstract class BaseModel<T> {
  abstract defaults(): T;
  [key:string]:any
  /**
   * Create an object from a dictionary of attributes and initializes the object with it,
   * only setting attributes that the model class has.
   * @param {object.<string, *>} attrs Object of attributes, where keys are the attribute names and the values are the attribute values
   */
  constructor(attrs?: T) {


    for (const [property, defaultValue] of Object.entries(this.defaults())) {
        this[property] = defaultValue;
    }

      if (attrs) {
          for (const [property, value] of Object.entries(attrs)) {
            merge(this, { [property]: value });
          }
      }
  }

  /**
   * Check to see if this object is set to the default values
   * @returns {boolean} true if this object has default values and false otherwise
   */
  isDefault() {
      return isEqual(this, this.constructor());
  }
}

export default BaseModel