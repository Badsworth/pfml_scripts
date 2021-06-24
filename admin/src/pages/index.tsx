import Image from 'next/image'
import styles from '../../styles/Home.module.css'
import {Helmet} from "react-helmet";

export default function Home() {
  return (
    <>
      <Helmet>
        <title>Dashboard</title>
      </Helmet>
      <h1>h1 HTML5 Kitchen Sink</h1>
    </>
  )
}
