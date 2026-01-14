"use client";

import ReactMarkdown from "react-markdown";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import { ComponentPropsWithoutRef } from "react";

interface MarkdownRendererProps {
    content: string;
}

export function MarkdownRenderer({ content }: MarkdownRendererProps) {
    return (
        <div className="markdown-content">
            <ReactMarkdown
                components={{
                    // Code blocks with syntax highlighting
                    code({ className, children, ...props }: ComponentPropsWithoutRef<"code">) {
                        const match = /language-(\w+)/.exec(className || "");
                        const codeString = String(children).replace(/\n$/, "");
                        
                        // Check if it's an inline code or code block
                        const isInline = !match && !codeString.includes("\n");
                        
                        if (isInline) {
                            return (
                                <code className="inline-code" {...props}>
                                    {children}
                                </code>
                            );
                        }
                        
                        return (
                            <div className="code-block-wrapper">
                                {match && (
                                    <div className="code-language">{match[1]}</div>
                                )}
                                <SyntaxHighlighter
                                    style={oneDark}
                                    language={match?.[1] || "text"}
                                    PreTag="div"
                                    customStyle={{
                                        margin: 0,
                                        borderRadius: "0 0 8px 8px",
                                        fontSize: "13px",
                                    }}
                                >
                                    {codeString}
                                </SyntaxHighlighter>
                            </div>
                        );
                    },
                    // Styled pre tag
                    pre({ children }) {
                        return <>{children}</>;
                    },
                    // Links
                    a({ href, children }) {
                        return (
                            <a
                                href={href}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="markdown-link"
                            >
                                {children}
                            </a>
                        );
                    },
                    // Lists
                    ul({ children }) {
                        return <ul className="markdown-list">{children}</ul>;
                    },
                    ol({ children }) {
                        return <ol className="markdown-list ordered">{children}</ol>;
                    },
                    // Headings
                    h1({ children }) {
                        return <h1 className="markdown-heading h1">{children}</h1>;
                    },
                    h2({ children }) {
                        return <h2 className="markdown-heading h2">{children}</h2>;
                    },
                    h3({ children }) {
                        return <h3 className="markdown-heading h3">{children}</h3>;
                    },
                    // Blockquote
                    blockquote({ children }) {
                        return <blockquote className="markdown-blockquote">{children}</blockquote>;
                    },
                    // Paragraph
                    p({ children }) {
                        return <p className="markdown-paragraph">{children}</p>;
                    },
                    // Strong/Bold
                    strong({ children }) {
                        return <strong className="markdown-strong">{children}</strong>;
                    },
                    // Table
                    table({ children }) {
                        return (
                            <div className="table-wrapper">
                                <table className="markdown-table">{children}</table>
                            </div>
                        );
                    },
                }}
            >
                {content}
            </ReactMarkdown>
        </div>
    );
}
