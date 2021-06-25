import Image from "next/image";
import Modal from "../components/Modal";

import { Helmet } from "react-helmet";

export default function Home() {
  return (
    <>
      <Helmet>
        <title>Dashboard</title>
      </Helmet>
      <h1>h1 HTML5 Kitchen Sink</h1>
      <Modal title="Enable Caring Leave Type" body="Lorum ipsum" />
    </>
  );
}
