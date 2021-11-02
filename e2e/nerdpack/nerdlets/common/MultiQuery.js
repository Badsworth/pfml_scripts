import { NrqlQuery } from "nr1";
import React from "react";

class MutiQuery extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      queryPromises: this.props.nrqlQueries.map(() => ({
        loading: true,
      })),
    };
    this.queries = [];
    this.shouldFetch = true;
  }

  componentDidUpdate() {
    if (this.shouldFetch) {
      this.fetchLatestDataByQuery();
      this.shouldFetch = false;
      this.queries = this.props.nrqlQueries;
    }
  }

  shouldComponentUpdate(nextProps, nextState) {
    if (this.queries.length !== nextProps.nrqlQueries.length) {
      this.shouldFetch = true;
      return true;
    }
    for (let i = 0; i < nextProps.nrqlQueries.length; i++) {
      if (nextProps.nrqlQueries[i].query !== this.queries[i].query) {
        this.shouldFetch = true;
        return true;
      }
    }
    return nextState.queryPromises !== this.state.queryPromises;
  }

  fetchLatestDataByQuery = () => {
    const queryPromises = this.props.nrqlQueries.map((nrqlQuery) =>
      NrqlQuery.query(nrqlQuery).then((res) => {
        let data;
        if (nrqlQuery.formatType === NrqlQuery.FORMAT_TYPE.RAW) {
          data = res.data;
        } else {
          data = res.data[0];
        }
        if (typeof nrqlQuery?.rowProcessor == "function") {
          if (data?.facets) {
            data.data = data.facets.map(nrqlQuery.rowProcessor);
          } else {
            data.data = data.data.map(nrqlQuery.rowProcessor);
          }
        }

        return data;
      })
    );

    Promise.all(queryPromises).then((data) => {
      this.setState({
        queryPromises: data,
      });
    });
  };

  render() {
    // if (this.state.queryPromises.length === 0) return null;
    return this.props.children(this.state.queryPromises);
  }
}

export { MutiQuery };
