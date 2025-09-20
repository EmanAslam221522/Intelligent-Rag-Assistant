import '../styles/globals.css'
import { Toaster } from 'react-hot-toast'
import { AuthProvider } from '../contexts/AuthContext'
import ErrorBoundary from '../components/ErrorBoundary'

export default function App({ Component, pageProps }) {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <Component {...pageProps} />
        <Toaster 
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#363636',
              color: '#fff',
            },
            success: {
              duration: 3000,
              iconTheme: {
                primary: '#4ade80',
                secondary: '#fff',
              },
            },
            error: {
              duration: 5000,
              iconTheme: {
                primary: '#ef4444',
                secondary: '#fff',
              },
            },
          }}
        />
      </AuthProvider>
    </ErrorBoundary>
  )
}
