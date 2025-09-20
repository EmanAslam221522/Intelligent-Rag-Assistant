export default function LoadingSpinner({ size = 'md', text = 'Loading...' }) {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12'
  }

  return (
    <div className="flex flex-col items-center justify-center p-4">
      <div className={`${sizeClasses[size]} border-4 border-blue-600 border-t-transparent rounded-full animate-spin`}></div>
      {text && <p className="mt-2 text-slate-300 text-sm">{text}</p>}
    </div>
  )
}


