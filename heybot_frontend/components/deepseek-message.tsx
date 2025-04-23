"use client"

import { useEffect, useState } from "react"

export function DeepSeekMessage() {
  const [message, setMessage] = useState("")

  useEffect(() => {
    const fetchMessage = async () => {
      try {
        const res = await fetch("http://localhost:8000/deepseek-message")
        const data = await res.json()
        setMessage(data.message)
      } catch (error) {
        setMessage("Fehler beim Laden der DeepSeek-Nachricht.")
      }
    }

    fetchMessage()
  }, [])

  return (
    <div className="mt-8 p-4 bg-[#161b22] border border-[#30363d] rounded-md text-sm text-[#c9d1d9] whitespace-pre-wrap">
      <h2 className="text-[#58a6ff] font-semibold mb-2">DeepSeek Nachricht</h2>
      <p>{message}</p>
    </div>
  )
}
