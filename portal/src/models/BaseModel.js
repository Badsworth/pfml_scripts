/**
 * Class representing the base class for the application's models
 */
export default class BaseModel {
  /**
   * Create an object from a dictionary of attributes and initializes the object with it,
   * only setting attributes that the model class has.
   * @param {object.<string, *>} attrs Object of attributes, where keys are the attribute names and the values are the attribute values
   */
  constructor(attrs) {
    attrs = attrs || {};

    for (const [property, defaultValue] of Object.entries(this.defaults)) {
      this[property] = defaultValue;
    }

    for (const [property, value] of Object.entries(attrs)) {
      // Ignore attributes that aren't part of the model class's defaults array
      if (!this.defaults.hasOwnProperty(property)) {
        if (process.env.NODE_ENV === "development") {
          // During development, log a warning since it might indicate a missing attribute in the model class
          // eslint-disable-next-line no-console
          console.warn(
            `Received unexpected attributes. You may need to update your model to include a new field. Received: ${Object.keys(
              attrs
            )} but only expected: ${Object.keys(this.defaults)}`
          );
        }
        continue;
      }

      this[property] = value;
    }
  }

  /**
   * Dictionary mapping properties to default values for those properties.
   * If a property has no default, use null as its default.
   * This is an abstract method that must be implemented by all subclasses of BaseModel.
   * @type {object.<string, *>}
   * @readonly
   * @abstract
   */
  get defaults() {
    throw new Error("Not implemented");
  }
}
