"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Moon, Sun, BookOpen, Key, ArrowRight } from "lucide-react"
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { Switch } from "@/components/ui/switch"
import { useToast } from "@/hooks/use-toast"
import { useRouter } from "next/navigation"
import axios from "axios"
import Link from "next/link"

export default function CanvasSetup() {
  const [darkMode, setDarkMode] = useState(false)
  const [canvasToken, setCanvasToken] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isSuccess, setIsSuccess] = useState(false)
  const { toast } = useToast()
  const router = useRouter()

  const toggleDarkMode = () => setDarkMode(!darkMode)

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setCanvasToken(e.target.value)
  }

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (!canvasToken.trim()) {
      toast({
        title: "Error",
        description: "Please enter a valid Canvas token",
        variant: "destructive",
      })
      return
    }

    setIsSubmitting(true)

    try {
      // Replace with your actual backend endpoint
      const response = await axios.post("http://0.0.0.0:8081/canvas-token", {
        token: canvasToken,
      })

      console.log("Token submission response:", response)

      setIsSuccess(true)
      toast({
        title: "Success",
        description: "Canvas token has been saved successfully",
      })

      // Clear the input after successful submission
      setCanvasToken("")
      router.push("/dashboard")

    } catch (error) {
      console.error("Error submitting Canvas token:", error)
      toast({
        title: "Error",
        description: "Failed to save Canvas token. Please try again.",
        variant: "destructive",
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className={`min-h-screen flex flex-col ${darkMode ? "dark" : ""}`}>
      <div className="flex-1 flex flex-col bg-background dark:bg-slate-950 transition-colors duration-200">
        <header className="border-b dark:border-slate-800" role="banner">
          <div className="container mx-auto py-4 px-4 md:px-6 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <BookOpen className="h-6 w-6 text-primary" />
              <h1 className="text-xl font-bold text-foreground">Educational Assistant</h1>
            </div>
            <div className="flex items-center space-x-2">
              <Sun className="h-4 w-4 text-foreground" />
              <Switch checked={darkMode} onCheckedChange={toggleDarkMode} id="dark-mode" />
              <Moon className="h-4 w-4 text-foreground" />
            </div>
          </div>
        </header>

        <main className="flex-1 container mx-auto py-6 px-4 md:px-6">
          <Card className="w-full max-w-md mx-auto">
            <CardHeader className="bg-primary/5 dark:bg-primary/10">
              <CardTitle className="flex items-center space-x-2">
                <Key className="h-5 w-5" />
                <span>Canvas Integration Setup</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="space-y-4">
                <p className="text-muted-foreground">
                  Enter your Canvas API token to connect your Canvas account with the Educational Assistant.
                </p>

                {isSuccess && (
                  <div className="bg-green-100 dark:bg-green-900/20 text-green-800 dark:text-green-300 p-3 rounded-md">
                    Canvas token has been saved successfully. You can now use the Educational Assistant with Canvas
                    integration.
                  </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-4">
                  <div className="space-y-2">
                    <label htmlFor="canvas-token" className="text-sm font-medium">
                      Canvas API Token
                    </label>
                    <Input
                      id="canvas-token"
                      type="password"
                      value={canvasToken}
                      onChange={handleInputChange}
                      placeholder="Enter your Canvas API token"
                      className="w-full"
                    />
                    <p className="text-xs text-muted-foreground">
                      You can generate an API token in your Canvas account settings.
                    </p>
                  </div>

                  <Button type="submit" className="w-full" disabled={isSubmitting || !canvasToken.trim()}>
                    {isSubmitting ? (
                      <div className="h-5 w-5 animate-spin rounded-full border-2 border-primary-foreground border-t-transparent" />
                    ) : (
                      "Save Canvas Token"
                    )}
                  </Button>
                </form>
              </div>
            </CardContent>
            <Separator />
            <CardFooter className="flex justify-center p-4">
              <Link href="/" className="flex items-center text-primary hover:underline">
                <span>Return to Chat</span>
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </CardFooter>
          </Card>
        </main>

        <footer className="border-t dark:border-slate-800">
          <div className="container mx-auto py-4 px-4 md:px-6 text-center text-sm text-muted-foreground">
            Educational Assistant © {new Date().getFullYear()} - Powered by AI
          </div>
        </footer>
      </div>
    </div>
  )
}

