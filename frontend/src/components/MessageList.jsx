import Message from './Message'

function MessageList({ messages }) {
  return (
    <div className="h-96 overflow-y-auto p-4 space-y-4">
      {messages.length === 0 ? (
        <div className="text-center text-gray-500 mt-20">
          <p>Start a conversation by asking a question</p>
        </div>
      ) : (
        messages.map(message => (
          <Message key={message.id} message={message} />
        ))
      )}
    </div>
  )
}

export default MessageList

