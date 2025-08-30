#!/usr/bin/env python3
"""
Demo script showing the enhanced sync progress reporting capabilities.

This script demonstrates how AI assistants can use the new sync tools to:
1. Start sync sessions with unique IDs
2. Monitor detailed progress with phases and activities  
3. Cancel running sync operations
4. View sync history

Usage:
    python demo_sync_progress.py
"""

import asyncio
import json
from src.d365fo_client.sync_models import SyncSession, SyncStatus, SyncPhase, SyncActivity
from src.d365fo_client.models import SyncStrategy

def demo_sync_models():
    """Demonstrate the enhanced sync models."""
    print("=== Enhanced Sync Models Demo ===\n")
    
    # Create a sample sync session
    session = SyncSession(
        global_version_id=12345,
        strategy=SyncStrategy.FULL,
        initiated_by="demo"
    )
    
    # Initialize phases for full sync
    phases = {
        SyncPhase.INITIALIZING: SyncActivity("Initializing", SyncStatus.COMPLETED, progress_percent=100.0),
        SyncPhase.VERSION_CHECK: SyncActivity("Version Check", SyncStatus.COMPLETED, progress_percent=100.0),
        SyncPhase.ENTITIES: SyncActivity("Entities", SyncStatus.RUNNING, progress_percent=45.0, items_processed=150, items_total=333),
        SyncPhase.SCHEMAS: SyncActivity("Schemas", SyncStatus.PENDING),
        SyncPhase.ENUMERATIONS: SyncActivity("Enumerations", SyncStatus.PENDING),
        SyncPhase.LABELS: SyncActivity("Labels", SyncStatus.PENDING),
        SyncPhase.INDEXING: SyncActivity("Indexing", SyncStatus.PENDING),
        SyncPhase.FINALIZING: SyncActivity("Finalizing", SyncStatus.PENDING)
    }
    
    session.phases = phases
    session.status = SyncStatus.RUNNING
    session.current_phase = SyncPhase.ENTITIES
    session.current_activity = "Processing entities"
    
    # Calculate overall progress
    session.progress_percent = session.get_overall_progress()
    
    print(f"Session ID: {session.session_id}")
    print(f"Status: {session.status}")
    print(f"Strategy: {session.strategy}")
    print(f"Overall Progress: {session.progress_percent:.1f}%")
    print(f"Current Phase: {session.current_phase}")
    print(f"Current Activity: {session.current_activity}")
    print(f"Initiated by: {session.initiated_by}")
    
    # Show current activity details
    current_activity = session.get_current_activity_detail()
    if current_activity:
        print(f"\nCurrent Activity Details:")
        print(f"  Name: {current_activity.name}")
        print(f"  Progress: {current_activity.progress_percent:.1f}%")
        print(f"  Items: {current_activity.items_processed}/{current_activity.items_total}")
    
    # Show phase breakdown
    print(f"\nPhase Breakdown:")
    for phase, activity in session.phases.items():
        status_icon = "✅" if activity.status == SyncStatus.COMPLETED else "🔄" if activity.status == SyncStatus.RUNNING else "⏳"
        print(f"  {status_icon} {activity.name}: {activity.status} ({activity.progress_percent:.0f}%)")
    
    print(f"\nJSON Representation:")
    print(json.dumps(session.to_dict(), indent=2))

def demo_mcp_tools():
    """Demonstrate the MCP tools interface."""
    print("\n\n=== MCP Tools Interface Demo ===\n")
    
    print("Available Sync Tools for AI Assistants:")
    print()
    
    tools = [
        {
            "name": "d365fo_start_sync",
            "description": "Start a metadata sync session",
            "example": {
                "strategy": "full",
                "global_version_id": None  # Auto-detect
            }
        },
        {
            "name": "d365fo_get_sync_progress", 
            "description": "Get detailed sync progress",
            "example": {
                "session_id": "abc123-def456-ghi789"
            }
        },
        {
            "name": "d365fo_cancel_sync",
            "description": "Cancel a running sync session",
            "example": {
                "session_id": "abc123-def456-ghi789"
            }
        },
        {
            "name": "d365fo_list_sync_sessions",
            "description": "List all active sync sessions",
            "example": {}
        },
        {
            "name": "d365fo_get_sync_history",
            "description": "Get sync session history",
            "example": {
                "limit": 20
            }
        }
    ]
    
    for tool in tools:
        print(f"Tool: {tool['name']}")
        print(f"Description: {tool['description']}")
        print(f"Example usage: {json.dumps(tool['example'], indent=2)}")
        print()

def demo_workflow():
    """Demonstrate a typical AI assistant workflow."""
    print("\n\n=== AI Assistant Workflow Demo ===\n")
    
    workflow_steps = [
        {
            "step": 1,
            "action": "Start Sync",
            "tool": "d365fo_start_sync",
            "description": "AI assistant starts a metadata sync session",
            "request": {"strategy": "full"},
            "response": {
                "success": True,
                "session_id": "abc123-def456-ghi789",
                "global_version_id": 12345,
                "strategy": "full",
                "message": "Sync session abc123-def456-ghi789 started successfully",
                "instructions": "Use d365fo_get_sync_progress with session_id 'abc123-def456-ghi789' to monitor progress"
            }
        },
        {
            "step": 2,
            "action": "Monitor Progress",
            "tool": "d365fo_get_sync_progress", 
            "description": "AI assistant checks sync progress periodically",
            "request": {"session_id": "abc123-def456-ghi789"},
            "response": {
                "success": True,
                "session": {
                    "session_id": "abc123-def456-ghi789",
                    "status": "running",
                    "progress_percent": 45.0,
                    "current_phase": "entities",
                    "current_activity": "Processing entities",
                    "estimated_remaining_seconds": 120
                },
                "summary": {
                    "status": "running",
                    "progress_percent": 45.0,
                    "is_running": True,
                    "can_cancel": True
                }
            }
        },
        {
            "step": 3,
            "action": "Check Completion",
            "tool": "d365fo_get_sync_progress",
            "description": "AI assistant checks if sync is completed",
            "request": {"session_id": "abc123-def456-ghi789"},
            "response": {
                "success": True,
                "session": {
                    "session_id": "abc123-def456-ghi789",
                    "status": "completed",
                    "progress_percent": 100.0,
                    "current_phase": "completed",
                    "result": {
                        "success": True,
                        "duration_ms": 45000,
                        "entity_count": 333,
                        "action_count": 1250,
                        "enumeration_count": 45,
                        "label_count": 2100
                    }
                }
            }
        }
    ]
    
    for step in workflow_steps:
        print(f"Step {step['step']}: {step['action']}")
        print(f"Description: {step['description']}")
        print(f"Tool: {step['tool']}")
        print(f"Request: {json.dumps(step['request'], indent=2)}")
        print(f"Response: {json.dumps(step['response'], indent=2)}")
        print()

def main():
    """Run the demo."""
    print("D365FO Enhanced Sync Progress Reporting Demo")
    print("=" * 50)
    
    demo_sync_models()
    demo_mcp_tools()
    demo_workflow()
    
    print("\n" + "=" * 50)
    print("Demo completed! The enhanced sync system provides:")
    print("✅ Session-based sync tracking with unique IDs")
    print("✅ Detailed progress reporting with phases and activities") 
    print("✅ Real-time progress updates and time estimation")
    print("✅ MCP tools for AI assistants to control sync operations")
    print("✅ Sync history and session management")
    print("✅ Backwards compatibility with existing sync manager")

if __name__ == "__main__":
    main()