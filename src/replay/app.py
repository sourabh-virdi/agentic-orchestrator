"""Streamlit Replay UI for debugging agent decisions and visualizing task DAGs."""

from __future__ import annotations

import json
from datetime import datetime

import streamlit as st

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore[assignment]

API_BASE = "http://localhost:8000/api/v1"

st.set_page_config(page_title="Agentic Orchestrator — Replay UI", page_icon="🔄", layout="wide")

st.title("Agentic Orchestrator — Replay UI")
st.markdown("Visual debugger for agent decisions and task graph execution.")


def fetch_replay_data(goal_id: str) -> dict | None:
    if httpx is None:
        st.error("httpx not installed")
        return None
    try:
        resp = httpx.get(f"{API_BASE}/replay/{goal_id}", timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        st.error(f"Failed to fetch replay data: {exc}")
        return None


def fetch_simulation(goal_title: str, goal_desc: str, seed: int, failure_rate: float) -> dict | None:
    if httpx is None:
        return None
    try:
        resp = httpx.post(
            f"{API_BASE}/simulate",
            json={
                "goal": {
                    "title": goal_title,
                    "description": goal_desc,
                    "constraints": {"channels": ["email", "in-app"]},
                },
                "seed": seed,
                "failure_rate": failure_rate,
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        st.error(f"Simulation failed: {exc}")
        return None


def render_dag(dag_data: dict) -> None:
    st.subheader("Task DAG")
    status_colors = {
        "completed": "🟢",
        "failed": "🔴",
        "running": "🟡",
        "pending": "⚪",
        "skipped": "⏭️",
    }
    for node in dag_data.get("nodes", []):
        icon = status_colors.get(node["status"], "❓")
        deps = ", ".join(node.get("dependencies", [])) or "none"
        st.markdown(f"{icon} **{node['name']}** ({node['agent_type']}) — deps: `{deps}`")
        if node.get("result"):
            with st.expander(f"Result for {node['name']}"):
                st.json(node["result"])


def render_timeline(timeline: list[dict]) -> None:
    st.subheader("Event Timeline")
    for event in timeline:
        ts = event.get("timestamp", "")
        agent = event.get("agent", "")
        action = event.get("action", "")
        st.markdown(f"`{ts}` — **{agent}** → {action}")
        if event.get("payload"):
            with st.expander("Payload"):
                st.json(event["payload"])


tab1, tab2 = st.tabs(["Replay", "Simulator"])

with tab1:
    goal_id = st.text_input("Goal ID", placeholder="Enter a goal UUID to replay")
    if st.button("Load Replay") and goal_id:
        data = fetch_replay_data(goal_id)
        if data:
            render_dag(data.get("dag", {}))
            render_timeline(data.get("timeline", []))

with tab2:
    st.subheader("Run Simulation")
    sim_title = st.text_input("Goal Title", "Q2 Email Campaign", key="sim_title")
    sim_desc = st.text_area("Goal Description", "Increase email open rates by 20%", key="sim_desc")
    col1, col2 = st.columns(2)
    with col1:
        sim_seed = st.number_input("Seed", value=42, min_value=0, key="sim_seed")
    with col2:
        sim_fail = st.slider("Failure Rate", 0.0, 1.0, 0.1, key="sim_fail")

    if st.button("Run Simulation"):
        result = fetch_simulation(sim_title, sim_desc, sim_seed, sim_fail)
        if result:
            st.metric("Total Steps", result["steps"])
            st.metric("Total Reward", f"{result['total_reward']:.2f}")
            render_dag(result.get("dag", {}))

            st.subheader("Execution Trace")
            for step in result.get("trace", []):
                icon = "🟢" if step["status"] == "completed" else "🔴" if step["status"] == "failed" else "🔄"
                st.markdown(
                    f"{icon} Step {step['step']}: **{step['task_name']}** "
                    f"— {step['status']} (reward: {step['reward']:.1f})"
                )
