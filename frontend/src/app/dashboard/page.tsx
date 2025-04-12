"use client";
import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Moon, Sun, Send, BookOpen, MessageSquare } from "lucide-react";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Switch } from "@/components/ui/switch";
import axios from "axios";

export default function EducationalChat() {
    const [darkMode, setDarkMode] = useState(false);
    interface Message {
        role: "user" | "assistant";
        content: string;
        image?: string;
    }

    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [status, setStatus] = useState("");
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const toggleDarkMode = () => setDarkMode(!darkMode);

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => setInput(e.target.value);

    const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        if (!input.trim()) return;

        const userMessage: Message = { role: "user", content: input };
        setMessages((prev) => [...prev, userMessage]);
        setStatus("submitted");

        try {
            const response = await axios.post("http://0.0.0.0:8080/query", {
                request: input,
                response: "",
            });

            console.log("got it from frontend", response);


            const { request, response: resContent } = response.data;
            console.log("big mac", request)

            // Check if the response is a base64 image by looking for base64 pattern
            const isBase64Image = resContent && /^([A-Za-z0-9+/]{4})*([A-Za-z0-9+/]{3}=|[A-Za-z0-9+/]{2}==)?$/.test(resContent);
            if (isBase64Image) {
                const assistantMessage: Message = {
                    role: "assistant",
                    content: "Here is the generated visualization:",
                    image: `data:image/png;base64,${resContent}`,
                };
                setMessages((prev) => [...prev, assistantMessage]);
            } else {
                const assistantMessage: Message = {
                    role: "assistant",
                    content: resContent || "No response received.",
                };
                setMessages((prev) => [...prev, assistantMessage]);
            }
        } catch (error) {
            console.error("Error sending message:", error);
            setMessages((prev) => [...prev, { role: "assistant", content: "Failed to get a response." }]);
        } finally {
            setStatus("");
            setInput("");
        }
    };


    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

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
                    <Card className="w-full h-[80vh] flex flex-col">
                        <CardHeader className="bg-primary/5 dark:bg-primary/10">
                            <CardTitle className="flex items-center space-x-2">
                                <MessageSquare className="h-5 w-5" />
                                <span>Chat with AI Assistant</span>
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
                            {messages.length === 0 ? (
                                <div className="h-full flex flex-col items-center justify-center text-center space-y-4 text-muted-foreground">
                                    <BookOpen className="h-12 w-12" />
                                    <div>
                                        <p className="text-lg font-medium">Welcome to the Educational Assistant!</p>
                                        <p>Ask me any question to get started.</p>
                                    </div>
                                </div>
                            ) : (
                                messages.map((message, index) => (
                                    <div key={index} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
                                        <div
                                            className={`max-w-[80%] rounded-lg px-4 py-2 ${message.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted text-foreground"
                                                }`}
                                        >
                                            <div className="whitespace-pre-wrap">
                                                {message.content}
                                                {message.image && (
                                                    <div className="mt-2">
                                                        <img src={message.image} alt="Generated visualization" className="max-w-full rounded-lg border" />
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                ))
                            )}
                            <div ref={messagesEndRef} />
                        </CardContent>
                        <Separator />
                        <CardFooter className="p-4">
                            <form onSubmit={handleSubmit} className="flex w-full space-x-2">
                                <Input
                                    value={input}
                                    onChange={handleInputChange}
                                    placeholder="Type your question here..."
                                    className="flex-1"
                                    disabled={status === "submitted" || status === "streaming"}
                                />
                                <Button type="submit" disabled={status === "submitted" || status === "streaming" || !input.trim()}>
                                    {status === "submitted" ? (
                                        <div className="h-5 w-5 animate-spin rounded-full border-2 border-primary-foreground border-t-transparent" />
                                    ) : (
                                        <Send className="h-4 w-4" />
                                    )}
                                </Button>
                            </form>
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
    );
}