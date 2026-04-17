# 🧠 Mnemo — A RAG Case Study for DevOps & SRE

> *"The cluster remembers. You just have to ask."*

This repository is a **case study** exploring how **Retrieval-Augmented Generation (RAG)** can transform the way DevOps engineers and SREs investigate their daily processes. It is not a finished product — it is a working demonstration of a pattern with real-world implications for operational intelligence. The example here is for kubernetes events.

---

## The Name

**Mnemo** is short for **Mnemosyne** — the Greek Titaness and goddess of memory, remembrance, and time. In myth, she was the keeper of all that has been and the mother of the nine Muses. The name is intentional: the core insight of this case study is that Kubernetes clusters suffer from *institutional amnesia*. Events expire. Timelines dissolve. On-call engineers arrive to a crime scene with no evidence tape.

Mnemosyne remembers everything. So does Mnemo.

---

## What This Case Study Is About

[https://www.linkedin.com/posts/hakob-mkoyan_case-study-rag-in-devopssre-processes-activity-7445524559430197248-NgdG?utm_source=share&utm_medium=member_desktop&rcm=ACoAADibxN0BxznOxKCNxXvYMbdjXLOWCyQXB_A](Find the full history here.)

Modern Kubernetes clusters generate thousands of events per day — pod scheduling decisions, image pull failures, OOMKills, CrashLoopBackOffs, node evictions, quota violations. The problem is not that this information doesn't exist. The problem is that:

- Kubernetes **deletes event history after 1 hour** by default
- Querying events requires **knowing what to look for** in advance
- Correlating events across namespaces and time requires **deep expert knowledge**
- At 3 AM during an incident, the cognitive load of kubectl archaeology is immense

This case study asks a simple question: **what happens when you apply RAG to this problem?**

The answer is Mnemo — a system that watches etcd in real time, encodes every cluster event as a semantic vector, and lets any engineer ask in plain English:

```
"Why is the crasher pod restarting?"
```

And receive a structured forensic report in under 2 seconds.

---

## Why RAG Fits This Problem

RAG is an AI architecture that combines two things: a retrieval system that fetches relevant documents from a knowledge base, and a generative LLM that reasons over those documents to produce an answer. Most RAG tutorials apply it to PDFs or wikis. This case study argues it is a **natural fit for operational data** — and here is why:

**The grounding problem.** In incident response, hallucination is unacceptable. An LLM that confidently invents a root cause is worse than no LLM at all. RAG solves this by constraining the model to reason *only* over retrieved evidence. If an event didn't happen, the system says so — it identifies the gap rather than filling it with fiction.

**The scale problem.** A cluster running 50+ workloads generates tens of thousands of events per day — far too many to fit in any LLM context window. RAG's retrieval step means the model only sees the handful of events semantically relevant to the query.

**The expertise problem.** `kubectl get events --field-selector reason=BackOff` returns all BackOff events but gives no causal context. RAG translates *intent* ("why is X broken?") into *evidence* (the relevant events), then lets the LLM reconstruct the causal chain. A junior engineer can run the same investigation that previously required a senior SRE.

**The memory problem.** Kubernetes garbage-collects its own event history. ChromaDB does not. Mnemo persists the forensic record indefinitely — making the cluster's history queryable long after `kubectl` has forgotten it.

---

## What Was Built

Mnemo is a minimal but complete RAG pipeline deployed inside the Kubernetes cluster it monitors:

```
etcd /registry/events
        │  real-time gRPC watch stream
        ▼
   EtcdManager       watches every event as it is written to etcd
        │
        ▼
     Chunker          decodes protobuf → JSON, builds semantic search_string
        │
        ▼
     Embedder         all-MiniLM-L6-v2 → 384-dim vector (in-cluster, CPU-only)
        │
        ▼
    ChromaDB          HNSW vector index, inner-product similarity, PVC-backed
        │
        ▼
   FastAPI /ask       embeds the query, retrieves top-K events
        │
        ▼
  MnemoNarrator       Groq (llama-3.1-8b-instant) → structured forensic report
```

**Stack:** Python · FastAPI · ChromaDB · sentence-transformers · Groq · etcd3

---

## The Live Result

A pod is deployed with an intentional failure: `kubectl run crasher --image=busybox -- /bin/sh -c "exit 1"`

Mnemo is queried: `GET /ask?q=why+is+the+crasher+pod+restarting`

ChromaDB retrieves the 6 semantically nearest events. The LLM returns:

```
Direct Answer:
The crasher pod is restarting due to a BackOff caused by the failure
of container crasher.

Event Chain:
10:30:07Z  Pod/crasher — Scheduled: Successfully assigned default/crasher to minikube
10:30:07Z  Pod/crasher — Pulling:   Pulling image "busybox"
10:30:11Z  Pod/crasher — Pulled:    Successfully pulled image "busybox" in 3.757s
10:30:11Z  Pod/crasher — Created:   Created container crasher
10:30:11Z  Pod/crasher — Started:   Started container crasher
10:30:14Z  Pod/crasher — BackOff:   Back-off restarting failed container (count: 13) ⚠

Root Cause:
Category: Application
Trigger: Container exits immediately after start — 3 seconds between
         Started (10:30:11Z) and BackOff (10:30:14Z)

Gaps:
- No OOMKilled event — memory exhaustion not evidenced
- No exit code in retrieved events — kubectl get pod crasher -o json
  | jq '.status.containerStatuses[0].lastState.terminated' would confirm exit code 1
```

In one query, with no prior kubectl knowledge, Mnemo reconstructed the full pod lifecycle, identified the application-layer root cause, and explicitly called out what evidence is missing. **End-to-end: under 2 seconds.**

---

## Key Engineering Lessons

These are the findings that matter most from building this system.

**Retrieval quality matters more than model size.**
The most impactful improvements came from retrieval fixes, not LLM upgrades. Deduplication, chronological sorting, and embedding COUNT in the document string all had more impact on answer quality than switching to a larger model.

**Deduplication is the most important RAG decision.**
Without it, a BackOff event firing 47 times creates 47 identical chunks that flood retrieval and leave no room for the lifecycle context that explains the failure. One chunk per `name.reason` key, always containing the latest count, is the fix.

**Small models hallucinate on structured context.**
Models under ~8B parameters invented OOMKilled events, fake node names, and non-existent deployments — even when given correct context. The minimum viable model for Kubernetes forensics is `llama-3.1-8b`. Hosted APIs (Groq, Gemini) provide better reliability with zero infrastructure overhead.

**Etcd is the ground truth.**
Reading directly from etcd (not kube-apiserver) gives access to MVCC revision history — every state transition, not just current state. This is what makes the system a genuine historian rather than a current-state query tool.

---

## SRE Workflows This Enables

**Incident Response**
```
"Why is the payment-service pod crashing?"
"What happened to the database StatefulSet in the last hour?"
"Are there any OOMKilled events in the production namespace?"
"Why was the frontend deployment evicted?"
```

**Post-Incident Review**
ChromaDB persists event history beyond the 1-hour Kubernetes TTL. Reconstruct full timelines for post-mortems without relying on kubectl output that has already expired.

**Deployment Validation**
```
"Did the v2.1.0 rollout complete without errors?"
"Were there any probe failures during the last deployment?"
```

**Capacity Planning**
Recurring events with high `count` values are chronic degradation signals: OOMKills suggest undersized memory limits, evictions suggest node pressure, FailedScheduling with `Insufficient CPU` means the node pool needs expanding.

---

## What This Is Not

This is a case study, not a production-ready platform. Known rough edges include:

- Groq API key is hardcoded in `narrator.py` — must be a Kubernetes Secret before any real deployment
- No timestamp range index — time-bounded queries rely on metadata `where` clauses
- The etcd watch stream has no reconnection logic — a network partition silently stalls ingestion
- All events share one unbounded ChromaDB collection — TTL-based cleanup is not implemented
- The `/ask` endpoint has no authentication

These are documented intentionally. The goal of this repository is to demonstrate the *pattern* — and to be honest about what a production-grade version would need.

---

## The Broader Argument

RAG is not just a pattern for document Q&A. This case study argues it is a natural fit for any domain where:

- Data is too voluminous for a single LLM context window
- Answers must be grounded in real, current data — not training knowledge
- The user knows *what* they want to understand but not *what to search for*
- Institutional memory is fragile and expert-dependent

Kubernetes event forensics satisfies all four conditions. So do application logs, CI/CD pipelines, infrastructure change histories, and security audit trails. Mnemo is one instance of a pattern that generalises.

---

*Built with etcd × sentence-transformers × ChromaDB × Groq*

*"Making the invisible history of your cluster queryable."*
