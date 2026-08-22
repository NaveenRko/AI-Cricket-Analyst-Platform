import random
import time
import logging
from typing import TypedDict, Optional, Annotated
import operator

from langgraph.graph import StateGraph, END
from langgraph.types import Send

from agents.unified_router import unified_route
from agents.hybrid_agents import get_hybrid_answer
from agents.rag_hybrid import get_rag_hybrid_answer
from agents.search_orchestrator import search_orchestrator
from agents.batting_agent import get_batting_result
from agents.bowling_agent import get_bowling_result
from agents.team_agent import get_team_result
from agents.season_agent import get_season_result
from agents.venue_agent import get_venue_result
from agents.matchup_agent import get_matchup_result
from agents.smalltalk import detect_smalltalk
from utils.alias_resolver import normalize_question
from memory.memory import memory

logger = logging.getLogger("graph_pipeline")
logging.basicConfig(level=logging.INFO)


def _timed(node_name):
    """Wraps a node function and logs how long it took. Shows up in
    Streamlit Cloud's 'Manage app' -> logs panel with a timestamp, so you
    can see exactly which node ate the time on a slow request."""
    def decorator(fn):
        def wrapped(*args, **kwargs):
            start = time.time()
            try:
                return fn(*args, **kwargs)
            finally:
                elapsed = round(time.time() - start, 2)
                logger.info(f"[TIMING] {node_name}: {elapsed}s")
        return wrapped
    return decorator

SQL_AGENT_MAP = {
    "batting": get_batting_result,
    "bowling": get_bowling_result,
    "venue": get_venue_result,
    "season": get_season_result,
    "team": get_team_result,
    "matchup": get_matchup_result,
}

OUT_OF_SCOPE_RESULT = {
    "answer": "I'm an IPL specialist AI analyst. Please ask IPL-related questions.",
    "generated_sql": None, "sql_result": None, "sql_error": None,
    "rag_docs": [], "tavily_sources": [], "search_used": "out_of_scope", "llm_calls": 0,
}

GREETING_REPLIES = [
    "Hey! 👋 Ask me anything about IPL — batting, bowling, venues, matchups, records.",
    "Hi there! I'm your IPL analyst — what would you like to know?",
    "Hello! Ready when you are — ask me an IPL stat, player, or match question.",
    "Hey, good to see you. What IPL question can I dig into for you?",
]

CLOSING_REPLIES = [
    "Anytime! Come back whenever you've got another IPL question. 🏏",
    "You're welcome! Catch you next time.",
    "Glad to help — see you around!",
    "Sure thing. I'll be here whenever you want more IPL stats.",
]


class PipelineState(TypedDict, total=False):
    question: str
    rewritten_question: str
    route: dict
    entity_results: Annotated[list, operator.add]
    final_answer: str
    pipeline: str
    intent: Optional[str]
    result: dict


# ---------------------------------------------------------------------------
# Node: free, zero-latency regex pre-filter for obvious greetings/closings.
# Only questions that DON'T match here pay for an LLM call at all — this
# keeps "let the LLM decide" for every real question while not spending a
# model round-trip on "hi" / "thanks".
# ---------------------------------------------------------------------------
def prefilter_node(state: PipelineState) -> PipelineState:
    hit = detect_smalltalk(state["question"])
    if hit:
        return {"route": {"type": "smalltalk", "smalltalk_kind": hit["type"],
                           "resolved_question": state["question"]}}
    return {"route": None}


def dispatch_prefilter(state: PipelineState) -> str:
    return "smalltalk" if state.get("route") else "route"


# ---------------------------------------------------------------------------
# Node: the single unified router call. This now does BOTH what the old
# separate rewrite_node (pronoun/coreference resolution via memory) and
# route_node (pipeline + sql_intent + entity extraction) did — merged into
# one LLM round-trip instead of two, cutting latency roughly in half for
# every question that isn't pure smalltalk. It also fixes the coreference
# bug: the old standalone rewrite prompt was explicitly told "do NOT infer
# a player from a generic name" / "preserve ambiguity", so "who is his
# wife?" never resolved to the actual player even when the previous turn
# made it obvious. This merged prompt is allowed to resolve pronouns when
# history unambiguously supports it.
# ---------------------------------------------------------------------------
def route_node(state: PipelineState, llm) -> PipelineState:
    history = memory.load_memory_variables({})
    normalized_question = normalize_question(state["question"])

    route = unified_route(llm, normalized_question, history=history)

    # Cheap local pass again on the LLM's resolved_question, in case it
    # substituted a raw alias name that still needs canonicalizing.
    resolved = normalize_question(route.get("resolved_question", normalized_question))
    route["resolved_question"] = resolved

    return {"route": route, "rewritten_question": resolved}


def dispatch(state: PipelineState):
    """Conditional edge out of route_node — decides which branch(es) run next."""
    route = state["route"]

    if route["type"] == "smalltalk":
        return "smalltalk"
    if route["type"] == "out_of_scope":
        return "out_of_scope"

    pipeline = route.get("pipeline")
    entities = route.get("entities") or []
    is_comparison = route.get("is_comparison", False)

    if pipeline == "combination" or (is_comparison and len(entities) >= 2):
        # fan out: one Send per entity, each re-running the single-entity
        # sql/rag/tavily lookup, then converge on the comparator node
        sql_intent = route.get("sql_intent")
        sends = []
        for entity in entities:
            sends.append(
                Send(
                    "single_entity_lookup",
                    {
                        "question": f"{entity}: {state['rewritten_question']}",
                        "entity": entity,
                        "sql_intent": sql_intent,
                        "pipeline": sql_intent and "sql" or "rag",
                    },
                )
            )
        return sends

    return pipeline  # "sql" | "rag" | "tavily"


# ---------------------------------------------------------------------------
# Terminal single-pipeline nodes (used for the common, non-comparison case)
# ---------------------------------------------------------------------------
def sql_node(state: PipelineState, llm) -> PipelineState:
    sql_intent = state["route"]["sql_intent"] or "batting"
    result = get_hybrid_answer(llm, state["rewritten_question"], SQL_AGENT_MAP[sql_intent])
    return {"pipeline": "sql", "intent": sql_intent, "result": result, "final_answer": result["answer"]}


def rag_node(state: PipelineState, llm) -> PipelineState:
    result = get_rag_hybrid_answer(llm, state["rewritten_question"])
    return {"pipeline": "rag", "intent": "rag", "result": result, "final_answer": result["answer"]}


def tavily_node(state: PipelineState, llm) -> PipelineState:
    result = search_orchestrator(llm, state["rewritten_question"])
    return {"pipeline": "tavily", "intent": "tavily", "result": result, "final_answer": result["answer"]}


def smalltalk_node(state: PipelineState) -> PipelineState:
    kind = state["route"]["smalltalk_kind"]
    answer = random.choice(GREETING_REPLIES if kind == "greeting" else CLOSING_REPLIES)
    return {"pipeline": "smalltalk", "intent": kind, "result": {}, "final_answer": answer}


def out_of_scope_node(state: PipelineState) -> PipelineState:
    return {"pipeline": "out_of_scope", "intent": None, "result": OUT_OF_SCOPE_RESULT,
            "final_answer": OUT_OF_SCOPE_RESULT["answer"]}


# ---------------------------------------------------------------------------
# Fan-out branch: one lookup per entity in a comparison question
# ---------------------------------------------------------------------------
def single_entity_lookup(state: dict, llm) -> PipelineState:
    entity = state["entity"]
    sql_intent = state.get("sql_intent")

    if sql_intent:
        result = get_hybrid_answer(llm, state["question"], SQL_AGENT_MAP[sql_intent])
    else:
        result = get_rag_hybrid_answer(llm, state["question"])

    return {"entity_results": [{"entity": entity, "answer": result["answer"]}]}


def comparator_node(state: PipelineState, llm) -> PipelineState:
    blocks = "\n\n".join(f"{r['entity']}: {r['answer']}" for r in state["entity_results"])
    prompt = f"""
Original question:
{state['rewritten_question']}

Per-entity results:
{blocks}

Using ONLY the numbers/facts above, answer the original question directly,
including any comparison or "who performed best" judgment it asked for.
Never invent facts not present above.
"""
    response = llm.invoke(prompt)
    return {"pipeline": "combination", "intent": None, "result": {},
            "final_answer": response.content}


# ---------------------------------------------------------------------------
# Build the graph
# ---------------------------------------------------------------------------
def build_graph(llm):
    graph = StateGraph(PipelineState)

    graph.add_node("prefilter", _timed("prefilter")(prefilter_node))
    graph.add_node("route", _timed("route")(lambda s: route_node(s, llm)))
    graph.add_node("sql", _timed("sql")(lambda s: sql_node(s, llm)))
    graph.add_node("rag", _timed("rag")(lambda s: rag_node(s, llm)))
    graph.add_node("tavily", _timed("tavily")(lambda s: tavily_node(s, llm)))
    graph.add_node("smalltalk", _timed("smalltalk")(smalltalk_node))
    graph.add_node("out_of_scope", _timed("out_of_scope")(out_of_scope_node))
    graph.add_node("single_entity_lookup", _timed("single_entity_lookup")(lambda s: single_entity_lookup(s, llm)))
    graph.add_node("comparator", _timed("comparator")(lambda s: comparator_node(s, llm)))

    graph.set_entry_point("prefilter")
    graph.add_conditional_edges("prefilter", dispatch_prefilter, {
        "smalltalk": "smalltalk",
        "route": "route",
    })
    graph.add_conditional_edges("route", dispatch, {
        "smalltalk": "smalltalk",
        "out_of_scope": "out_of_scope",
        "sql": "sql",
        "rag": "rag",
        "tavily": "tavily",
        "combination": "comparator",  # fallback label; real fan-out goes via Send
    })

    graph.add_edge("single_entity_lookup", "comparator")

    for terminal in ("sql", "rag", "tavily", "smalltalk", "out_of_scope", "comparator"):
        graph.add_edge(terminal, END)

    return graph.compile()