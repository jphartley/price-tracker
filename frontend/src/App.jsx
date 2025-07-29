import { useState, useEffect } from 'react'

function App() {
  // Helper function to get currency symbol
  const getCurrencySymbol = (currency) => {
    const symbols = {
      'USD': '$',
      'GBP': '£',
      'EUR': '€'
    }
    return symbols[currency] || currency
  }
  const [products, setProducts] = useState([])
  const [newUrl, setNewUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')

  const API_BASE = 'http://localhost:8000'

  useEffect(() => {
    fetchProducts()
  }, [])

  const fetchProducts = async () => {
    try {
      const response = await fetch(`${API_BASE}/products`)
      if (response.ok) {
        const data = await response.json()
        setProducts(data)
      }
    } catch (error) {
      console.error('Error fetching products:', error)
    }
  }

  const addProduct = async (e) => {
    e.preventDefault()
    if (!newUrl.trim()) return

    setLoading(true)
    setMessage('')

    try {
      const response = await fetch(`${API_BASE}/products`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url: newUrl }),
      })

      if (response.ok) {
        setMessage('Product added successfully!')
        setNewUrl('')
        fetchProducts()
      } else {
        const error = await response.json()
        setMessage(`Error: ${error.detail}`)
      }
    } catch (error) {
      setMessage('Error adding product')
      console.error('Error:', error)
    }

    setLoading(false)
  }

  const checkPrice = async (productId) => {
    setLoading(true)
    setMessage('')

    try {
      const response = await fetch(`${API_BASE}/products/${productId}/check-price`, {
        method: 'POST',
      })

      if (response.ok) {
        const data = await response.json()
        const currencySymbol = getCurrencySymbol(data.currency || 'GBP')
        setMessage(`Price updated: ${currencySymbol}${data.new_price} for ${data.name}`)
        fetchProducts()
      } else {
        const error = await response.json()
        setMessage(`Error: ${error.detail}`)
      }
    } catch (error) {
      setMessage('Error checking price')
      console.error('Error:', error)
    }

    setLoading(false)
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Price Tracker</h1>
          <p className="text-gray-600 mb-6">Track Paul Smith product prices and get notified of drops</p>

          <form onSubmit={addProduct} className="mb-6">
            <div className="flex gap-3">
              <input
                type="url"
                value={newUrl}
                onChange={(e) => setNewUrl(e.target.value)}
                placeholder="Paste Paul Smith product URL here..."
                className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={loading}
              />
              <button
                type="submit"
                disabled={loading || !newUrl.trim()}
                className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Adding...' : 'Add Product'}
              </button>
            </div>
          </form>

          {message && (
            <div className={`p-3 rounded-md mb-4 ${message.startsWith('Error') ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>
              {message}
            </div>
          )}
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Tracked Products</h2>

          {products.length === 0 ? (
            <p className="text-gray-500 text-center py-8">No products being tracked yet. Add a Paul Smith product URL above to get started!</p>
          ) : (
            <div className="space-y-4">
              {products.map((product) => (
                <div key={product.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <h3 className="font-medium text-gray-900 mb-2">{product.name}</h3>
                      <p className="text-sm text-gray-500 mb-2 truncate">
                        <a href={product.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                          {product.url}
                        </a>
                      </p>
                      <div className="flex items-center gap-4">
                        <span className="text-lg font-semibold text-green-600">
                          {product.current_price !== null && product.current_price !== undefined 
                            ? `${getCurrencySymbol(product.currency)}${product.current_price.toFixed(2)}`
                            : 'N/A'}
                        </span>
                        <span className="text-sm text-gray-500">
                          Added {new Date(product.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                    <button
                      onClick={() => checkPrice(product.id)}
                      disabled={loading}
                      className="ml-4 px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 disabled:opacity-50"
                    >
                      Check Price
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default App
