# AISOP Command Center — Enterprise Operations Guide

Welcome to the **Hospitality AI Operations Assistant (AISOP)**. This platform acts as a secure, local, and cloud-linked intelligence center for hotel staff. It translates complex hotel handbooks, Standard Operating Procedures (SOPs), and manuals into instant, actionable instructions.

> [!NOTE]
> This platform runs in **Secure Enterprise Mode**. All user queries and data retrievals are kept local to the server node, ensuring guest and hotel policy privacy.

---

## 🚀 Key Advantages for Hotel Hub Operations

| Feature | Operational Benefit | Technical Pipeline |
| :--- | :--- | :--- |
| **Instant SOP Retrieval** | Zero downtime searching printed manuals during front desk rushes or kitchen prep. | SQLite document matching + index retrieval. |
| **Hybrid Search Ranker** | Pinpoint precision on numbers, limits, and timelines. | Cosine Semantic + Keyword + Numeric Matching. |
| **Clickable Citations** | Instant verification directly to the source file name and section. | Automatic metadata tag alignment. |
| **Multi-Tier Fallback** | 100% service uptime even under cloud rate-limiting or network loss. | Llama 3.3 70B ➔ Llama 3.1 8B ➔ Local RAG. |

---

## 🛠️ How to Use the Interface

### 1. Starting a New Conversational Session
* Open your browser and navigate to `http://127.0.0.1:3000`.
* Click the **New Session** button at the top of the left sidebar to start a clean thread.

### 2. Live System Status Console
* The landing page dashboard lists active system metrics in real-time:
  * **Indexed SOPs**: Active count of synced files in your database.
  * **Chroma DB**: Vector embeddings count for semantically indexed paragraphs.
  * **NIM Latency**: Active LLM response latency (typically under 100ms on active NIM).
  * **Network**: Real-time socket connectivity state.

### 3. Running Sample Prompts
* Click any of the pre-configured prompt cards on the landing page (e.g., *Front Desk early check-in*, *Food safety temperature rules*) to run quick queries.

### 4. Filtering Chat History
* Type keywords into the search box in the sidebar to filter past conversation titles in real-time.

### 5. Message Hover Actions
* Hover over any assistant response to show the floating glass actions panel:
  * **Copy**: Copy the formatted markdown response text to your clipboard.
  * **Likes / Dislikes**: Rate response accuracy.

---

## 💡 Example Inquiries by Department

### 🏨 Front Desk & Reservations
* *"What is the policy for processing a guest cancellation within the penalty period?"*
* *"How do I handle a guest requesting an early check-in when rooms are not ready?"*
* *"What are the check-in and check-out time limits?"*

### 🍳 F&B and Food Safety
* *"What are the temperature rules for cooling poultry and ground meat?"*
* *"What is the hot and cold holding temperature threshold?"*
* *"Explain the procedure for receiving refrigerated food deliveries."*

### 🧹 Housekeeping & Maintenance
* *"What is the standard checklist for a guestroom inspection?"*
* *"What is the policy for handling high-value lost items?"*
* *"How do I report a maintenance defect in a guest room?"*

### 🚨 Safety & Emergency
* *"What is the exact evacuation procedure during a fire alarm?"*
* *"How do we handle a guest injury medical emergency?"*

---

## 🔍 Troubleshooting & FAQs

### Q: Why do I see a `Local Retrieval Mode` warning in the chat?
> [!WARNING]
> This occurs when the Cloud AI endpoint is rate-limited or the network is disconnected. The assistant automatically shifts to local RAG extraction, retrieving raw rules and tables directly from the local database so you are never left without answers.

### Q: Can I ask general questions not related to hotel operations?
Yes. The system's instructions distinguish between **operations queries** (strictly grounded in uploaded documents) and **general queries** (answered using general training knowledge, e.g., *"Translate this email to French"* or *"What is the time zone in India?"*).

### Q: How do I index new SOP documents?
Placing a markdown file (`.md`) inside the `Information/` directory and restarting the backend service will trigger the **Lifecycle Seeder**, indexing all files and creating vector embeddings automatically.
