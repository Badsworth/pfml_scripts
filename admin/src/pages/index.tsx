import Modal from "../components/Modal";
import { Helmet } from "react-helmet";
import { useState } from "react";

export default function Home() {
  const [showModal, setShowModal] = useState(false);

  const modalCancelCallback = () => {
    setShowModal(false);
  };

  const modalContinueCallback = () => {
    setShowModal(false);
  };

  return (
    <>
      <Helmet>
        <title>Dashboard</title>
      </Helmet>
      <h1>h1 HTML5 Kitchen Sink</h1>
      <button onClick={() => setShowModal(true)}>
        <span>Click to open</span>
      </button>
      {showModal && (
        <Modal
          title="Enable Caring Leave Type"
          body="Lorum ipsum"
          handleCancelCallback={modalCancelCallback}
          handleContinueCallback={modalContinueCallback}
        />
      )}
    </>
  );
}
