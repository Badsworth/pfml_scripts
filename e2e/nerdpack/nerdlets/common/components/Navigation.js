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
          className={
            this.active === "view-environment-overview" ? "active" : ""
          }
          to={navigation.getOpenNerdletLocation({
            id: "view-environment-overview",
          })}
        >
          Environment Overview
        </Link>
        <Link
          className={this.active === "view-daily-overview" ? "active" : ""}
          to={navigation.getOpenNerdletLocation({
            id: "view-daily-overview",
          })}
        >
          Daily Overview
        </Link>
      </nav>
    );
  }
}
