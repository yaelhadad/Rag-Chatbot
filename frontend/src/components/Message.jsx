import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import Sources from './Sources'

function Message({ message }) {
  const [showSources, setShowSources] = useState(false)

  return (
    <div className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-3xl rounded-lg p-4 ${
          message.role === 'user'
            ? 'bg-blue-500 text-white'
            : message.isError
            ? 'bg-red-50 text-red-800 border border-red-200'
            : 'bg-gray-100 text-gray-900'
        }`}
      >
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="font-semibold mb-1">
              {message.role === 'user' ? 'You' : message.method_name || 'Assistant'}
            </div>
            {message.role === 'user' ? (
              <div className="whitespace-pre-wrap break-words">{message.content}</div>
            ) : (
              <div className="prose prose-sm max-w-none break-words">
                <ReactMarkdown>{message.content || 'No answer provided'}</ReactMarkdown>
              </div>
            )}
          </div>
        </div>

        {message.metadata && (
          <div className="mt-2 text-xs opacity-75">
            Execution time: {(message.execution_time / 1000).toFixed(2)}s
          </div>
        )}

        {message.sources && message.sources.length > 0 && (
          <div className="mt-3">
            <button
              onClick={() => setShowSources(!showSources)}
              className="text-xs underline hover:no-underline"
            >
              {showSources ? 'Hide' : 'Show'} Sources ({message.sources.length})
            </button>
            {showSources && <Sources sources={message.sources} />}
          </div>
        )}
      </div>
    </div>
  )
}

export default Message

