import BaseModel from "./BaseModel";

class Flag extends BaseModel {
  get defaults() {
    return {
      enabled: false,
      name: null,
      options: {},
      start: null,
      end: null,
    };
  }
}

export default Flag;
