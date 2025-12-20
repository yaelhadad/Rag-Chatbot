import { useState } from 'react'
import MessageList from './MessageList'
import MethodSelector from './MethodSelector'
import InputArea from './InputArea'

function ChatInterface() {
  const [messages, setMessages] = useState([])
  const [selectedMethod, setSelectedMethod] = useState(1)
  const [isLoading, setIsLoading] = useState(false)

  const handleSendMessage = async (question) => {
    if (!question.trim() || isLoading) return

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: question,
      method_id: selectedMethod,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setIsLoading(true)

    try {
      const response = await fetch('/api/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          method_id: selectedMethod,
          question: question
        })
      })

      // Check if response is OK and has content
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      // Check if response has content before parsing
      const text = await response.text()
      if (!text) {
        throw new Error('Empty response from server')
      }

      const data = JSON.parse(text)

      if (data.success) {
        const assistantMessage = {
          id: Date.now() + 1,
          role: 'assistant',
          content: data.answer,
          sources: data.sources,
          metadata: data.metadata,
          method_name: data.method_name,
          execution_time: data.execution_time_ms,
          timestamp: new Date()
        }
        setMessages(prev => [...prev, assistantMessage])
      } else {
        const errorMessage = {
          id: Date.now() + 1,
          role: 'assistant',
          content: `Error: ${data.error?.message || 'Unknown error'}`,
          isError: true,
          timestamp: new Date()
        }
        setMessages(prev => [...prev, errorMessage])
      }
    } catch (error) {
      const errorMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: `Error: ${error.message}`,
        isError: true,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto">
      <MethodSelector
        selectedMethod={selectedMethod}
        onMethodChange={setSelectedMethod}
      />
      <div className="bg-white rounded-lg shadow-lg mt-4">
        <MessageList messages={messages} />
        <InputArea
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
        />
      </div>
    </div>
  )
}

export default ChatInterface

