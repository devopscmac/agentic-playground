"""
Gradio-based web interface for the agentic playground.
"""

import asyncio
import json
from typing import Optional, List, Tuple
from datetime import datetime
import gradio as gr
import plotly.graph_objects as go
import pandas as pd

from ..core import Agent, AgentConfig, Message, MessageType, Orchestrator, LLMAgent
from ..llm import AnthropicProvider, OpenAIProvider


class AgenticWebUI:
    """
    Web UI for managing and interacting with agents.

    Features:
    - Live chat interface with agents
    - Agent creation and management
    - Message history viewer
    - Agent interaction visualization
    """

    def __init__(self):
        self.orchestrator = Orchestrator()
        self.chat_history: List[Tuple[str, str]] = []
        self.orchestrator_task: Optional[asyncio.Task] = None
        self.memory_manager = None
        self.storage = None
        self.current_session_id = None

    def create_interface(self) -> gr.Blocks:
        """Create the Gradio interface."""

        with gr.Blocks(title="Agentic Playground") as interface:
            gr.Markdown("# 🤖 Agentic Playground - Multi-Agent System")
            gr.Markdown("Create, manage, and interact with AI agents in real-time.")

            with gr.Tabs():
                # Tab 1: Live Chat
                with gr.Tab("💬 Live Chat"):
                    self._create_chat_tab()

                # Tab 2: Agent Management
                with gr.Tab("⚙️ Agent Management"):
                    self._create_agent_management_tab()

                # Tab 3: Message History
                with gr.Tab("📜 Message History"):
                    self._create_history_tab()

                # Tab 4: Memory Settings
                with gr.Tab("🧠 Memory Settings"):
                    self._create_memory_tab()

                # Tab 5: Visualization
                with gr.Tab("📊 Visualization"):
                    self._create_visualization_tab()

        return interface

    def _create_chat_tab(self):
        """Create the live chat interface tab."""
        gr.Markdown("### Send messages to agents and see responses in real-time")

        with gr.Row():
            with gr.Column(scale=2):
                chatbot = gr.Chatbot(
                    label="Agent Conversation",
                    height=500,
                    show_label=True
                )

                with gr.Row():
                    msg_input = gr.Textbox(
                        label="Your Message",
                        placeholder="Type your message here...",
                        lines=2,
                        scale=4
                    )
                    send_btn = gr.Button("Send", variant="primary", scale=1)

                with gr.Row():
                    recipient_dropdown = gr.Dropdown(
                        label="Send to Agent",
                        choices=[],
                        value=None,
                        interactive=True
                    )
                    msg_type_dropdown = gr.Dropdown(
                        label="Message Type",
                        choices=["QUERY", "TASK", "BROADCAST"],
                        value="QUERY",
                        interactive=True
                    )

                clear_btn = gr.Button("Clear Chat")

            with gr.Column(scale=1):
                gr.Markdown("### Active Agents")
                agent_list = gr.Textbox(
                    label="Registered Agents",
                    lines=10,
                    interactive=False
                )
                refresh_btn = gr.Button("Refresh Agents")

        # Event handlers
        def send_message(message: str, recipient: str, msg_type: str, history):
            """Send a message to an agent."""
            if not message.strip():
                return history, "", self._get_agent_list()

            try:
                # Create and send message
                msg = Message(
                    type=MessageType[msg_type],
                    sender="user",
                    recipient=recipient if recipient else None,
                    content=message
                )

                # Run async send
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                if recipient:
                    loop.run_until_complete(
                        self.orchestrator.send_message_to_agent(recipient, msg)
                    )
                else:
                    loop.run_until_complete(
                        self.orchestrator.broadcast_message(msg)
                    )

                loop.close()

                # Update chat history
                history.append((f"You → {recipient or 'All'}: {message}", None))

                # Get recent responses
                recent_messages = self.orchestrator.get_message_history()[-5:]
                for m in recent_messages:
                    if m.type == MessageType.RESPONSE and m.sender != "user":
                        history.append((None, f"{m.sender}: {m.content}"))

                return history, "", self._get_agent_list()

            except Exception as e:
                history.append((None, f"Error: {str(e)}"))
                return history, message, self._get_agent_list()

        def refresh_agents():
            """Refresh the agent list and dropdown."""
            return self._get_agent_list(), gr.Dropdown(choices=self._get_agent_names())

        def clear_chat():
            """Clear the chat history."""
            return []

        send_btn.click(
            send_message,
            inputs=[msg_input, recipient_dropdown, msg_type_dropdown, chatbot],
            outputs=[chatbot, msg_input, agent_list]
        )

        msg_input.submit(
            send_message,
            inputs=[msg_input, recipient_dropdown, msg_type_dropdown, chatbot],
            outputs=[chatbot, msg_input, agent_list]
        )

        refresh_btn.click(
            refresh_agents,
            outputs=[agent_list, recipient_dropdown]
        )

        clear_btn.click(clear_chat, outputs=[chatbot])

    def _create_agent_management_tab(self):
        """Create the agent management interface tab."""
        gr.Markdown("### Create and configure new agents")

        with gr.Row():
            with gr.Column():
                gr.Markdown("#### Create New Agent")

                agent_name = gr.Textbox(
                    label="Agent Name",
                    placeholder="e.g., assistant, researcher, etc."
                )

                agent_role = gr.Textbox(
                    label="Role Description",
                    placeholder="e.g., Helpful assistant, Data analyst, etc."
                )

                system_prompt = gr.Textbox(
                    label="System Prompt",
                    placeholder="Instructions for the agent...",
                    lines=5
                )

                llm_provider = gr.Dropdown(
                    label="LLM Provider",
                    choices=["Anthropic", "OpenAI", "None (Echo Agent)"],
                    value="Anthropic"
                )

                llm_model = gr.Textbox(
                    label="Model Name",
                    placeholder="e.g., claude-sonnet-4-20250514, gpt-4-turbo-preview",
                    value="claude-sonnet-4-20250514"
                )

                create_btn = gr.Button("Create Agent", variant="primary")
                create_status = gr.Textbox(label="Status", interactive=False)

            with gr.Column():
                gr.Markdown("#### Existing Agents")

                agents_display = gr.Dataframe(
                    headers=["Name", "Role", "Type"],
                    interactive=False,
                    wrap=True
                )

                refresh_agents_btn = gr.Button("Refresh List")

                gr.Markdown("#### Start/Stop Orchestrator")

                with gr.Row():
                    start_btn = gr.Button("Start Orchestrator", variant="primary")
                    stop_btn = gr.Button("Stop Orchestrator", variant="stop")

                orch_status = gr.Textbox(label="Orchestrator Status", interactive=False)

        def create_agent(name: str, role: str, prompt: str, provider: str, model: str):
            """Create a new agent."""
            try:
                if not name or not role:
                    return "Error: Name and role are required", self._get_agents_dataframe()

                if name in self.orchestrator.agents:
                    return f"Error: Agent '{name}' already exists", self._get_agents_dataframe()

                config = AgentConfig(
                    name=name,
                    role=role,
                    system_prompt=prompt if prompt else None
                )

                # Create agent based on provider
                if provider == "None (Echo Agent)":
                    from ..agents import EchoAgent
                    agent = EchoAgent(name=name)
                elif provider == "Anthropic":
                    llm = AnthropicProvider(model=model if model else "claude-sonnet-4-20250514")
                    agent = LLMAgent(config, llm)
                elif provider == "OpenAI":
                    llm = OpenAIProvider(model=model if model else "gpt-4-turbo-preview")
                    agent = LLMAgent(config, llm)
                else:
                    return f"Error: Unknown provider '{provider}'", self._get_agents_dataframe()

                self.orchestrator.register_agent(agent)

                return f"✓ Agent '{name}' created successfully!", self._get_agents_dataframe()

            except Exception as e:
                return f"Error: {str(e)}", self._get_agents_dataframe()

        def start_orchestrator():
            """Start the orchestrator."""
            try:
                if self.orchestrator.running:
                    return "Orchestrator is already running"

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.orchestrator.start())
                loop.close()

                return "✓ Orchestrator started"
            except Exception as e:
                return f"Error: {str(e)}"

        def stop_orchestrator():
            """Stop the orchestrator."""
            try:
                if not self.orchestrator.running:
                    return "Orchestrator is not running"

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.orchestrator.stop())
                loop.close()

                return "✓ Orchestrator stopped"
            except Exception as e:
                return f"Error: {str(e)}"

        create_btn.click(
            create_agent,
            inputs=[agent_name, agent_role, system_prompt, llm_provider, llm_model],
            outputs=[create_status, agents_display]
        )

        refresh_agents_btn.click(
            lambda: self._get_agents_dataframe(),
            outputs=[agents_display]
        )

        start_btn.click(start_orchestrator, outputs=[orch_status])
        stop_btn.click(stop_orchestrator, outputs=[orch_status])

    def _create_history_tab(self):
        """Create the message history viewer tab."""
        gr.Markdown("### View and filter conversation history")

        with gr.Row():
            filter_agent = gr.Dropdown(
                label="Filter by Agent",
                choices=["All"] + self._get_agent_names(),
                value="All"
            )

            filter_type = gr.Dropdown(
                label="Filter by Message Type",
                choices=["All"] + [t.value for t in MessageType],
                value="All"
            )

            refresh_history_btn = gr.Button("Refresh", variant="primary")

        history_display = gr.Dataframe(
            headers=["Timestamp", "Type", "Sender", "Recipient", "Content"],
            interactive=False,
            wrap=True
        )

        stats_display = gr.Markdown("### Statistics\nNo messages yet.")

        def refresh_history(agent_filter: str, type_filter: str):
            """Refresh the message history display."""
            messages = self.orchestrator.get_message_history()

            # Apply filters
            if agent_filter != "All":
                messages = [m for m in messages if m.sender == agent_filter or m.recipient == agent_filter]

            if type_filter != "All":
                messages = [m for m in messages if m.type.value == type_filter]

            # Create dataframe
            data = []
            for msg in messages:
                data.append([
                    msg.timestamp.strftime("%H:%M:%S"),
                    msg.type.value,
                    msg.sender,
                    msg.recipient or "All",
                    msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
                ])

            # Generate statistics
            total = len(self.orchestrator.get_message_history())
            filtered = len(messages)
            type_counts = {}
            for msg in self.orchestrator.get_message_history():
                type_counts[msg.type.value] = type_counts.get(msg.type.value, 0) + 1

            stats = f"""### Statistics
- **Total Messages**: {total}
- **Filtered Messages**: {filtered}
- **By Type**: {', '.join(f"{k}: {v}" for k, v in type_counts.items())}
"""

            return data, stats

        refresh_history_btn.click(
            refresh_history,
            inputs=[filter_agent, filter_type],
            outputs=[history_display, stats_display]
        )

    def _create_memory_tab(self):
        """Create the memory settings interface tab."""
        gr.Markdown("### Configure persistent memory and session management")

        with gr.Row():
            with gr.Column():
                gr.Markdown("#### Memory Settings")

                memory_enabled = gr.Checkbox(
                    label="Enable Persistent Memory",
                    value=False,
                    info="Store conversation history and agent states"
                )

                storage_path = gr.Textbox(
                    label="Storage Path",
                    value="./data/sessions.db",
                    placeholder="Path to SQLite database file"
                )

                with gr.Row():
                    enable_btn = gr.Button("Enable Memory", variant="primary")
                    disable_btn = gr.Button("Disable Memory")

                memory_status = gr.Textbox(
                    label="Memory Status",
                    value="Memory is disabled",
                    interactive=False
                )

                gr.Markdown("---")
                gr.Markdown("#### Session Management")

                session_info = gr.Markdown("**Current Session:** None")

                session_dropdown = gr.Dropdown(
                    label="Available Sessions",
                    choices=[],
                    value=None,
                    interactive=True
                )

                with gr.Row():
                    new_session_btn = gr.Button("New Session", variant="primary")
                    load_session_btn = gr.Button("Load Session")
                    refresh_sessions_btn = gr.Button("Refresh")

                with gr.Row():
                    save_session_btn = gr.Button("Save Current Session")
                    delete_session_btn = gr.Button("Delete Session", variant="stop")

                session_status = gr.Textbox(
                    label="Session Status",
                    interactive=False
                )

            with gr.Column():
                gr.Markdown("#### Session Details")

                session_details = gr.Dataframe(
                    headers=["Session ID", "Created", "Last Active", "Messages"],
                    interactive=False,
                    wrap=True
                )

                gr.Markdown("#### Memory Statistics")

                memory_stats = gr.Markdown("Enable memory to see statistics")

        def enable_memory(path: str):
            """Enable memory system."""
            try:
                from agentic_playground.memory import MemoryManager, SQLiteStorage

                # Initialize storage
                self.storage = SQLiteStorage(path)
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.storage.initialize())
                loop.close()

                # Create memory manager
                self.memory_manager = MemoryManager(self.storage)

                return (
                    True,
                    f"✓ Memory enabled at {path}",
                    self._get_session_info(),
                    self._get_session_choices(),
                    self._get_session_details(),
                    self._get_memory_stats()
                )

            except Exception as e:
                return (
                    False,
                    f"Error enabling memory: {str(e)}",
                    "**Current Session:** None",
                    [],
                    [],
                    "Error loading statistics"
                )

        def disable_memory():
            """Disable memory system."""
            try:
                if self.storage:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.storage.close())
                    loop.close()

                self.storage = None
                self.memory_manager = None
                self.current_session_id = None

                return (
                    False,
                    "Memory disabled",
                    "**Current Session:** None",
                    [],
                    [],
                    "Memory is disabled"
                )

            except Exception as e:
                return (
                    False,
                    f"Error disabling memory: {str(e)}",
                    "**Current Session:** None",
                    [],
                    [],
                    "Error"
                )

        def create_new_session():
            """Create a new session."""
            try:
                if not self.memory_manager:
                    return "Error: Memory is not enabled", self._get_session_info(), [], [], ""

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                session_id = loop.run_until_complete(
                    self.memory_manager.create_session(metadata={"created_via": "webui"})
                )
                loop.close()

                # Attach to orchestrator
                self.current_session_id = session_id
                self.orchestrator.attach_memory_manager(self.memory_manager, session_id)

                return (
                    f"✓ Created session: {session_id[:8]}...",
                    self._get_session_info(),
                    self._get_session_choices(),
                    self._get_session_details(),
                    self._get_memory_stats()
                )

            except Exception as e:
                return f"Error: {str(e)}", self._get_session_info(), [], [], ""

        def load_session(session_id: str):
            """Load an existing session."""
            try:
                if not self.memory_manager or not session_id:
                    return "Error: Memory not enabled or no session selected", self._get_session_info(), []

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                # Restore session
                loop.run_until_complete(self.orchestrator.restore_session(session_id))
                self.current_session_id = session_id

                loop.close()

                return (
                    f"✓ Loaded session: {session_id[:8]}...",
                    self._get_session_info(),
                    self._get_memory_stats()
                )

            except Exception as e:
                return f"Error: {str(e)}", self._get_session_info(), ""

        def save_current_session():
            """Save the current session."""
            try:
                if not self.memory_manager or not self.current_session_id:
                    return "Error: No active session", self._get_memory_stats()

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.orchestrator.save_session())
                loop.close()

                return f"✓ Session saved", self._get_memory_stats()

            except Exception as e:
                return f"Error: {str(e)}", ""

        def delete_session(session_id: str):
            """Delete a session."""
            try:
                if not self.memory_manager or not session_id:
                    return "Error: No session selected", [], [], ""

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.memory_manager.delete_session(session_id))
                loop.close()

                if session_id == self.current_session_id:
                    self.current_session_id = None

                return (
                    f"✓ Deleted session: {session_id[:8]}...",
                    self._get_session_choices(),
                    self._get_session_details(),
                    self._get_memory_stats()
                )

            except Exception as e:
                return f"Error: {str(e)}", [], [], ""

        def refresh_sessions():
            """Refresh session list."""
            return (
                self._get_session_choices(),
                self._get_session_details()
            )

        # Event handlers
        enable_btn.click(
            enable_memory,
            inputs=[storage_path],
            outputs=[memory_enabled, memory_status, session_info, session_dropdown,
                    session_details, memory_stats]
        )

        disable_btn.click(
            disable_memory,
            outputs=[memory_enabled, memory_status, session_info, session_dropdown,
                    session_details, memory_stats]
        )

        new_session_btn.click(
            create_new_session,
            outputs=[session_status, session_info, session_dropdown, session_details, memory_stats]
        )

        load_session_btn.click(
            load_session,
            inputs=[session_dropdown],
            outputs=[session_status, session_info, memory_stats]
        )

        save_session_btn.click(
            save_current_session,
            outputs=[session_status, memory_stats]
        )

        delete_session_btn.click(
            delete_session,
            inputs=[session_dropdown],
            outputs=[session_status, session_dropdown, session_details, memory_stats]
        )

        refresh_sessions_btn.click(
            refresh_sessions,
            outputs=[session_dropdown, session_details]
        )

    def _get_session_info(self) -> str:
        """Get current session information."""
        if not self.current_session_id:
            return "**Current Session:** None"
        return f"**Current Session:** {self.current_session_id[:8]}..."

    def _get_session_choices(self) -> List[str]:
        """Get list of available sessions."""
        if not self.memory_manager:
            return []

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            sessions = loop.run_until_complete(
                self.memory_manager.list_sessions(limit=50)
            )
            loop.close()
            return [s.session_id for s in sessions]
        except:
            return []

    def _get_session_details(self) -> List[List[str]]:
        """Get session details for dataframe."""
        if not self.memory_manager:
            return []

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            sessions = loop.run_until_complete(
                self.memory_manager.list_sessions(limit=20)
            )
            loop.close()

            data = []
            for session in sessions:
                msg_count_task = loop.run_until_complete(
                    self.memory_manager.get_message_count(session.session_id)
                )
                data.append([
                    session.session_id[:12] + "...",
                    session.created_at.strftime("%Y-%m-%d %H:%M"),
                    session.last_active.strftime("%Y-%m-%d %H:%M"),
                    str(msg_count_task)
                ])

            return data
        except Exception as e:
            return [[f"Error: {str(e)}", "", "", ""]]

    def _get_memory_stats(self) -> str:
        """Get memory statistics."""
        if not self.memory_manager or not self.current_session_id:
            return "No active session"

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            summary = loop.run_until_complete(
                self.memory_manager.get_session_summary(self.current_session_id)
            )
            loop.close()

            if not summary:
                return "Session not found"

            return f"""#### Session Statistics
- **Session ID:** {summary['session_id'][:12]}...
- **Created:** {summary['created_at'].strftime("%Y-%m-%d %H:%M:%S")}
- **Last Active:** {summary['last_active'].strftime("%Y-%m-%d %H:%M:%S")}
- **Total Messages:** {summary['message_count']}
"""
        except Exception as e:
            return f"Error: {str(e)}"

    def _create_visualization_tab(self):
        """Create the agent interaction visualization tab."""
        gr.Markdown("### Visualize agent interactions and message flows")

        refresh_viz_btn = gr.Button("Refresh Visualization", variant="primary")

        network_plot = gr.Plot(label="Agent Interaction Network")
        timeline_plot = gr.Plot(label="Message Timeline")

        def create_network_visualization():
            """Create a network graph of agent interactions."""
            messages = self.orchestrator.get_message_history()

            if not messages:
                # Empty plot
                fig = go.Figure()
                fig.add_annotation(
                    text="No messages yet. Send some messages to see the network!",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=16)
                )
                return fig

            # Build network from messages
            nodes = set()
            edges = []
            edge_counts = {}

            for msg in messages:
                nodes.add(msg.sender)
                if msg.recipient:
                    nodes.add(msg.recipient)
                    edge_key = (msg.sender, msg.recipient)
                    edge_counts[edge_key] = edge_counts.get(edge_key, 0) + 1
                    edges.append(edge_key)

            # Create node positions in a circle
            import math
            node_list = list(nodes)
            n = len(node_list)
            node_pos = {}
            for i, node in enumerate(node_list):
                angle = 2 * math.pi * i / n
                node_pos[node] = (math.cos(angle), math.sin(angle))

            # Create edge traces
            edge_traces = []
            for (src, dst), count in edge_counts.items():
                x0, y0 = node_pos[src]
                x1, y1 = node_pos[dst]

                edge_trace = go.Scatter(
                    x=[x0, x1, None],
                    y=[y0, y1, None],
                    mode='lines',
                    line=dict(width=min(count, 10), color='#888'),
                    hoverinfo='text',
                    text=f"{src} → {dst}: {count} messages",
                    showlegend=False
                )
                edge_traces.append(edge_trace)

            # Create node trace
            node_x = [node_pos[node][0] for node in node_list]
            node_y = [node_pos[node][1] for node in node_list]

            node_trace = go.Scatter(
                x=node_x,
                y=node_y,
                mode='markers+text',
                text=node_list,
                textposition="top center",
                marker=dict(
                    size=30,
                    color='lightblue',
                    line=dict(width=2, color='darkblue')
                ),
                hoverinfo='text',
                showlegend=False
            )

            # Create figure
            fig = go.Figure(data=edge_traces + [node_trace])
            fig.update_layout(
                title="Agent Interaction Network",
                showlegend=False,
                hovermode='closest',
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                height=500
            )

            return fig

        def create_timeline_visualization():
            """Create a timeline of messages."""
            messages = self.orchestrator.get_message_history()

            if not messages:
                fig = go.Figure()
                fig.add_annotation(
                    text="No messages yet.",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False
                )
                return fig

            # Prepare data
            data = {
                'timestamp': [msg.timestamp for msg in messages],
                'sender': [msg.sender for msg in messages],
                'type': [msg.type.value for msg in messages],
                'content': [msg.content[:50] + "..." if len(msg.content) > 50 else msg.content for msg in messages]
            }

            df = pd.DataFrame(data)

            # Create scatter plot
            fig = go.Figure()

            for msg_type in df['type'].unique():
                type_df = df[df['type'] == msg_type]
                fig.add_trace(go.Scatter(
                    x=type_df['timestamp'],
                    y=[msg_type] * len(type_df),
                    mode='markers',
                    name=msg_type,
                    marker=dict(size=10),
                    text=type_df['sender'] + ": " + type_df['content'],
                    hoverinfo='text'
                ))

            fig.update_layout(
                title="Message Timeline",
                xaxis_title="Time",
                yaxis_title="Message Type",
                height=400,
                hovermode='closest'
            )

            return fig

        def refresh_visualizations():
            """Refresh both visualizations."""
            return create_network_visualization(), create_timeline_visualization()

        refresh_viz_btn.click(
            refresh_visualizations,
            outputs=[network_plot, timeline_plot]
        )

    def _get_agent_list(self) -> str:
        """Get a formatted list of registered agents."""
        if not self.orchestrator.agents:
            return "No agents registered yet."

        lines = []
        for agent_id, agent in self.orchestrator.agents.items():
            lines.append(f"• {agent_id} ({agent.config.role})")

        return "\n".join(lines)

    def _get_agent_names(self) -> List[str]:
        """Get a list of agent names."""
        return list(self.orchestrator.agents.keys())

    def _get_agents_dataframe(self) -> List[List[str]]:
        """Get agent data for the dataframe."""
        data = []
        for agent_id, agent in self.orchestrator.agents.items():
            agent_type = "LLM Agent" if isinstance(agent, LLMAgent) else "Basic Agent"
            data.append([agent_id, agent.config.role, agent_type])
        return data

    def launch(self, share: bool = False, **kwargs):
        """
        Launch the web interface.

        Args:
            share: Whether to create a public share link
            **kwargs: Additional arguments for gradio.launch()
        """
        interface = self.create_interface()
        # Add default theme if not specified
        if 'theme' not in kwargs:
            kwargs['theme'] = gr.themes.Soft()
        interface.launch(share=share, **kwargs)
