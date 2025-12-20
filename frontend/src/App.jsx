import { useState } from 'react'
import ChatInterface from './components/ChatInterface'

function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <header className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            RAG Chatbot
          </h1>
          <p className="text-gray-600">
            Ask questions using different RAG methods
          </p>
        </header>
        <ChatInterface />
      </div>
    </div>
  )
}

export default App

