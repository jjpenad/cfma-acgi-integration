import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from src.models import SchedulingConfig
from src.services.integration_service import IntegrationService
import threading
import time

logger = logging.getLogger(__name__)

class SchedulerService:
    def __init__(self):
        try:
            self.scheduler = BackgroundScheduler()
            self.integration_service = IntegrationService()
            self.is_running = False
            logger.info("SchedulerService initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing SchedulerService: {str(e)}")
            raise
        self._lock = threading.Lock()
        
    def start(self):
        """Start the scheduler service"""
        try:
            with self._lock:
                if not self.is_running:
                    self.scheduler.start()
                    self.is_running = True
                    logger.info("Scheduler service started")
                    
                    # Load and apply existing configuration
                    self._load_and_apply_config()
                    
        except Exception as e:
            logger.error(f"Error starting scheduler service: {str(e)}")
    
    def stop(self):
        """Stop the scheduler service"""
        try:
            with self._lock:
                if self.is_running:
                    self.scheduler.shutdown()
                    self.is_running = False
                    logger.info("Scheduler service stopped")
        except Exception as e:
            logger.error(f"Error stopping scheduler service: {str(e)}")
    
    def _load_and_apply_config(self):
        """Load scheduling configuration and apply it to the scheduler"""
        try:
            config = SchedulingConfig.get_config()
            logger.info(f"Loading scheduling config: {config}")
            
            if config and config.get('enabled'):
                logger.info("Found enabled config, applying to scheduler")
                self._apply_config(config)
            else:
                logger.info("No active scheduling configuration found")
        except Exception as e:
            logger.error(f"Error loading scheduling configuration: {str(e)}")
    
    def _apply_config(self, config):
        """Apply scheduling configuration to the scheduler"""
        try:
            # Remove any existing jobs
            self.scheduler.remove_all_jobs()
            logger.info("Removed all existing jobs")
            
            # Add new job based on configuration
            frequency_minutes = config.get('frequency', 15)
            job_id = 'acgi_hubspot_sync'
            
            logger.info(f"Adding job with frequency: {frequency_minutes} minutes")
            
            self.scheduler.add_job(
                func=self._run_sync_job,
                trigger=IntervalTrigger(minutes=frequency_minutes),
                id=job_id,
                name='ACGI to HubSpot Sync',
                replace_existing=True,
                args=[config]
            )
            
            logger.info(f"Scheduled sync job to run every {frequency_minutes} minutes")
            
            # Verify job was added
            jobs = self.scheduler.get_jobs()
            logger.info(f"Current jobs after adding: {len(jobs)}")
            
        except Exception as e:
            logger.error(f"Error applying scheduling configuration: {str(e)}")
    
    def _run_sync_job(self, config):
        """Run the synchronization job"""
        try:
            from datetime import datetime
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"=== SCHEDULED SYNC JOB STARTED at {current_time} ===")
            logger.info(f"Sync job configuration: {config}")
            
            # Run the sync
            result = self.integration_service.run_sync(config)
            
            if result.get('success'):
                # Update last sync timestamp
                SchedulingConfig.update_last_sync()
                logger.info(f"=== SCHEDULED SYNC JOB COMPLETED SUCCESSFULLY at {current_time} ===")
                logger.info(f"Results: Contacts: {result.get('contacts_synced', 0)}, "
                          f"Memberships: {result.get('memberships_synced', 0)}")
                logger.info(f"Full result: {result}")
            else:
                logger.error(f"=== SCHEDULED SYNC JOB FAILED at {current_time} ===")
                logger.error(f"Error: {result.get('error', 'Unknown error')}")
                logger.error(f"Full result: {result}")
                
        except Exception as e:
            from datetime import datetime
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.error(f"=== SCHEDULED SYNC JOB EXCEPTION at {current_time} ===")
            logger.error(f"Exception: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
                
        except Exception as e:
            logger.error(f"Error in scheduled sync job: {str(e)}")
    
    def update_config(self, config_data):
        """Update the scheduling configuration"""
        try:
            logger.info(f"Updating config with data: {config_data}")
            
            # If customer_ids is empty, preserve the existing ones
            if not config_data.get('customer_ids', '').strip():
                existing_config = SchedulingConfig.get_config()
                if existing_config and existing_config.get('customer_ids'):
                    config_data['customer_ids'] = existing_config['customer_ids']
            
            # Save the configuration
            success = SchedulingConfig.save_config(config_data)
            if not success:
                logger.error("Failed to save scheduling configuration")
                return False
            
            # Apply the new configuration if enabled
            if config_data.get('enabled'):
                self._apply_config(config_data)
                logger.info("Scheduling configuration updated and applied")
            else:
                # Remove all jobs if disabled
                self.scheduler.remove_all_jobs()
                logger.info("Scheduling disabled - all jobs removed")
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating scheduling configuration: {str(e)}")
            return False
    
    def get_status(self):
        """Get the current status of the scheduler"""
        try:
            config = SchedulingConfig.get_config()
            jobs = self.scheduler.get_jobs()
            
            logger.info(f"Scheduler status - config: {config}")
            logger.info(f"Scheduler status - jobs: {len(jobs)}")
            logger.info(f"Scheduler status - is_running: {self.is_running}")
            
            status = {
                'is_running': self.is_running,
                'has_config': config is not None,
                'enabled': config.get('enabled', False) if config else False,
                'frequency': config.get('frequency', None) if config else None,
                'last_sync': config.get('last_sync', None) if config else None,
                'active_jobs': len(jobs),
                'next_run': None
            }
            
            logger.info(f"Scheduler status - final status: {status}")
            
            # Debug: Try to calculate next run time manually
            if jobs:
                next_job = jobs[0]
                logger.info(f"Debug - Job ID: {next_job.id}")
                logger.info(f"Debug - Job Name: {next_job.name}")
                logger.info(f"Debug - Job Trigger: {next_job.trigger}")
                logger.info(f"Debug - Job Trigger Type: {type(next_job.trigger)}")
                
                # Try to get next run time using different methods
                try:
                    # Method 1: Direct attribute
                    if hasattr(next_job, 'next_run_time'):
                        logger.info(f"Debug - next_run_time attribute: {next_job.next_run_time}")
                    
                    # Method 2: Trigger method
                    if hasattr(next_job.trigger, 'next_fire_time'):
                        logger.info(f"Debug - trigger.next_fire_time: {next_job.trigger.next_fire_time}")
                    
                    # Method 3: Calculate manually for interval trigger
                    if hasattr(next_job.trigger, 'interval'):
                        from datetime import datetime, timedelta
                        now = datetime.now()
                        interval_seconds = next_job.trigger.interval.total_seconds()
                        next_run = now + timedelta(seconds=interval_seconds)
                        logger.info(f"Debug - Calculated next run: {next_run}")
                        status['next_run'] = next_run.isoformat()
                        
                except Exception as e:
                    logger.info(f"Debug - Error calculating next run time: {e}")
            
            # Get next run time if there are active jobs
            if jobs:
                next_job = jobs[0]
                logger.info(f"Next job: {next_job.id}, trigger: {next_job.trigger}")
                
                # Use the correct method to get next run time
                try:
                    next_run_time = next_job.next_run_time
                    logger.info(f"Using next_run_time: {next_run_time}")
                    status['next_run'] = next_run_time.isoformat() if next_run_time else None
                except AttributeError:
                    logger.info("next_run_time not available, trying trigger.next_fire_time")
                    # Fallback for newer APScheduler versions
                    try:
                        next_run_time = next_job.trigger.next_fire_time
                        logger.info(f"Using trigger.next_fire_time: {next_run_time}")
                        status['next_run'] = next_run_time.isoformat() if next_run_time else None
                    except (AttributeError, TypeError) as e:
                        logger.info(f"trigger.next_fire_time also failed: {e}")
                        # Try to get next run time from trigger
                        try:
                            if hasattr(next_job.trigger, 'next_fire_time'):
                                next_run_time = next_job.trigger.next_fire_time
                                status['next_run'] = next_run_time.isoformat() if next_run_time else None
                            else:
                                logger.info("No next_fire_time method found on trigger")
                                status['next_run'] = None
                        except Exception as e2:
                            logger.info(f"All attempts to get next run time failed: {e2}")
                            status['next_run'] = None
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting scheduler status: {str(e)}")
            return {
                'is_running': False,
                'has_config': False,
                'enabled': False,
                'frequency': None,
                'last_sync': None,
                'active_jobs': 0,
                'next_run': None,
                'error': str(e)
            }
    
    def run_manual_sync(self):
        """Run a manual synchronization"""
        try:
            logger.info("Attempting to get scheduling configuration")
            config = SchedulingConfig.get_config()
            logger.info(f"Retrieved config: {config}")
            
            if not config:
                return {'success': False, 'error': 'No scheduling configuration found'}
            
            # For manual sync, we don't require scheduling to be enabled
            # Just check if we have the required configuration
            if not config.get('customer_ids', '').strip():
                return {'success': False, 'error': 'No customer IDs configured for sync'}
            
            logger.info("Starting manual sync")
            logger.info(f"Manual sync configuration: {config}")
            result = self.integration_service.run_sync(config)
            
            if result.get('success'):
                SchedulingConfig.update_last_sync()
                logger.info("Manual sync completed successfully")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in manual sync: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {'success': False, 'error': str(e)}

# Global scheduler instance
scheduler_service = SchedulerService() 