"use client"

import { useEffect, useState } from "react"

export function DeepSeekMessage() {
  const [message, setMessage] = useState("")

  useEffect(() => {
    const fetchMessage = async () => {
      try {
        // console.log("Fetching DeepSeek message..."); // Uncomment for debugging
        // const res = await fetch("/api/deepseek-message"); // If using a proxy via next.config.mjs
        const res = await fetch("http://localhost:8080/deepseek-message") // UPDATED PORT
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
