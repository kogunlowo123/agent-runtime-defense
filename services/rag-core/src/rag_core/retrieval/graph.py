"""LangGraph-based retrieval pipeline."""
from __future__ import annotations

from typing import TypedDict

from langgraph.graph import StateGraph, END


class RetrievalState(TypedDict):
    query: str
    query_vector: list[float]
    filters: dict
    raw_results: list
    filtered_results: list
    reranked_results: list


def build_retrieval_graph(
    retriever,
    acl_filter,
    reranker,
    embedder,
):
    """Build a LangGraph pipeline for RAG retrieval."""

    def embed_query(state: RetrievalState) -> RetrievalState:
        state["query_vector"] = embedder.embed(state["query"])
        return state

    def retrieve(state: RetrievalState) -> RetrievalState:
        state["raw_results"] = retriever.retrieve(
            query_vector=state["query_vector"],
            query_text=state["query"],
            filters=state.get("filters"),
        )
        return state

    def apply_acl(state: RetrievalState) -> RetrievalState:
        principal_id = state.get("filters", {}).get("principal_id", "anonymous")
        state["filtered_results"] = acl_filter.filter(
            results=state["raw_results"],
            principal_id=principal_id,
        )
        return state

    def rerank(state: RetrievalState) -> RetrievalState:
        state["reranked_results"] = reranker.rerank(
            query=state["query"],
            candidates=state["filtered_results"],
        )
        return state

    graph = StateGraph(RetrievalState)
    graph.add_node("embed_query", embed_query)
    graph.add_node("retrieve", retrieve)
    graph.add_node("apply_acl", apply_acl)
    graph.add_node("rerank", rerank)

    graph.set_entry_point("embed_query")
    graph.add_edge("embed_query", "retrieve")
    graph.add_edge("retrieve", "apply_acl")
    graph.add_edge("apply_acl", "rerank")
    graph.add_edge("rerank", END)

    return graph.compile()
