"""
Slack Routes for SEO Audit System
Handles Slack slash commands and interactions
"""
import asyncio
import os
import logging
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from slack_sdk.web import WebClient
from slack_sdk.signature import SignatureVerifier
import json

from ..services.seo_audit_orchestrator import SEOAuditOrchestrator
from ..services.sheets_service import GoogleSheetsService
from ..services.claude_service import ClaudeService

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize services
slack_client = WebClient(token=os.getenv('SLACK_BOT_TOKEN'))
signature_verifier = SignatureVerifier(os.getenv('SLACK_SIGNING_SECRET'))
sheets_service = GoogleSheetsService()
claude_service = ClaudeService()

@router.post("/slack/seo-audit")
async def handle_seo_audit_command(request: Request):
    """
    Handle /seo-audit slash command from Slack
    Expected format: /seo-audit website.com [main-topic]
    """
    try:
        # Parse form data
        form_data = await request.form()
        text = form_data.get('text', '').strip()
        user_id = form_data.get('user_id')
        channel_id = form_data.get('channel_id')
        
        # Parse command arguments
        args = text.split()
        if not args:
            return JSONResponse({
                "response_type": "ephemeral",
                "text": "❌ Please provide a website URL. Usage: `/seo-audit website.com [main-topic]`"
            })
        
        target_domain = args[0]
        main_topic = args[1] if len(args) > 1 else None
        
        # Validate domain format
        if not _is_valid_domain(target_domain):
            return JSONResponse({
                "response_type": "ephemeral",
                "text": "❌ Invalid domain format. Please use format like 'example.com'"
            })
        
        # Send initial acknowledgment
        initial_response = JSONResponse({
            "response_type": "in_channel",
            "text": f"🔍 Starting SEO audit for *{target_domain}*...\nThis may take 5-10 minutes. I'll notify you when complete!"
        })
        
        # Start audit in background
        asyncio.create_task(_run_audit_async(target_domain, main_topic, channel_id, user_id))
        
        return initial_response
        
    except Exception as e:
        logger.error(f"Error handling SEO audit command: {e}")
        return JSONResponse({
            "response_type": "ephemeral",
            "text": f"❌ Error: {str(e)}"
        })

async def _run_audit_async(target_domain: str, main_topic: str, channel_id: str, user_id: str):
    """Run the SEO audit asynchronously and send results to Slack"""
    try:
        # Initialize orchestrator
        orchestrator = SEOAuditOrchestrator()
        
        # Run complete audit
        audit_results = await orchestrator.run_complete_audit(target_domain, main_topic)
        
        if audit_results.get('error'):
            await _send_slack_message(
                channel_id,
                f"❌ SEO audit failed for *{target_domain}*: {audit_results['error']}"
            )
            return
        
        # Send to Claude for analysis
        claude_analysis = await claude_service.analyze_audit_results(audit_results, target_domain)
        
        # Create Google Sheets report
        sheets_url = await sheets_service.create_seo_report(audit_results, claude_analysis, target_domain)
        
        # Send completion message with sheets link
        await _send_slack_message(
            channel_id,
            f"✅ SEO audit completed for *{target_domain}*!\n\n"
            f"📊 **Report**: {sheets_url}\n\n"
            f"🤖 **AI Analysis Summary**:\n{claude_analysis.get('summary', 'Analysis completed')}"
        )
        
    except Exception as e:
        logger.error(f"Error in async audit: {e}")
        await _send_slack_message(
            channel_id,
            f"❌ SEO audit failed for *{target_domain}*: {str(e)}"
        )

async def _send_slack_message(channel_id: str, text: str):
    """Send message to Slack channel"""
    try:
        slack_client.chat_postMessage(
            channel=channel_id,
            text=text
        )
    except Exception as e:
        logger.error(f"Failed to send Slack message: {e}")

def _is_valid_domain(domain: str) -> bool:
    """Basic domain validation"""
    if not domain or '.' not in domain:
        return False
    
    # Remove protocol if present
    domain = domain.replace('https://', '').replace('http://', '').replace('www.', '')
    
    # Basic validation
    parts = domain.split('.')
    return len(parts) >= 2 and all(part for part in parts)

@router.post("/slack/interactive")
async def handle_slack_interactions(request: Request):
    """Handle Slack interactive components (buttons, modals, etc.)"""
    try:
        form_data = await request.form()
        payload = json.loads(form_data.get('payload', '{}'))
        
        # Handle different interaction types
        if payload.get('type') == 'block_actions':
            return _handle_block_actions(payload)
        elif payload.get('type') == 'view_submission':
            return _handle_view_submission(payload)
        
        return JSONResponse({"text": "Interaction handled"})
        
    except Exception as e:
        logger.error(f"Error handling Slack interaction: {e}")
        return JSONResponse({"text": "Error processing interaction"})

def _handle_block_actions(payload: dict) -> JSONResponse:
    """Handle button clicks and other block actions"""
    # Implementation for handling button clicks, etc.
    return JSONResponse({"text": "Action processed"})

def _handle_view_submission(payload: dict) -> JSONResponse:
    """Handle modal submissions"""
    # Implementation for handling modal submissions
    return JSONResponse({"text": "Submission processed"})
