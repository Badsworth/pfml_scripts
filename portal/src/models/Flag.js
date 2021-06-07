import BaseModel from "./BaseModel";

class Flag extends BaseModel {
  get defaults() {
    return {
      enabled: false,
      options: {},
      start: null,
      end: null,
    };
  }
}

export default Flag;
