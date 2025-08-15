import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from src.models import SchedulingConfig
from src.services.integration_service import IntegrationService
import threading
import time
import concurrent.futures
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class SchedulerService:
    def __init__(self):
        try:
            self.scheduler = BackgroundScheduler()
            self.integration_service = IntegrationService()
            self.is_running = False
            # Thread pool for concurrent object syncing
            self.thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)
            logger.info("SchedulerService initialized successfully with thread pool")
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
                    # Shutdown thread pool
                    self.thread_pool.shutdown(wait=True)
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
        """Run the synchronization job with multi-threaded object syncing"""
        try:
            from datetime import datetime
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"=== SCHEDULED SYNC JOB STARTED at {current_time} ===")
            logger.info(f"Sync job configuration: {config}")
            
            # Run the sync with multi-threading
            result = self._run_multi_threaded_sync(config)
            
            if result.get('success'):
                # Update last sync timestamp
                SchedulingConfig.update_last_sync()
                logger.info(f"=== SCHEDULED SYNC JOB COMPLETED SUCCESSFULLY at {current_time} ===")
                logger.info(f"Results: Contacts: {result.get('contacts_synced', 0)}, "
                          f"Memberships: {result.get('memberships_synced', 0)}, "
                          f"Orders: {result.get('orders_synced', 0)}, "
                          f"Events: {result.get('events_synced', 0)}")
                logger.info(f"Full result: {result}")
            else:
                logger.error(f"=== SCHEDULED SYNC JOB FAILED at {current_time} ===")
                logger.error(f"Error: {result.get('error', 'Unknown error')}")
                logger.error(f"Full result: {result}")
                
        except Exception as e:
            from datetime import datetime
            current_time = datetime.now().strftime("%Y-%M-%d %H:%M:%S")
            logger.error(f"=== SCHEDULED SYNC JOB EXCEPTION at {current_time} ===")
            logger.error(f"Exception: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    def _run_multi_threaded_sync(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Run synchronization using multiple threads for each object type"""
        try:
            logger.info("Starting multi-threaded synchronization")
            
            # Get customer IDs
            customer_ids = self.integration_service._parse_customer_ids(config.get('customer_ids', ''))
            if not customer_ids:
                return {'success': False, 'error': 'No valid customer IDs provided'}
            
            # Prepare sync tasks for each object type
            sync_tasks = []
            
            # Contacts sync task
            if config.get('sync_contacts', True):
                sync_tasks.append(('contacts', self._sync_contacts_thread, customer_ids, config))
            
            # Memberships sync task
            if config.get('sync_memberships', True):
                sync_tasks.append(('memberships', self._sync_memberships_thread, customer_ids, config))
            
            # Orders sync task
            if config.get('sync_orders', True):
                sync_tasks.append(('orders', self._sync_orders_thread, customer_ids, config))
            
            # Events sync task
            if config.get('sync_events', True):
                sync_tasks.append(('events', self._sync_events_thread, customer_ids, config))
            
            if not sync_tasks:
                return {'success': False, 'error': 'No sync tasks enabled'}
            
            logger.info(f"Starting {len(sync_tasks)} sync threads")
            
            # Submit all tasks to thread pool
            future_to_task = {}
            for task_name, task_func, task_customer_ids, task_config in sync_tasks:
                future = self.thread_pool.submit(task_func, task_customer_ids, task_config)
                future_to_task[future] = task_name
            
            # Collect results
            results = {
                'success': True,
                'total_customers': len(customer_ids),
                'contacts_synced': 0,
                'memberships_synced': 0,
                'orders_synced': 0,
                'events_synced': 0,
                'errors': [],
                'thread_results': {}
            }
            
            # Wait for all tasks to complete
            for future in concurrent.futures.as_completed(future_to_task):
                task_name = future_to_task[future]
                try:
                    task_result = future.result()
                    logger.info(f"Thread {task_name} completed: {task_result}")
                    
                    if task_result.get('success'):
                        results[f'{task_name}_synced'] = task_result.get('total_processed', 0)
                        results['thread_results'][task_name] = task_result
                    else:
                        results['errors'].append(f"{task_name}: {task_result.get('error', 'Unknown error')}")
                        results['thread_results'][task_name] = task_result
                        
                except Exception as e:
                    error_msg = f"Thread {task_name} failed with exception: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
                    results['thread_results'][task_name] = {'success': False, 'error': str(e)}
            
            logger.info(f"Multi-threaded sync completed. Results: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Error in multi-threaded sync: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _sync_contacts_thread(self, customer_ids: List[str], config: Dict[str, Any]) -> Dict[str, Any]:
        """Sync contacts in a separate thread with dedicated HubSpot client"""
        try:
            logger.info(f"Starting contacts sync thread for {len(customer_ids)} customers")
            
            # Create dedicated integration service instance for this thread
            thread_integration_service = IntegrationService()
            
            # Run contacts sync
            result = thread_integration_service._sync_contacts_batch(customer_ids, config)
            logger.info(f"Contacts sync thread completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error in contacts sync thread: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _sync_memberships_thread(self, customer_ids: List[str], config: Dict[str, Any]) -> Dict[str, Any]:
        """Sync memberships in a separate thread with dedicated HubSpot client"""
        try:
            logger.info(f"Starting memberships sync thread for {len(customer_ids)} customers")
            
            # Create dedicated integration service instance for this thread
            thread_integration_service = IntegrationService()
            
            # Run memberships sync
            result = thread_integration_service._sync_memberships_batch(customer_ids, config)
            logger.info(f"Memberships sync thread completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error in memberships sync thread: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _sync_orders_thread(self, customer_ids: List[str], config: Dict[str, Any]) -> Dict[str, Any]:
        """Sync orders in a separate thread with dedicated HubSpot client"""
        try:
            logger.info(f"Starting orders sync thread for {len(customer_ids)} customers")
            
            # Create dedicated integration service instance for this thread
            thread_integration_service = IntegrationService()
            
            # Run orders sync
            result = thread_integration_service._sync_orders_batch(customer_ids, config)
            logger.info(f"Orders sync thread completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error in orders sync thread: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _sync_events_thread(self, customer_ids: List[str], config: Dict[str, Any]) -> Dict[str, Any]:
        """Sync events in a separate thread with dedicated HubSpot client"""
        try:
            logger.info(f"Starting events sync thread for {len(customer_ids)} customers")
            
            # Create dedicated integration service instance for this thread
            thread_integration_service = IntegrationService()
            
            # Run events sync
            result = thread_integration_service._sync_events_batch(customer_ids, config)
            logger.info(f"Events sync thread completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error in events sync thread: {str(e)}")
            return {'success': False, 'error': str(e)}
    
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
                'next_run': None,
                'thread_pool_size': self.thread_pool._max_workers
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
            
            # Use multi-threaded sync for manual sync as well
            result = self._run_multi_threaded_sync(config)
            
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