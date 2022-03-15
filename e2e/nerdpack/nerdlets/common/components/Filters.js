import React from "react";
import { labelEnv, setDefault } from "../index";

export class BaseFilter extends React.Component {
  static RETURN_TYPES = {
    NRQL: "nrql",
    OBJECT: "object",
    ARRAY: "array",
    ALL: "all",
  };

  constructor(props) {
    super(props);
    this.handleUpdate = props.handleUpdate;
    this.returnType = setDefault(props.returnType, "nrql");
    this.RETURN_TYPES = FilterByEnv.RETURN_TYPES;
  }

  clearAll = () => {
    const state = { ...this.state };
    Object.keys(state).map((key) => {
      state[key] = false;
    });
    this.setState(state, this.sendUpdateEvent);
  };

  checkAll = () => {
    const state = { ...this.state };
    Object.keys(state).map((key) => {
      state[key] = true;
    });
    this.setState(state, this.sendUpdateEvent);
  };

  handleInputChange = (event) => {
    const target = event.target;
    const value = target.type === "checkbox" ? target.checked : target.value;
    const name = target.name;

    const state = { ...this.state, [name]: value };
    this.setState(state, this.sendUpdateEvent);
  };

  sendUpdateEvent = () => {
    if (typeof this.handleUpdate === "function") {
      if (this.returnType === this.RETURN_TYPES.OBJECT) {
        this.handleUpdate(this.state);
      } else if (this.returnType === this.RETURN_TYPES.ARRAY) {
        this.handleUpdate(this.getStateArray());
      } else if (this.returnType === this.RETURN_TYPES.NRQL) {
        this.handleUpdate(this.getStateNRQL());
      } else if (this.returnType === this.RETURN_TYPES.ALL) {
        this.handleUpdate(
          this.getStateNRQL(),
          this.state,
          this.getStateArray()
        );
      }
    }
  };

  getStateNRQL = () => {
    return "";
  };

  getStateArray = () => {
    return Object.keys(this.state).reduce((collection, key) => {
      if (this.state[key]) {
        collection.push(key);
      }
      return collection;
    }, []);
  };
}

export class FilterByEnv extends BaseFilter {
  state = {
    breakfix: true,
    training: true,
    trn2: true,
    uat: true,
    performance: true,
    stage: true,
    long: true,
    "cps-preview": true,
    test: true,
  };

  constructor(props) {
    super(props);
    this.sendUpdateEvent();
  }

  getStateNRQL = () => {
    let WHERE = [];
    Object.keys(this.state).map((env) => {
      if (this.state[env]) {
        WHERE.push(`environment = '${env}'`);
      }
    });
    if (WHERE.length) {
      return `( ${WHERE.join(" OR ")} )`;
    }
    return "";
  };

  render() {
    return (
      <div className={"filters"}>
        FILTERS:
        <button
          onClick={() => {
            this.clearAll("env");
          }}
        >
          Clear All
        </button>
        <button
          onClick={() => {
            this.checkAll("env");
          }}
        >
          Check All
        </button>
        {Object.keys(this.state).map((status) => {
          return (
            <label>
              <input
                name={status}
                type={"checkbox"}
                checked={this.state[status]}
                onChange={this.handleInputChange}
              />
              {labelEnv(status)}
            </label>
          );
        })}
      </div>
    );
  }
}

export class FilterByTag extends BaseFilter {
  state = {
    morning: true,
    manual: true,
    deploy: true,
    pr: true,
  };

  whereMatch = {
    morning: `(tag like '%Morning%' OR tag like '%Sanity Check%' OR tag like '%Post Morning Run Check%' )`,
    deploy: `tag like '%deploy%'`,
    pr: `(tag like 'PR,%' OR tag like '% - PR%')`,
    manual: `(tag LIKE 'Manual%')`,
  };

  constructor(props) {
    super(props);
    this.sendUpdateEvent();
  }

  getStateNRQL = () => {
    let WHERE = [];
    Object.keys(this.state).map((key) => {
      if (this.state[key]) {
        WHERE.push(this.whereMatch[key]);
      }
    });
    if (WHERE.length) {
      return `( ${WHERE.join(" OR ")} )`;
    }
    return "";
  };

  render() {
    return (
      <div className={"filters"}>
        TAGS:
        <button
          onClick={() => {
            this.clearAll("tags");
          }}
        >
          Clear All
        </button>
        <button
          onClick={() => {
            this.checkAll("tags");
          }}
        >
          Check All
        </button>
        {Object.keys(this.state).map((status) => {
          return (
            <label>
              <input
                name={status}
                type={"checkbox"}
                checked={this.state[status]}
                onChange={this.handleInputChange}
              />
              {status}
            </label>
          );
        })}
      </div>
    );
  }
}
