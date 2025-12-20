function Sources({ sources }) {
  return (
    <div className="mt-2 space-y-2">
      {sources.map((source, index) => (
        <div
          key={index}
          className="bg-white border border-gray-200 rounded p-3 text-sm"
        >
          <div className="font-semibold text-gray-700 mb-1">
            {source.tool_name || source.type || `Source ${index + 1}`}
          </div>
          {source.content && (
            <div className="text-gray-600 text-xs whitespace-pre-wrap max-h-32 overflow-y-auto">
              {source.content}
            </div>
          )}
          {source.metadata && (
            <div className="mt-2 text-xs text-gray-500">
              {source.metadata.title && (
                <div>Document: {source.metadata.title}</div>
              )}
              {source.metadata.page && (
                <div>Page: {source.metadata.page}</div>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

export default Sources

