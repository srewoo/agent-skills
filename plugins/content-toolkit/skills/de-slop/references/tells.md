# Catalogue of AI-writing tells

Each tell is a **candidate**, not a verdict. One "robust" in a database article is a technical term. Twelve tells in 300 words is a pattern. Fix patterns and leave isolated, correct uses alone.

"Replace with" gives the default move. The best fix is usually the specific fact the vague phrase was standing in for. If the draft doesn't contain that fact, cut the phrase and don't invent one.

## 1. Vocabulary

| Tell | Why it reads as AI | Replace with |
|---|---|---|
| delve / delve into | Rare in human prose and very common in model output | "look at", "cover", "dig into", or just start the topic |
| tapestry, rich tapestry | Decorative metaphor with no content | Name the actual parts: "a mix of X, Y and Z" |
| testament to | Inflated praise | "shows", "proves", or the evidence itself |
| navigate the (complex) landscape / waters | Abstract travel metaphor | The concrete task: "choose a CRM", "comply with GDPR" |
| landscape (competitive, digital, evolving) | Filler noun | "market", "industry", or delete |
| leverage (as a verb) | Corporate inflation | "use". Keep it in finance (borrowed money) |
| robust | Vague strength claim | What it withstands: "handles 10k requests/sec", "survives a power cut" |
| seamless / seamlessly | Unprovable smoothness claim | What the user doesn't have to do: "no re-login", "imports in one click" |
| elevate | Vague improvement | The measured change: "raises conversion from 2% to 3%" |
| unlock (potential, growth, value) | Treasure metaphor | "lets you", "makes possible", or the outcome |
| in today's fast-paced / digital / ever-changing world | Empty scene-setter | Delete. Start with the point |
| it's important to note (that) | Throat-clearing | Delete. State the thing |
| realm, embark, pivotal, holistic, synergy, paradigm shift, game-changer, cutting-edge | Inflated register | Plain word: "area", "start", "key", "whole", "new", or the specific novelty |
| foster, underscore, showcase, empower, harness | Ceremony verbs | "build", "show", "let", "use" |
| revolutionise, transformative, meticulous, intricate, vibrant, bustling, unparalleled, treasure trove | Adjective inflation | Cut, or replace with the measurable detail |

## 2. Structures

| Tell | Example | Replace with |
|---|---|---|
| Contrast framing "It's not X, it's Y" | "It's not a tool, it's a mindset." | State Y directly: "It changes how the team works." Keep the contrast only when readers really do believe X |
| "Not just X, but Y" | "not just faster, but smarter" | Pick the claim you can support and say it once |
| Rule-of-three everywhere | "faster, cheaper, and better" in every paragraph | Keep a triad only where there really are three items. Otherwise use one or two, or four |
| Rhetorical question opener | "Ever wondered why churn spikes in Q1?" | Answer it: "Churn spikes in Q1 because annual contracts renew in January." |
| "Here's the thing / Here's why / The truth is / Let's be honest" | "Here's the thing: most teams skip this." | Delete the announcer: "Most teams skip this." |
| Colon or question reveal | "The result? A 40% lift." / "The secret is simple:" | Plain sentence: "Sign-ups rose 40%." |
| Signposting | "Let's dive in.", "In this article we'll explore…", "Without further ado" | Delete. Headings already signpost |
| Summary-restating conclusion | "In conclusion, X, Y and Z are important." | End on the last new point, a next step, or an open question. Cut the recap unless the piece is 2,000+ words |
| Every paragraph the same shape | Claim → three bullets → one-line moral | Vary: some paragraphs one sentence, some with no bullets |

## 3. Punctuation and formatting

| Tell | Threshold | Replace with |
|---|---|---|
| Em-dash overuse | More than about 1 per 200 words, or two in one sentence | Commas, full stops, parentheses, or a colon. Keep the author's own habit if their samples use it |
| Excessive bold | More than about 1 bold span per 100 words, or bold mid-sentence for emphasis | Bold only terms a skimmer must find. Let sentence order carry emphasis |
| Emoji bullets | 🚀 ✅ 💡 at the start of list items | Plain hyphen bullets, or prose. Keep emoji if the channel and author use them |
| Headings on every 80 words | H2/H3 over a single paragraph | Merge sections. Heading roughly every 200-400 words in long-form |
| Title Case Everywhere | "How To Build A Better Funnel" | Follow the publication's style; sentence case if unknown |

## 4. Hedging and filler

| Tell | Replace with |
|---|---|
| it's worth noting / it's worth mentioning | Delete |
| arguably, generally speaking, in many ways, to some extent | Delete, or state the actual condition: "for teams under 20 people" |
| may potentially / could potentially | "may" or "could", not both |
| plays a crucial / vital / key role in | Say what it does: "cuts setup time" |
| when it comes to X | "For X", or start with X |
| in order to | "to" |
| the fact that | Usually delete: "Because sales fell" not "Due to the fact that sales fell" |
| a wide range / variety / array of, a myriad of | The number, or "many", or the list |
| needless to say | Delete the phrase (and the sentence, if truly needless) |

## 5. Rhythm (burstiness)

Model prose often runs sentences of 15-22 words, one after another. Human prose mixes 4-word sentences with 30-word ones.

- **Check:** read five consecutive sentences. If none is under 8 words and none over 25, the rhythm is flat. The script flags a coefficient of variation below 0.35.
- **Fix:** split one long sentence into a short punch and a follow-up. Join two medium sentences with "and", "but", or "which". Allow a fragment where the author's voice permits it.
- Don't force it. Technical instructions can stay even. Burstiness matters most in narrative, opinion and marketing copy.

## 6. Generic examples

| Tell | Replace with |
|---|---|
| "Imagine a company that…", "Picture this:" | A real case from the draft or the author's notes. If none exists, ask the user for one or cut the example. Never invent a named company, customer, or number |
| "Company X", "John Doe", "Acme" | The real (or approved anonymised) example: "a 40-person logistics firm in Leeds" only if the author supplied it |
| "For example, businesses can improve efficiency" | An example must have a who, a what and a result. If it lacks all three, it isn't an example |

## 7. Sycophantic openings and closings

These appear when a chat answer is pasted into a document.

| Tell | Replace with |
|---|---|
| "Great question!", "Absolutely!", "Certainly!" | Delete |
| "I hope this helps!", "Happy to help", "Feel free to reach out", "Let me know if you have any questions" | Delete, or the channel's real CTA ("Reply to this email if…") if the author wants one |
| "As an AI…" | Delete the sentence |
| "You're absolutely right" | Delete |

## Leave these alone

- Technical terms that happen to be on the list: "robust regression", "robust against", "financial leverage", "unlock a device", "landscape orientation", "test harness", "elevated privileges", "Keycloak realm", the ACME protocol. In engineering docs, one "leverage" or "robust" is a style nit at most; don't rewrite a clean technical doc over it.
- Quoted speech, citations, product names, legal text.
- A habit the author's own published samples show (for example, an author who always uses em dashes or opens with a question). Note it in the summary instead of removing it.
