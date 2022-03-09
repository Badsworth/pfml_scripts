import { Helmet } from "react-helmet-async";
import { StaticPropsPermissions } from "../menus";

export default function Help() {
  return (
    <>
      <Helmet>
        <title>Help</title>
      </Helmet>
      <h1> This is the help page</h1>
    </>
  );
}

export async function getStaticProps(): Promise<StaticPropsPermissions> {
  return {
    props: {
      permissions: [],
    },
  };
}
