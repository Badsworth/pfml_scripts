import '../styles/globals.css'
import Head from 'next/head'
import type { AppProps } from 'next/app'

function MyApp({ Component, pageProps }: AppProps) {
  return (
    <div className="page">
      <Head>
        <title>Admin Portal</title>
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <header class="page__header">
          LOGO HERE        
      </header>
      <aside class="page__sidebar">
        <nav>
          <ul>
            <li>Hey there!</li>
          </ul>
        </nav>
      </aside>
      <main class="page__main">
        <Component {...pageProps} />
      </main>
    </div>
  )
}
export default MyApp
