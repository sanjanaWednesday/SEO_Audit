"""
MongoDB Service for SEO Audit System
Handles all database operations for workflow tracking and data storage
"""
from pymongo import MongoClient
from datetime import datetime
from typing import Dict, List, Optional
import os
import logging
from bson import ObjectId

from models.workflow_excecution import WorkflowExecution, WorkflowStatus
from models.competitor_analysis import CompetitorAnalysis
from models.execution_logs import ExecutionLogs, LogStatus

logger = logging.getLogger(__name__)

class MongoService:
    def __init__(self):
        self.client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017/"))
        self.db = self.client.get_database("seo_audit")
        
        # Collections
        self.workflow_executions = self.db.workflow_executions
        self.competitor_analysis = self.db.competitor_analysis
        self.execution_logs = self.db.execution_logs
        self.audit_results = self.db.audit_results
        
    def create_workflow_execution(
        self, 
        execution_id: str,
        site_url: str,
        slack_user_id: str,
        user_email: Optional[str] = None,
        main_topic: Optional[str] = None
    ) -> str:
        """Create a new workflow execution record"""
        try:
            workflow_doc = {
                "execution_id": execution_id,
                "site_url": site_url,
                "slack_user_id": slack_user_id,
                "user_email": user_email,
                "status": WorkflowStatus.STARTED.value,
                "started_at": datetime.utcnow(),
                "main_topic": main_topic,
                "completed_at": None,
                "report_url": None,
                "top_competitors": None,
                "error_message": None
            }
            
            result = self.workflow_executions.insert_one(workflow_doc)
            logger.info(f"Created workflow execution: {execution_id}")
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Failed to create workflow execution: {e}")
            raise
    
    def update_workflow_status(
        self,
        execution_id: str,
        status: WorkflowStatus,
        error_message: Optional[str] = None
    ):
        """Update workflow execution status"""
        try:
            update_data = {
                "status": status.value,
                "updated_at": datetime.utcnow()
            }
            
            if status == WorkflowStatus.COMPLETED or status == WorkflowStatus.FAILED:
                update_data["completed_at"] = datetime.utcnow()
            
            if error_message:
                update_data["error_message"] = error_message
            
            self.workflow_executions.update_one(
                {"execution_id": execution_id},
                {"$set": update_data}
            )
            logger.info(f"Updated workflow {execution_id} status to {status.value}")
            
        except Exception as e:
            logger.error(f"Failed to update workflow status: {e}")
            raise
    
    def update_workflow_competitors(
        self,
        execution_id: str,
        competitors: List[str]
    ):
        """Update workflow with discovered competitors"""
        try:
            self.workflow_executions.update_one(
                {"execution_id": execution_id},
                {"$set": {
                    "top_competitors": competitors,
                    "updated_at": datetime.utcnow()
                }}
            )
            logger.info(f"Updated workflow {execution_id} with {len(competitors)} competitors")
            
        except Exception as e:
            logger.error(f"Failed to update workflow competitors: {e}")
            raise
    
    def update_workflow_report_url(
        self,
        execution_id: str,
        report_url: str
    ):
        """Update workflow with Google Sheets report URL"""
        try:
            self.workflow_executions.update_one(
                {"execution_id": execution_id},
                {"$set": {
                    "report_url": report_url,
                    "updated_at": datetime.utcnow()
                }}
            )
            logger.info(f"Updated workflow {execution_id} with report URL")
            
        except Exception as e:
            logger.error(f"Failed to update workflow report URL: {e}")
            raise
    
    def get_workflow_execution(self, execution_id: str) -> Optional[Dict]:
        """Get workflow execution by ID"""
        try:
            workflow = self.workflow_executions.find_one({"execution_id": execution_id})
            if workflow:
                workflow['_id'] = str(workflow['_id'])
            return workflow
            
        except Exception as e:
            logger.error(f"Failed to get workflow execution: {e}")
            return None
    
    def store_competitor_analysis(
        self,
        execution_id: str,
        competitor_domain: str,
        analysis_data: Dict
    ) -> str:
        """Store competitor analysis results"""
        try:
            competitor_doc = {
                "execution_id": execution_id,
                "competitor_domain": competitor_domain,
                "analysis_data": analysis_data,
                "created_at": datetime.utcnow(),
                "keyword_ranking": analysis_data.get('ranked_keywords', []),
                "domain_metrics": analysis_data.get('domain_metrics', {}),
                "backlinks_summary": analysis_data.get('backlinks_summary', {})
            }
            
            result = self.competitor_analysis.insert_one(competitor_doc)
            logger.info(f"Stored competitor analysis for {competitor_domain}")
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Failed to store competitor analysis: {e}")
            raise
    
    def get_competitor_analysis(self, execution_id: str) -> List[Dict]:
        """Get all competitor analysis for a workflow execution"""
        try:
            competitors = list(self.competitor_analysis.find({"execution_id": execution_id}))
            for comp in competitors:
                comp['_id'] = str(comp['_id'])
            return competitors
            
        except Exception as e:
            logger.error(f"Failed to get competitor analysis: {e}")
            return []
    
    def store_audit_results(
        self,
        execution_id: str,
        site_url: str,
        audit_data: Dict
    ) -> str:
        """Store complete audit results"""
        try:
            audit_doc = {
                "execution_id": execution_id,
                "site_url": site_url,
                "audit_data": audit_data,
                "created_at": datetime.utcnow(),
                "baseline": audit_data.get('baseline', {}),
                "competitors": audit_data.get('competitors', []),
                "opportunities": audit_data.get('opportunities', {}),
                "prioritized_keywords": audit_data.get('prioritized_keywords', {}),
                "serp_analysis": audit_data.get('serp_analysis', {})
            }
            
            result = self.audit_results.insert_one(audit_doc)
            logger.info(f"Stored audit results for {site_url}")
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Failed to store audit results: {e}")
            raise
    
    def get_audit_results(self, execution_id: str) -> Optional[Dict]:
        """Get audit results by execution ID"""
        try:
            results = self.audit_results.find_one({"execution_id": execution_id})
            if results:
                results['_id'] = str(results['_id'])
            return results
            
        except Exception as e:
            logger.error(f"Failed to get audit results: {e}")
            return None
    
    def log_execution_step(
        self,
        execution_id: str,
        step_name: str,
        status: LogStatus,
        execution_time: int = 0,
        error_message: Optional[str] = None
    ) -> str:
        """Log an execution step"""
        try:
            log_doc = {
                "log_id": f"{execution_id}_{step_name}_{datetime.utcnow().timestamp()}",
                "execution_id": execution_id,
                "step_name": step_name,
                "status": status.value,
                "execution_time": execution_time,
                "timestamp": datetime.utcnow(),
                "error_message": error_message
            }
            
            result = self.execution_logs.insert_one(log_doc)
            logger.debug(f"Logged execution step: {step_name} - {status.value}")
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Failed to log execution step: {e}")
            raise
    
    def get_execution_logs(self, execution_id: str) -> List[Dict]:
        """Get all execution logs for a workflow"""
        try:
            logs = list(self.execution_logs.find({"execution_id": execution_id}).sort("timestamp", 1))
            for log in logs:
                log['_id'] = str(log['_id'])
            return logs
            
        except Exception as e:
            logger.error(f"Failed to get execution logs: {e}")
            return []
    
    def get_user_workflows(self, slack_user_id: str, limit: int = 10) -> List[Dict]:
        """Get recent workflow executions for a user"""
        try:
            workflows = list(
                self.workflow_executions
                .find({"slack_user_id": slack_user_id})
                .sort("started_at", -1)
                .limit(limit)
            )
            for workflow in workflows:
                workflow['_id'] = str(workflow['_id'])
            return workflows
            
        except Exception as e:
            logger.error(f"Failed to get user workflows: {e}")
            return []
