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
from utils.alias_resolver import normalize_question
from memory.memory import memory

logger = logging.getLogger("graph_pipeline")
logging.basicConfig(level=logging.INFO)

FALLBACK_ANSWER = (
    "Sorry, I hit a snag answering that one (the model timed out). "
    "Please try asking again — a re-try usually goes through fine."
)


def _timed(node_name):
    """Wraps a node function, logs how long it took (visible in Streamlit
    Cloud's 'Manage app' -> logs as `[TIMING] node: Xs`), AND catches any
    exception the node raises so a single failed LLM/network call can never
    crash the whole Streamlit session."""
    def decorator(fn):
        def wrapped(*args, **kwargs):
            start = time.time()
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                elapsed = round(time.time() - start, 2)
                logger.error(f"[TIMING] {node_name}: FAILED after {elapsed}s -> {e}")
                return {
                    "pipeline": node_name,
                    "intent": None,
                    "result": {"error": str(e)},
                    "final_answer": FALLBACK_ANSWER,
                }
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


class PipelineState(TypedDict, total=False):
    question: str
    rewritten_question: str
    route: dict
    entity_results: Annotated[list, operator.add]
    final_answer: str
    pipeline: str
    intent: Optional[str]
    result: dict
    last_entities: list


# ---------------------------------------------------------------------------
# Node: the single unified router call. EVERY message — including "hi" and
# "bye" — goes through this. No regex pre-filter and no hardcoded reply
# lists: the LLM itself decides the category (smalltalk / out_of_scope /
# answerable) AND writes the actual reply text for smalltalk/out_of_scope
# in the same JSON response (see "direct_reply" in unified_router.py). This
# is a deliberate latency-for-fidelity tradeoff you asked for — a "hi" now
# costs one fast_llm call instead of being free, but nothing in the app is
# instruction-matched/templated anymore; the LLM is genuinely deciding and
# generating every reply.
# ---------------------------------------------------------------------------
def route_node(state: PipelineState, fast_llm) -> PipelineState:
    history = memory.load_memory_variables({})
    normalized_question = normalize_question(state["question"])
    prior_entities = state.get("last_entities") or []

    route = unified_route(fast_llm, normalized_question, history=history,
                           last_entities=prior_entities)

    resolved = normalize_question(route.get("resolved_question", normalized_question))
    route["resolved_question"] = resolved

    # Carry this turn's entities forward as the hint for the NEXT question.
    # Only overwrite if this turn actually established something — an
    # out_of_scope/smalltalk turn (or a turn with no entities) shouldn't
    # wipe out a still-relevant earlier subject.
    new_entities = route.get("entities") or []
    next_last_entities = new_entities if new_entities else prior_entities

    return {"route": route, "rewritten_question": resolved, "last_entities": next_last_entities}


def dispatch(state: PipelineState):
    # If the "route" node itself raised (e.g. an unexpected KeyError while
    # parsing the LLM response), _timed() catches it and returns a state
    # update with no "route" key at all rather than letting it crash the
    # graph invocation. Fall back to rag on the raw question instead of
    # raising a second, harder-to-diagnose KeyError right here.
    route = state.get("route")
    if route is None:
        return "rag"

    if route["type"] == "smalltalk":
        return "smalltalk"
    if route["type"] == "out_of_scope":
        return "out_of_scope"

    pipeline = route.get("pipeline")
    entities = route.get("entities") or []
    is_comparison = route.get("is_comparison", False)

    if pipeline == "multi_aspect":
        return "multi_aspect"

    if pipeline == "combination" or (is_comparison and len(entities) >= 2):
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
# Terminal single-pipeline nodes
# ---------------------------------------------------------------------------
def _result_mentions_entities(df, entities) -> bool:
    """Sanity check: if the question named specific player(s), the SQL
    result should actually contain that name somewhere (a player_name
    column, typically). A result that's non-empty but never mentions the
    player asked about is the signature of a query that silently dropped
    its WHERE-clause player filter and aggregated across everyone instead
    (e.g. "how many runs he scored" -> SUM(ps.runs) with no player filter
    -> a plausible-looking but wrong single number). If nothing was named
    (a ranking question, "who scored the most"), there's nothing to check
    against, so this passes trivially."""
    if not entities:
        return True
    if df is None or df.empty:
        return False
    blob = " ".join(df.astype(str).values.flatten()).lower()
    return any(name.lower() in blob for name in entities)


def _extract_result_entities(df) -> list:
    """Pull player_name values out of a SQL result to use as the tracked
    entity for the NEXT turn's pronoun resolution. This is necessary
    because a ranking question like "who is the top run scorer" never
    names a player in its OWN text — the name only exists once the SQL
    executes — so route_node's text-only extraction (which runs BEFORE
    execution) can never catch it. If the result has more than one player
    (a "top 5" list), that's fine: route_node's Step 0 already only
    resolves a pronoun when last_entities has EXACTLY ONE name, so a
    multi-row result correctly stays ambiguous rather than guessing."""
    if df is None or df.empty or "player_name" not in df.columns:
        return []
    return df["player_name"].dropna().unique().tolist()


def sql_node(state: PipelineState, llm, fast_llm) -> PipelineState:
    sql_intent = state["route"]["sql_intent"] or "batting"
    agent_fn = SQL_AGENT_MAP[sql_intent]
    question = state["rewritten_question"]
    entities = state["route"].get("entities") or []

    # Tier 1: fast, non-reasoning model. Covers the large majority of
    # straightforward stat lookups against a fixed, well-documented schema.
    sql_result = agent_fn(fast_llm, question)

    tier1_valid = (
        sql_result["result_df"] is not None
        and not sql_result["result_df"].empty
        and _result_mentions_entities(sql_result["result_df"], entities)
    )

    if not tier1_valid:
        # Tier 2: retry with the deep reasoning model — triggers not just
        # on an empty result, but also on a non-empty result that never
        # mentions the player(s) the question was actually about.
        sql_result = agent_fn(llm, question)

    if sql_result["result_df"] is not None and not sql_result["result_df"].empty:
        result = {
            "answer": sql_result["result_text"],
            "generated_sql": sql_result["generated_sql"],
            "sql_result": sql_result["result_json"],
            "sql_error": sql_result["error"],
            "rag_docs": [], "tavily_sources": [], "search_used": "sql",
        }
    else:
        # Neither tier found rows — fall back to RAG/Tavily, deep model for
        # answer quality.
        result = search_orchestrator(llm, question)

    result_entities = _extract_result_entities(sql_result.get("result_df"))
    next_last_entities = result_entities if result_entities else entities

    return {"pipeline": "sql", "intent": sql_intent, "result": result,
            "final_answer": result["answer"], "last_entities": next_last_entities}


def rag_node(state: PipelineState, llm) -> PipelineState:
    # Falls back to the raw "question" if routing failed upstream and
    # "rewritten_question" was never set (see dispatch()'s route=None case).
    question = state.get("rewritten_question") or state["question"]
    result = get_rag_hybrid_answer(llm, question)
    return {"pipeline": "rag", "intent": "rag", "result": result, "final_answer": result["answer"]}


def tavily_node(state: PipelineState, llm) -> PipelineState:
    result = search_orchestrator(llm, state["rewritten_question"])
    return {"pipeline": "tavily", "intent": "tavily", "result": result, "final_answer": result["answer"]}


def smalltalk_node(state: PipelineState) -> PipelineState:
    # No hardcoded list — the router already wrote this in the same LLM
    # call that classified the message as smalltalk.
    route = state["route"]
    answer = route.get("direct_reply") or "Hey! What IPL question can I help with?"
    return {"pipeline": "smalltalk", "intent": route.get("smalltalk_kind"),
            "result": {}, "final_answer": answer}


def out_of_scope_node(state: PipelineState) -> PipelineState:
    # No hardcoded template — same story, the router wrote the decline text.
    route = state["route"]
    answer = route.get("direct_reply") or "I'm an IPL specialist — ask me something about the IPL!"
    return {"pipeline": "out_of_scope", "intent": None,
            "result": {"answer": answer, "generated_sql": None, "sql_result": None,
                       "sql_error": None, "rag_docs": [], "tavily_sources": [],
                       "search_used": "out_of_scope", "llm_calls": 0},
            "final_answer": answer}


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


_PRONOUNS = ("he ", "his ", "him ", "she ", "her ", "they ", "their ",
             "he'", "his'", "the player", "that player")


def _run_aspect(aspect: dict, llm, fast_llm):
    """Runs one aspect (sql/rag/tavily) using the same tiered logic as the
    main sql_node, returning (answer_text, result_df_or_None)."""
    pipeline = aspect.get("pipeline")
    question = aspect.get("sub_question", "")

    if pipeline == "sql":
        sql_intent = aspect.get("sql_intent") or "batting"
        agent_fn = SQL_AGENT_MAP.get(sql_intent, get_batting_result)
        sql_result = agent_fn(fast_llm, question)
        if sql_result["result_df"] is None or sql_result["result_df"].empty:
            sql_result = agent_fn(llm, question)
        if sql_result["result_df"] is not None and not sql_result["result_df"].empty:
            return sql_result["result_text"], sql_result["result_df"]
        fallback = search_orchestrator(llm, question)
        return fallback["answer"], None

    if pipeline == "tavily":
        result = search_orchestrator(llm, question)
        return result["answer"], None

    # default: rag
    result = get_rag_hybrid_answer(llm, question)
    return result["answer"], None


def multi_aspect_node(state: PipelineState, llm, fast_llm) -> PipelineState:
    aspects = state["route"].get("aspects") or []

    if len(aspects) < 2:
        # Router said multi_aspect but didn't actually fill 2 aspects —
        # fall back to a single rag lookup on the whole question rather
        # than crash on a malformed route.
        result = get_rag_hybrid_answer(llm, state["rewritten_question"])
        return {"pipeline": "multi_aspect", "intent": None, "result": {},
                "final_answer": result["answer"]}

    aspect_1, aspect_2 = aspects[0], aspects[1]

    # Aspect 1 runs as written — it's the part that establishes/names the
    # subject (e.g. the SQL ranking that resolves to a specific player).
    answer_1, df_1 = _run_aspect(aspect_1, llm, fast_llm)

    # Pull the actual resolved entity out of aspect 1's RESULT, not just
    # the route's text-based entity extraction — same reasoning as
    # sql_node's last_entities fix: a ranking question's subject only
    # exists once its query executes.
    resolved_entities = _extract_result_entities(df_1)
    prior_entities = state["route"].get("entities") or []
    entity = (resolved_entities[0] if len(resolved_entities) == 1
              else prior_entities[0] if len(prior_entities) == 1
              else None)

    # Substitute the resolved entity into aspect 2's sub_question if it
    # was written with a pronoun/placeholder, per the router's instructions.
    sub_q_2 = aspect_2.get("sub_question", "")
    if entity:
        lowered = sub_q_2.lower()
        if any(p in lowered for p in _PRONOUNS):
            aspect_2 = {**aspect_2, "sub_question": f"Regarding {entity}: {sub_q_2}"}
        else:
            aspect_2 = {**aspect_2, "sub_question": normalize_question(sub_q_2)}

    answer_2, _ = _run_aspect(aspect_2, llm, fast_llm)

    synthesis_prompt = f"""
Original question:
{state['rewritten_question']}

Part 1 answer:
{answer_1}

Part 2 answer:
{answer_2}

Combine these into one direct, natural answer to the original question.
Use ONLY the facts given above — never invent anything not present in them.
If either part indicates no data was found, say so plainly for that part
rather than making something up.
"""
    response = llm.invoke(synthesis_prompt)

    next_last_entities = [entity] if entity else prior_entities

    return {"pipeline": "multi_aspect", "intent": None, "result": {},
            "final_answer": response.content, "last_entities": next_last_entities}


# ---------------------------------------------------------------------------
# Build the graph — entry point is the router itself, no pre-filter
# ---------------------------------------------------------------------------
def build_graph(llm, fast_llm):
    graph = StateGraph(PipelineState)

    graph.add_node("route", _timed("route")(lambda s: route_node(s, fast_llm)))
    graph.add_node("sql", _timed("sql")(lambda s: sql_node(s, llm, fast_llm)))
    graph.add_node("rag", _timed("rag")(lambda s: rag_node(s, llm)))
    graph.add_node("tavily", _timed("tavily")(lambda s: tavily_node(s, llm)))
    graph.add_node("smalltalk", _timed("smalltalk")(smalltalk_node))
    graph.add_node("out_of_scope", _timed("out_of_scope")(out_of_scope_node))
    graph.add_node("single_entity_lookup", _timed("single_entity_lookup")(lambda s: single_entity_lookup(s, llm)))
    graph.add_node("comparator", _timed("comparator")(lambda s: comparator_node(s, llm)))
    graph.add_node("multi_aspect", _timed("multi_aspect")(lambda s: multi_aspect_node(s, llm, fast_llm)))

    graph.set_entry_point("route")
    graph.add_conditional_edges("route", dispatch, {
        "smalltalk": "smalltalk",
        "out_of_scope": "out_of_scope",
        "sql": "sql",
        "rag": "rag",
        "tavily": "tavily",
        "combination": "comparator",  # fallback label; real fan-out goes via Send
        "multi_aspect": "multi_aspect",
    })

    graph.add_edge("single_entity_lookup", "comparator")

    for terminal in ("sql", "rag", "tavily", "smalltalk", "out_of_scope", "comparator", "multi_aspect"):
        graph.add_edge(terminal, END)

    return graph.compile()