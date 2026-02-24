"use client";

import Link from "next/link";
import FeatureLayout from "../../components/FeatureLayout";

const SECTIONS = [
  {
    num: "01",
    title: "Sub-navigation",
    desc: "Generate (main flow) and Site Review (this page) so you can switch between building and reviewing the Code Gen UI.",
  },
  {
    num: "02",
    title: "Generate a project card",
    desc: "One prompt input, framework pills (React, Next.js, Streamlit, Node, Python, Vue, Svelte), and a primary “Generate project” button — like a single place to describe and go.",
  },
  {
    num: "03",
    title: "Generated project result",
    desc: "After generation: “How to run” instructions (e.g. Vercel Sandbox), a file list (click to select), and a code viewer with “Copy file.” Split panel: files left, editor right.",
  },
];

export default function CodegenReviewPage() {
  return (
    <FeatureLayout
      title="Code Gen · Site Review"
      description="What the Code Gen UI looks like — layout, sections, and a live preview of the generator page."
      icon="👁️"
      endpoints={[]}
    >
      <div className="codegenSubNav">
        <Link href="/codegen" className="codegenSubNavLink">
          ← Generate
        </Link>
        <span className="codegenSubNavCurrent">Site Review</span>
      </div>

      <div className="featureCard">
        <div className="cardHeader">
          <h2>
            <span className="cardIcon">👁️</span>
            What the Code Gen UI looks like
          </h2>
        </div>
        <p className="featureCardSubtitle">
          A quick review of the Code Gen page layout and sections, plus a live preview below.
        </p>

        <div className="codegenReviewInspiration">
          <strong>Inspired by</strong> tools like{" "}
          <a href="https://openlovable.com" target="_blank" rel="noopener noreferrer" className="codegenReviewInspirationLink">
            Open Lovable
          </a>
          — one input, clear options, instant result.
        </div>

        <ul className="codegenReviewSections">
          {SECTIONS.map((s, i) => (
            <li key={i} className="codegenReviewSectionItem">
              <span className="codegenReviewSectionNum">{s.num}</span>
              <div>
                <strong>{s.title}</strong> — {s.desc}
              </div>
            </li>
          ))}
        </ul>

        <div className="codegenReviewPreviewWrap">
          <div className="codegenReviewPreviewHeader">
            <span>Live preview</span>
            <a href="/codegen" target="_blank" rel="noopener noreferrer" className="codegenSubNavLink">
              Open in new tab →
            </a>
          </div>
          <iframe
            src="/codegen"
            title="Code Gen page preview"
            className="codegenReviewIframe"
          />
        </div>
      </div>
    </FeatureLayout>
  );
}
