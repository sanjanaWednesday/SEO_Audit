"""
Slack Routes for SEO Audit System
Handles Slack slash commands and interactions
"""
import asyncio
import os
import logging
import uuid
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from slack_sdk.web import WebClient
from slack_sdk.signature import SignatureVerifier
from slack_sdk.errors import SlackApiError
import json

from services.seo_audit_orchestrator import SEOAuditOrchestrator
from services.sheets_service_personal import GoogleSheetsServicePersonal
from services.claude_service import ClaudeService
from services.mongo_service import MongoService
from models.workflow_excecution import WorkflowStatus

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize services
slack_client = WebClient(token=os.getenv('SLACK_BOT_TOKEN'))
signature_verifier = SignatureVerifier(os.getenv('SLACK_SIGNING_SECRET'))
sheets_service = GoogleSheetsServicePersonal()
claude_service = ClaudeService()
mongo_service = MongoService()

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
        
        # Get user email
        user_email = await _get_user_email(user_id)
        
        # Send initial acknowledgment
        initial_response = JSONResponse({
            "response_type": "in_channel",
            "text": f"🔍 Starting SEO audit for *{target_domain}*...\nThis may take 5-10 minutes. I'll notify you when complete!"
        })
        
        # Start audit in background
        asyncio.create_task(_run_audit_async(target_domain, main_topic, channel_id, user_id, user_email))
        
        return initial_response
        
    except Exception as e:
        logger.error(f"Error handling SEO audit command: {e}")
        return JSONResponse({
            "response_type": "ephemeral",
            "text": f"❌ Error: {str(e)}"
        })

async def _run_audit_async(target_domain: str, main_topic: str, channel_id: str, user_id: str, user_email: str = None):
    """Run the SEO audit asynchronously and send results to Slack"""
    execution_id = str(uuid.uuid4())
    
    try:
        # Create workflow execution in MongoDB
        logger.info(f"Creating workflow execution: {execution_id}")
        mongo_service.create_workflow_execution(
            execution_id=execution_id,
            site_url=f"https://{target_domain}",
            slack_user_id=user_id,
            user_email=user_email,
            main_topic=main_topic
        )
        
        # Update status to in progress
        mongo_service.update_workflow_status(execution_id, WorkflowStatus.IN_PROGRESS)
        
        # Initialize orchestrator with MongoDB service
        orchestrator = SEOAuditOrchestrator(mongo_service=mongo_service, execution_id=execution_id)
        
        # Run complete audit
        audit_results = await orchestrator.run_complete_audit(target_domain, main_topic)
        
        if audit_results.get('error'):
            mongo_service.update_workflow_status(
                execution_id, 
                WorkflowStatus.FAILED,
                error_message=audit_results['error']
            )
            await _send_slack_message(
                channel_id,
                f"❌ SEO audit failed for *{target_domain}*: {audit_results['error']}"
            )
            return
        
        # Store audit results in MongoDB
        mongo_service.store_audit_results(execution_id, target_domain, audit_results)
        
        # Send to Claude for analysis
        logger.info("Sending to Claude for analysis...")
        claude_analysis = await claude_service.analyze_audit_results(audit_results, target_domain)
        
        # Create Google Sheets report (share with user email if available)
        logger.info("Creating Google Sheets report...")
        sheets_url = await sheets_service.create_seo_report(
            audit_results, 
            claude_analysis, 
            target_domain,
            user_email=user_email
        )
        
        # Update workflow with report URL
        mongo_service.update_workflow_report_url(execution_id, sheets_url)
        mongo_service.update_workflow_status(execution_id, WorkflowStatus.COMPLETED)
        
        # Send completion message with sheets link
        await _send_slack_message(
            channel_id,
            f"✅ SEO audit completed for *{target_domain}*!\n\n"
            f"📊 **Report**: {sheets_url}\n\n"
            f"🤖 **AI Analysis Summary**:\n{claude_analysis.get('summary', 'Analysis completed')}\n\n"
            f"_Execution ID: {execution_id}_"
        )
        
    except Exception as e:
        logger.error(f"Error in async audit: {e}")
        mongo_service.update_workflow_status(
            execution_id,
            WorkflowStatus.FAILED,
            error_message=str(e)
        )
        await _send_slack_message(
            channel_id,
            f"❌ SEO audit failed for *{target_domain}*: {str(e)}"
        )

async def _get_user_email(user_id: str) -> str:
    """Get user email from Slack user ID"""
    try:
        response = slack_client.users_info(user=user_id)
        if response['ok'] and response.get('user'):
            user_email = response['user'].get('profile', {}).get('email')
            if user_email:
                logger.info(f"Retrieved email for user {user_id}: {user_email}")
                return user_email
            else:
                logger.warning(f"No email found for user {user_id}")
                return None
        else:
            logger.error(f"Failed to get user info from Slack: {response}")
            return None
    except SlackApiError as e:
        logger.error(f"Slack API error getting user info: {e}")
        return None
    except Exception as e:
        logger.error(f"Error getting user email: {e}")
        return None

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
