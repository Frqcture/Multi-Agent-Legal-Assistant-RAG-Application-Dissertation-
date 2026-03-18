# Frontend Documentation

This document offers a detailed breakdown of the Legal Assistant RAG Application's frontend user interface. The UI is implemented as a **Single Page Application (SPA)** using **React 19**, bundled with **Vite**, and styled with modular CSS.

## 1. Core Technologies & Tooling

- **Library/Framework:** React 19 (Hooks-based architecture) mapped to TypeScript.
- **Bundler:** Vite – Offering ultra-fast Hot Module Replacement (HMR) and optimized build times.
- **Typing:** TypeScript – Used heavily across components to define interfaces for LLM responses, tool calls, and API shapes.
- **Routing:** `react-router-dom` v7 handling protected pathing and component rendering.
- **Styling:** CSS Modules (`.module.css`) to enforce heavily encapsulated and localized styling rules, preventing global CSS collisions.
- **Icons:** `react-icons` (using specific sets like `Bi` (BoxIcons) and `Fi` (Feather Icons)).

---

## 2. Project Layout

```text
Frontend/RAGapp/
├── public/                 # Static public assets
├── src/
│   ├── main.tsx            # Standard React initialization (createRoot)
│   ├── App.tsx             # Root component handling Router and Layout orchestration
│   ├── App.css / index.css # Global resets and base thematic variables
│   └── Components/
│       ├── useAuth.ts      # Custom Hook for guarding protected routes
│       ├── Login/          # User Login logic & form
│       ├── Register/       # Sub-component for registering users
│       └── Search/         # Main Logic Nexus: Chat, Uploads, Dashboards
│           ├── Search.tsx
│           ├── Search.module.css
│           ├── ProactiveDashboard.tsx
│           └── ProactiveDashboard.module.css
│       └── Workflow/       # Experimental workflow UI (currently not routed in App.tsx)
├── package.json
├── tsconfig.json
└── vite.config.ts          # Defines entry point & env variable resolutions
```

---

## 3. State Management & Data Flow

### 3.1 Authentication Handlers
**Route Guarding (`useAuth.ts` & `App.tsx`)**
- Upon loading `App.tsx`, the application evaluates `isAuthenticated` utilizing the custom `useAuth` hook.
- If the backend's `/me` endpoint returns `200`, the user may navigate to `/search`. If `401`, they are forced to fallback views (`/login` or `/register`).
- Authentication fundamentally relies on **cookies** rather than passing header tokens manually. Operations send requests with `{ credentials: 'include' }` so that JWTs and CSRF tokens handle state transparently against the FastAPI backend.
- A client-side helper function `getCookie(name)` parses `document.cookie` specifically to extract `csrf_token` requirements for mutating requests (POST/DELETE).

### 3.2 Main Chat Loop (`Search.tsx`)
The `Search.tsx` view handles the predominant interactivity loop of the application via local component state:
- `messages (Message[])`: An array mapping the back-and-forth log between the 'user' and the 'bot'.
- `inputValue (string)`: State linked to the main input box.
- The `askQuestion` API call resolves the LLM request. The output JSON appends `.answer`, unrolls the `steps` array, and includes web fallback metadata (`web_searched`, `web_sources`) when applicable.
- **Agent Step Visualization:** When `showSteps` is toggled true, the UI maps out internal orchestrator operations with icons for `planner`, `retriever`, `responder`, and `drafter`.
- `Search.tsx` also maintains `lastAskedQuery` (for proactive-insights refresh context) and jurisdiction badge state propagated from `ProactiveDashboard`.

### 3.3 The Document Library Modals
- Inside `Search.tsx`, users can prompt the Library modal.
- `fetchFiles()` routes to `GET /files` polling isolated user document lists. The files render iteratively with a capability mapped to `DELETE /files/{filename}`.
- A hidden `<input type="file" multiple accept=".pdf" />` handles document uploading. Upon changing, an asynchronous multipart `FormData` is appended and fired against `POST /upload`.

---

## 4. Components

### `ProactiveDashboard`
An intelligent, proactive dashboard dynamically reacting to the knowledge base's facts.
- **Triggers:** Queries `/proactive-insights` upon initial initialization or upon querying changes. (The backend returns a cached version if polled rapidly).
- **Cards Rendered (dynamic):**
  1. `NextActionsCard`: High, medium, low priority steps advised to the user.
  2. `StatutesCard`: Mappings of relevant statutes and jurisdiction constraints.
  3. `ChecklistCard`: A to-do list mapping. Critically, this interacts with `localStorage` (via `CHECKLIST_STORAGE_KEY`) to persist browser-local completion variables (`completed: boolean`), merged against fresh insights retrieved over the network.
  4. `InfoGapsCard`: Identifies vulnerabilities in the loaded documentation.
  5. `DeadlinesCard`: Date-driven deadline tracking with urgency countdowns.
  6. `ConflictsCard`: Cross-document conflict-of-interest signals.
- The backend returns `visible_sections`; the UI renders only those sections (typically the top-ranked set by relevance).
- **Scroll Behavior:** Uses an intuitive scroll auto-collapsing design interacting with `Search.tsx`'s `contentWrapperRef`. If a user scrolls deeply into their chat log, the cards collapse neatly, exposing optimal real-estate for text interaction. Expand handlers permit manual override.
- `ProactiveDashboard` also forwards detected jurisdiction metadata to `Search.tsx` for badge display.

### `Search`
The main chat UI wrapper. Split roughly into three segments:
- **Navigation Bar:** Exposes Steps Toggles, the Library Viewer overlay toggler, and the Logout dispatch.
- **Messaging Interface (`contentWrapper`):** Renders all arrays sequentially against `.messageBubble`. Embeds the Proactive Insights dashboard inherently near the top track, including optional web-source banners for fallback answers.
- **Search Footer:** Maintains the input track and exposes dual action buttons to upload files (Book icon) and submit requests (Arrow right).

### `Login` & `Register`
Standard React controlled-form abstractions binding standard states (`username`, `password`) against `application/x-www-form-urlencoded` HTTP requirements imposed by OAuth2 backend strictures.

---

## 5. Styling Configuration
The project fundamentally anchors on CSS modules for encapsulation:
- **`Search.module.css`**: Configures the primary flex properties of the view layout.
- **`ProactiveDashboard.module.css`**: Highly dynamic elements leveraging specific badge coloring styles (`.badgeHigh`, `.badgeMedium`), shimmer gradients for loading tracks, chevron animations conditionally wrapping `cardBodyOpen` max-height interpolations. 

## 6. Environment Configurations
Configuration constants defer to Vite's environment handling wrapper:
```javascript
const BASE_URL = import.meta.env.VITE_API_BASE_URL;
```
When running locally, this generally aliases against `http://localhost:8000` (FastAPI instance). Make sure the `.env` variable resides safely in `Frontend/RAGapp/`.