import { createContext, useContext, useReducer, useEffect } from 'react'
import toast from 'react-hot-toast'

const AuthContext = createContext()

const initialState = {
  user: null,
  token: null,
  isAuthenticated: false,
  isLoading: true,
}

const authReducer = (state, action) => {
  switch (action.type) {
    case 'LOGIN_START':
      return { ...state, isLoading: true }
    case 'LOGIN_SUCCESS':
      return {
        ...state,
        user: action.payload.user,
        token: action.payload.token,
        isAuthenticated: true,
        isLoading: false,
      }
    case 'LOGIN_FAILURE':
      return {
        ...state,
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false,
      }
    case 'LOGOUT':
      return {
        ...state,
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false,
      }
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload }
    default:
      return state
  }
}

export const AuthProvider = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, initialState)

  // Check for existing token on app load
  useEffect(() => {
    const loadAuthFromStorage = () => {
      const token = localStorage.getItem('auth_token')
      const user = localStorage.getItem('user')
      
      console.log('Loading from localStorage:', { token: !!token, user: !!user })
      
      if (token && user) {
        try {
          const userData = JSON.parse(user)
          console.log('Setting token from localStorage:', token.substring(0, 20) + '...')
          dispatch({
            type: 'LOGIN_SUCCESS',
            payload: { token, user: userData }
          })
          return true
        } catch (error) {
          console.error('Error parsing user data:', error)
          localStorage.removeItem('auth_token')
          localStorage.removeItem('user')
        }
      }
      dispatch({ type: 'SET_LOADING', payload: false })
      return false
    }
    
    // Try to load auth immediately
    loadAuthFromStorage()
    
    // Also listen for storage changes (in case of multiple tabs)
    const handleStorageChange = (e) => {
      if (e.key === 'auth_token' || e.key === 'user') {
        loadAuthFromStorage()
      }
    }
    
    window.addEventListener('storage', handleStorageChange)
    return () => window.removeEventListener('storage', handleStorageChange)
  }, [])

  // Debug logging
  useEffect(() => {
    console.log('Auth state changed:', { 
      isAuthenticated: state.isAuthenticated, 
      hasToken: !!state.token,
      user: state.user 
    })
  }, [state])

  const login = async (email, password) => {
    dispatch({ type: 'LOGIN_START' })
    
    try {
      const formData = new FormData()
      formData.append('email', email)
      formData.append('password', password)

      const response = await fetch('/api/auth/login', {
        method: 'POST',
        body: formData,
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Login failed')
      }

      // Store token and user data
      localStorage.setItem('auth_token', data.access_token)
      localStorage.setItem('user', JSON.stringify(data.user))

      dispatch({
        type: 'LOGIN_SUCCESS',
        payload: { token: data.access_token, user: data.user }
      })

      toast.success('Login successful!')
      return { success: true }
    } catch (error) {
      dispatch({ type: 'LOGIN_FAILURE' })
      toast.error(error.message || 'Login failed')
      return { success: false, error: error.message }
    }
  }

  const register = async (username, email, password) => {
    dispatch({ type: 'LOGIN_START' })
    
    try {
      const formData = new FormData()
      formData.append('username', username)
      formData.append('email', email)
      formData.append('password', password)

      const response = await fetch('/api/auth/register', {
        method: 'POST',
        body: formData,
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Registration failed')
      }

      // Auto-login after registration
      return await login(email, password)
    } catch (error) {
      dispatch({ type: 'LOGIN_FAILURE' })
      toast.error(error.message || 'Registration failed')
      return { success: false, error: error.message }
    }
  }

  const logout = () => {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user')
    dispatch({ type: 'LOGOUT' })
    toast.success('Logged out successfully')
  }

  const refreshToken = async () => {
    try {
      const currentToken = state.token || localStorage.getItem('auth_token')
      if (!currentToken) return null
      
      const response = await fetch('/api/auth/refresh', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${currentToken}`
        }
      })
      
      if (response.ok) {
        const data = await response.json()
        const newToken = data.access_token
        
        // Update token in state and localStorage
        dispatch({
          type: 'LOGIN_SUCCESS',
          payload: { token: newToken, user: state.user }
        })
        localStorage.setItem('auth_token', newToken)
        
        console.log('Token refreshed successfully')
        return newToken
      }
    } catch (error) {
      console.error('Token refresh failed:', error)
    }
    return null
  }

  const getAuthHeaders = async () => {
    // First check state token
    let token = state.token
    
    // If no token in state, try to get from localStorage
    if (!token) {
      token = localStorage.getItem('auth_token')
      console.log('No token in state, checking localStorage:', !!token)
    }
    
    console.log('getAuthHeaders called, token exists:', !!token)
    console.log('Current state:', { isAuthenticated: state.isAuthenticated, hasUser: !!state.user, hasToken: !!state.token })
    
    if (!token) {
      console.log('No token available, returning empty headers')
      return {}
    }
    
    const headers = {
      'Authorization': `Bearer ${token}`
    }
    console.log('Returning auth headers:', { Authorization: `Bearer ${token.substring(0, 20)}...` })
    return headers
  }

  const value = {
    ...state,
    login,
    register,
    logout,
    getAuthHeaders,
    refreshToken
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
