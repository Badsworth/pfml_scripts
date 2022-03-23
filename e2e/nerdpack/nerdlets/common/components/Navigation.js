import React from "react";
import { Link, navigation } from "nr1";

export default class Navigation extends React.PureComponent {
  constructor(props) {
    super(props);
    this.active = props.active;
  }
  render() {
    return (
      <nav className={"nav"}>
        <Link
          className={this.active === "environment-v1" ? "active" : ""}
          to={navigation.getOpenNerdletLocation({
            id: "environments",
          })}
        >
          Environments
        </Link>
        <Link
          className={this.active === "error-v1" ? "active" : ""}
          to={navigation.getOpenNerdletLocation({
            id: "errorlist",
          })}
        >
          Error List
        </Link>
        <Link
          className={this.active === "morning-v1" ? "active" : ""}
          to={navigation.getOpenNerdletLocation({
            id: "morning",
          })}
        >
          Daily Overview
        </Link>
        <Link
          className={
            this.active === "view-environment-overview" ? "active" : ""
          }
          to={navigation.getOpenNerdletLocation({
            id: "view-environment-overview",
          })}
        >
          Beta - Environment Overview
        </Link>
        <Link
          className={this.active === "view-daily-overview" ? "active" : ""}
          to={navigation.getOpenNerdletLocation({
            id: "view-daily-overview",
          })}
        >
          Beta - Daily Overview
        </Link>
      </nav>
    );
  }
}
