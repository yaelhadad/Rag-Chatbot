function MethodSelector({ selectedMethod, onMethodChange }) {
  const methods = [
    { id: 1, name: 'Simple Vector RAG', description: 'Fast FAISS vector search' },
    { id: 2, name: 'Parent-Child RAG', description: 'Precise chunks + complete context' },
    { id: 3, name: 'Agentic RAG', description: 'Multi-tool agent with graph search' }
  ]

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h2 className="text-lg font-semibold mb-3 text-gray-800">Select RAG Method</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {methods.map(method => (
          <button
            key={method.id}
            onClick={() => onMethodChange(method.id)}
            className={`p-4 rounded-lg border-2 transition-all ${
              selectedMethod === method.id
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <div className="font-semibold text-gray-900">{method.name}</div>
            <div className="text-sm text-gray-600 mt-1">{method.description}</div>
          </button>
        ))}
      </div>
    </div>
  )
}

export default MethodSelector

