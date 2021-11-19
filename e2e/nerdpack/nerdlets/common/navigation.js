import React from "react";
import { Link, navigation } from "nr1";

export default class Navigation extends React.PureComponent {
  render() {
    return (
      <nav className={"nav"}>
        <Link
          to={navigation.getOpenNerdletLocation({
            id: "environments",
          })}
        >
          Environments
        </Link>
        <Link
          to={navigation.getOpenNerdletLocation({
            id: "errorlist",
          })}
        >
          Error List
        </Link>
      </nav>
    );
  }
}
